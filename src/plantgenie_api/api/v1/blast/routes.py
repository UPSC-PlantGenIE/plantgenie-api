import os
import uuid
from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal, Optional, Tuple

from celery import chain
from celery.result import AsyncResult
from fastapi import APIRouter, File, HTTPException, UploadFile, Form
from fastapi.responses import StreamingResponse
from loguru import logger
from swiftclient.service import (  # type: ignore
    SwiftService,
)

from plantgenie_api import SafeDuckDbConnection
from plantgenie_api.dependencies import backend_config

# from plantgenie_api import DUCKDB_DATABASE_PATH, ENV_DATA_PATH
from plantgenie_api.api.v1 import BACKEND_DATA_PATH, DATABASE_PATH
from plantgenie_api.api.v1.blast.models import (
    AvailableDatabase,
    BlastVersion,
    BlastSubmitResponse,
    BlastPollResponse,
)
from plantgenie_api.api.v1.blast.tasks import (
    # handle_query_file_not_found,
    verify_query_file_exists,
    validate_fasta_query,
    execute_blast_search,
    format_blast_result_tsv,
    format_blast_result_html,
    upload_blast_data_to_storage_bucket,
    delete_blast_data,
)
from plantgenie_api.dependencies import get_swift_service


router = APIRouter(prefix="/blast", tags=["v1", "blast"])


@router.get(path="/{program}/version")
async def get_program_version(
    program: Literal["blastn", "blastp", "blastx"],
) -> BlastVersion:
    logger.debug(f"received {program}")
    return BlastVersion(program=program, version="2.16.0+")


@router.get(path="/version")
async def get_blast_package_version() -> BlastVersion:
    return BlastVersion(program="blast package", version="2.16.0")


@router.get(path="/available-databases")
async def get_available_databases() -> List[AvailableDatabase]:
    with SafeDuckDbConnection(DATABASE_PATH) as connection:
        sql = connection.sql(
            """
                SELECT
                    s.species_name,
                    g.version as genome_version,
                    bd.sequence_type,
                    bd.program,
                    bd.database_path,
                  FROM
                    blast_databases bd
                  JOIN
                    species s ON bd.species_id = s.id
                  JOIN
                    genomes g ON bd.genome_id = g.id;
            """
        )
        results = sql.fetchall()

    return [
        AvailableDatabase(
            species=result[0],
            genome=result[1],
            sequence_type=result[2],
            program=result[3],
            database_path=result[4],
        )
        for result in results
    ]


@router.post(path="/{program}/submit")
async def submit_blast(
    species_id: Annotated[int, Form()],
    genome_id: Annotated[int, Form()],
    program: Literal["blastn", "blastp", "blastx"],
    database_type: Literal["cds", "mrna", "prot", "genome"],
    file: UploadFile = File(...),
) -> BlastSubmitResponse:
    with SafeDuckDbConnection(DATABASE_PATH) as connection:
        query = f"""
                SELECT
                    database_path
                FROM
                    blast_databases
                WHERE
                    species_id = {species_id} AND
                    genome_id = {genome_id} AND
                    \"program\" = '{program}' AND
                    sequence_type = '{database_type}'
            """
        logger.debug(query)
        sql = connection.sql(query=query)
        blast_path_result: Optional[Tuple[str]] = sql.fetchone()

        if blast_path_result is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Blast configuration species_id={species_id},"
                    f" genome_id={genome_id}, program={program},"
                    f" database_type={database_type} was not found"
                ),
            )
        (blast_path,) = blast_path_result

        logger.debug(sql.fetchone())
        logger.debug(BACKEND_DATA_PATH / blast_path)

    if file.size and (file.size > 2**20):
        raise HTTPException(
            status_code=413,
            detail=f"Size of your uploaded file - {file.size} > 1MB",
        )

    file_content = await file.read()

    job_id = str(uuid.uuid4())
    host_file_path = (
        BACKEND_DATA_PATH / "blast_queries" / f"{job_id}.fa"
    ).resolve()

    with open(host_file_path, "wb") as host_file:
        host_file.write(file_content)

    chain(
        verify_query_file_exists.s(
            {
                "query_path": host_file_path.as_posix(),
                "program": program,
                "database_path": (
                    BACKEND_DATA_PATH / blast_path
                ).as_posix(),
                "evalue": 0.0001,
                "max_hits": 10,
            }
        ),
        validate_fasta_query.s(),
        execute_blast_search.s(),
        format_blast_result_tsv.s(),
        format_blast_result_html.s(),
        upload_blast_data_to_storage_bucket.s(),
    ).apply_async(task_id=job_id)

    delete_blast_data.s({"job_id": job_id}).apply_async(countdown=15 * 60)

    return BlastSubmitResponse(
        job_id=job_id,
        file_size=file.size,
        program=program,
        database_type=database_type,
    )


@router.get(path="/poll/{job_id}")
def poll_blast_job(job_id: str):
    job_result: AsyncResult = AsyncResult(job_id)

    return BlastPollResponse(
        job_id=job_id,
        status=job_result.state,
        completed_at=(
            job_result.date_done.isoformat()
            if job_result.date_done is not None
            else None
        ),
    )


def file_iterator_and_cleanup(path: Path):
    with open(path, "rb") as f:
        yield from f
    path.unlink()


@router.get(path="/retrieve/{job_id}/{output_format}")
def retrieve_blast_result(
    job_id: str, output_format: Literal["tsv", "html"]
) -> StreamingResponse:
    job_result: AsyncResult = AsyncResult(job_id)

    if job_result.state == "FAILURE":
        raise HTTPException(
            status_code=404,
            detail="The job failed, no results to retrieve",
        )

    if job_result.state != "SUCCESS":
        raise HTTPException(
            status_code=404, detail="The job is not complete"
        )

    nfs_storage_location = Path(
        BACKEND_DATA_PATH / "blast_results" / f"{job_id}.{output_format}"
    )

    if nfs_storage_location.exists():

        def iter_file():
            with open(nfs_storage_location, mode="rb") as file_like:
                yield from file_like

        return StreamingResponse(
            iter_file(),
            media_type=(
                "text/tab-separated-values"
                if format == "tsv"
                else "text/html"
            ),
        )

    swift_output_path = (
        BACKEND_DATA_PATH
        / "blast_object_store_downloads"
        / f"{job_id}.{output_format}"
    )

    swift_service = get_swift_service(backend_config)

    result: Dict[str, Any] = next(
        swift_service.download(
            container="plantgenie-share",
            objects=[f"blast_results/{job_id}.{output_format}"],
            options={"out_file": swift_output_path.as_posix()},
        )
    )

    if result.get("success", False):
        return StreamingResponse(
            file_iterator_and_cleanup(swift_output_path),
            media_type=(
                "text/tab-separated-values"
                if output_format == "tsv"
                else "text/html"
            ),
        )

    raise HTTPException(
        status_code=404,
        detail=f"{output_format} result for job_id = {job_id} was not found",
    )
