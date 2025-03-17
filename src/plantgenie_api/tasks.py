import time
from celery import Celery
from .celery import celery_app  # Import the Celery instance

@celery_app.task(bind=True)
def fake_blast_task(self, job_id: str):
    """
    Simulates running BLAST by sleeping for 5 seconds, then returning a fake result.
    """
    time.sleep(5)  # Simulate BLAST processing time
    return f"Fake BLAST result for job {job_id}"
