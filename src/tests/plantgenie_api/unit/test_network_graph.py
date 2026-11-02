import hashlib
import sqlite3

import pytest
from httpx import AsyncClient

from plantgenie_api.api.v2.network.coexpression import (
    TooManyEdges,
    expression_pairs,
)
from plantgenie_api.api.v2.network.graph import (
    ExpressionProfiles,
    build_graph,
)
from plantgenie_api.api.v2.network.models import GraphNode
from plantgenie_api.dependencies import get_neo4j_session
from plantgenie_api.main import app
from tests.plantgenie_api.unit.conftest import FakeNeo4jResult

ADA = "1111111111111111"
BOB = "2222222222222222"
URL = "/v2/network-graph/graph"


def test_expression_pairs_is_pearson():
    rows: list[list[float | None]] = [
        [1, 2, 3, 4],
        [2, 4, 6, 8],
        [4, 3, 2, 1],
        [5, 5, 5, 5],
        [1, None, 3, 4],
    ]

    pairs = expression_pairs(["a", "b", "c", "flat", "gap"], rows)

    assert pairs[("a", "b")] == 1.0
    assert ("a", "c") not in pairs
    assert not any("flat" in key for key in pairs)
    assert pairs[("a", "gap")] > 0.9


def genes(*gene_ids: str) -> list[GraphNode]:
    return [GraphNode(id=gene_id, description="") for gene_id in gene_ids]


def test_build_graph_keeps_the_best_score_over_experiments():
    profiles = [
        ExpressionProfiles(["p1", "p2"], [[1, 2, 3], [2, 4, 7]]),
        ExpressionProfiles(["p1", "p2"], [[1, 2, 3], [2, 4, 6]]),
    ]

    graph = build_graph(genes("p1", "p2"), profiles, 100)

    [edge] = graph.edges
    assert (edge.source, edge.target, edge.score) == ("p1", "p2", 1.0)


def test_build_graph_without_experiments_has_nodes_and_no_edges():
    graph = build_graph(genes("p1", "p2"), [], 100)

    assert [node.id for node in graph.nodes] == ["p1", "p2"]
    assert graph.edges == []


def test_too_many_edges_is_an_error():
    profiles = [
        ExpressionProfiles(
            ["p1", "p2", "p3"], [[1, 2, 3], [2, 4, 7], [3, 5, 8]]
        )
    ]

    with pytest.raises(TooManyEdges):
        build_graph(genes("p1", "p2", "p3"), profiles, max_edges=1)


class RoutedNeo4jSession:
    def __init__(self) -> None:
        self.expression_gene_ids: list[str] = []

    async def run(self, query: str, **params):
        if "EXPRESSED_IN" in query:
            self.expression_gene_ids = params["geneIds"]
            values = {"p1": [1, 2, 3], "p2": [2, 4, 7], "p3": [3, 2, 1]}
            records = [
                {"geneId": gene_id, "value": value}
                for gene_id in params["geneIds"]
                if gene_id in values
                for value in values[gene_id]
            ]
        elif "HAS_EXPERIMENT" in query:
            known = params["annotationId"] == "pinsy-v1.0" and (
                params["experimentId"] == "pinsy-cold-roots"
            )
            records = [{"id": params["experimentId"]}] if known else []
        else:
            descriptions = {"p1": "first pine", "p2": "second pine"}
            records = [
                {"id": gene_id, "description": descriptions[gene_id]}
                for gene_id in params["geneIds"]
                if gene_id in descriptions
            ]
        return FakeNeo4jResult(records)


@pytest.fixture
def graph_session():
    session = RoutedNeo4jSession()

    async def override():
        yield session

    app.dependency_overrides[get_neo4j_session] = override
    yield session
    app.dependency_overrides.pop(get_neo4j_session, None)


def add_account(connection: sqlite3.Connection, account_id: str) -> str:
    account_hash = hashlib.sha256(account_id.encode()).hexdigest()
    connection.execute(
        "INSERT INTO accounts (account_hash) VALUES (?)", (account_hash,)
    )
    return account_hash


@pytest.fixture
def headers(sqlite_conn: sqlite3.Connection) -> dict[str, str]:
    ada = add_account(sqlite_conn, ADA)
    bob = add_account(sqlite_conn, BOB)
    for list_id, account_hash, gene_ids in (
        ("pines", ada, ["p1", "p2", "p3"]),
        ("bobs", bob, ["p1", "p2"]),
    ):
        sqlite_conn.execute(
            "INSERT INTO gene_lists (list_id, name, annotation_id, "
            "taxon_name, account_hash) VALUES (?, ?, 'pinsy-v1.0', "
            "'Pinus sylvestris', ?)",
            (list_id, list_id.title(), account_hash),
        )
        sqlite_conn.executemany(
            "INSERT INTO gene_list_members (list_id, gene_id) "
            "VALUES (?, ?)",
            [(list_id, gene_id) for gene_id in gene_ids],
        )
    sqlite_conn.commit()
    return {"Authorization": f"Bearer {ADA}"}


@pytest.mark.anyio
async def test_graph_requires_an_account(
    async_client: AsyncClient, graph_session
):
    response = await async_client.post(URL, json={"listId": "pines"})

    assert response.status_code == 401


@pytest.mark.anyio
async def test_graph_has_the_list_genes_and_their_expression_edges(
    async_client: AsyncClient, graph_session, headers
):
    response = await async_client.post(
        URL,
        headers=headers,
        json={"listId": "pines", "experimentIds": ["pinsy-cold-roots"]},
    )

    assert response.status_code == 200
    assert response.json() == {
        "nodes": [
            {"id": "p1", "description": "first pine"},
            {"id": "p2", "description": "second pine"},
            {"id": "p3", "description": ""},
        ],
        "edges": [{"source": "p1", "target": "p2", "score": 0.9934}],
    }


@pytest.mark.anyio
async def test_graph_without_experiments_has_no_edges(
    async_client: AsyncClient, graph_session, headers
):
    response = await async_client.post(
        URL, headers=headers, json={"listId": "pines"}
    )

    assert response.status_code == 200
    assert len(response.json()["nodes"]) == 3
    assert response.json()["edges"] == []


@pytest.mark.anyio
async def test_graph_can_be_limited_to_some_genes_of_the_list(
    async_client: AsyncClient, graph_session, headers
):
    response = await async_client.post(
        URL,
        headers=headers,
        json={
            "listId": "pines",
            "geneIds": ["p1", "p3", "not-in-list"],
            "experimentIds": ["pinsy-cold-roots"],
        },
    )

    assert [node["id"] for node in response.json()["nodes"]] == [
        "p1",
        "p3",
    ]
    assert graph_session.expression_gene_ids == ["p1", "p3"]


@pytest.mark.anyio
async def test_graph_of_another_accounts_list_is_not_found(
    async_client: AsyncClient, graph_session, headers
):
    for list_id in ("bobs", "nope"):
        response = await async_client.post(
            URL, headers=headers, json={"listId": list_id}
        )

        assert response.status_code == 404


@pytest.mark.anyio
async def test_graph_rejects_an_empty_selection(
    async_client: AsyncClient, graph_session, headers
):
    response = await async_client.post(
        URL, headers=headers, json={"listId": "pines", "geneIds": []}
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_graph_rejects_an_experiment_of_another_annotation(
    async_client: AsyncClient, graph_session, headers
):
    response = await async_client.post(
        URL,
        headers=headers,
        json={"listId": "pines", "experimentIds": ["potra-wood"]},
    )

    assert response.status_code == 422
    assert "potra-wood" in response.json()["detail"]
