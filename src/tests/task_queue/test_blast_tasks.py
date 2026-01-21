from pathlib import Path
from typing import Any, List, Tuple
from uuid import uuid4

import pytest
import requests
from celery import Celery
from celery.result import AsyncResult, GroupResult
from shared.constants import OBJECT_STORE_URL
from task_queue.blast.exceptions import (
    DuplicateSequenceIdentifiersError,
    NoFirstCaretError,
)
from task_queue.blast.models import ExecuteBlastPipelineArgs
from task_queue.blast.tasks import (
    execute_blast_pipeline,
    verify_blast_is_installed,
    verify_query_file_exists,
    verify_query_is_fasta,
)
from testcontainers.core.container import DockerContainer, ExecResult

FIXTURES_BUCKET = "pg-testing-fixtures"


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
def example_blast_database(
    module_data_directory: Path, docker_data_directory: Path
):
    response = requests.get(f"{OBJECT_STORE_URL}/{FIXTURES_BUCKET}")

    available_files = [
        x
        for x in response.text.split("\n")
        if x.startswith("Potra02_CDS.fa")
    ]

    available_file_paths = [
        module_data_directory / f for f in available_files
    ]

    for f, fpath in zip(available_files, available_file_paths):
        response = requests.get(
            f"{OBJECT_STORE_URL}/{FIXTURES_BUCKET}/{f}", stream=True
        )

        with fpath.open("ab") as out:
            for chunk in response.iter_content(chunk_size=100):
                out.write(chunk)

    yield docker_data_directory / "Potra02_CDS.fa"

    for fpath in available_file_paths:
        fpath.unlink()


@pytest.fixture(scope="module")
def example_fasta_for_blast(
    module_data_directory: Path, docker_data_directory: Path
):
    response = requests.get(
        f"{OBJECT_STORE_URL}/{FIXTURES_BUCKET}/test_single_sequence_blast.fasta",
        stream=True,
    )
    fasta_path = module_data_directory / "test_single_sequence_blast.fasta"

    with fasta_path.open("ab") as fasta_handle:
        for chunk in response.iter_content(chunk_size=100):
            fasta_handle.write(chunk)

    yield docker_data_directory / fasta_path.name

    fasta_path.unlink()
    # suffixes = [".asn"]
    suffixes = [".html", ".tsv", ".asn"]

    for suffix in suffixes:
        fasta_path.with_suffix(suffix).unlink()
    # Path(f"{fasta_path.parent}/{fasta_path.stem}.asn").unlink()
    # Path(f"{fasta_path.parent}/{fasta_path.stem}.html").unlink()
    # Path(f"{fasta_path.parent}/{fasta_path.stem}.tsv").unlink()


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
    result_retriever = verify_blast_is_installed.delay(
        blast_program="blastn"
    )
    # .get() will raise an exception if the task failed.
    # If it completes, the task was successful. The return value is None.
    result = result_retriever.get(timeout=10)
    assert result is None
    assert result_retriever.successful()


def test_verify_blast_fails_with_uninstalled_program(
    celery_container: DockerContainer,
    configured_celery_test_app: Celery,
):
    result_retriever = verify_blast_is_installed.delay(
        blast_program="blastnnnn", blast_args=["-bad"]
    )
    with pytest.raises(FileNotFoundError, match="blastnnnn"):
        result_retriever.get(timeout=10)


def test_query_exists(
    good_fasta_file: Path,
    celery_container: DockerContainer,
    configured_celery_test_app: Celery,
):
    # Test success
    result: AsyncResult[str] = verify_query_file_exists.delay(
        query_path=good_fasta_file.as_posix()
    )
    value: str = result.get(timeout=10)
    assert value == good_fasta_file.as_posix()

    # Test failure with custom message
    with pytest.raises(FileNotFoundError, match="Query file not found at"):
        verify_query_file_exists.delay(query_path="blah.txt").get(
            timeout=10
        )


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


def test_blast_pipeline_executes(
    example_blast_database: Path,
    example_fasta_for_blast: Path,
    celery_container: DockerContainer,
    configured_celery_test_app: Celery,
):
    result: ExecResult = celery_container.exec(
        ["test", "-f", example_fasta_for_blast.as_posix()]
    )

    assert result.exit_code == 0

    result: ExecResult = celery_container.exec(
        ["ls", "/tests/test_blast_tasks"]
    )

    print(result.output)

    # assert result.exit_code == 0

    job_id = str(uuid4())

    example_args = ExecuteBlastPipelineArgs(
        job_id=job_id,
        query_path=example_fasta_for_blast.as_posix(),
        database_path=example_blast_database.as_posix(),
        blast_program="blastn",
    )
    # print(example_args)

    async_result: AsyncResult = execute_blast_pipeline.apply_async(
        args=(example_args.model_dump(),), task_id=job_id
    )

    final_result = async_result.get()
    # parent_result = async_result.parent

    # results: List[Tuple[AsyncResult, Any]] = list(async_result.collect())

    # result: ExecResult = celery_container.exec(
    #     ["ls", "/tests/test_blast_tasks"]
    # )

    # print(result.output)

    # assert result.exit_code == 0

    print(f"AsyncResult ID: {async_result.id} {job_id}")
    # Now use collect() on the orchestrator to see its sub-tasks
    # for res, value in async_result.collect():
    #     print(f"Task: {res.name} | Status: {res.status} | Value: {value}")
    # print(chain_final_node)
    # print(get_full_chain_status(chain_final_node))

    print(async_result.name, async_result.result, async_result.id, async_result.status)

    for res in async_result.collect():
        try:
            res0: AsyncResult = res[0]
            print(res0.name, res0.result, res0.id, res0.status)
            if isinstance(res0, GroupResult):
                for r in res0.collect():
                    print(r[0].name, r[0].result, r[0].id, r[0].status)
        except AttributeError:
            pass

    result: ExecResult = celery_container.exec(
        ["ls", "/tests/test_blast_tasks"]
    )

    print(result.output)

    # assert async_result.state == "SUCCESS"

    # for res in results:
    #     print(res)
    # print(res[0].status, res[0].get())
