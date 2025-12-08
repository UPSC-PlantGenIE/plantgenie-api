from pathlib import Path
from typing import Literal

from shared.db import SafeDuckDbConnection
from task_queue.celery import app


@app.task(name="enrichment.verify_target")
def verify_target_genes_file(target_path: Path) -> Path:
    if not target_path.exists():
        raise FileNotFoundError(
            f"{target_path.resolve().as_posix()} was not found"
        )

    return target_path


@app.task(name="enrichment.verify_background")
def verify_background_genes_file(background_path: Path) -> Path:
    if not background_path.exists():
        raise FileNotFoundError(
            f"{background_path.resolve().as_posix()} was not found"
        )

    return background_path


@app.task(name="enrichment.run_analysis")
def run_enrichment(
    target_path: Path, background: Path, method: Literal["classic"]
):
    pass
