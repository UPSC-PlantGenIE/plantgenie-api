import threading
from pathlib import Path

import pytest
from httpx import AsyncClient
from kombu.exceptions import OperationalError
from task_queue.blast.tasks import run_blast_search

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
            }
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
            }
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
