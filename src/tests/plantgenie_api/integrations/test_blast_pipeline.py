from pathlib import Path

import requests
import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.image import DockerImage

# from task_queue.blast.tasks import execute_blast
from shared.constants import OBJECT_STORE_URL

FIXTURES_BUCKET = "pg-testing-fixtures"


@pytest.fixture(scope="package")
def example_blast_database():
    response = requests.get(f"{OBJECT_STORE_URL}/{FIXTURES_BUCKET}")

    available_files = [
        x
        for x in response.text.split("\n")
        if x.startswith("Potra02_CDS.fa")
    ]

    available_file_paths = [
        Path(__file__).parent / f for f in available_files
    ]

    for f, fpath in zip(available_files, available_file_paths):
        response = requests.get(
            f"{OBJECT_STORE_URL}/{FIXTURES_BUCKET}/{f}", stream=True
        )

        with fpath.open("ab") as out:
            for chunk in response.iter_content(chunk_size=100):
                out.write(chunk)

    yield available_file_paths

    for fpath in available_file_paths:
        fpath.unlink()


@pytest.fixture(scope="package")
def example_fasta_file():
    response = requests.get(
        f"{OBJECT_STORE_URL}/{FIXTURES_BUCKET}/test_single_sequence_blast.fasta",
        stream=True,
    )
    fasta_path = Path(__file__).parent / "test_single_sequence_blast.fasta"

    with fasta_path.open("ab") as fasta_handle:
        for chunk in response.iter_content(chunk_size=100):
            fasta_handle.write(chunk)

    yield fasta_path

    fasta_path.unlink()
