import math
import subprocess
import time
from pathlib import Path
from typing import List, Optional

import pendulum
from celery import Task
from FastaValidator import fasta_validator
from loguru import logger
from pydantic import BaseModel, Field
from swiftclient.service import (
    SwiftService,
    SwiftUploadObject,
)

from plantgenie_api import BACKEND_DATA_PATH, ENV_DATA_PATH
from plantgenie_api.celery import celery_app

BLAST_PATH = Path(ENV_DATA_PATH) if ENV_DATA_PATH else Path(__file__).parent

swift_service = SwiftService()


class BlastTaskInput(BaseModel):
    query_path: str
    program: str
    database_path: str
    evalue: Optional[float] = Field(default=0.0001)
    max_hits: Optional[int] = Field(default=10)


class BlastSubmitOutput(BaseModel):
    results: List[str]
    errors: List[str]


class RetrieveQueryArgs(BaseModel):
    query_path: str
    program: str
    database_path: str
    evalue: Optional[float] = Field(default=0.0001)
    max_hits: Optional[int] = Field(default=10)


class RetrieveQueryResult(BaseModel):
    program: str
    database_path: str
    evalue: Optional[float] = Field(default=0.0001)
    max_hits: Optional[int] = Field(default=10)
    output_path: Optional[str] = Field(default=None)
    error: Optional[str] = Field(default=None)


class VerifyExistsArgs(BaseModel):
    query_path: str
    program: str
    database_path: str
    evalue: Optional[float] = Field(default=0.0001)
    max_hits: Optional[int] = Field(default=10)


class VerifyExistsResult(BaseModel):
    query_path: str
    program: str
    database_path: str
    evalue: Optional[float] = Field(default=0.0001)
    max_hits: Optional[int] = Field(default=10)


ValidateFastaArgs = VerifyExistsArgs
ValidateFastaResult = VerifyExistsResult


class BlastExecutionResult(BaseModel):
    output_path: str


FormatTsvResult = BlastExecutionResult
FormatHtmlResult = BlastExecutionResult


class ExecuteBlastResult(BaseModel):
    output_path: Optional[str] = Field(default=None)
    stdout: Optional[str] = Field(default=None)
    stderr: Optional[str] = Field(default=None)
    error: bool = Field(default=False)


class BlastFormatOutput(BaseModel):
    command: List[str]
    stdout: Optional[str]
    stderr: Optional[str]
    exit_code: int
    output_path: Optional[str] = Field(default=None)


class BlastFormatResult(BaseModel):
    results: List[BlastFormatOutput]


class UploadPath(BaseModel):
    container: str
    host_path: str
    object_path: str
    error: bool = Field(default=False)


class UploadResult(BaseModel):
    results: List[UploadPath]


class DeleteBlastDataResponse(BaseModel):
    paths: List[str]


def handle_query_file_not_found(task_id: Optional[str], message: str):
    if task_id is None:
        return

    timestamped_message = f"{pendulum.now().to_iso8601_string()} - {message}"

    error_log_path = (BACKEND_DATA_PATH / f"{task_id}-errors.log").resolve()

    with open(error_log_path, "a") as error_log_file:
        print(timestamped_message, file=error_log_file)


NUCLEOTIDES = "ACGTUNRYKMSWBDHV"
AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"
NUCLEOTIDES_SET = set(NUCLEOTIDES)  # IUPAC codes for nucleotides
AMINO_ACIDS_SET = set(AMINO_ACIDS)


@celery_app.task(name="blast.verify_query_exists", bind=True, pydantic=True)
def verify_query_file_exists(
    self: Task, task_args: VerifyExistsArgs
) -> VerifyExistsResult:
    max_retry_attempts = 5

    query_path = Path(task_args.query_path)

    for x in range(0, max_retry_attempts):
        if query_path.exists():
            print(f"Sleeping: {math.pow(2, x)}")
            return VerifyExistsResult(**task_args.model_dump())
        logger.debug(f"Sleeping: {math.pow(2, x)}")
        time.sleep(math.pow(2, x))

    message = f"[{self.name}] {query_path} was not found"
    handle_query_file_not_found(self.request.get("id"), message=message)
    raise FileNotFoundError(message)


@celery_app.task(name="blast.validate_fasta", bind=True, pydantic=True)
def validate_fasta_query(
    self: Task, task_args: ValidateFastaArgs
) -> ValidateFastaResult:
    return_code = fasta_validator(task_args.query_path)
    match return_code:
        case 0:
            print("basic fasta validation passed")
        case 1:
            raise SyntaxError(
                f"{task_args.query_path}, first line does not start with '>'"
            )
        case 2:
            raise SyntaxError(f"{task_args.query_path}, duplicate sequence identifiers")
        case _:
            raise RuntimeError(
                f"Some error occured while processing {task_args.query_path}"
            )

    expected_sequence_characters = (
        AMINO_ACIDS if task_args.program in {"blastp", "blastx"} else NUCLEOTIDES
    )

    expected_sequence_characters_set = (
        AMINO_ACIDS_SET
        if task_args.program in {"blastp", "blastx"}
        else NUCLEOTIDES_SET
    )

    with open(task_args.query_path) as input_fasta:
        for i, line in enumerate(input_fasta):
            if line.startswith(">"):
                continue
            for character in line.strip():
                if character.upper() not in expected_sequence_characters_set:
                    raise ValueError(
                        f"{character} not in {",".join(expected_sequence_characters.split())}"
                    )

    return ValidateFastaResult(**task_args.model_dump())


