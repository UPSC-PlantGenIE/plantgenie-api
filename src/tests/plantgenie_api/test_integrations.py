import pytest

from shared.config import backend_config
from shared.services import get_swift_service
from shared.constants import BLAST_DATABASE_CONTAINER_URL

from task_queue.celery import app
from task_queue.blast.tasks import execute_blast


@pytest.fixture(autouse=True)
def swift_service():
    return get_swift_service(backend_config)


# @pytest.fixture
# def blast_query():


# def test_can_run_blast():
#     execute_blast.delay(args={"query_path": "/tests/blast_query_for_testing.fasta"})


# def test_can_write_result_to_bucket():
#     assert 1+1 == 2
