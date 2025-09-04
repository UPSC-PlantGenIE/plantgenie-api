from typing import Dict, List, Tuple

from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from loguru import logger

from plantgenie_api import SafeDuckDbConnection
from plantgenie_api.api.v1 import DATABASE_PATH
from plantgenie_api.api.v1.expression.models import (
    ExpressionRequest,
    ExpressionResponse,
    AvailableExperimentsResponse,
    Experiment,
)

router = APIRouter(prefix="/expression")


@router.post(path="")
async def get_expression_data(
    request: ExpressionRequest,
) -> ExpressionResponse:
    with SafeDuckDbConnection(DATABASE_PATH) as connection:
        experiment = connection.sql(
            "SELECT relation_name, expression_units FROM experiments WHERE id = ?",
            params=[request.experiment_id],
        ).fetchone()

        if experiment is None:
            raise HTTPException(
                status_code=422,
                detail=f"Experiment with id={request.experiment_id} not found",
            )

        try:
            table_name, expression_units = experiment
        except IndexError:
            raise HTTPException(
                status_code=422,
                detail=f"Either experiment table or units not found {experiment}",
            )

        # all those \t are just for readability when printing it out for debugging
        gene_values = ",\n\t\t\t".join(
            [
                f"({i}, '{gene}')"
                for i, gene in enumerate(request.gene_ids, start=1)
            ]
        )

        query = f"""
            WITH
                sample_collector AS (
                    SELECT
                        ROW_NUMBER() OVER () AS sample_order,
                        abbreviation AS sample_id
                    FROM expression_metadata
                    WHERE experiment_id = {request.experiment_id}
                ),
                requested_genes_with_order(gene_order, gene_id) AS (
                    VALUES
                        {gene_values}
                ),
                gene_collector AS (
                    SELECT
                        first(gene_order) as gene_order,
                        gene_id
                    FROM requested_genes_with_order
                    GROUP BY gene_id
                ),
                sample_gene_matrix AS (
                    SELECT
                        s.sample_id,
                        s.sample_order,
                        g.gene_id,
                        g.gene_order
                    FROM sample_collector s
                    CROSS JOIN gene_collector g
                ),
                expression_values AS (
                    SELECT
                        m.sample_id,
                        m.gene_id,
                        e.expression_value,
                        m.sample_order,
                        m.gene_order
                    FROM sample_gene_matrix m
                    JOIN {table_name} e
                        ON m.sample_id = e.sample_id
                       AND m.gene_id = e.gene_id
                )
            SELECT
                sample_id,
                gene_id,
                expression_value
            FROM expression_values
            ORDER BY gene_order, sample_order;
        """
        logger.debug(query)
        query_relation = connection.sql(query=query)
        logger.debug("\n" + query_relation.__str__())
        results = query_relation.fetchall()

    sample_order: Dict[str, int] = {}
    gene_order: Dict[str, int] = {}
    samples: List[str] = []
    genes: List[str] = []
    values: List[float] = []

    for sample_id, gene_id, expression_value in results:
        if sample_id not in sample_order:
            sample_order[sample_id] = len(samples)
            samples.append(sample_id)
        if gene_id not in gene_order:
            gene_order[gene_id] = len(genes)
            genes.append(gene_id)
        values.append(expression_value)

    missing_genes = [
        gene_id
        for gene_id in request.gene_ids
        if gene_id not in gene_order
    ]
    return ExpressionResponse(
        gene_ids=genes,
        samples=samples,
        values=values,
        units=expression_units,
        missing_gene_ids=missing_genes,
    )


@router.get(path="/available-experiments")
async def get_available_experiments() -> AvailableExperimentsResponse:
    with SafeDuckDbConnection(DATABASE_PATH) as connection:
        experiments: List[Tuple[int, int, int, str, str, str]] = (
            connection.sql(
                """
                    SELECT
                        e.id AS experiment_id,
                        s.id AS species_id,
                        g.id AS genome_id,
                        e.title AS experiment_title,
                        s.species_name,
                        g.version AS genome_version,
                    FROM experiments e
                        JOIN genomes g ON (e.genome_id = g.id)
                        JOIN species s ON (s.id = g.species_id);
                """
            ).fetchall()
        )

    return AvailableExperimentsResponse(
        experiments=[
            Experiment(
                experiment_id=row[0],
                species_id=row[1],
                genome_id=row[2],
                experiment_title=row[3],
                species_name=row[4],
                genome_version=row[5],
            )
            for row in experiments
        ]
    )
