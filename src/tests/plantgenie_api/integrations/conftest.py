from pathlib import Path

import requests
import pytest

from shared.constants import OBJECT_STORE_URL

FIXTURES_BUCKET = "pg-testing-fixtures"

@pytest.fixture(scope="module")
def module_data_directory(host_data_directory: Path):
    p = host_data_directory / "test_integrations"
    p.mkdir(exist_ok=True, parents=True)
    yield p
    p.rmdir()


@pytest.fixture(scope="module")
def docker_data_directory():
    p = Path("/tests/test_integrations")
    yield p


@pytest.fixture(scope="package")
def example_blast_database(module_data_directory: Path):
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

    yield available_file_paths

    for fpath in available_file_paths:
        fpath.unlink()


@pytest.fixture(scope="package")
def example_fasta_file(module_data_directory: Path):
    response = requests.get(
        f"{OBJECT_STORE_URL}/{FIXTURES_BUCKET}/test_single_sequence_blast.fasta",
        stream=True,
    )
    fasta_path = module_data_directory / "test_single_sequence_blast.fasta"

    with fasta_path.open("ab") as fasta_handle:
        for chunk in response.iter_content(chunk_size=100):
            fasta_handle.write(chunk)

    yield fasta_path

    fasta_path.unlink()
