from pathlib import Path
from subprocess import CalledProcessError

import pytest
from celery import Celery
from testcontainers.core.container import DockerContainer

from task_queue.blast.tasks import (
    verify_blast_is_installed,
    verify_query_file_exists,
    verify_query_is_fasta,
)
from task_queue.blast.exceptions import (
    DuplicateSequenceIdentifiersError,
    NoFirstCaretError,
)


@pytest.fixture(scope="module")
def module_data_directory(host_data_directory: Path):
    p = host_data_directory / "test_blast_tasks"
    p.mkdir(exist_ok=True, parents=True)
    yield p
    p.rmdir()


@pytest.fixture(scope="module")
def docker_data_directory():
    p = Path("/tests/test_blast_tasks")
    yield p


@pytest.fixture(scope="module")
def fasta_file_no_first_caret(
    module_data_directory: Path, docker_data_directory: Path
):
    fasta_path = module_data_directory / "test_no_caret.fa"
    fasta_path.write_text("test_sequence\nACGTACAGTCGATCGATCAGCTA")

    yield docker_data_directory / fasta_path.name

    fasta_path.unlink()


@pytest.fixture(scope="module")
def fasta_file_duplicate_ids(
    module_data_directory: Path, docker_data_directory: Path
):
    fasta_path = module_data_directory / "test_duplicates.fa"
    fasta_path.write_text(
        (
            ">test_sequence\n"
            "ACGTACAGTCGATCGATCAGCTA\n"
            ">test_sequence\n"
            "ACGTACAGTCGATCGATCAGCTAATCGCTAGCATCG"
        )
    )
    yield docker_data_directory / fasta_path.name
    fasta_path.unlink()


@pytest.fixture(scope="module")
def good_fasta_file(
    module_data_directory: Path, docker_data_directory: Path
):
    fasta_path = module_data_directory / "test_good.fa"
    fasta_path.write_text(
        (
            ">test_sequence_0\n"
            "ACGTACAGTCGATCGATCAGCTA\n"
            ">test_sequence_1\n"
            "ACGTACAGTCGATCGATCAGCTAATCGCTAGCATCG"
        )
    )
    yield docker_data_directory / fasta_path.name
    fasta_path.unlink()


def test_blast_installed(
    celery_container: DockerContainer,
    configured_celery_test_app: Celery,
):
    result = verify_blast_is_installed.delay()
    value = result.get(timeout=10)

    assert value
    result.forget()


def test_query_exists(
    good_fasta_file: Path,
    celery_container: DockerContainer,
    configured_celery_test_app: Celery,
):
    result = verify_query_file_exists.delay(
        query_path=good_fasta_file.as_posix()
    )
    value = result.get(timeout=10)

    assert value == good_fasta_file.as_posix()
    result.forget()


def test_error_if_bad_args_to_blast(
    celery_container: DockerContainer,
    configured_celery_test_app: Celery,
):
    with pytest.raises(CalledProcessError):
        result = verify_blast_is_installed.delay(blast_args=["-bad"])
        result.get(timeout=10)
        result.forget()


def test_fasta_validation_fails_if_not_startswith_caret(
    fasta_file_no_first_caret: Path,
    celery_container: DockerContainer,
    configured_celery_test_app: Celery,
):
    with pytest.raises(NoFirstCaretError):
        verify_query_is_fasta.delay(
            blast_program="blastn",
            query_path=fasta_file_no_first_caret.as_posix(),
        ).get(timeout=10)


def test_fasta_validation_fails_with_duplicate_ids(
    fasta_file_duplicate_ids: Path,
    celery_container: DockerContainer,
    configured_celery_test_app: Celery,
):
    with pytest.raises(DuplicateSequenceIdentifiersError):
        result = verify_query_is_fasta.delay(
            blast_program="blastn",
            # query_path=f"/tests/{fasta_file_duplicate_ids.name}",
            query_path=fasta_file_duplicate_ids.as_posix(),
        )
        result.get(timeout=10)
        result.forget()


def test_fasta_validation_passes(
    good_fasta_file: Path,
    celery_container: DockerContainer,
    configured_celery_test_app: Celery,
):
    result = verify_query_is_fasta.delay(
        blast_program="blastn",
        query_path=good_fasta_file.as_posix(),
    )
    value = result.get(timeout=10)

    assert value == good_fasta_file.as_posix()
