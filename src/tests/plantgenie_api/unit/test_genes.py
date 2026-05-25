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
