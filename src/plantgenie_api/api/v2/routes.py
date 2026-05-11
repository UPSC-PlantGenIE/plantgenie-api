from typing import Optional

from fastapi import APIRouter, HTTPException

from plantgenie_api.api.v2.genes.routes import router as genes_router
from plantgenie_api.api.v2.lists.routes import router as user_lists_router
from plantgenie_api.api.v2.models import (
    Annotation,
    AnnotationsResponse,
    AssembliesResponse,
    Assembly,
    TaxaResponse,
    Taxon,
)
from plantgenie_api.dependencies import Neo4jDep

router = APIRouter(prefix="/v2", tags=["v2"])

router.include_router(user_lists_router)
router.include_router(genes_router)


@router.get("/taxa", response_model=TaxaResponse, tags=["taxon"])
async def retrieve_taxa(
    session: Neo4jDep, abbreviation: Optional[str] = None
) -> TaxaResponse:
    if abbreviation is None:
        result = await session.run(
            "MATCH (t:Taxon) RETURN t ORDER BY t.id"
        )
    else:
        result = await session.run(
            "MATCH (t:Taxon {abbreviation: $abbreviation}) RETURN t",
            abbreviation=abbreviation,
        )
    records = [record async for record in result]
    return TaxaResponse(taxa=[Taxon(**record["t"]) for record in records])


@router.get(
    "/assemblies",
    response_model=AssembliesResponse,
    tags=["assembly"],
)
async def retrieve_assemblies(
    session: Neo4jDep, taxon: Optional[str] = None
) -> AssembliesResponse:
    if taxon is None:
        result = await session.run(
            "MATCH (t:Taxon)-[:HAS_ASSEMBLY]->(a:Assembly) "
            "RETURN a, t.abbreviation AS taxonAbbreviation "
            "ORDER BY t.scientificName, a.version"
        )
    else:
        result = await session.run(
            "MATCH (t:Taxon {abbreviation: $taxon})-[:HAS_ASSEMBLY]->(a:Assembly) "
            "RETURN a, t.abbreviation AS taxonAbbreviation "
            "ORDER BY a.version",
            taxon=taxon,
        )
    records = [record async for record in result]
    return AssembliesResponse(
        assemblies=[
            Assembly(
                **record["a"],
                taxon_abbreviation=record["taxonAbbreviation"],
            )
            for record in records
        ]
    )


@router.get(
    "/annotations",
    response_model=AnnotationsResponse,
    tags=["annotations"],
)
async def retrieve_annotations(
    session: Neo4jDep,
    assembly: Optional[str] = None,
    taxon: Optional[str] = None,
) -> AnnotationsResponse:
    if assembly and taxon:
        raise HTTPException(
            status_code=400,
            detail="Specify either 'assembly' or 'taxon', not both",
        )

    if assembly is not None:
        result = await session.run(
            "MATCH (a:Assembly {id: $assembly})-[:HAS_ANNOTATION]->(n:Annotation) "
            "RETURN n {.id, .version, .geneCount, .isDefault} AS n, a.id AS assemblyId",
            assembly=assembly,
        )

    elif taxon is not None:
        result = await session.run(
            "MATCH (:Taxon {abbreviation: $taxon})-[:HAS_ASSEMBLY]->(a:Assembly)"
            "-[:HAS_ANNOTATION]->(n:Annotation) "
            "RETURN n {.id, .version, .geneCount, .isDefault} AS n, a.id AS assemblyId ORDER BY a.version, n.version",
            taxon=taxon,
        )

    else:
        result = await session.run(
            "MATCH (a:Assembly)-[:HAS_ANNOTATION]->(n:Annotation) "
            "RETURN n {.id, .version, .geneCount, .isDefault} AS n, a.id AS assemblyId"
        )

    records = [record async for record in result]
    return AnnotationsResponse(
        annotations=[
            Annotation(
                **record["n"],
                assembly_id=record["assemblyId"],
            )
            for record in records
        ]
    )
