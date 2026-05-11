from fastapi import APIRouter

from plantgenie_api.api.v2.genes.models import (
    LookupGene,
    LookupGenesRequest,
    LookupGenesResponse,
)
from plantgenie_api.dependencies import Neo4jDep

router = APIRouter(prefix="/genes", tags=["genes"])


@router.post("/lookup", response_model=LookupGenesResponse)
async def lookup_genes(
    body: LookupGenesRequest, session: Neo4jDep
) -> LookupGenesResponse:
    result = await session.run(
        "MATCH (:Annotation {id: $annotationId})-[:HAS_GENE]->(g:Gene) "
        "WHERE g.geneId IN $geneIds "
        "RETURN g {.geneId, .name, .description} AS g",
        annotationId=body.annotation_id,
        geneIds=body.gene_ids,
    )
    found = [LookupGene(**dict(r["g"])) async for r in result]
    found_ids = {g.gene_id for g in found}
    not_found = [g for g in body.gene_ids if g not in found_ids]
    return LookupGenesResponse(found=found, not_found=not_found)
