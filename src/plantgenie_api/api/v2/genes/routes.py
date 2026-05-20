from fastapi import APIRouter, HTTPException

from plantgenie_api.api.v2.genes.models import (
    GeneDetail,
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
        "WHERE g.id IN $geneIds "
        "RETURN g {geneId: g.id, .name, .description} AS g",
        annotationId=body.annotation_id,
        geneIds=body.gene_ids,
    )
    found = [LookupGene(**dict(r["g"])) async for r in result]
    found_ids = {g.gene_id for g in found}
    not_found = [g for g in body.gene_ids if g not in found_ids]
    return LookupGenesResponse(found=found, not_found=not_found)


@router.get("/{annotation_id}/{gene_id}", response_model=GeneDetail)
async def get_gene(
    session: Neo4jDep, annotation_id: str, gene_id: str
) -> GeneDetail:
    result = await session.run(
        "MATCH (:Annotation {id: $annotationId})-[:HAS_GENE]->"
        "(g:Gene {id: $geneId}) "
        "RETURN g {geneId: g.id, .name, .description, .chromosome, "
        ".startPosition, .endPosition, .strand} AS g",
        annotationId=annotation_id,
        geneId=gene_id,
    )
    records = [record async for record in result]
    if not records:
        raise HTTPException(status_code=404, detail="Gene not found")
    return GeneDetail(**dict(records[0]["g"]))
