from typing import List, Tuple

from duckdb import DuckDBPyRelation
from fastapi import APIRouter
from loguru import logger

from plantgenie_api.api.v1.annotation.models import (
    AnnotationsRequest,
    AnnotationsResponse,
    GeneAnnotation,
)
from plantgenie_api.dependencies import DatabaseDep

router = APIRouter(prefix="/annotations", tags=["v1", "annotations"])


@router.post("")
async def get_annotations(
    request: AnnotationsRequest, db_connection: DatabaseDep
) -> AnnotationsResponse:
    if len(request.gene_ids) == 0:
        return AnnotationsResponse(results=[])

    # all those \t are just for readability when printing it out for debugging
    gene_values = "\t" + ",\n\t\t".join(
        [
            f"({i}, '{gene}')"
            for i, gene in enumerate(request.gene_ids, start=1)
        ]
    )

    query = f"""
        WITH requested_genes(gene_order, gene_id) AS (
            VALUES
            {gene_values}
        ),
        genes_from_gff AS (
            SELECT * FROM requested_genes
                JOIN gff ON (requested_genes.gene_id = gff.feature_id)
        ) SELECT
            genes_from_gff.gene_id, gene_name, description
        FROM genes_from_gff
            LEFT JOIN annotations ON (annotations.gene_id = genes_from_gff.gene_id)
        ORDER BY genes_from_gff.gene_order;
    """
    logger.debug(query)
    query_relation: DuckDBPyRelation = db_connection.sql(
        query=query,
    )
    logger.debug("\n" + query_relation.__str__())
    results: List[Tuple[int, str, str]] = query_relation.fetchall()

    return AnnotationsResponse(
        results=[
            GeneAnnotation(
                gene_id=r[0], gene_name=r[1], description=r[2]
            )
            for r in results
        ]
    )
