import os
import tempfile
import uuid
from typing import Annotated, List, Literal

import duckdb
from celery import chain
from celery.result import AsyncResult
from fastapi import APIRouter, File, HTTPException, UploadFile, Form
from fastapi.responses import FileResponse
from swiftclient.service import (
    SwiftService,
    SwiftUploadObject,
    ClientException,
    SwiftError,
)

from plantgenie_api import DUCKDB_DATABASE_PATH, ENV_DATA_PATH
from plantgenie_api.api.v1.blast.models import (
    AvailableDatabase,
    BlastVersion,
    BlastSubmitResponse,
    BlastPollResponse,
)
from plantgenie_api.api.v1.blast.tasks import (
    retrieve_query_from_object_store,
    execute_blast_query,
    format_blast_result,
    upload_blast_result,
)
from plantgenie_api.api.v1.blast.utils import download_object_from_object_store


router = APIRouter(prefix="/blast")

swift_service = SwiftService(
    options={
        "auth_type": os.environ["OS_AUTH_TYPE"],
        "auth_url": os.environ["OS_AUTH_URL"],
        "identity_api_version": os.environ["OS_IDENTITY_API_VERSION"],
        "region_name": os.environ["OS_REGION_NAME"],
        "interface": os.environ["OS_INTERFACE"],
        "application_credential_id": os.environ["OS_APPLICATION_CREDENTIAL_ID"],
        "application_credential_secret": os.environ["OS_APPLICATION_CREDENTIAL_SECRET"],
    }
)

@router.get(path="/version")
async def get_blast_version() -> BlastVersion:
    return BlastVersion(version="2.16.0+")


@router.get(path="/available-databases")
async def get_available_databases() -> List[AvailableDatabase]:
    with duckdb.connect(DUCKDB_DATABASE_PATH, read_only=True) as connection:
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


@router.post(path="/submit")
async def submit_blast(
    species: Annotated[str, Form()],
    file: UploadFile = File(...),
    program: Annotated[Literal["blastn", "blastp", "blastx"], Form()] = "blastn",
    database_type: Annotated[
        Literal["cds", "mrna", "prot", "genome"], Form()
    ] = "genome",
) -> BlastSubmitResponse:

    file_content = await file.read()
    temp_file = tempfile.NamedTemporaryFile(delete=False)

    job_id = str(uuid.uuid4())
    try:
        temp_file.write(file_content)
        temp_file.close()

        object_name = f"blast_files/{job_id}.fasta"

        upload_object = SwiftUploadObject(
            source=temp_file.name, object_name=object_name
        )

        print(temp_file.name, object_name)

        result = swift_service.upload("plantgenie-share", objects=[upload_object])
        print(result)

        if result:
            chain(
                retrieve_query_from_object_store.s(
                    {
                        "query_path": object_name,
                        "program": "blastn",
                        "database_path": "/data/picea-abies/v2.0/blast/Picab02_230926_at01_all_cds.fa",  # needs to be retrieved from duckdb
                        "evalue": 0.0001,
                        "max_hits": 10,
                    }
                ),
                execute_blast_query.s(),
                format_blast_result.s(),
                upload_blast_result.s(),
            ).apply_async(task_id=job_id, countdown=10)

    except (ClientException, SwiftError) as error:
        if isinstance(error, ClientException):
            raise HTTPException(status_code=422, detail=error.msg)
        if isinstance(error, SwiftError):
            raise HTTPException(status_code=422, detail=str(error.value))
    finally:
        print(list(result))
        os.unlink(temp_file.name)

    return BlastSubmitResponse(
        job_id=job_id,
        program=program,
        database_type=database_type,
        file_size=len(file_content),
    )


@router.get(path="/poll/{job_id}")
def poll_blast_job(job_id: str):
    job_result = AsyncResult(job_id)

    match job_result.state:
        case "SUCCESS":
            return_result = job_result.result
            completed_at = job_result.date_done.isoformat()
        case "FAILURE":
            return_result = str(job_result.result)
            completed_at = job_result.date_done.isoformat()
        case _:
            return_result = None
            completed_at = None

    return BlastPollResponse(
        job_id=job_id,
        status=job_result.state,
        result=return_result,
        completed_at=completed_at,
    )


@router.get(path="/retrieve/{job_id}")
def retrieve_blast_result(job_id: str):
    job_result = AsyncResult(job_id)

    result = download_object_from_object_store(
        container="plantgenie-share",
        object_path=f"blast_files/{job_id}.tsv",
        output_directory=ENV_DATA_PATH,
    )

    if job_result.state == "SUCCESS" and result["output_path"]:
        return FileResponse(result["output_path"])

    raise HTTPException(
        status_code=404, detail=f"TSV result for job_id = {job_id} was not found"
    )
