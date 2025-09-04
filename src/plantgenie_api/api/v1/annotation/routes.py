from typing import List, Tuple
from duckdb import DuckDBPyRelation
from fastapi import APIRouter
from loguru import logger

from plantgenie_api import SafeDuckDbConnection
from plantgenie_api.api.v1 import DATABASE_PATH
from plantgenie_api.api.v1.annotation.models import (
    AnnotationsRequest,
    AnnotationsResponse,
    GeneAnnotation,
)

router = APIRouter(prefix="/annotations")


@router.post("")
async def get_annotations(
    request: AnnotationsRequest,
) -> AnnotationsResponse:
    if len(request.gene_ids) == 0:
        return AnnotationsResponse(results=[])

    # all those \t are just for readability when printing it out for debugging
    gene_values = ",\n\t\t\t".join(
        [
            f"({i}, '{gene}')"
            for i, gene in enumerate(request.gene_ids, start=1)
        ]
    )

    query = f"""
        WITH requested_genes(gene_order, gene_id) AS (
            VALUES
                {gene_values}
        ) SELECT
            annotations.gene_id, gene_name, description
        FROM annotations
            JOIN requested_genes
                ON (annotations.gene_id = requested_genes.gene_id)
        ORDER BY requested_genes.gene_order;
    """

    with SafeDuckDbConnection(DATABASE_PATH) as connection:
        logger.debug(query)
        query_relation: DuckDBPyRelation = connection.sql(
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
