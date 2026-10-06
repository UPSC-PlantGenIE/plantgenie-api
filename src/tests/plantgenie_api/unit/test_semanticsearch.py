import numpy
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from plantgenie_api import semanticsearch


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    # Embedding files for potra only; every other species has none.
    (tmp_path / "potra.csv").write_text("g1,first gene\ng2,second gene\n")
    numpy.save(tmp_path / "potra-gene-ids.npy", numpy.array(["g1", "g2"]))
    numpy.save(tmp_path / "potra-embeddings.npy", numpy.eye(2))
    monkeypatch.setenv("SEMANTIC_SEARCH_DATA_DIR", str(tmp_path))
    app = FastAPI()
    app.include_router(semanticsearch.router, prefix="/v2")
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
