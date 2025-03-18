import os
import subprocess
import tempfile
import time
from celery import Celery
from .celery import celery_app  # Import the Celery instance

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
        "program": "blastx",
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

        # Create a temporary file to store the query sequence
        # with tempfile.NamedTemporaryFile(mode="w", delete=False) as query_file:
        #     # query_file.write(query_sequence)
        #     query_file_path = query_file.name

        # Construct BLAST command
        results_file_path = f"{BLAST_DB_PATH}/{self.request.id}_blast_results.tsv"
        blast_cmd = [
            blast_program,
            "-query",
            query_file_path,
            "-db",
            blast_db,
            "-outfmt",
            "6",  # Tabular output format
            "-evalue",
            str(evalue),
            "-max_target_seqs",
            str(max_hits),
            "-out", results_file_path
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


# @celery_app.task(bind=True)
# def fake_blast_task(self, job_id: str):
#     """
#     Simulates running BLAST by sleeping for 5 seconds, then returning a fake result.
#     """
#     time.sleep(5)  # Simulate BLAST processing time
#     return f"Fake BLAST result for job {self.request.id}"
