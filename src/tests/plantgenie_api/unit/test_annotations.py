import pytest
from httpx import AsyncClient

from tests.plantgenie_api.unit.conftest import FakeNeo4jSession


@pytest.mark.anyio
async def test_get_annotation_returns_taxon_and_assembly(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
):
    neo4j_session.next_records = [
        {
            "n": {
                "id": "pinsy01-v1.0",
                "version": "v1.0",
                "geneCount": 42000,
                "isDefault": True,
            },
            "assemblyId": "pinsy01",
            "taxonAbbreviation": "pinsy",
            "taxonScientificName": "Pinus sylvestris",
        }
    ]

    response = await async_client.get("/v2/annotations/pinsy01-v1.0")

    assert response.status_code == 200
    assert response.json() == {
        "id": "pinsy01-v1.0",
        "version": "v1.0",
        "geneCount": 42000,
        "isDefault": True,
        "assemblyId": "pinsy01",
        "taxonAbbreviation": "pinsy",
        "taxonScientificName": "Pinus sylvestris",
    }


@pytest.mark.anyio
async def test_get_annotation_returns_404_when_missing(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
):
    neo4j_session.next_records = []

    response = await async_client.get("/v2/annotations/does-not-exist")

    assert response.status_code == 404