@celery_app.task(name="blast.execute_search", bind=True, pydantic=True)
def execute_blast_search(
    self: Task, task_args: ValidateFastaResult
) -> BlastExecutionResult:

    result_base_path = Path(task_args.query_path).stem
    result_output_path = (
        (BACKEND_DATA_PATH / "blast_results" / f"{result_base_path}.asn")
        .resolve()
        .as_posix()
    )

    blast_cmd = [
        task_args.program,
        "-query",
        task_args.query_path,
        "-db",
        task_args.database_path,
        "-outfmt",
        "11",  # 11 = BLAST archive (ASN.1),
        "-evalue",
        str(task_args.evalue),
        "-max_target_seqs",
        str(task_args.max_hits),
        "-out",
        result_output_path,
    ]

    completed_blast_process = subprocess.run(blast_cmd, capture_output=True, text=True)
    completed_blast_process.check_returncode()

    return BlastExecutionResult(output_path=result_output_path)


@celery_app.task(name="blast.format_result_tsv", bind=True, pydantic=True)
def format_blast_result_tsv(
    self: Task, task_args: BlastExecutionResult
) -> FormatTsvResult:
    result_path = Path(task_args.output_path)
    output_tsv = f"{result_path.parent}/{result_path.stem}.tsv"

    blast_format_tsv = [
        "blast_formatter",
        "-archive",
        task_args.output_path,
        "-outfmt",
        "6",
        "-out",
        output_tsv,
    ]

    blast_format_process = subprocess.run(
        blast_format_tsv, capture_output=True, text=True
    )
    blast_format_process.check_returncode()

    return FormatTsvResult(output_path=output_tsv)


@celery_app.task(name="blast.format_result_html", bind=True, pydantic=True)
def format_blast_result_html(
    self: Task, task_args: BlastExecutionResult
) -> FormatHtmlResult:
    # result_path is the tsv result from the previous task
    result_path = Path(task_args.output_path)
    asn_path = f"{result_path.parent}/{result_path.stem}.asn"
    output_html = f"{result_path.parent}/{result_path.stem}.html"

    blast_format_html = [
        "blast_formatter",
        "-archive",
        asn_path,
        "-out",
        output_html,
        "-html"
    ]

    blast_format_process = subprocess.run(
        blast_format_html, capture_output=True, text=True
    )
    blast_format_process.check_returncode()

    return FormatHtmlResult(output_path=output_html)


@celery_app.task(
    name="blast.upload_to_bucket", bind=True, acks_late=True, pydantic=True
)
def upload_blast_data_to_storage_bucket(
    self: Task, task_args: FormatHtmlResult
) -> UploadResult:
    job_id = Path(task_args.output_path).stem
    query_file = BACKEND_DATA_PATH / "blast_queries" / f"{job_id}.fa"
    results_glob = (BACKEND_DATA_PATH / "blast_results").glob(f"{job_id}.*")
    logs_glob = (BACKEND_DATA_PATH / "blast_logs").glob(f"{job_id}.*")

    upload_objects = [
        SwiftUploadObject(
            source=query_file.as_posix(), object_name=f"blast_queries/{query_file.name}"
        )
    ]

    for result in results_glob:
        upload_objects.append(
            SwiftUploadObject(
                source=result.as_posix(), object_name=f"blast_results/{result.name}"
            )
        )

    for log in logs_glob:
        upload_objects.append(
            SwiftUploadObject(
                source=log.as_posix(), object_name=f"blast_logs/{log.name}"
            )
        )

    results = swift_service.upload("plantgenie-share", objects=upload_objects)

    # get rid of container create result
    next(results)

    return UploadResult(
        results=[
            UploadPath(
                container="plantgenie-share",
                host_path=obj.source,
                object_path=obj.object_name,
                error="error" in result,
            )
            for obj, result in zip(upload_objects, results)
        ]
    )


class DeleteBlastDataArgs(BaseModel):
    job_id: str


@celery_app.task(name="blast.delete_data", bind=True, pydantic=True)
def delete_blast_data(
    self: Task, task_args: DeleteBlastDataArgs
) -> DeleteBlastDataResponse:
    query_file = BACKEND_DATA_PATH / "blast_queries" / f"{task_args.job_id}.fa"
    results_glob = (BACKEND_DATA_PATH / "blast_results").glob(f"{task_args.job_id}.*")
    logs_glob = (BACKEND_DATA_PATH / "blast_logs").glob(f"{task_args.job_id}.*")

    data_to_delete = [query_file, *list(results_glob), *list(logs_glob)]

    for f in data_to_delete:
        f.unlink()

    return DeleteBlastDataResponse(
        paths=[uploaded_object.as_posix() for uploaded_object in data_to_delete]
    )
