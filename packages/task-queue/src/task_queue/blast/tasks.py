import mimetypes
import subprocess
from pathlib import Path
from typing import List

from celery import Task, chain
from FastaValidator import fasta_validator  # type: ignore
from shared.constants import BLAST_SERVICE_BUCKET_NAME
from shared.services.openstack import (
    SwiftClient,
    SwiftUploadableObject,
)

from task_queue.blast import BlastProgram
from task_queue.blast.exceptions import (
    DuplicateSequenceIdentifiersError,
    NoFirstCaretError,
)
from task_queue.blast.models import (
    ExecuteBlastPipelineArgs,
)
from task_queue.celery import app
from task_queue.tasks import (
    PathValidationTask,
    SubprocessPathValidationTask,
    SubprocessTask,
)

NUCLEOTIDES = "ACGTUNRYKMSWBDHV"
AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"
NUCLEOTIDES_SET = set(NUCLEOTIDES)
AMINO_ACIDS_SET = set(AMINO_ACIDS)
mimetypes.add_type("application/octet-stream", ".asn")


@app.task(
    name="blast.verify_installation",
    typing=True,
    bind=True,
    base=SubprocessTask,
)
def verify_blast_is_installed(
    self: Task,
    blast_program: BlastProgram = "blastn",
    blast_args: List[str] = ["-version"],
) -> None:
    subprocess.run(
        args=[blast_program, *blast_args],
        check=False,
        capture_output=True,
        text=True,
    )


@app.task(
    name="blast.verify_query_exists",
    base=PathValidationTask,
    files_to_validate={"query_path": "Query file"},
)
def verify_query_file_exists(query_path: str) -> str:
    return query_path


@app.task(name="blast.verify_query_is_fasta")
def verify_query_is_fasta(
    query_path: str, blast_program: BlastProgram
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
                        f"{character} found on line {i} not in {','.join(expected_sequence_characters.split())}"
                    )
    return query_path


@app.task(
    name="blast.execute_search",
    base=SubprocessPathValidationTask,
    files_to_validate={
        "query_path": "Query file",
        # "database_path": "Blast database",
    },
)
def execute_blast(
    blast_program: BlastProgram,
    query_path: str,
    database_path: str,
    evalue: float = 0.0001,
    max_hits: int = 10,
) -> str:
    resolved_query_path = Path(query_path).resolve()
    resolved_database_path = Path(database_path).resolve()
    result_path = resolved_query_path.with_suffix(".asn").as_posix()

    blast_cmd = [
        blast_program,
        "-query",
        resolved_query_path.as_posix(),
        "-db",
        resolved_database_path.as_posix(),
        "-outfmt",
        "11",  # 11 = BLAST archive (ASN.1),
        "-evalue",
        str(evalue),
        "-max_target_seqs",
        str(max_hits),
        "-out",
        result_path,
    ]

    subprocess.run(blast_cmd, capture_output=True, text=True, check=True)

    return result_path


@app.task(
    name="blast.format_result_tsv",
    base=SubprocessPathValidationTask,
    files_to_validate={"input_asn_path": "Input ASN file"},
)
def blast_result_format_tsv(input_asn_path: str) -> str:
    resolved_input_path = Path(input_asn_path).resolve()
    output_path = resolved_input_path.with_suffix(".tsv").as_posix()

    blast_format_tsv = [
        "blast_formatter",
        "-archive",
        resolved_input_path.as_posix(),
        "-outfmt",
        "6",
        "-out",
        output_path,
    ]

    subprocess.run(
        blast_format_tsv, capture_output=True, text=True, check=True
    )

    return input_asn_path


@app.task(
    name="blast.format_result_html",
    base=SubprocessPathValidationTask,
    files_to_validate={"input_asn_path": "Input ASN file"},
)
def blast_result_format_html(input_asn_path: str) -> str:
    resolved_input_path = Path(input_asn_path).resolve()
    output_path = resolved_input_path.with_suffix(".html").as_posix()

    blast_format_html = [
        "blast_formatter",
        "-archive",
        resolved_input_path.as_posix(),
        "-out",
        output_path,
        "-html",
    ]

    subprocess.run(
        blast_format_html, capture_output=True, text=True, check=True
    )

    return input_asn_path


@app.task(
    name="blast.upload_results_to_object_store",
    base=PathValidationTask,
    files_to_validate={"query_path": "Query file"},
)
def upload_results_to_object_store(query_path: str) -> List[str]:
    resolved_query_path = Path(query_path).resolve()
    blast_files_glob = resolved_query_path.parent.glob(
        f"{resolved_query_path.stem}.*"
    )

    swift_client = SwiftClient()

    uploadables = [
        SwiftUploadableObject(
            local_path=f.as_posix(),
            object_name=f.name,
            content_type=mimetypes.guess_type(f.name)[0],
        )
        for f in blast_files_glob
    ]

    swift_client.upload_objects(
        container=BLAST_SERVICE_BUCKET_NAME, objects=uploadables
    )

    return [obj.local_path for obj in uploadables]


@app.task(name="blast.execute_blast_pipeline", pydantic=True)
def execute_blast_pipeline(args: ExecuteBlastPipelineArgs):
    workflow = chain(
        verify_blast_is_installed.si(
            blast_program=args.blast_program, blast_args=["-version"]
        ),
        verify_query_file_exists.si(query_path=args.query_path),
        execute_blast.si(
            blast_program=args.blast_program,
            query_path=args.query_path,
            database_path=args.database_path,
            evalue=args.evalue,
            max_hits=args.max_hits,
        ),
        blast_result_format_html.s(),
        blast_result_format_tsv.s(),
        upload_results_to_object_store.si(query_path=args.query_path),
    )

    return workflow()
