import os
import uuid

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal, Optional

import duckdb

from celery.result import AsyncResult
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import HTTPException

from plantgenie_api.client import AsyncSwiftClient

from plantgenie_api.models import (
    AnnotationsRequest,
    AnnotationsResponse,
    AvailableGenome,
    AvailableGenomesResponse,
    AvailableSpecies,
    AvailableSpeciesResponse,
    ExpressionRequest,
    ExpressionResponse,
    GeneAnnotation,
    GeneInfo,
    SampleInfo,
)

from plantgenie_api.api.v1.blast.routes import router as blast_router

from plantgenie_api.tasks import (
    fake_blast_task,
    real_blast_task,
)

ENV_DATA_PATH = os.environ.get("DATA_PATH")

DATA_PATH = (
    Path(ENV_DATA_PATH)
    if ENV_DATA_PATH
    else Path(__file__).parent.parent / "example_data"
)


DATABASE_PATH = DATA_PATH / "upsc-plantgenie.db"
GENOMES_PATH = DATA_PATH / "genomes"

BLAST_DB_MAPPER = {
    "Picea abies": {
        "v2.0": {
            "cds": GENOMES_PATH
            / "picea-abies/Picab02_230926/blast"
            / "Picab02_230926_at01_all_cds.fa",
            "mrna": DATA_PATH
            / "picea-abies/Picab02_230926/blast"
            / "Picab02_230926_at01_all_mRNA.fa",
            "protein": DATA_PATH
            / "picea-abies/Picab02_230926/blast"
            / "Picab02_230926_at01_all_aa.fa",
            "genome": DATA_PATH
            / "picea-abies/Picab02_230926/blast"
            / "Picab02_chromosomes_and_unplaced.fa",
        }
    },
    "Pinus sylvestris": {
        "v1.0": {
            "cds": DATA_PATH
            / "pinus-sylvestris/Pinsy01_240308/blast"
            / "Pinsy01_240308_at01_all_cds.fa",
            "mrna": DATA_PATH
            / "pinus-sylvestris/Pinsy01_240308/blast"
            / "Pinsy01_240308_at01_all_mRNA.fa",
            "protein": DATA_PATH
            / "pinus-sylvestris/Pinsy01_240308/blast"
            / "Pinsy01_240308_at01_all_aa.fa",
            "genome": DATA_PATH
            / "pinus-sylvestris/Pinsy01_240308/blast"
            / "Pinsy01_chromosomes_and_unplaced.fa",
        }
    },
}

