from typing import cast

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from plantgenie_api.api.v2.network_graph.models import (
    CorrelationRequest,
    CorrelationResponse,
    compute_correlation_values,
    expression_to_array,
)
from plantgenie_api.dependencies import Neo4jDep

router = APIRouter(tags=["network-graph"])


@router.post("/experiments/{experiment_id}/correlation", response_model=CorrelationResponse)
async def retrieve_correlation(
    session: Neo4jDep, experiment_id: str, body: CorrelationRequest
) -> CorrelationResponse:
    result = await session.run(
        "MATCH (e:Experiment {id: $experimentId})<-[:PART_OF]-(s:Sample) "
        "WITH s ORDER BY s.order "
        "WITH collect(s) AS samples "
        "UNWIND $geneIds AS geneId "
        "MATCH (g:Gene {id: geneId}) "
        "UNWIND samples AS sample "
        "OPTIONAL MATCH (g)-[r:EXPRESSED_IN]->(sample) "
        "RETURN geneId, sample.abbreviation AS sampleId, "
        "r.value AS value",
        experimentId=experiment_id,
        geneIds=body.gene_ids,
    )
    records = [record async for record in result]
    if not records:
        raise HTTPException(status_code=404, detail="Experiment not found")

    sample_ids: dict[str, None] = {}
    values_by_gene: dict[str, dict[str, float | None]] = {}

    for record in records:
        sample_id = cast(str, record["sampleId"])
        sample_ids.setdefault(sample_id)
        gene_id = cast(str, record["geneId"])
        values_by_gene.setdefault(gene_id, {})[sample_id] = cast(
            float | None, record["value"])
        

    gene_ids: list[str] = []
    values: list[list[float | None]] = []
    missing_gene_ids: list[str] = []

    for gene_id in body.gene_ids:
        gene_values = values_by_gene.get(gene_id, {})
        row = [gene_values.get(sample_id) for sample_id in sample_ids]
        if all(value is None for value in row):
            missing_gene_ids.append(gene_id)
            continue
        gene_ids.append(gene_id)
        values.append(row)

    if len(gene_ids) < 2:
        raise HTTPException(
            status_code=422,
            detail="At least 2 genes with expression data are required",)
        

    correlation_values = await run_in_threadpool(
        lambda: compute_correlation_values(
            expression_to_array(values), gene_ids))
        
    
    return CorrelationResponse(
        experiment_id=experiment_id,
        gene_ids=gene_ids,
        missing_gene_ids=missing_gene_ids,
        correlation_values=correlation_values,
    )
