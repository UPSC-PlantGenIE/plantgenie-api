import pytest
from httpx import AsyncClient

from tests.plantgenie_api.unit.conftest import FakeNeo4jSession


#A record is a Neo4J table row. This funcction is based on the geneIds present in the user's list.
def gene_records(
    gene_id: str, values: list[float | None]) -> list[dict]:
    return [
        {
            "geneId": gene_id,
            "sampleId": f"sample-{index}",
            "value": value,
        }
        for index, value in enumerate(values)
    ]



@pytest.mark.anyio
async def test_correlation_excludes_genes_without_values_from_computation(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession):

    neo4j_session.next_records = [
        *gene_records("G1", [1.0, 2.0, 3.0]),
        *gene_records("G2", [2.0, 4.0, 6.0]),
        *gene_records("G3", [None, None, None])]

    response = await async_client.post(
        "/v2/experiments/picab-v2.0-cold-roots/correlation",
        json={"geneIds": ["G1", "G2", "G3"]})
    
    assert response.status_code == 200

    assert response.json()["geneIds"] == ["G1", "G2"]
    assert response.json()["missingGeneIds"] == ["G3"]


#threshold at 0.6
@pytest.mark.anyio
async def test_correlation_returns_pairs_above_threshold(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession):

    neo4j_session.next_records = [
        *gene_records("G1", [1.0, 2.0, 3.0, 4.0]),
        *gene_records("G2", [2.0, 4.0, 6.0, 8.0]),
        *gene_records("G3", [4.0, 3.0, 2.0, 1.0]),]

    response = await async_client.post(
        "/v2/experiments/picab-v2.0-cold-roots/correlation",
        json={"geneIds": ["G1", "G2", "G3"]})

    assert response.status_code == 200
    assert response.json() == {
        "experimentId": "picab-v2.0-cold-roots",
        "geneIds": ["G1", "G2", "G3"],
        "missingGeneIds": [],
        "correlationValues": [{"genePair": ["G1", "G2"], "correlation": pytest.approx(1.0)}]
        }
            
                            

#min periods 3 
@pytest.mark.anyio
async def test_correlation_skips_genes_with_fewer_than_three_expression_values(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession):

    neo4j_session.next_records = [
        *gene_records("G1", [1.0, 2.0, 3.0, 4.0]),
        *gene_records("G2", [2.0, 4.0, 6.0, None]),
        *gene_records("G3", [3.0, 6.0, None, None])]

    response = await async_client.post(
        "/v2/experiments/picab-v2.0-cold-roots/correlation",
        json={"geneIds": ["G1", "G2", "G3"]})

    assert response.status_code == 200 
    assert response.json() == {
        "experimentId": "picab-v2.0-cold-roots",
        "geneIds" : ["G1", "G2", "G3"],
        "missingGeneIds" : [],
        "correlationValues" : [{"genePair": ["G1", "G2"],"correlation": pytest.approx(1.0)}]   
    }




        
#Only in case an experiment is removed from the database without removing it from the UI.
@pytest.mark.anyio
async def test_correlation_returns_404_for_unknown_experiment(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,):

    neo4j_session.next_records = []

    response = await async_client.post(
        "/v2/experiments/does-not-exist/correlation",
        json={"geneIds": ["G1", "G2"]},)
    assert response.status_code == 404       




#This can be removed if the button of the network graph is unavailable for less than 2 items in the list, along with the next test. 
@pytest.mark.anyio
async def test_correlation_requires_two_genes_with_data(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,
):
    neo4j_session.next_records = [
        *gene_records("G1", [1.0, 2.0, 3.0]),
        *gene_records("G2", [None, None, None]),
    ]

    response = await async_client.post(
        "/v2/experiments/picab-v2.0-cold-roots/correlation",
        json={"geneIds": ["G1", "G2"]},
    )
    assert response.status_code == 422



@pytest.mark.anyio
async def test_correlation_rejects_empty_gene_ids(
    async_client: AsyncClient,
    neo4j_session: FakeNeo4jSession,):

    response = await async_client.post(
        "/v2/experiments/picab-v2.0-cold-roots/correlation",
        json={"geneIds": []},)
    
    assert response.status_code == 422
