import uuid
from typing import Annotated

import requests
from celery.result import AsyncResult
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from go_enrich.methods import EnrichmentMethod
from loguru import logger
from shared.constants import GO_ENRICH_BUCKET_NAME
from shared.services.openstack import SwiftClient
from task_queue.enrichment.models import GoEnrichPipelineArgs
from task_queue.enrichment.tasks import run_go_enrichment_pipeline

from plantgenie_api.api.v1.enrichment.models import EnrichmentPollResponse
from plantgenie_api.dependencies import DatabaseDep, GoEnrichmentPathDep

MAX_FILE_SIZE = 2**20

router = APIRouter(prefix="/go-enrichment", tags=["v1", "go-enrichment"])


@router.post(path="/submit")
async def submit_go_enrichment_job(
    db_connection: DatabaseDep,
    go_enrichment_output_path: GoEnrichmentPathDep,
    genome_id: Annotated[int, Form()],
    method: Annotated[
        EnrichmentMethod,
        Form(
            description="enrichment method to use: independent, parent-child-intersection, parent_child_union"
        ),
    ] = EnrichmentMethod.independent,
    base_fdr: Annotated[
        float,
        Form(
            description="Base false discovery rate correction, between 0 and 1"
        ),
    ] = 0.01,
    target_genes: UploadFile = File(
        description="Line-delimited list of target genes, maximum size of 1MB"
    ),
    background_genes: UploadFile = File(
        description="Line-delimited list of background genes, maximum size of 1MB"
    ),
):
    if target_genes.size and (target_genes.size > MAX_FILE_SIZE):
        raise HTTPException(
            status_code=413,
            detail=f"Size of target genes file - {target_genes.size} > 1MB",
        )

    if background_genes.size and (background_genes.size > MAX_FILE_SIZE):
        raise HTTPException(
            status_code=413,
            detail=f"Size of background genes file - {background_genes.size} > 1MB",
        )

    sql = db_connection.query(
        "SELECT * FROM genomes WHERE id = ?", params=[genome_id]
    )
    logger.debug(sql)

    if not sql.project("id").fetchone() == (genome_id,):
        raise HTTPException(
            status_code=422,
            detail=(f"Genome with id = {genome_id} was not found"),
        )

    go_enrich_job_id = str(uuid.uuid4())
    target_genes_path = (
        go_enrichment_output_path / f"{go_enrich_job_id}-target.txt"
    ).resolve()
    background_genes_path = (
        go_enrichment_output_path / f"{go_enrich_job_id}-background.txt"
    ).resolve()

    target_genes_path.write_bytes(await target_genes.read())
    background_genes_path.write_bytes(await background_genes.read())

    pipeline_args = GoEnrichPipelineArgs(
        target_path=target_genes_path.resolve(True).as_posix(),
        background_path=background_genes_path.resolve(True).as_posix(),
        genome_id=genome_id,
        method=method,
        base_fdr=base_fdr,
    )

    run_go_enrichment_pipeline.apply_async(
        args=(pipeline_args.model_dump(),), task_id=go_enrich_job_id
    )

    return {"job_id": go_enrich_job_id}


@router.get(path="/poll/{job_id}")
def poll_blast_job(job_id: str):
    job_result: AsyncResult = AsyncResult(job_id)

    return EnrichmentPollResponse(
        job_id=job_id,
        status=job_result.state,
        completed_at=(
            job_result.date_done.isoformat()
            if job_result.date_done is not None
            else None
        ),
    )


@router.get("/retrieve/{job_id}")
def retrieve_go_enrichment_result(
    go_enrichment_output_path: GoEnrichmentPathDep, job_id: str
) -> FileResponse:
    job_result: AsyncResult = AsyncResult(job_id)

    if job_result.state == "FAILURE":
        raise HTTPException(
            status_code=422,
            detail="The job failed, no results to retrieve",
        )

    nfs_storage_location = (
        go_enrichment_output_path / f"{job_id}-go-enrichment-results.tsv"
    )

    if nfs_storage_location.exists():
        return FileResponse(
            nfs_storage_location, media_type="text/tab-separated-values"
        )

    swift_client = SwiftClient()

    retrieve_object_response: requests.Response | None = (
        swift_client.download_object(
            container=GO_ENRICH_BUCKET_NAME,
            object=f"{job_id}-go-enrichment-results.tsv",
            output_path=nfs_storage_location,
        )
    )

    if (
        retrieve_object_response
        and retrieve_object_response.status_code == 200
    ):
        return FileResponse(
            nfs_storage_location, media_type="text/tab-separated-values"
        )

    raise HTTPException(
        status_code=404,
        detail=f"Result for job_id = {job_id} was not found",
    )
