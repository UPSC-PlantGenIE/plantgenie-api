from loguru import logger
from task_queue.enrichment.tasks import run_go_enrichment_pipeline
from go_enrich.methods import EnrichmentMethod
from task_queue.enrichment.models import GoEnrichPipelineArgs
import uuid
from typing import Annotated
from fastapi import APIRouter, UploadFile, File, Form, HTTPException


from plantgenie_api.dependencies import DatabaseDep, GoEnrichmentPathDep

router = APIRouter(prefix="/go-enrichment", tags=["v1", "go-enrichment"])

MAX_FILE_SIZE = 2**20


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
