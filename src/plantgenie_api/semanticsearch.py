"""Semantic (embedding based) gene search, exposed as a FastAPI router.

Gene embeddings live in Neo4j (``Gene.embedding``, indexed by the vector
index ``gene_desc_embedding``) and are kept up to date by
``plantgenie_api.embeddings_worker``. The BioLORD sentence-transformer
model is preloaded in a background thread at startup, so the API comes
up immediately and searches are fast once loading has finished. A search
that arrives earlier loads the model itself and still works.

Environment variables:
    SEMANTIC_SEARCH_PRELOAD        set to 0 to disable startup preloading
    SEMANTIC_SEARCH_TORCH_THREADS  CPU threads for the model (default
                                   min(4, cpu count); using every core
                                   makes single queries much slower)

The HuggingFace model cache is ``$DATA_PATH/huggingface``.
"""

import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from threading import Lock, Thread
from typing import Any, AsyncIterator

from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool

from plantgenie_api.dependencies import Neo4jDep
from plantgenie_api.models import PlantGenieModel

MODEL_NAME = "FremyCompany/BioLORD-2023"
INDEX_NAME = "gene_desc_embedding"
EMBEDDING_DIMENSIONS = 768
RETRIEVAL_PROMPT = (
    "Represent this sentence for searching relevant passages: "
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SemanticSpecies:
    abbreviation: str  # matches Taxon.abbreviation in the main API
    scientific_name: str


SEMANTIC_SPECIES: dict[str, SemanticSpecies] = {
    s.abbreviation: s
    for s in (
        SemanticSpecies("pinsy", "Pinus sylvestris"),
        SemanticSpecies("potra", "Populus tremula"),
        SemanticSpecies("picab", "Picea abies"),
        SemanticSpecies("betpe", "Betula pendula"),
        SemanticSpecies("arath", "Arabidopsis thaliana"),
        SemanticSpecies("pruav", "Prunus avium"),
    )
}


class SemanticSpeciesResponse(PlantGenieModel):
    abbreviation: str
    scientific_name: str


class SemanticSearchHit(PlantGenieModel):
    gene_id: str
    description: str
    similarity: float


_model: Any = None
_lock = Lock()

# Cosine similarity of the query against each Gene, restricted to the
# species. The vector index spans all species, so the nearest `k` genes
# are fetched first and filtered afterwards (see _rank).
RANK_QUERY = (
    "CYPHER 25 "
    "MATCH (g:Gene) SEARCH g IN ("
    f"VECTOR INDEX {INDEX_NAME} FOR $embedding LIMIT $k"
    ") SCORE AS score "
    "MATCH (:Taxon {abbreviation: $species})-[:HAS_ASSEMBLY]->"
    "(:Assembly)-[:HAS_ANNOTATION]->(:Annotation)-[:HAS_GENE]->(g) "
    # A gene id can appear under several annotations of one species.
    "RETURN DISTINCT g.id AS geneId, g.description AS description, "
    "score ORDER BY score DESC LIMIT $limit"
)

SPECIES_WITH_EMBEDDINGS_QUERY = (
    "UNWIND $species AS abbreviation "
    "CALL (abbreviation) { "
    "MATCH (:Taxon {abbreviation: abbreviation})-[:HAS_ASSEMBLY]->"
    "(:Assembly)-[:HAS_ANNOTATION]->(:Annotation)-[:HAS_GENE]->"
    "(g:Gene) WHERE g.embedding IS NOT NULL RETURN true AS found LIMIT 1 "
    "} RETURN abbreviation"
)

# Start by fetching this many neighbours per requested result and grow
# until enough belong to the species, never beyond MAX_NEIGHBOURS.
INITIAL_OVERFETCH = 10
OVERFETCH_GROWTH = 4
MAX_NEIGHBOURS = 20_000


def _torch_threads() -> int:
    configured = os.environ.get("SEMANTIC_SEARCH_TORCH_THREADS")
    if configured:
        return max(1, int(configured))
    return max(1, min(4, os.cpu_count() or 1))


def configure_model_cache() -> None:
    """Keep the HuggingFace cache next to the data (persisted by the
    mount), as the container user has no home directory."""
    os.environ.setdefault(
        "HF_HOME",
        str(Path(os.environ.get("DATA_PATH", ".")) / "huggingface"),
    )


def _get_model() -> Any:
    global _model
    if _model is None:
        configure_model_cache()
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as error:
            raise HTTPException(
                status_code=503,
                detail="Semantic search dependencies are not installed",
            ) from error
        import torch

        torch.set_num_threads(_torch_threads())
        _model = SentenceTransformer(
            MODEL_NAME, prompts={"retrieval": RETRIEVAL_PROMPT}
        )
        _model.encode_query("warm up")  # first call is slower
    return _model


@lru_cache(maxsize=256)
def _encode_query(query: str) -> list[float]:
    return [float(x) for x in _get_model().encode_query(query)]


def _embed_query(query: str) -> list[float]:
    """Blocking: load the model if needed and embed the query."""
    with _lock:
        _get_model()
    return _encode_query(query.strip())


def preload() -> None:
    """Load the model so the first search does not have to."""
    with _lock:
        _get_model()
    logger.info("Semantic search preloaded")


def _preload_safely() -> None:
    try:
        preload()
    except Exception:  # searches fall back to lazy loading
        logger.exception("Semantic search preload failed")


@asynccontextmanager
async def _lifespan(_: Any) -> AsyncIterator[None]:
    if os.environ.get("SEMANTIC_SEARCH_PRELOAD", "1") != "0":
        Thread(target=_preload_safely, daemon=True).start()
    yield


router = APIRouter(
    prefix="/semantic-search",
    tags=["semantic-search"],
    lifespan=_lifespan,
)


@router.get("/species", response_model=list[SemanticSpeciesResponse])
async def list_semantic_species(
    session: Neo4jDep,
) -> list[SemanticSpeciesResponse]:
    """Species whose genes currently have embeddings in Neo4j."""
    result = await session.run(
        SPECIES_WITH_EMBEDDINGS_QUERY, species=list(SEMANTIC_SPECIES)
    )
    available = {record["abbreviation"] async for record in result}
    return [
        SemanticSpeciesResponse(
            abbreviation=species.abbreviation,
            scientific_name=species.scientific_name,
        )
        for species in SEMANTIC_SPECIES.values()
        if species.abbreviation in available
    ]


async def _rank(
    session: Neo4jDep,
    species: str,
    query_embedding: list[float],
    number_of_results: int,
) -> list[SemanticSearchHit]:
    """Nearest genes of one species, as cosine similarities."""
    neighbours = number_of_results * INITIAL_OVERFETCH
    while True:
        neighbours = min(neighbours, MAX_NEIGHBOURS)
        result = await session.run(
            RANK_QUERY,
            k=neighbours,
            embedding=query_embedding,
            species=species,
            limit=number_of_results,
        )
        hits = [
            SemanticSearchHit(
                gene_id=record["geneId"],
                description=record["description"] or "",
                # Neo4j scores cosine as (1 + cos) / 2; undo that.
                similarity=2 * record["score"] - 1,
            )
            async for record in result
        ]
        if len(hits) >= number_of_results or neighbours >= MAX_NEIGHBOURS:
            return hits
        neighbours *= OVERFETCH_GROWTH


@router.get("", response_model=list[SemanticSearchHit])
async def semantic_search(
    session: Neo4jDep,
    species: str = Query(description="Taxon abbreviation, e.g. potra"),
    query: str = Query(min_length=1),
    number_of_results: int = Query(default=10, ge=1),
) -> list[SemanticSearchHit]:
    if species not in SEMANTIC_SPECIES:
        raise HTTPException(
            status_code=404,
            detail=f"Semantic search is not available for '{species}'",
        )

    # Model loading and encoding are blocking, so run them in a thread.
    query_embedding = await run_in_threadpool(_embed_query, query)
    return await _rank(session, species, query_embedding, number_of_results)