app = FastAPI(
    root_path="/api",
    title="UPSC PlantGenIE API",
    version="0.0.1",
    description="Backend for the PlantGenIE React Frontend",
)
app.add_middleware(  # type: ignore[bad-argument-type]
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # Allow all origins (change this to specific origins in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)
# app.include_router(router=genome_router, prefix="/api")
app.include_router(router=blast_router, prefix="/v1")



@app.post("/submit-blast")
def submit_blast():
    """
    Simulate submitting a BLAST job.
    Returns a UUID representing the job ID.
    """
    job_id = str(uuid.uuid4())  # Generate a random job ID
    task = fake_blast_task.apply_async(args=(job_id,))  # Enqueue task in Celery

    return {"job_id": task.id}  # Return Celery task ID


@app.get("/check-blast/{job_id}")
def check_blast(job_id: str):
    """
    Check the status of a BLAST job using the Celery result backend (Redis).
    """
    result = AsyncResult(job_id)

    if result.state == "PENDING":
        return {"job_id": job_id, "status": "pending", "result": None}
    elif result.state == "SUCCESS":
        return {"job_id": job_id, "status": "completed", "result": result.result}
    elif result.state == "FAILURE":
        return {"job_id": job_id, "status": "failed", "result": str(result.result)}
    else:
        return {"job_id": job_id, "status": result.state, "result": None}

@app.post("/submit-blast-query/")
async def submit_blast_query(
    program: Annotated[Literal["blastn", "blastp", "blastx"], Form()],
    file: UploadFile = File(...),  # File upload
    description: str = Form(...),  # Form field: description
    dbtype: str = Form(...),
    species: str = Form(...),
):
    if program not in ["blastn", "blastx", "blastp"]:
        raise HTTPException(
            status_code=422, detail=f"{program} not a valid blast program"
        )

    if dbtype not in ["protein", "mrna", "cds", "genome"]:
        raise HTTPException(
            status_code=422, detail=f"{dbtype} not a valid dbtype parameter"
        )

    if file.size and (file.size > 2**20):
        raise HTTPException(
            status_code=413,
            detail=f"Size of your uploaded file - {file.size} - > 1MB",
        )

    match species:
        case "Picea abies":
            version = "v2.0"
        case "Pinus sylvestris":
            version = "v1.0"
        case _:
            raise HTTPException(
                status_code=422, detail=f"database for {species} not found"
            )

    database_path = BLAST_DB_MAPPER[species][version][dbtype].absolute().as_posix()

    file_content = await file.read()

    host_file_path = f"{DATA_PATH}/{uuid.uuid4()}_query.fasta"

    with open(host_file_path, "wb") as f:
        f.write(file_content)

    task = real_blast_task.apply_async(args=(host_file_path, program, database_path))

    return JSONResponse(
        content={
            "filename": file.filename,
            "description": description,
            "dbtype": dbtype,
            "file_size": len(file_content),
            "job_id": task.id,
        }
    )


@app.get("/poll-for-blast-result/{job_id}")
def poll_for_blast_result(job_id: str):
    job_result = AsyncResult(job_id)

    if job_result.state == "PENDING":
        return_result = None
    elif job_result.state == "SUCCESS":
        return_result = job_result.result
    elif job_result.state == "FAILURE":
        return_result = str(job_result.result)
    else:
        return_result = None

    return JSONResponse(
        content={
            "job_id": job_id,
            "status": job_result.state,
            "result": return_result,
            "completed_at": (
                job_result.date_done.isoformat()
                if (job_result.state == "SUCCESS" or job_result.state == "FAILURE")
                and job_result.date_done is not None
                else None
            ),
        }
    )


@app.get("/retrieve-blast-result/{job_id}")
def retrieve_blast_result(job_id: str):
    result = AsyncResult(job_id)

    if result.state == "SUCCESS":
        return FileResponse(f"{DATA_PATH}/{job_id}_blast_results.tsv")

    raise HTTPException(
        status_code=404,
        detail=f"tab-delimited result for requested job id - {job_id} - was not found",
    )


@app.get("/retrieve-blast-result-as-tsv/{job_id}")
def retrieve_blast_result_as_tsv(job_id: str):
    pass


@app.get("/retrieve-blast-result-as-html/{job_id}")
def retrieve_blast_result_as_html(job_id: str):
    result = AsyncResult(job_id)

    if result.state == "SUCCESS":
        return FileResponse(f"{DATA_PATH}/{job_id}_blast_results.html")

    raise HTTPException(
        status_code=404,
        detail=f"html result for requested job id - {job_id} - was not found",
    )


@app.get("/available-species")
async def get_available_species() -> AvailableSpeciesResponse:
    with duckdb.connect(DATABASE_PATH, read_only=True) as connection:
        query_relation = connection.sql("select * from species;")

        return AvailableSpeciesResponse(
            species=[
                AvailableSpecies(
                    **{
                        k: v
                        for k, v in zip(AvailableSpecies.model_fields.keys(), result)
                    }
                )
                for result in query_relation.fetchall()
            ]
        )


@app.get("/available-genomes")
async def get_available_genomes() -> AvailableGenomesResponse:
    with duckdb.connect(DATABASE_PATH, read_only=True) as connection:
        query_relation = connection.sql(
            "select * from genomes join species on (genomes.species_id = species.id);"
        ).project(
            "id", "species_id", "species_name", "version", "publication_date", "doi"
        )
        print(query_relation)

        return AvailableGenomesResponse(
            genomes=[
                AvailableGenome(
                    **{
                        k: v
                        for k, v in zip(AvailableGenome.model_fields.keys(), result)
                    }
                )
                for result in query_relation.fetchall()
            ]
        )


@app.post("/annotations")
async def get_annotations_duckdb(request: AnnotationsRequest) -> AnnotationsResponse:
    if len(request.gene_ids) == 0:
        return AnnotationsResponse(results=[])

    gene_ids = GeneInfo.split_gene_ids_from_request(request.gene_ids)

    # Map gene_ids to their original order for sorting results later
    gene_id_order = {
        (gene.chromosome_id, gene.gene_id): i for i, gene in enumerate(gene_ids)
    }

    # build query template with (?, ?) for each gene_id
    query = (
        "SELECT * FROM annotations WHERE (chromosome_id, gene_id) IN ("
        + ", ".join(["(?, ?)"] * len(request.gene_ids))
        + ")"
    )

    with duckdb.connect(DATABASE_PATH, read_only=True) as connection:
        query_relation = connection.sql(
            query=query,
            params=[
                value
                for gene in gene_ids
                for value in (gene.chromosome_id, gene.gene_id)
            ],
        ).project(  # we don't need id or genome_id here
            "chromosome_id",
            "gene_id",
            # "tool",
            "evalue",
            "score",
            "seed_ortholog",
            "description",
            "preferred_name",
        )

        # Collect and reorder results based on original input order
        annotations = [
            GeneAnnotation(
                **{k: v for k, v in zip(GeneAnnotation.model_fields.keys(), result)}
            )
            for result in query_relation.fetchall()
        ]

        # Sort by the original order of gene_ids
        ordered_annotations = sorted(
            annotations,
            key=lambda annotation: gene_id_order[
                (annotation.chromosome_id, annotation.gene_id)
            ],
        )

        return AnnotationsResponse(results=ordered_annotations)


@app.post("/expression")
async def get_expression_duckdb(request: ExpressionRequest) -> ExpressionResponse:
    if len(request.gene_ids) == 0:
        return ExpressionResponse(genes=[], samples=[], values=[])

    gene_ids = GeneInfo.split_gene_ids_from_request(request.gene_ids)

    gene_id_order = {
        (gene.chromosome_id, gene.gene_id): i for i, gene in enumerate(gene_ids)
    }

    with duckdb.connect(DATABASE_PATH, read_only=True) as connection:
        experiment = connection.sql(
            "SELECT relation_name FROM experiments WHERE id = ?",
            params=[request.experiment_id],
        ).fetchone()

        if experiment is None:
            raise HTTPException(status_code=422, detail=f"Experiment with id={request.experiment_id} not found")

        experiment = experiment[0]

        samples_ordered = [
            SampleInfo(
                experiment=experiment,
                sample_id=sample[0], # type: ignore
                reference=sample[1],
                sequencing_id=sample[2], #type: ignore
                condition=sample[3],
            )
            for sample in connection.sql(
                "SELECT id, reference, sample_filename, condition from samples WHERE experiment_id = ?",
                params=[request.experiment_id],
            )
            .order("id")
            .fetchall()
        ]

        sample_info_order = {
            sample.sample_id: i for i, sample in enumerate(samples_ordered)
        }

        query = (
            f"SELECT sample_id, chromosome_id, gene_id, sum(tpm) as tpm from {experiment} "
            f"WHERE (chromosome_id, gene_id) IN ({", ".join(["(?, ?)"] * len(gene_ids))}) GROUP BY sample_id, chromosome_id, gene_id"
        )

        query_relation = connection.sql(
            query=query,
            params=[
                value
                for gene in gene_ids
                for value in (gene.chromosome_id, gene.gene_id)
            ],
        )

        gene_infos = [
            GeneInfo(chromosome_id=gene[0], gene_id=gene[1]) #type: ignore
            for gene in query_relation.project("chromosome_id", "gene_id")
            .distinct()
            .order("chromosome_id, gene_id")
            .fetchall()
        ]

        results = query_relation.project(
            "chromosome_id", "gene_id", "sample_id", "tpm"
        ).fetchall()

        results_ordered = sorted(
            results,
            # sort first by chromosome_id, gene_id, then by sample_id
            key=lambda result: (
                gene_id_order[(result[0], result[1])],
                sample_info_order[result[2]],
            ),
        )

        gene_infos_ordered = sorted(
            gene_infos,
            key=lambda gene_info: gene_id_order[
                (gene_info.chromosome_id, gene_info.gene_id)
            ],
        )

        return ExpressionResponse(
            samples=samples_ordered,
            genes=gene_infos_ordered,
            values=[x[3] for x in results_ordered],
        )
