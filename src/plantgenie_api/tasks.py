import os
import subprocess
import tempfile
import time
from celery import Celery, chain
from .celery import celery_app  # Import the Celery instance

from os import PathLike

from celery import Task

BLAST_DB_PATH = "/data"

# Mapping query types to BLAST programs and databases
BLAST_CONFIG = {
    "protein": {
        "db": os.path.join(BLAST_DB_PATH, "Picab02_230926_at01_all_aa.fa"),
        "program": "blastp",
    },
    "mrna": {
        "db": os.path.join(BLAST_DB_PATH, "Picab02_230926_at01_all_mRNA.fa"),
        "program": "blastn",
    },
    "cds": {
        "db": os.path.join(BLAST_DB_PATH, "Picab02_230926_at01_all_cds.fa"),
        "program": "blastn",
    },
    "genome": {
        "db": os.path.join(BLAST_DB_PATH, "Picab02_chromosomes_bgzipped.fasta"),
        "program": "blastn",
    },
}


class BlastTask(Task):
    name = "bioinformatics.blast_task"
    acks_late = True

    def run(
        self,
        query_file_path: str,
        blast_type: str,
        evalue: float = 0.001,
        max_hits: int = 10,
    ):
        """
        Executes a BLAST search using the specified query sequence and BLAST type.

        :param query_sequence: Nucleotide or protein sequence to search.
        :param blast_type: Type of BLAST DB to use (protein, mrna, cds, genome).
        :param evalue: E-value threshold for hits.
        :param max_hits: Maximum number of hits to return.
        :return: BLAST output as a string.
        """
        if blast_type not in BLAST_CONFIG:
            raise ValueError(
                f"Invalid BLAST type: {blast_type}. Choose from {list(BLAST_CONFIG.keys())}."
            )

        blast_program = BLAST_CONFIG[blast_type]["program"]
        blast_db = BLAST_CONFIG[blast_type]["db"]

        # Construct BLAST command
        results_file_path = f"{BLAST_DB_PATH}/{self.request.id}_blast_results.asn"
        blast_cmd = [
            blast_program,
            "-query",
            query_file_path,
            "-db",
            blast_db,
            "-outfmt",
            "11",  # Tabular output format
            "-evalue",
            str(evalue),
            "-max_target_seqs",
            str(max_hits),
            "-out",
            results_file_path,
        ]

        try:
            # Execute BLAST
            result = subprocess.run(
                blast_cmd, capture_output=True, text=True, check=True
            )
            output = result.stdout
        except subprocess.CalledProcessError as e:
            output = f"BLAST error: {e.stderr}"

        # chain(blast_formatter_task).apply_async(args=(results_file_path,))
        # chain(delete_results_task).apply_async(
        #     args=(query_file_path, results_file_path), countdown=1800
        # )

        return output


class BlastResultToHtmlTask(Task):
    def run(self, results_file_path: str):
        blast_cmd = [
            "blast_formatter",
            "-archive",
            results_file_path,
            "-out",
            results_file_path.split(".")[0] + ".html",
            "-html",
        ]

        try:
            # Execute BLAST
            result = subprocess.run(
                blast_cmd, capture_output=True, text=True, check=True
            )
            output = result.stdout
        except subprocess.CalledProcessError as e:
            output = f"BLAST error: {e.stderr}"

        return output


class BlastResultToTabularTask(Task):
    def run(self, results_file_path: str):
        blast_cmd = [
            "blast_formatter",
            "-archive",
            results_file_path,
            "-outfmt 6"
            "-out",
            results_file_path.split(".")[0] + ".tsv",
            "-html",
        ]

        try:
            # Execute BLAST
            result = subprocess.run(
                blast_cmd, capture_output=True, text=True, check=True
            )
            output = result.stdout
        except subprocess.CalledProcessError as e:
            output = f"BLAST error: {e.stderr}"

        return output

class DeleteResultsTask(Task):
    name = "bioinformatics.clean_up"
    acks_late = True

    def run(self, query_file_path: str, results_file_path: str):
        if os.path.exists(path=query_file_path):
            # clean dir
            pass

        if os.path.exists(path=results_file_path):
            pass

        if os.path.exists(path=results_file_path.split(".")[0] + ".html"):
            pass


class FakeBlastTask(Task):
    name = "custom.fake_blast_task"
    acks_late = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run(self, job_id: str):
        time.sleep(5)
        return f"Fake BLAST result for job {self.request.id}"


fake_blast_task = celery_app.register_task(FakeBlastTask())
real_blast_task = celery_app.register_task(BlastTask())
blast_formatter_task = celery_app.register_task(BlastResultToHtmlTask())
delete_results_task = celery_app.register_task(DeleteResultsTask())

# @celery_app.task(bind=True)
# def fake_blast_task(self, job_id: str):
#     """
#     Simulates running BLAST by sleeping for 5 seconds, then returning a fake result.
#     """
#     time.sleep(5)  # Simulate BLAST processing time
#     return f"Fake BLAST result for job {self.request.id}"
