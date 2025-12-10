import subprocess
from pathlib import Path
from typing import List, Literal

from celery import chain, group
from FastaValidator import fasta_validator
from swiftclient.service import SwiftUploadObject

from task_queue.celery import app
from task_queue.blast.models import (
    ExecuteBlastArgs,
)

from task_queue.blast.exceptions import (
    NoFirstCaretError,
    DuplicateSequenceIdentifiersError,
)

from shared.config import backend_config
from shared.constants import BLAST_SERVICE_BUCKET_NAME
from shared.services import get_swift_service

NUCLEOTIDES = "ACGTUNRYKMSWBDHV"
AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"
NUCLEOTIDES_SET = set(NUCLEOTIDES)  # IUPAC codes for nucleotides
AMINO_ACIDS_SET = set(AMINO_ACIDS)


@app.task(name="blast.verify_installation")
def verify_blast_is_installed(
    blast_args: List[str] = ["-version"],
) -> bool:
    subprocess.run(
        ["blastn"] + blast_args, check=True, capture_output=True, text=True
    )
    return True


@app.task(name="blast.verify_query_exists")
def verify_query_file_exists(query_path: str) -> str:
    query_as_path = Path(query_path)
    if not Path(query_as_path).exists():
        raise FileNotFoundError(
            f"{query_as_path.resolve().as_posix()} was not found"
        )
    return query_path


@app.task(name="blast.verify_query_is_fasta")
def verify_query_is_fasta(
    query_path: str, blast_program: Literal["blastn", "blastx", "blastp"]
) -> str:
    return_code = fasta_validator(query_path)

    match return_code:
        case 0:
            print("basic fasta validation passed")
        case 1:
            raise NoFirstCaretError(
                f"{query_path}, first line does not start with '>'"
            )
        case 2:
            raise DuplicateSequenceIdentifiersError(
                f"{query_path}, duplicate sequence identifiers"
            )
        case _:
            raise RuntimeError(
                f"Some error occured while processing {query_path}"
            )

    expected_sequence_characters = (
        AMINO_ACIDS
        if blast_program in {"blastp", "blastx"}
        else NUCLEOTIDES
    )

    expected_sequence_characters_set = (
        AMINO_ACIDS_SET
        if blast_program in {"blastp", "blastx"}
        else NUCLEOTIDES_SET
    )

    with open(query_path) as input_fasta:
        for i, line in enumerate(input_fasta):
            if line.startswith(">"):
                continue
            for character in line.strip():
                if (
                    character.upper()
                    not in expected_sequence_characters_set
                ):
                    raise ValueError(
                        f"{character} found on line {i} not in {",".join(expected_sequence_characters.split())}"
                    )
    return query_path


@app.task(name="blast.execute_search", pydantic=True)
def execute_blast(args: ExecuteBlastArgs) -> str:
    # raises FileNotFoundError if file doesn't exist
    query_path = Path(args.query_path).resolve(strict=True)
    # raises FileNotFoundError if file doesn't exist
    database_path = Path(args.database_path).resolve(strict=True)
    result_path = f"{query_path.parent}/{query_path.stem}.asn"

    blast_cmd = [
        args.program_name,
        "-query",
        query_path.as_posix(),
        "-db",
        database_path.as_posix(),
        "-outfmt",
        "11",  # 11 = BLAST archive (ASN.1),
        "-evalue",
        str(args.evalue),
        "-max_target_seqs",
        str(args.max_hits),
        "-out",
        result_path,
    ]

    subprocess.run(blast_cmd, capture_output=True, text=True, check=True)

    return result_path


@app.task(name="blast.format_result_tsv")
def blast_result_format_tsv(input_asn_path: str) -> str:
    # raises FileNotFoundError if file doesn't exist
    input_path = Path(input_asn_path).resolve(strict=True)
    output_path = f"{input_path.parent}/{input_path.stem}.tsv"

    blast_format_tsv = [
        "blast_formatter",
        "-archive",
        input_asn_path,
        "-outfmt",
        "6",
        "-out",
        output_path,
    ]

    # raises CalledProcessError
    subprocess.run(
        blast_format_tsv, capture_output=True, text=True, check=True
    )

    return output_path


@app.task(name="blast.format_result_html")
def blast_result_format_html(input_asn_path: str) -> str:
    # raises FileNotFoundError if file doesn't exist
    input_path = Path(input_asn_path).resolve(strict=True)
    output_path = f"{input_path.parent}/{input_path.stem}.html"

    blast_format_html = [
        "blast_formatter",
        "-archive",
        input_asn_path,
        "-out",
        output_path,
        "-html",
    ]

    # raises CalledProcessError
    subprocess.run(
        blast_format_html, capture_output=True, text=True, check=True
    )

    return output_path


@app.task(name="blast.upload_results_to_object_store")
def upload_results_to_object_store(query_path: str) -> List[str]:
    input_query_path = Path(query_path).resolve(strict=True)
    blast_files_glob = input_query_path.glob(f"{input_query_path.stem}.*")

    swift_service = get_swift_service(backend_config)

    upload_objects = [
        SwiftUploadObject(source=f.as_posix(), object_name=f.name)
        for f in blast_files_glob
    ]

    results = swift_service.upload(
        BLAST_SERVICE_BUCKET_NAME, objects=upload_objects
    )

    # tries to create bucket everytime instead of just checking existence
    next(results)

    for res in results:
        pass

    return [obj.source for obj in upload_objects]


@app.task(name="blast.purge_results")
def purge_blast_data(query_path: str) -> List[str]:
    # raises FileNotFoundError
    input_query_path = Path(query_path).resolve(strict=True)
    blast_files_glob = input_query_path.glob(f"{input_query_path.stem}.*")

    for f in blast_files_glob:
        f.unlink()

    return [f.as_posix() for f in blast_files_glob]
