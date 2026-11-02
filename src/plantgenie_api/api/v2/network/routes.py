import os

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from plantgenie_api.api.v2.network.coexpression import TooManyEdges
from plantgenie_api.api.v2.network.graph import (
    ExpressionProfiles,
    build_graph,
)
from plantgenie_api.api.v2.network.models import (
    GraphNode,
    GraphRequest,
    GraphResponse,
)
from plantgenie_api.dependencies import AccountDep, Neo4jDep, SqliteDep

router = APIRouter(prefix="/network-graph", tags=["v2", "network-graph"])

MAX_EDGES = int(os.environ.get("NETWORK_GRAPH_MAX_EDGES", "100000"))

DESCRIPTIONS_QUERY = (
    "MATCH (:Annotation {id: $annotationId})-[:HAS_GENE]->(g:Gene) "
    "WHERE g.id IN $geneIds "
    "RETURN g.id AS id, g.description AS description"
)

EXPERIMENT_QUERY = (
    "MATCH (:Annotation {id: $annotationId})-[:HAS_EXPERIMENT]->"
    "(e:Experiment {id: $experimentId}) "
    "RETURN e.id AS id"
)

EXPRESSION_QUERY = (
    "MATCH (e:Experiment {id: $experimentId})<-[:PART_OF]-(s:Sample) "
    "WITH s ORDER BY s.order "
    "WITH collect(s) AS samples "
    "UNWIND $geneIds AS geneId "
    "MATCH (g:Gene {id: geneId}) "
    "UNWIND samples AS sample "
    "OPTIONAL MATCH (g)-[r:EXPRESSED_IN]->(sample) "
    "RETURN geneId, r.value AS value"
)


async def records(session, query: str, **params) -> list:
    result = await session.run(query, **params)
    return [record async for record in result]


async def list_genes(
    connection,
    session,
    account_hash: str,
    list_id: str,
    gene_ids: list[str] | None,
) -> tuple[str, list[GraphNode]]:
    async with connection.execute(
        "SELECT annotation_id FROM gene_lists "
        "WHERE list_id = ? AND account_hash = ?",
        (list_id, account_hash),
    ) as cursor:
        row = await cursor.fetchone()
    if row is None:
        raise HTTPException(404, f"List '{list_id}' not found")
    annotation_id = row[0]
    async with connection.execute(
        "SELECT gene_id FROM gene_list_members "
        "WHERE list_id = ? ORDER BY added_at, gene_id",
        (list_id,),
    ) as cursor:
        members = [member[0] for member in await cursor.fetchall()]
    if gene_ids is not None:
        wanted = set(gene_ids)
        members = [gene_id for gene_id in members if gene_id in wanted]
    if not members:
        raise HTTPException(422, "No genes selected")
    descriptions = {
        record["id"]: record["description"] or ""
        for record in await records(
            session,
            DESCRIPTIONS_QUERY,
            annotationId=annotation_id,
            geneIds=members,
        )
    }
    return annotation_id, [
        GraphNode(id=gene_id, description=descriptions.get(gene_id, ""))
        for gene_id in members
    ]


async def expression_profiles(
    session, annotation_id: str, experiment_id: str, gene_ids: list[str]
) -> ExpressionProfiles:
    if not await records(
        session,
        EXPERIMENT_QUERY,
        annotationId=annotation_id,
        experimentId=experiment_id,
    ):
        raise HTTPException(
            422,
            f"Experiment '{experiment_id}' does not belong to "
            f"annotation '{annotation_id}'",
        )
    values: dict[str, list[float | None]] = {}
    for record in await records(
        session,
        EXPRESSION_QUERY,
        experimentId=experiment_id,
        geneIds=gene_ids,
    ):
        values.setdefault(record["geneId"], []).append(record["value"])
    measured = [
        gene_id
        for gene_id in gene_ids
        if any(value is not None for value in values.get(gene_id, []))
    ]
    return ExpressionProfiles(
        measured, [values[gene_id] for gene_id in measured]
    )


@router.post("/graph")
async def graph(
    body: GraphRequest,
    connection: SqliteDep,
    session: Neo4jDep,
    account_hash: AccountDep,
) -> GraphResponse:
    annotation_id, nodes = await list_genes(
        connection, session, account_hash, body.list_id, body.gene_ids
    )
    gene_ids = [node.id for node in nodes]
    profiles = [
        await expression_profiles(
            session, annotation_id, experiment_id, gene_ids
        )
        for experiment_id in body.experiment_ids
    ]
    try:
        return await run_in_threadpool(
            build_graph, nodes, profiles, MAX_EDGES
        )
    except TooManyEdges as error:
        raise HTTPException(422, str(error)) from error
