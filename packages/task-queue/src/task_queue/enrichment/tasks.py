from pathlib import Path
from typing import Literal

from task_queue.celery import app
from task_queue.tasks import PathValidationTask

from shared.services.database import SafeDuckDbConnection


@app.task(name="enrichment.verify_target", base=PathValidationTask)
def verify_target_genes_file(target_path: str) -> str:
    return target_path


@app.task(name="enrichment.verify_background", base=PathValidationTask)
def verify_background_genes_file(background_path: str) -> str:
    return background_path


@app.task(name="enrichment.run_analysis")
def run_enrichment(
    target_path: Path, background: Path, method: Literal["classic"]
):
    pass
