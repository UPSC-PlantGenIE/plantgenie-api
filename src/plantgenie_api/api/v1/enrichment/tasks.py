import networkx

from celery import Task
from pydantic import BaseModel

from plantgenie_api import BACKEND_DATA_PATH, SafeDuckDbConnection
from plantgenie_api.celery import celery_app


class GeneOntologyEnrichmentArgs(BaseModel):
    pass


class GeneOntologyEnrichmentResults(BaseModel):
    pass


@celery_app.task(
    name="enrichment.perform_go_enrichment", bind=True, pydantic=True
)
def run_enrichment_analysis(
    self: Task, task_args: GeneOntologyEnrichmentArgs
) -> GeneOntologyEnrichmentResults:
    return GeneOntologyEnrichmentResults()
