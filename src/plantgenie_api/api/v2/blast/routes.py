import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from task_queue.blast.tasks import run_blast_search

from plantgenie_api.api.v2.blast import fasta
from plantgenie_api.api.v2.blast.models import (
    PROGRAMS,
    BlastDatabase,
    BlastDatabasesResponse,
    BlastHit,
    BlastPollResponse,
    BlastResultsResponse,
    SubmitBlastRequest,
    SubmitBlastResponse,
)
from plantgenie_api.dependencies import (
    BlastPathDep,
    EnvironmentDep,
    Neo4jDep,
)

MAX_QUERY_BYTES = 2**20

router = APIRouter(prefix="/blast", tags=["v2", "blast"])


@router.get("/databases", response_model=BlastDatabasesResponse)
async def get_blast_databases(session: Neo4jDep) -> BlastDatabasesResponse:
    result = await session.run(
        "MATCH (t:Taxon)-[:HAS_ASSEMBLY]->(a:Assembly) "
        "OPTIONAL MATCH (a)-[:HAS_ANNOTATION]->(n:Annotation) "
        "WITH t, [x IN [a, n] WHERE x IS NOT NULL] AS owners "
        "UNWIND owners AS owner "
        "MATCH (owner)-[:HAS_BLAST_DB]->(b:BlastDatabase) "
        "RETURN DISTINCT b {.id, .name, .sequenceType, .moleculeType, "
        "taxonScientificName: t.scientificName} AS db "
        "ORDER BY db.taxonScientificName, db.id",
    )

    return BlastDatabasesResponse(
        databases=[
            BlastDatabase(**dict(record["db"])) async for record in result
        ]
    )


@router.post("")
async def submit_blast(
    body: SubmitBlastRequest,
    session: Neo4jDep,
    blast_path: BlastPathDep,
    environment: EnvironmentDep,
) -> SubmitBlastResponse:
    if len(body.query.encode()) > MAX_QUERY_BYTES:
        raise HTTPException(
            status_code=413, detail="Query must be smaller than 1 MB"
        )

    try:
        records = fasta.parse(body.query)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    result = await session.run(
        "MATCH (b:BlastDatabase {id: $databaseId}) "
        "RETURN b {.id, .moleculeType, .path} AS db",
        databaseId=body.database_id,
    )
    database_records = [record async for record in result]

    if not database_records:
        raise HTTPException(
            status_code=404,
            detail=f"Blast database '{body.database_id}' not found",
        )

    database = dict(database_records[0]["db"])
    query_molecule_type = fasta.molecule_type(records)
    allowed = PROGRAMS[(query_molecule_type, database["moleculeType"])]

    if body.program not in allowed:
        raise HTTPException(
            status_code=422,
            detail=(
                f"{body.program} cannot search a "
                f"{database['moleculeType']} database with a "
                f"{query_molecule_type} query. Use one of: "
                f"{', '.join(allowed)}"
            ),
        )

    job_id = str(uuid.uuid4())
    blast_path.mkdir(parents=True, exist_ok=True)
    query_path = blast_path / f"{job_id}.fa"
    query_path.write_text(body.query)

    run_blast_search.apply_async(
        kwargs={
            "job_id": job_id,
            "program": body.program,
            "query_path": query_path.as_posix(),
            "database_path": (
                Path(environment["DATA_PATH"]) / database["path"]
            ).as_posix(),
            "parameters": body.parameters.model_dump(exclude_none=True),
        },
        task_id=job_id,
    )

    return SubmitBlastResponse(job_id=job_id)


@router.get("/poll/{job_id}", response_model=BlastPollResponse)
async def poll_blast_job(job_id: uuid.UUID) -> BlastPollResponse:
    return BlastPollResponse(
        status=run_blast_search.AsyncResult(str(job_id)).state
    )


@router.get("/{job_id}/{output_format}", response_model=None)
async def retrieve_blast_results(
    job_id: uuid.UUID,
    output_format: Literal["json", "tsv", "html"],
    blast_path: BlastPathDep,
) -> BlastResultsResponse | FileResponse:
    suffix = "tsv" if output_format == "json" else output_format
    path = blast_path / f"{job_id}.{suffix}"

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No {output_format} results for job '{job_id}'",
        )

    if output_format == "json":
        return BlastResultsResponse(
            results=BlastHit.from_tsv(path.read_text())
        )

    return FileResponse(
        path,
        media_type=(
            "text/html"
            if output_format == "html"
            else "text/tab-separated-values"
        ),
        filename=path.name,
    )
