import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from plantgenie_api import semanticsearch
from plantgenie_api.dependencies import get_neo4j_session


class FakeSession:
    """Answers the species query and the vector-search query."""

    calls: list[dict] = []
    rank_rows: list[dict] = []
    species_with_embeddings: list[str] = ["potra"]

    async def run(self, query: str, **params):
        FakeSession.calls.append({"query": query, **params})

        async def records():
            if query == semanticsearch.SPECIES_WITH_EMBEDDINGS_QUERY:
                for abbreviation in FakeSession.species_with_embeddings:
                    yield {"abbreviation": abbreviation}
            else:
                for row in FakeSession.rank_rows:
                    yield row

        return records()


@pytest.fixture(autouse=True)
def reset_session():
    FakeSession.calls = []
    FakeSession.rank_rows = []
    FakeSession.species_with_embeddings = ["potra"]


@pytest.fixture
def client(monkeypatch) -> TestClient:
    monkeypatch.setattr(
        semanticsearch, "_embed_query", lambda query: [0.1, 0.2]
    )
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
    assert set(FakeSession.calls[0]["species"]) == set(
        semanticsearch.SEMANTIC_SPECIES
    )


def test_search_unsupported_species_is_404(client: TestClient):
    response = client.get(
        "/v2/semantic-search", params={"species": "pinco", "query": "x"}
    )

    assert response.status_code == 404


def test_search_returns_cosine_similarity_from_neo4j(client: TestClient):
    FakeSession.rank_rows = [
        {"geneId": "g2", "description": "second gene", "score": 0.95},
        {"geneId": "g1", "description": None, "score": 0.75},
    ]

    response = client.get(
        "/v2/semantic-search",
        params={"species": "potra", "query": "x", "number_of_results": 2},
    )

    assert response.status_code == 200
    # Neo4j scores are (1 + cosine) / 2, the API returns the cosine.
    assert response.json() == [
        {
            "geneId": "g2",
            "description": "second gene",
            "similarity": pytest.approx(0.9),
        },
        {"geneId": "g1", "description": "", "similarity": 0.5},
    ]
    call = FakeSession.calls[0]
    assert call["query"] == semanticsearch.RANK_QUERY
    assert call["species"] == "potra"
    assert call["embedding"] == [0.1, 0.2]
    assert call["limit"] == 2


def test_search_widens_neighbourhood_until_enough_hits(
    client: TestClient, monkeypatch
):
    """The vector index spans every species, so too few hits for the
    requested species triggers a larger nearest-neighbour fetch."""
    monkeypatch.setattr(semanticsearch, "MAX_NEIGHBOURS", 1000)
    FakeSession.rank_rows = [
        {"geneId": "g1", "description": "d", "score": 0.9}
    ]

    response = client.get(
        "/v2/semantic-search",
        params={"species": "potra", "query": "x", "number_of_results": 5},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    fetched = [call["k"] for call in FakeSession.calls]
    assert fetched == [50, 200, 800, 1000]
