import gzip
import threading
from pathlib import Path

import pytest
from httpx import AsyncClient
from kombu.exceptions import OperationalError
from task_queue.blast.tasks import add_gene_columns, run_blast_search

from tests.plantgenie_api.unit.conftest import FakeNeo4jSession

MAX_QUERY_BYTES = 2**20
VALID_QUERY = ">my sequence\nACGTACGTACGT"


@pytest.mark.anyio
async def test_submit_blast_413s_when_the_query_is_over_a_megabyte(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
):
    query = ">too big\n" + "A" * MAX_QUERY_BYTES

    response = await async_client.post(
        "/v2/blast",
        json={
            "databaseId": "picab-v2.0-cds",
            "program": "blastn",
            "query": query,
        },
    )

    assert response.status_code == 413


@pytest.mark.parametrize(
    "query",
    [
        "ACGTACGTACGT",
        ">a header with no sequence under it\n",
        ">contains characters that are neither\nACGT1234@@@",
    ],
    ids=["no header", "no residues", "illegal characters"],
)
@pytest.mark.anyio
async def test_submit_blast_422s_when_the_query_is_not_fasta(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
    query: str,
):
    response = await async_client.post(
        "/v2/blast",
        json={
            "databaseId": "picab-v2.0-cds",
            "program": "blastn",
            "query": query,
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_submit_blast_404s_for_an_unknown_database(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
):
    neo4j_session.next_records = []

    response = await async_client.post(
        "/v2/blast",
        json={
            "databaseId": "no-such-database",
            "program": "blastn",
            "query": VALID_QUERY,
        },
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    "program,molecule_type",
    [
        ("blastp", "nucl"),
        ("blastn", "prot"),
        ("tblastn", "nucl"),
    ],
    ids=[
        "protein program against nucleotides",
        "nucleotide program against proteins",
        "protein query program for a nucleotide query",
    ],
)
@pytest.mark.anyio
async def test_submit_blast_422s_when_the_program_does_not_fit(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
    program: str,
    molecule_type: str,
):
    neo4j_session.next_records = [
        {
            "db": {
                "id": "picab-v2.0-cds",
                "moleculeType": molecule_type,
                "path": "picab/v2/v2.0/blast/nucl/coding-sequences.fa",
            }
        }
    ]

    response = await async_client.post(
        "/v2/blast",
        json={
            "databaseId": "picab-v2.0-cds",
            "program": program,
            "query": VALID_QUERY,
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "marker_exists,expected_status", [(True, 200), (False, 503)]
)
@pytest.mark.anyio
async def test_submit_blast_requires_the_data_ready_marker(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    marker_exists: bool,
    expected_status: int,
):
    monkeypatch.setattr(
        run_blast_search, "apply_async", lambda **kwargs: None
    )
    if marker_exists:
        (tmp_path / ".data-ready").touch()
    neo4j_session.next_records = [
        {
            "db": {
                "id": "picab-v2.0-cds",
                "moleculeType": "nucl",
                "path": "picab/v2/v2.0/blast/nucl/coding-sequences.fa",
            },
            "annotationId": "picab-v2.0",
            "annotationPath": "picab/v2/v2.0",
        }
    ]

    response = await async_client.post(
        "/v2/blast",
        json={
            "databaseId": "picab-v2.0-cds",
            "program": "blastn",
            "query": VALID_QUERY,
        },
    )

    assert response.status_code == expected_status


async def submit_valid_blast(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
    tmp_path: Path,
):
    (tmp_path / ".data-ready").touch()
    neo4j_session.next_records = [
        {
            "db": {
                "id": "picab-v2.0-cds",
                "moleculeType": "nucl",
                "path": "picab/v2/v2.0/blast/nucl/coding-sequences.fa",
            },
            "annotationId": "picab-v2.0",
            "annotationPath": "picab/v2/v2.0",
        }
    ]

    return await async_client.post(
        "/v2/blast",
        json={
            "databaseId": "picab-v2.0-cds",
            "program": "blastn",
            "query": VALID_QUERY,
        },
    )


@pytest.mark.anyio
async def test_submit_blast_sends_the_job_off_the_event_loop_thread(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    sending_threads: list[threading.Thread] = []
    monkeypatch.setattr(
        run_blast_search,
        "apply_async",
        lambda **kwargs: sending_threads.append(threading.current_thread()),
    )

    await submit_valid_blast(async_client, neo4j_session, tmp_path)

    assert sending_threads[0] is not threading.current_thread()


@pytest.mark.anyio
async def test_submit_blast_503s_when_the_broker_is_unreachable(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    def raise_broker_error(**kwargs):
        raise OperationalError("timed out")

    monkeypatch.setattr(run_blast_search, "apply_async", raise_broker_error)

    response = await submit_valid_blast(
        async_client, neo4j_session, tmp_path
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "BLAST is temporarily unavailable, try again later"
    }


@pytest.mark.parametrize(
    "parameters",
    [{"evalue": 11}, {"evalue": 1e-31}, {"maxTargetSeqs": 101}],
    ids=["evalue too high", "evalue too low", "too many hits"],
)
@pytest.mark.anyio
async def test_submit_blast_422s_when_a_parameter_is_out_of_range(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
    parameters: dict[str, float],
):
    response = await async_client.post(
        "/v2/blast",
        json={
            "databaseId": "picab-v2.0-cds",
            "program": "blastn",
            "query": VALID_QUERY,
            "parameters": parameters,
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_blast_results_include_the_aligned_sequences(
    async_client: AsyncClient, tmp_path: Path
):
    job_id = "6f1c2b4e-0000-4000-8000-000000000001"
    blast_path = tmp_path / "pg-service-blast"
    blast_path.mkdir()
    (blast_path / f"{job_id}.tsv").write_text(
        "query1\tPA_chr01_G000001.mRNA.1\t95.0\t20\t1\t0\t1\t20\t101\t120"
        "\t1e-5\t40.1\tATGGCTTCAAGTGCAGTTCC\tATGGCTACAAGTGCAGTTCC\n"
    )

    response = await async_client.get(f"/v2/blast/{job_id}/json")

    hit = response.json()["results"][0]
    assert hit["querySequence"] == "ATGGCTTCAAGTGCAGTTCC"
    assert hit["subjectSequence"] == "ATGGCTACAAGTGCAGTTCC"


@pytest.mark.anyio
async def test_blast_results_name_the_gene_of_each_hit(
    async_client: AsyncClient, tmp_path: Path
):
    job_id = "6f1c2b4e-0000-4000-8000-000000000002"
    blast_path = tmp_path / "pg-service-blast"
    blast_path.mkdir()
    (blast_path / f"{job_id}.tsv").write_text(
        "query1\tPA_chr01_G000001.mRNA.1\t95.0\t20\t1\t0\t1\t20\t101\t120"
        "\t1e-5\t40.1\tATGG\tATGG\tpicab-v2.0\tPA_chr01_G000001\n"
    )

    response = await async_client.get(f"/v2/blast/{job_id}/json")

    hit = response.json()["results"][0]
    assert hit["annotationId"] == "picab-v2.0"
    assert hit["geneId"] == "PA_chr01_G000001"


def test_add_gene_columns_names_the_parent_gene(tmp_path: Path):
    tsv_path = tmp_path / "job.tsv"
    tsv_path.write_text(
        "query1\tFUN_000003-T1\t95.0\t20\t1\t0\t1\t20\t101\t120"
        "\t1e-5\t40.1\tATGG\tATGG\n"
    )
    gff_path = tmp_path / "gff.gz"
    with gzip.open(gff_path, "wt") as gff:
        gff.write("##gff-version 3\n")
        gff.write(
            "chr1\tfunannotate\tgene\t1\t900\t.\t+\t.\tID=FUN_000003;\n"
        )
        gff.write(
            "chr1\tfunannotate\tmRNA\t1\t900\t.\t+\t.\t"
            "ID=FUN_000003-T1;Parent=FUN_000003;product=hypothetical\n"
        )

    add_gene_columns(tsv_path, gff_path.as_posix(), "pruav-v2.0")

    assert tsv_path.read_text().rstrip("\n").split("\t")[-2:] == [
        "pruav-v2.0",
        "FUN_000003",
    ]


@pytest.mark.anyio
async def test_submit_blast_passes_the_annotation_gff_to_the_task(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    sent_kwargs = []
    monkeypatch.setattr(
        run_blast_search,
        "apply_async",
        lambda **kwargs: sent_kwargs.append(kwargs["kwargs"]),
    )

    await submit_valid_blast(async_client, neo4j_session, tmp_path)

    assert sent_kwargs[0]["annotation_id"] == "picab-v2.0"
    assert sent_kwargs[0]["gff_path"] == (
        tmp_path / "picab/v2/v2.0/gff.gz"
    ).as_posix()
