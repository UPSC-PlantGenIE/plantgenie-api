import pytest

from plantgenie_api.dependencies import backend_config, get_swift_service

from task_queue.celery import app
from task_queue.blast.tasks import execute_blast

BLAST_DATABASE_CONTAINER_URL = (
    "https://north-1.cloud.snic.se:8080"
    "/swift/v1/AUTH_d9d5ac98cb2b4a3091b60040077e8efc"
    "/plantgenie-blast"
)


@pytest.fixture(autouse=True)
def swift_service():
    return get_swift_service(backend_config)


# @pytest.fixture
# def blast_query():


# def test_can_run_blast():
#     execute_blast.delay(args={"query_path": "/tests/blast_query_for_testing.fasta"})


# def test_can_write_result_to_bucket():
#     assert 1+1 == 2
