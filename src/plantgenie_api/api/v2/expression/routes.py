from typing import cast

from fastapi import APIRouter, HTTPException

from plantgenie_api.api.v2.expression.models import (
    Experiment,
    ExperimentsResponse,
    ExpressionRequest,
    ExpressionResponse,
    ExpressionSample,
)
from plantgenie_api.dependencies import Neo4jDep

router = APIRouter(tags=["expression"])


@router.get(
    "/annotations/{annotation_id}/experiments",
    response_model=ExperimentsResponse,
)
async def retrieve_experiments(
    session: Neo4jDep, annotation_id: str
) -> ExperimentsResponse:
    result = await session.run(
        "MATCH (:Annotation {id: $annotationId})-[:HAS_EXPERIMENT]->"
        "(e:Experiment) "
        "RETURN e {.id, .name, .description, .unit} AS e, "
        "count {(e)<-[:PART_OF]-(:Sample)} AS sampleCount "
        "ORDER BY e.name",
        annotationId=annotation_id,
    )
    records = [record async for record in result]
    return ExperimentsResponse(
        experiments=[
            Experiment.model_validate(
                cast(dict[str, object], record["e"])
                | {"sampleCount": cast(int, record["sampleCount"])}
            )
            for record in records
        ]
    )


@router.post(
    "/experiments/{experiment_id}/expression",
    response_model=ExpressionResponse,
)
async def retrieve_expression(
    session: Neo4jDep, experiment_id: str, body: ExpressionRequest
) -> ExpressionResponse:
    result = await session.run(
        "MATCH (e:Experiment {id: $experimentId})<-[:PART_OF]-(s:Sample) "
        "WITH e, s ORDER BY s.order "
        "WITH e, collect(s) AS samples "
        "UNWIND $geneIds AS geneId "
        "MATCH (g:Gene {id: geneId}) "
        "UNWIND samples AS sample "
        "OPTIONAL MATCH (g)-[r:EXPRESSED_IN]->(sample) "
        "RETURN e.unit AS unit, geneId, "
        "sample.abbreviation AS sampleId, sample.group AS sampleGroup, "
        "sample.order AS sampleOrder, r.value AS value",
        experimentId=experiment_id,
        geneIds=body.gene_ids,
    )
    records = [record async for record in result]
    if not records:
        raise HTTPException(status_code=404, detail="Experiment not found")

    samples: list[ExpressionSample] = []
    seen_samples: set[str] = set()
    values_by_gene: dict[str, dict[str, float | None]] = {}

    for record in records:
        sample_id = cast(str, record["sampleId"])
        if sample_id not in seen_samples:
            seen_samples.add(sample_id)
            samples.append(
                ExpressionSample(
                    id=sample_id,
                    group=cast(int, record["sampleGroup"]),
                    order=cast(int, record["sampleOrder"]),
                )
            )
        gene_id = cast(str, record["geneId"])
        values_by_gene.setdefault(gene_id, {})[sample_id] = cast(
            float | None, record["value"]
        )

    gene_ids: list[str] = []
    values: list[list[float | None]] = []
    missing_gene_ids: list[str] = []

    for gene_id in body.gene_ids:
        gene_values = values_by_gene.get(gene_id, {})
        row = [gene_values.get(sample.id) for sample in samples]
        if all(value is None for value in row):
            missing_gene_ids.append(gene_id)
            continue
        gene_ids.append(gene_id)
        values.append(row)

    return ExpressionResponse(
        experiment_id=experiment_id,
        unit=cast(str, records[0]["unit"]),
        samples=samples,
        gene_ids=gene_ids,
        values=values,
        missing_gene_ids=missing_gene_ids,
    )
