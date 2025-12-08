import subprocess
from pathlib import Path
from typing import List

from FastaValidator import fasta_validator  # type: ignore

from task_queue.celery import app
from task_queue.blast.models import (
    ExecuteBlastArgs,
)

from task_queue.blast.exceptions import (
    NoFirstCaretError,
    DuplicateSequenceIdentifiersError,
)

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
def verify_query_is_fasta(query_path: str, blast_program: str) -> str:
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
    query_path = Path(args.query_path)
    database_path = Path(args.database_path)
    result_path = Path(args.result_path)
    blast_cmd = [
        args.program,
        "-query",
        query_path.resolve().as_posix(),
        "-db",
        database_path.resolve().as_posix(),
        "-outfmt",
        "11",  # 11 = BLAST archive (ASN.1),
        "-evalue",
        str(args.evalue),
        "-max_target_seqs",
        str(args.max_hits),
        "-out",
        result_path.resolve().as_posix(),
    ]

    subprocess.run(blast_cmd, capture_output=True, text=True, check=True)

    return args.result_path


@app.task(name="blast.format_result_tsv")
def blast_result_format_tsv():
    pass


@app.task(name="blast.format_result_html")
def blast_result_format_html():
    pass
