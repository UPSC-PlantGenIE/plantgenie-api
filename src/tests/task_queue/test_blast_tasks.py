from pathlib import Path
from subprocess import CalledProcessError

from celery import Celery
import pytest

from task_queue.blast.tasks import (
    verify_blast_is_installed,
    verify_query_file_exists,
    verify_query_is_fasta,
)
from task_queue.blast.exceptions import (
    DuplicateSequenceIdentifiersError,
    NoFirstCaretError,
)
from testcontainers.core.container import DockerContainer  # type: ignore
from testcontainers.rabbitmq import RabbitMqContainer  # type: ignore
from testcontainers.redis import RedisContainer  # type: ignore


@pytest.fixture(scope="module")
def fasta_file_no_first_caret():
    fasta_path = Path(__file__).parent / "test_no_caret.fa"
    fasta_path.write_text("test_sequence\nACGTACAGTCGATCGATCAGCTA")
    yield fasta_path
    fasta_path.unlink()


@pytest.fixture(scope="module")
def fasta_file_duplicate_ids():
    fasta_path = Path(__file__).parent / "test_duplicates.fa"
    fasta_path.write_text(
        (
            ">test_sequence\n"
            "ACGTACAGTCGATCGATCAGCTA\n"
            ">test_sequence\n"
            "ACGTACAGTCGATCGATCAGCTAATCGCTAGCATCG"
        )
    )
    yield fasta_path
    fasta_path.unlink()


@pytest.fixture(scope="module")
def good_fasta_file():
    fasta_path = Path(__file__).parent / "test_good.fa"
    fasta_path.write_text(
        (
            ">test_sequence_0\n"
            "ACGTACAGTCGATCGATCAGCTA\n"
            ">test_sequence_1\n"
            "ACGTACAGTCGATCGATCAGCTAATCGCTAGCATCG"
        )
    )
    yield fasta_path
    fasta_path.unlink()


def test_blast_installed(
    rabbitmq_container: RabbitMqContainer,
    redis_container: RedisContainer,
    celery_container: DockerContainer,
    configured_celery_test_app: Celery,
):
    result = verify_blast_is_installed.delay()
    value = result.get(timeout=10)

    assert value
    result.forget()


def test_query_exists(
    good_fasta_file: Path,
    rabbitmq_container: RabbitMqContainer,
    redis_container: RedisContainer,
    celery_container: DockerContainer,
    configured_celery_test_app: Celery,
):
    result = verify_query_file_exists.delay(
        query_path=f"/tests/{good_fasta_file.name}"
    )
    value = result.get(timeout=10)

    assert value == f"/tests/{good_fasta_file.name}"
    result.forget()


def test_error_if_bad_args_to_blast(
    rabbitmq_container: RabbitMqContainer,
    redis_container: RedisContainer,
    celery_container: DockerContainer,
    configured_celery_test_app: Celery,
):
    with pytest.raises(CalledProcessError):
        result = verify_blast_is_installed.delay(blast_args=["-bad"])
        result.get(timeout=10)
        result.forget()


def test_fasta_validation_fails_if_not_startswith_caret(
    fasta_file_no_first_caret: Path,
    rabbitmq_container: RabbitMqContainer,
    redis_container: RedisContainer,
    celery_container: DockerContainer,
    configured_celery_test_app: Celery,
):
    with pytest.raises(NoFirstCaretError):
        verify_query_is_fasta.delay(
            blast_program="blastn",
            query_path=f"/tests/{fasta_file_no_first_caret.name}",
        ).get(timeout=10)


def test_fasta_validation_fails_with_duplicate_ids(
    fasta_file_duplicate_ids: Path,
    rabbitmq_container: RabbitMqContainer,
    redis_container: RedisContainer,
    celery_container: DockerContainer,
    configured_celery_test_app: Celery,
):
    with pytest.raises(DuplicateSequenceIdentifiersError):
        result = verify_query_is_fasta.delay(
            blast_program="blastn",
            query_path=f"/tests/{fasta_file_duplicate_ids.name}",
        )
        result.get(timeout=10)
        result.forget()


def test_fasta_validation_passes(
    good_fasta_file: Path,
    # rabbitmq_container: RabbitMqContainer,
    # redis_container: RedisContainer,
    celery_container: DockerContainer,
    configured_celery_test_app: Celery,
):
    result = verify_query_is_fasta.delay(
        blast_program="blastn", query_path=f"/tests/{good_fasta_file.name}"
    )
    value = result.get(timeout=10)

    assert value == f"/tests/{good_fasta_file.name}"
