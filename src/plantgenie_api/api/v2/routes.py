import secrets
from typing import Optional

from fastapi import APIRouter, HTTPException

from plantgenie_api.api.v2.models import (
    Annotation,
    AnnotationsResponse,
    AssembliesResponse,
    Assembly,
    CreateListRequest,
    CreateListResponse,
    Taxon,
    TaxaResponse,
)
from plantgenie_api.dependencies import Neo4jDep, SqliteDep

router = APIRouter(prefix="/v2")


@router.post(
    "/lists", status_code=201, response_model=CreateListResponse
)
async def create_list(
    body: CreateListRequest, conn: SqliteDep
) -> CreateListResponse:
    list_id = secrets.token_hex(8)
    await conn.execute(
        "INSERT INTO gene_lists (list_id, name, annotation_id) "
        "VALUES (?, ?, ?)",
        (list_id, body.name, body.annotation_id),
    )
    await conn.commit()
    return CreateListResponse(account_id="stub", list_id=list_id)


@router.get("/lists/{list_id}")
async def get_list(list_id: str, conn: SqliteDep) -> dict:
    async with conn.execute(
        "SELECT list_id, name, annotation_id FROM gene_lists "
        "WHERE list_id = ?",
        (list_id,),
    ) as cursor:
        row = await cursor.fetchone()
    if row is None:
        raise HTTPException(
            status_code=404, detail=f"List '{list_id}' not found"
        )
    return {"listId": row[0], "name": row[1], "annotationId": row[2]}


@router.get("/taxa", response_model=TaxaResponse, tags=["v2", "taxon"])
async def list_taxa(
    session: Neo4jDep, abbreviation: Optional[str] = None
) -> TaxaResponse:
    if abbreviation is None:
        result = await session.run("MATCH (t:Taxon) RETURN t ORDER BY t.id")
    else:
        result = await session.run(
            "MATCH (t:Taxon {abbreviation: $abbreviation}) RETURN t",
            abbreviation=abbreviation,
        )
    records = [record async for record in result]
    return TaxaResponse(taxa=[Taxon(**record["t"]) for record in records])


@router.get(
    "/assemblies",
    response_model=AssembliesResponse,
    tags=["v2", "assembly"],
)
async def list_assemblies(
    session: Neo4jDep, taxon: Optional[str] = None
) -> AssembliesResponse:
    if taxon is None:
        result = await session.run(
            "MATCH (t:Taxon)-[:HAS_ASSEMBLY]->(a:Assembly) "
            "RETURN a, t.abbreviation AS taxonAbbreviation "
            "ORDER BY t.scientificName, a.version"
        )
    else:
        result = await session.run(
            "MATCH (t:Taxon {abbreviation: $taxon})-[:HAS_ASSEMBLY]->(a:Assembly) "
            "RETURN a, t.abbreviation AS taxonAbbreviation "
            "ORDER BY a.version",
            taxon=taxon,
        )
    records = [record async for record in result]
    return AssembliesResponse(
        assemblies=[
            Assembly(
                **record["a"],
                taxon_abbreviation=record["taxonAbbreviation"],
            )
            for record in records
        ]
    )


@router.get(
    "/annotations",
    response_model=AnnotationsResponse,
    tags=["v2", "annotation"],
)
async def list_annotations(
    session: Neo4jDep,
    assembly: Optional[str] = None,
    taxon: Optional[str] = None,
) -> AnnotationsResponse:
    if assembly is not None and taxon is not None:
        raise HTTPException(
            status_code=400,
            detail="Specify either 'assembly' or 'taxon', not both",
        )
    if assembly is not None:
        result = await session.run(
            "MATCH (a:Assembly {id: $assembly})-[:HAS_ANNOTATION]->(n:Annotation) "
            "RETURN n {.id, .version, .geneCount, .isDefault} AS n, a.id AS assemblyId",
            assembly=assembly,
        )
    elif taxon is not None:
        result = await session.run(
            "MATCH (:Taxon {abbreviation: $taxon})-[:HAS_ASSEMBLY]->(a:Assembly)"
            "-[:HAS_ANNOTATION]->(n:Annotation) "
            "RETURN n {.id, .version, .geneCount, .isDefault} AS n, a.id AS assemblyId ORDER BY a.version, n.version",
            taxon=taxon,
        )
    else:
        result = await session.run(
            "MATCH (a:Assembly)-[:HAS_ANNOTATION]->(n:Annotation) "
            "RETURN n {.id, .version, .geneCount, .isDefault} AS n, a.id AS assemblyId"
        )
    records = [record async for record in result]
    return AnnotationsResponse(
        annotations=[
            Annotation(
                **record["n"],
                assembly_id=record["assemblyId"],
            )
            for record in records
        ]
    )
