import numpy
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from plantgenie_api import semanticsearch
from plantgenie_api.dependencies import get_neo4j_session


class FakeSession:
    last_params: dict | None = None

    async def run(self, query: str, **params):
        FakeSession.last_params = params

        async def records():
            yield {"geneId": "g2", "description": "second gene"}
            yield {"geneId": "g2", "description": "duplicate version"}

        return records()


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    # Embedding files for potra only; every other species has none.
    numpy.save(tmp_path / "potra-gene-ids.npy", numpy.array(["g1", "g2"]))
    numpy.save(tmp_path / "potra-embeddings.npy", numpy.eye(2))
    monkeypatch.setenv("SEMANTIC_SEARCH_DATA_DIR", str(tmp_path))
    app = FastAPI()
    app.include_router(semanticsearch.router, prefix="/v2")

    async def fake_session():
        yield FakeSession()

    app.dependency_overrides[get_neo4j_session] = fake_session
    return TestClient(app)


def test_species_lists_only_those_with_embeddings(client: TestClient):
    response = client.get("/v2/semantic-search/species")

    assert response.status_code == 200
    assert response.json() == [
        {"abbreviation": "potra", "scientificName": "Populus tremula"}
    ]


def test_search_unsupported_species_is_404(client: TestClient):
    response = client.get(
        "/v2/semantic-search", params={"species": "pinco", "query": "x"}
    )

    assert response.status_code == 404


def test_search_species_without_embeddings_is_404(client: TestClient):
    response = client.get(
        "/v2/semantic-search", params={"species": "picab", "query": "x"}
    )

    assert response.status_code == 404


def test_search_takes_descriptions_from_neo4j(client: TestClient, monkeypatch):
    monkeypatch.setattr(
        semanticsearch, "_rank", lambda *_: [("g2", 0.9), ("g1", 0.5)]
    )

    response = client.get(
        "/v2/semantic-search", params={"species": "potra", "query": "x"}
    )

    assert response.status_code == 200
    assert response.json() == [
        {"geneId": "g2", "description": "second gene", "similarity": 0.9},
        {"geneId": "g1", "description": "", "similarity": 0.5},
    ]
    assert FakeSession.last_params == {
        "species": "potra",
        "geneIds": ["g2", "g1"],
    }
