import os
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import HTTPException
from celery.result import AsyncResult
from plantgenie_api.tasks import (
    fake_blast_task,
    real_blast_task,
)  # Import the Celery task

DATA_PATH = (
    Path(os.environ.get("DATA_PATH")) or Path(__file__).parent.parent / "example_data"
)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # Allow all origins (change this to specific origins in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


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
    file: UploadFile = File(...),  # File upload
    description: str = Form(...),  # Form field: description
    dbtype: str = Form(...),
):

    if dbtype not in ["protein", "mrna", "cds", "genome"]:
        raise HTTPException(
            status_code=422, detail=f"{dbtype} not a valid dbtype parameter"
        )

    if file.size > 2**20:
        raise HTTPException(
            status_code=413,
            detail=f"Size of your uploaded file - {file.size} - > 1MB",
        )

    file_content = await file.read()

    host_file_path = f"{DATA_PATH}/{uuid.uuid4()}_query.fasta"

    with open(host_file_path, "wb") as f:
        f.write(file_content)

    task = real_blast_task.apply_async(args=(host_file_path, dbtype))

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
            "completed_at": job_result.date_done.isoformat(),
        }
    )


@app.get("/retrieve-blast-result/{job_id}")
def retrieve_blast_result(job_id: str):
    result = AsyncResult(job_id)

    if result.state == "SUCCESS":
        return FileResponse(f"{DATA_PATH}/{job_id}_blast_results.tsv")

    raise HTTPException(
        status_code=404,
        detail=f"result for requested job id - {job_id} - was not found",
    )


@app.get("/retrieve-blast-result-as-tsv/{job_id}")
def retrieve_blast_result_as_html(job_id: str):
    pass


@app.get("/retrieve-blast-result-as-html/{job_id}")
def retrieve_blast_result_as_html(job_id: str):
    pass
