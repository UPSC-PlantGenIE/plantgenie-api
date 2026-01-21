import requests
import uuid
from pathlib import Path
from typing import Annotated, List, Literal, Optional, Tuple

from celery.result import AsyncResult
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from loguru import logger
from shared.config import backend_config
from shared.constants import BLAST_SERVICE_BUCKET_NAME
from shared.services.database import SafeDuckDbConnection
from shared.services.openstack import SwiftClient
from task_queue.blast.models import ExecuteBlastPipelineArgs
from task_queue.blast.tasks import execute_blast_pipeline

from plantgenie_api.api.v1 import BACKEND_DATA_PATH
from plantgenie_api.api.v1.blast.models import (
    AvailableDatabase,
    BlastPollResponse,
    BlastSubmitResponse,
    BlastVersion,
)

MAX_FILE_SIZE = 2**20  # 1 Megabyte

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
    DATA_DIRECTORY: Optional[str] = backend_config.get("DATA_PATH")

    with SafeDuckDbConnection(
        f"{backend_config.get("DATA_PATH")}/{backend_config.get("DATABASE_NAME")}",
        allowed_directories=[DATA_DIRECTORY] if DATA_DIRECTORY else None,
        read_only=True,
    ) as connection:
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
        results: List[Tuple[str, str, str, str, str]] = sql.fetchall()

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
    file: UploadFile = File(
        description="Fasta-formatted sequences to use as blast query."
    ),
) -> BlastSubmitResponse:
    DATA_DIRECTORY: Optional[str] = backend_config.get("DATA_PATH")

    with SafeDuckDbConnection(
        f"{backend_config.get("DATA_PATH")}/{backend_config.get("DATABASE_NAME")}",
        allowed_directories=[DATA_DIRECTORY] if DATA_DIRECTORY else None,
        read_only=True,
    ) as connection:
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

        blast_path: str = blast_path_result[0]

        logger.debug(sql.fetchone())
        logger.debug(BACKEND_DATA_PATH / blast_path)

    if file.size and (file.size > MAX_FILE_SIZE):
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

    blast_pipeline_args = ExecuteBlastPipelineArgs(
        job_id=job_id,
        blast_program=program,
        query_path=host_file_path.as_posix(),
        database_path=(BACKEND_DATA_PATH / blast_path).as_posix(),
    )
    execute_blast_pipeline.apply_async(
        args=(blast_pipeline_args.model_dump(),), task_id=job_id
    )

    # delete_blast_data.s({"job_id": job_id}).apply_async(countdown=15 * 60)

    return BlastSubmitResponse(
        job_id=job_id,
        file_size=file.size or 0,
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
            status_code=422,
            detail="The job failed, no results to retrieve",
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

    swift_client = SwiftClient()

    result: requests.Response | None = swift_client.download_object(
        container=BLAST_SERVICE_BUCKET_NAME,
        object=f"{job_id}.{output_format}",
        output_path=nfs_storage_location
    )

    if result and result.status_code == 200:
        return StreamingResponse(
            file_iterator_and_cleanup(nfs_storage_location),
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

# @router.get(path="/retrieve/{job_id}/{output_format}")
# def retrieve_blast_result(
#     job_id: str, output_format: Literal["tsv", "html"]
# ) -> StreamingResponse:
#     job_result: AsyncResult = AsyncResult(job_id)

#     if job_result.state == "FAILURE":
#         raise HTTPException(
#             status_code=404,
#             detail="The job failed, no results to retrieve",
#         )

#     if job_result.state != "SUCCESS":
#         raise HTTPException(
#             status_code=404, detail="The job is not complete"
#         )

#     nfs_storage_location = Path(
#         BACKEND_DATA_PATH / "blast_results" / f"{job_id}.{output_format}"
#     )

#     if nfs_storage_location.exists():

#         def iter_file():
#             with open(nfs_storage_location, mode="rb") as file_like:
#                 yield from file_like

#         return StreamingResponse(
#             iter_file(),
#             media_type=(
#                 "text/tab-separated-values"
#                 if format == "tsv"
#                 else "text/html"
#             ),
#         )

#     swift_client = SwiftClient()

#     result: requests.Response | None = swift_client.download_object(
#         container=BLAST_SERVICE_BUCKET_NAME,
#         object=f"{job_id}.{output_format}",
#         output_path=nfs_storage_location
#     )

#     if result and result.status_code == 200:
#         return StreamingResponse(
#             file_iterator_and_cleanup(nfs_storage_location),
#             media_type=(
#                 "text/tab-separated-values"
#                 if output_format == "tsv"
#                 else "text/html"
#             ),
#         )

#     raise HTTPException(
#         status_code=404,
#         detail=f"{output_format} result for job_id = {job_id} was not found",
#     )
