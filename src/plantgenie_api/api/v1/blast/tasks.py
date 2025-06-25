import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from celery import Task
from pydantic import BaseModel, Field
from swiftclient.service import (
    SwiftService,
    ClientException,
    SwiftError,
    SwiftUploadObject,
)

from plantgenie_api import ENV_DATA_PATH
from plantgenie_api.celery import celery_app

BLAST_PATH = Path(ENV_DATA_PATH) if ENV_DATA_PATH else Path(__file__).parent

# swift_service = SwiftService(
#     options={
#         "auth_type": os.environ["OS_AUTH_TYPE"],
#         "auth_url": os.environ["OS_AUTH_URL"],
#         "identity_api_version": os.environ["OS_IDENTITY_API_VERSION"],
#         "region_name": os.environ["OS_REGION_NAME"],
#         "interface": os.environ["OS_INTERFACE"],
#         "application_credential_id": os.environ["OS_APPLICATION_CREDENTIAL_ID"],
#         "application_credential_secret": os.environ["OS_APPLICATION_CREDENTIAL_SECRET"],
#     }
# )

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
    output_path: Optional[str]
    error: Optional[str]


class ExecuteBlastResult(BaseModel):
    output_path: Optional[str]
    stdout: Optional[str]
    stderr: Optional[str]
    error: bool = Field(default=False)


class BlastFormatOutput(BaseModel):
    command: List[str]
    stdout: Optional[str]
    stderr: Optional[str]
    exit_code: int
    output_path: Optional[str]


class BlastFormatResult(BaseModel):
    results: List[BlastFormatOutput]


class UploadPath(BaseModel):
    container: str
    host_path: str
    object_path: str
    error: bool = Field(default=False)


class UploadResult(BaseModel):
    results: List[UploadPath]


@celery_app.task(name="blast.retrieve_query", bind=True, acks_late=True, pydantic=True)
def retrieve_query_from_object_store(
    self: Task, task_args: RetrieveQueryArgs
) -> RetrieveQueryResult:

    # print(task_args)
    # print(f"[blast_execute_task] path to download {task_args.query_path}")

    max_attempts = 5

    for attempt in range(max_attempts):
        result = next(
            swift_service.download(
                container="plantgenie-share",
                objects=[task_args.query_path],
                options={"out_directory": BLAST_PATH},
            )
        )

        # don't sleep on last attempt
        if result["success"] or attempt == (max_attempts - 1):
            break

        if "error" in result and isinstance(result["error"], ClientException):
            time.sleep((attempt + 1) * 2)
            continue

    return RetrieveQueryResult(
        program=task_args.program,
        database_path=task_args.database_path,
        evalue=task_args.evalue,
        max_hits=task_args.max_hits,
        output_path=result["path"] if "path" in result else None,
        error=result["error"] if "error" in result else None,
    )


