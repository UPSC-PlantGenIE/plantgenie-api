import uuid
from fastapi import FastAPI
from celery.result import AsyncResult
from plantgenie_api.tasks import fake_blast_task  # Import the Celery task

app = FastAPI()

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
