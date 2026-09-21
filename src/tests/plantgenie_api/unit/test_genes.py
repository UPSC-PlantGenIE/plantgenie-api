import sqlite3
from pathlib import Path

import pysam
import pytest
from httpx import AsyncClient

from tests.plantgenie_api.unit.conftest import FakeNeo4jSession


@pytest.mark.anyio
async def test_lookup_splits_known_and_unknown(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
):
    neo4j_session.next_records = [
        {
            "g": {
                "geneId": "AT1G01010",
                "name": "GENE1",
                "description": "First gene",
            }
        },
    ]

    response = await async_client.post(
        "/v2/genes/lookup",
        json={
            "annotationId": "arath-Araport11",
            "geneIds": ["AT1G01010", "UNKNOWN"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["found"] == [
        {
            "geneId": "AT1G01010",
            "name": "GENE1",
            "description": "First gene",
        }
    ]
    assert body["notFound"] == ["UNKNOWN"]


@pytest.mark.anyio
async def test_get_gene_returns_full_record(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
):
    neo4j_session.next_records = [
        {
            "g": {
                "geneId": "AT1G01010",
                "name": "GENE1",
                "description": "First gene",
                "chromosome": "Chr1",
                "startPosition": 3631,
                "endPosition": 5899,
                "strand": "+",
            }
        }
    ]

    response = await async_client.get("/v2/genes/arath-Araport11/AT1G01010")

    assert response.status_code == 200
    assert response.json() == {
        "geneId": "AT1G01010",
        "name": "GENE1",
        "description": "First gene",
        "chromosome": "Chr1",
        "startPosition": 3631,
        "endPosition": 5899,
        "strand": "+",
    }


@pytest.mark.anyio
async def test_get_gene_returns_404_when_missing(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
):
    neo4j_session.next_records = []

    response = await async_client.get("/v2/genes/arath-Araport11/UNKNOWN")

    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_gene_go_terms_returns_terms(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
):
    neo4j_session.next_records = [
        {
            "t": {
                "id": "GO:0009408",
                "name": "response to heat",
                "namespace": "biological_process",
            }
        },
        {
            "t": {
                "id": "GO:0005634",
                "name": "nucleus",
                "namespace": "cellular_component",
            }
        },
    ]

    response = await async_client.get(
        "/v2/genes/pinsy-v1.0/PINSY_000001/go-terms"
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "GO:0009408",
            "name": "response to heat",
            "namespace": "biological_process",
        },
        {
            "id": "GO:0005634",
            "name": "nucleus",
            "namespace": "cellular_component",
        },
    ]


@pytest.mark.anyio
async def test_get_gene_go_terms_returns_empty_list_when_none(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
):
    neo4j_session.next_records = []

    response = await async_client.get(
        "/v2/genes/arath-Araport11/UNKNOWN/go-terms"
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_get_gene_arabidopsis_hit_responds_200(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
):
    neo4j_session.next_records = [
        {
            "hit": {
                "geneId": "AT1G01010",
                "name": "NAC001",
                "description": "NAC domain containing protein 1",
                "evalue": 3.2e-155,
                "bitscore": 442.6,
            }
        }
    ]

    response = await async_client.get(
        "/v2/genes/potra-v2.2/Potra2n1c1/arabidopsis-hit"
    )

    assert response.status_code == 200


@pytest.mark.anyio
async def test_get_gene_arabidopsis_hit_returns_hit(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
):
    neo4j_session.next_records = [
        {
            "hit": {
                "geneId": "AT1G01010",
                "name": "NAC001",
                "description": "NAC domain containing protein 1",
                "evalue": 3.2e-155,
                "bitscore": 442.6,
            }
        }
    ]

    response = await async_client.get(
        "/v2/genes/potra-v2.2/Potra2n1c1/arabidopsis-hit"
    )

    assert response.json() == {
        "geneId": "AT1G01010",
        "name": "NAC001",
        "description": "NAC domain containing protein 1",
        "evalue": 3.2e-155,
        "bitscore": 442.6,
    }


@pytest.mark.anyio
async def test_get_gene_arabidopsis_hit_returns_null_when_no_hit(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
):
    neo4j_session.next_records = [{"hit": None}]

    response = await async_client.get(
        "/v2/genes/arath-araport11/AT1G01010/arabidopsis-hit"
    )

    assert response.json() is None


@pytest.mark.anyio
async def test_get_gene_arabidopsis_hit_returns_404_when_gene_missing(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
):
    neo4j_session.next_records = []

    response = await async_client.get(
        "/v2/genes/potra-v2.2/UNKNOWN/arabidopsis-hit"
    )

    assert response.status_code == 404


@pytest.fixture
def sequence_files(
    sqlite_conn: sqlite3.Connection, tmp_path: Path
) -> Path:
    directory = tmp_path / "potra/T89-2026/h1"
    directory.mkdir(parents=True)

    contents = {
        "coding-sequences.fa": ">T89h1c1g00010.1\nATGGATAATGAA\n",
        "transcript-sequences.fa": (
            ">T89h1c1g00010.1 CDS=1-12\nATGGATAATGAAGGC\n"
        ),
        "amino-acid-sequences.fa": ">T89h1c1g00010.1\nMDNEGNIIND\n",
    }

    for name, text in contents.items():
        plain_path = directory / name
        plain_path.write_text(text)
        pysam.tabix_compress(str(plain_path), f"{plain_path}.gz")
        pysam.faidx(f"{plain_path}.gz")

    return directory


@pytest.mark.anyio
async def test_get_gene_sequences_returns_all_three(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
    sequence_files: Path,
):
    neo4j_session.next_records = [
        {
            "transcriptId": "T89h1c1g00010.1",
            "path": "potra/T89-2026/h1",
        }
    ]

    response = await async_client.get(
        "/v2/genes/potra-T89-2026-h1/T89h1c1g00010/sequences"
    )

    assert response.status_code == 200
    assert response.json() == {
        "geneId": "T89h1c1g00010",
        "transcriptId": "T89h1c1g00010.1",
        "cds": "ATGGATAATGAA",
        "transcript": "ATGGATAATGAAGGC",
        "protein": "MDNEGNIIND",
    }


@pytest.mark.anyio
async def test_get_gene_sequences_returns_only_the_requested_type(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
    sequence_files: Path,
):
    neo4j_session.next_records = [
        {
            "transcriptId": "T89h1c1g00010.1",
            "path": "potra/T89-2026/h1",
        }
    ]

    response = await async_client.get(
        "/v2/genes/potra-T89-2026-h1/T89h1c1g00010/sequences",
        params={"sequenceType": "protein"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "geneId": "T89h1c1g00010",
        "transcriptId": "T89h1c1g00010.1",
        "cds": None,
        "transcript": None,
        "protein": "MDNEGNIIND",
    }


@pytest.mark.anyio
async def test_get_gene_sequences_returns_404_when_gene_missing(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
    sequence_files: Path,
):
    neo4j_session.next_records = []

    response = await async_client.get(
        "/v2/genes/potra-T89-2026-h1/UNKNOWN/sequences"
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_gene_sequences_returns_nulls_without_a_transcript(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
    sequence_files: Path,
):
    neo4j_session.next_records = [
        {
            "transcriptId": None,
            "path": "potra/T89-2026/h1",
        }
    ]

    response = await async_client.get(
        "/v2/genes/potra-T89-2026-h1/T89h1c1g99999/sequences"
    )

    assert response.status_code == 200
    assert response.json() == {
        "geneId": "T89h1c1g99999",
        "transcriptId": None,
        "cds": None,
        "transcript": None,
        "protein": None,
    }


@pytest.mark.anyio
async def test_get_gene_sequences_returns_nulls_when_fasta_lacks_id(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
    sequence_files: Path,
):
    neo4j_session.next_records = [
        {
            "transcriptId": "T89h1c9g99999.1",
            "path": "potra/T89-2026/h1",
        }
    ]

    response = await async_client.get(
        "/v2/genes/potra-T89-2026-h1/T89h1c9g99999/sequences"
    )

    assert response.status_code == 200
    assert response.json() == {
        "geneId": "T89h1c9g99999",
        "transcriptId": "T89h1c9g99999.1",
        "cds": None,
        "transcript": None,
        "protein": None,
    }