@celery_app.task(name="blast.execute_query", bind=True, pydantic=True)
def execute_blast_query(
    self: Task, task_args: RetrieveQueryResult
) -> ExecuteBlastResult:

    if task_args.error is not None:
        return ExecuteBlastResult(error=True)

    result_base_path = Path(task_args.output_path).stem
    result_output_path = f"{BLAST_PATH}/blast_files/{result_base_path}.asn"

    blast_cmd = [
        task_args.program,
        "-query",
        task_args.output_path,
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

    command_errored = False
    result_stdout = None
    result_stderr = None

    try:
        blast_result = subprocess.run(
            blast_cmd, capture_output=True, text=True, check=True
        )
        result_stdout = blast_result.stdout
        result_stderr = blast_result.stderr
    except subprocess.CalledProcessError as error:
        command_errored = True
        result_stderr = error.stderr

    return ExecuteBlastResult(
        output_path=result_output_path if not (command_errored) else None,
        stdout=result_stdout,
        stderr=result_stderr,
        error=command_errored,
    )


@celery_app.task(name="blast.format_result", bind=True, pydantic=True)
def format_blast_result(self: Task, task_args: ExecuteBlastResult) -> BlastFormatResult:

    result_path = Path(task_args.output_path)
    output_html = f"{result_path.parent}/{result_path.stem}.html"
    output_tsv = f"{result_path.parent}/{result_path.stem}.tsv"

    blast_format_html = [
        "blast_formatter",
        "-archive",
        task_args.output_path,
        "-out",
        output_html,
        "-html",
    ]

    blast_format_tsv = [
        "blast_formatter",
        "-archive",
        task_args.output_path,
        "-outfmt",
        "6",
        "-out",
        output_tsv,
    ]

    try:
        result = subprocess.run(
            blast_format_html,
            capture_output=True,
            text=True,
            check=True,
        )

        html_output = BlastFormatOutput(
            command=result.args,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            output_path=output_html,
        )
    except subprocess.CalledProcessError as error:
        html_output = BlastFormatOutput(
            command=error.cmd,
            stdout=error.stdout,
            stderr=error.stderr,
            exit_code=error.returncode,
        )

    try:
        result = subprocess.run(
            blast_format_tsv,
            capture_output=True,
            text=True,
            check=True,
        )

        tsv_output = BlastFormatOutput(
            command=result.args,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            output_path=output_tsv,
        )
    except subprocess.CalledProcessError as error:
        tsv_output = BlastFormatOutput(
            command=error.cmd,
            stdout=error.stdout,
            stderr=error.stderr,
            exit_code=error.returncode,
        )

    return BlastFormatResult(
        results=[
            BlastFormatOutput(
                command=[],
                output_path=task_args.output_path,
                exit_code=0,
                stdout=None,
                stderr=None,
            ),
            html_output,
            tsv_output,
        ]
    )


@celery_app.task(name="blast.upload_result", bind=True, pydantic=True)
def upload_blast_result(self: Task, task_args: BlastFormatResult) -> UploadResult:
    objects_to_upload = []
    for result in task_args.results:
        if result.exit_code != 0:
            continue
        output_path = Path(result.output_path)
        upload_object = SwiftUploadObject(
            source=result.output_path, object_name=f"blast_files/{output_path.name}"
        )
        objects_to_upload.append(upload_object)

    results = swift_service.upload("plantgenie-share", objects=objects_to_upload)

    # get rid of create_container result
    next(results)

    return UploadResult(
        results=[
            UploadPath(
                container="plantgenie-share",
                host_path=obj.source,
                object_path=obj.object_name,
                error="error" in result,
            )
            for obj, result in zip(objects_to_upload, results)
        ]
    )


celery_app.register_task(retrieve_query_from_object_store)

# @celery_app.task(name="blast.submit", bind=True, acks_late=True, pydantic=True)
# def blast_submit_task(self: Task, task_args: BlastTaskInput) -> BlastSubmitOutput:
#     results_base_path = f"{BLAST_PATH}/{self.request.id}_results"

#     output = BlastSubmitOutput(results=[], errors=[])
#     local_download_path: Optional[str] = None

#     try:
#         results = swift_service.download(
#             container="plantgenie-share",
#             objects=[task_args.query_path],
#             options={"out_directory": BLAST_PATH},
#         )

#         for result in results:
#             # output.results.append(result["success"])
#             print(result)
#             local_download_path = result.get("path", None)

#     except (ClientException, SwiftError) as err:
#         # output.errors.append(err.)
#         pass

#     if local_download_path is None:
#         output.errors.append(f"No output path found for {task_args.query_path}")
#         return output

#     blast_cmd = [
#         task_args.program,
#         "-query",
#         task_args.query_path,
#         "-db",
#         task_args.database_path,
#         "-outfmt",
#         "11",  # Tabular output format
#         "-evalue",
#         str(task_args.evalue),
#         "-max_target_seqs",
#         str(task_args.max_hits),
#         "-out",
#         f"{results_base_path}.asn",
#     ]

#     output.results.append(f"Executed command: {" ".join(blast_cmd)}\n")

#     try:
#         blast_result = subprocess.run(
#             blast_cmd, capture_output=True, text=True, check=True
#         )
#         output.results.append(f"BLAST results: {blast_result.stdout}")
#     except subprocess.CalledProcessError as err:
#         output.errors.append(f"BLAST error: {err.stderr}")
#         return output

#     blast_cmd = [
#         "blast_formatter",
#         "-archive",
#         f"{results_base_path}.asn",
#         "-out",
#         f"{results_base_path}.html",
#         "-html",
#     ]

#     try:
#         blast_html_result = subprocess.run(
#             blast_cmd, capture_output=True, text=True, check=True
#         )
#         output.results.append(f"BLAST format HTML results: {blast_html_result.stdout}")

#     except subprocess.CalledProcessError as e:
#         output.errors.append(f"BLAST format HTML error: {e.stderr}")
#         return output

#     blast_cmd = [
#         "blast_formatter",
#         "-archive",
#         f"{results_base_path}.asn",
#         "-outfmt",
#         "6",
#         "-out",
#         f"{results_base_path}.tsv",
#     ]

#     try:
#         blast_tsv_result = subprocess.run(
#             blast_cmd, capture_output=True, text=True, check=True
#         )
#         output.results.append(f"BLAST format tsv results: {blast_tsv_result.stdout}")
#     except subprocess.CalledProcessError as e:
#         output.errors.append(f"BLAST format tsv error: {e.stderr}")
#         return output
#     return output
