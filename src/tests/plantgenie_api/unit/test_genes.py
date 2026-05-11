import pytest
from httpx import AsyncClient

from .conftest import FakeNeo4jSession


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
