from pathlib import Path

from testcontainers.core.container import DockerContainer, ExecResult


def test_can_execute_blast(
    celery_container: DockerContainer,
):
    result: ExecResult = celery_container.exec(["blastn", "-help"])
    assert result.exit_code == 0


def test_execute_simple_blast(
    example_blast_database: Path,
    example_fasta_file: Path,
    celery_container: DockerContainer,
):
    result: ExecResult = celery_container.exec(
        [
            "blastn",
            "-query",
            example_fasta_file.as_posix(),
            "-db",
            example_blast_database.as_posix(),
            "-outfmt",
            "6",
            "-evalue",
            "0.01",
            "-max_target_seqs",
            "10",
        ],
    )

    assert result.exit_code == 0
