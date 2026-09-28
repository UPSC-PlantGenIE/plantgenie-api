import pytest
from httpx import AsyncClient

from tests.plantgenie_api.unit.conftest import FakeNeo4jSession


@pytest.mark.anyio
async def test_get_experiments_for_annotation(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
):
    neo4j_session.next_records = [
        {
            "e": {
                "id": "picab-v2.0-cold-roots",
                "name": "Picab Cold Roots",
                "description": "Effect of cold stress on roots",
                "unit": "tpm",
            },
            "sampleCount": 27,
        }
    ]

    response = await async_client.get(
        "/v2/annotations/picab-v2.0/experiments"
    )

    assert response.status_code == 200
    assert response.json() == {
        "experiments": [
            {
                "id": "picab-v2.0-cold-roots",
                "name": "Picab Cold Roots",
                "description": "Effect of cold stress on roots",
                "unit": "tpm",
                "sampleCount": 27,
            }
        ]
    }


def expression_record(
    gene_id: str,
    sample_id: str,
    sample_order: int,
    value: float | None,
) -> dict:
    return {
        "unit": "tpm",
        "geneId": gene_id,
        "sampleId": sample_id,
        "sampleGroup": 1,
        "sampleOrder": sample_order,
        "value": value,
    }


@pytest.mark.anyio
async def test_expression_returns_matrix_in_request_order(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
):
    neo4j_session.next_records = [
        expression_record("PA_chr01_G000102", "control-1", 1, 7.5),
        expression_record("PA_chr01_G000102", "cold-1", 2, 1.5),
        expression_record("PA_chr01_G000106", "control-1", 1, 0.0),
        expression_record("PA_chr01_G000106", "cold-1", 2, 3.25),
    ]

    response = await async_client.post(
        "/v2/experiments/picab-v2.0-cold-roots/expression",
        json={"geneIds": ["PA_chr01_G000102", "PA_chr01_G000106"]},
    )

    assert response.status_code == 200
    assert response.json() == {
        "experimentId": "picab-v2.0-cold-roots",
        "unit": "tpm",
        "samples": [
            {"id": "control-1", "group": 1, "order": 1},
            {"id": "cold-1", "group": 1, "order": 2},
        ],
        "geneIds": ["PA_chr01_G000102", "PA_chr01_G000106"],
        "values": [[7.5, 1.5], [0.0, 3.25]],
        "missingGeneIds": [],
    }


@pytest.mark.anyio
async def test_expression_reports_genes_without_values(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
):
    neo4j_session.next_records = [
        expression_record("PA_chr01_G000102", "control-1", 1, 7.5),
        expression_record("PA_chr01_G000106", "control-1", 1, None),
    ]

    response = await async_client.post(
        "/v2/experiments/picab-v2.0-cold-roots/expression",
        json={"geneIds": ["PA_chr01_G000102", "PA_chr01_G000106"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["geneIds"] == ["PA_chr01_G000102"]
    assert body["values"] == [[7.5]]
    assert body["missingGeneIds"] == ["PA_chr01_G000106"]


@pytest.mark.anyio
async def test_expression_returns_404_for_unknown_experiment(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
):
    neo4j_session.next_records = []

    response = await async_client.post(
        "/v2/experiments/does-not-exist/expression",
        json={"geneIds": ["PA_chr01_G000102"]},
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_expression_rejects_empty_gene_ids(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
):
    response = await async_client.post(
        "/v2/experiments/picab-v2.0-cold-roots/expression",
        json={"geneIds": []},
    )

    assert response.status_code == 422
