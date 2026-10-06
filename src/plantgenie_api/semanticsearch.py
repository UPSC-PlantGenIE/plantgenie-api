"""Semantic (embedding based) gene search, exposed as a FastAPI router.

Embeddings are precomputed per species (see the Feature_integrated
project). The BioLORD sentence-transformer model and all available
embeddings are preloaded in a background thread at startup, so the API
comes up immediately and searches are fast once loading has finished. A
search that arrives earlier loads what it needs itself and still works.

Environment variables:
    SEMANTIC_SEARCH_DATA_DIR       embeddings directory (see below)
    SEMANTIC_SEARCH_PRELOAD        set to 0 to disable startup preloading
    SEMANTIC_SEARCH_TORCH_THREADS  CPU threads for the model (default
                                   min(4, cpu count); using every core
                                   makes single queries much slower)

Layout of the embeddings directory (``SEMANTIC_SEARCH_DATA_DIR``,
default ``$DATA_PATH/embeddings``)::

    <prefix>.csv                 gene id, description (one per line)
    <prefix>-gene-ids.npy        gene ids aligned with the embeddings
    <prefix>-embeddings.npy      one embedding row per gene
"""

import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from threading import Lock, Thread
from typing import Any, AsyncIterator

import numpy
from fastapi import APIRouter, HTTPException, Query

from plantgenie_api.models import PlantGenieModel

MODEL_NAME = "FremyCompany/BioLORD-2023"
RETRIEVAL_PROMPT = (
    "Represent this sentence for searching relevant passages: "
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SemanticSpecies:
    abbreviation: str  # matches Taxon.abbreviation in the main API
    scientific_name: str
    file_prefix: str  # prefix of the embedding files


SEMANTIC_SPECIES: dict[str, SemanticSpecies] = {
    s.abbreviation: s
    for s in (
        SemanticSpecies("pinsy", "Pinus sylvestris", "pinsy"),
        SemanticSpecies("potra", "Populus tremula", "potra"),
        SemanticSpecies("picab", "Picea abies", "picab"),
        SemanticSpecies("betpe", "Betula pendula", "bepen"),
        SemanticSpecies("arath", "Arabidopsis thaliana", "arabidopsis"),
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
_embeddings: dict[str, dict[str, Any]] = {}
_lock = Lock()


def _torch_threads() -> int:
    configured = os.environ.get("SEMANTIC_SEARCH_TORCH_THREADS")
    if configured:
        return max(1, int(configured))
    return max(1, min(4, os.cpu_count() or 1))


def _data_dir() -> Path:
    configured = os.environ.get("SEMANTIC_SEARCH_DATA_DIR")
    if configured:
        return Path(configured)
    return Path(os.environ.get("DATA_PATH", ".")) / "embeddings"


def _species_files(species: SemanticSpecies) -> tuple[Path, Path, Path]:
    base = _data_dir() / species.file_prefix
    return (
        base.with_suffix(".csv"),
        Path(f"{base}-gene-ids.npy"),
        Path(f"{base}-embeddings.npy"),
    )


def _has_data(species: SemanticSpecies) -> bool:
    return all(path.is_file() for path in _species_files(species))


def _get_model() -> Any:
    global _model
    if _model is None:
        # The container user has no home directory, so keep the
        # HuggingFace cache next to the data (persisted by the mount).
        os.environ.setdefault(
            "HF_HOME", str(_data_dir().parent / "huggingface")
        )
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


def _get_embeddings(species: SemanticSpecies) -> dict[str, Any]:
    if species.abbreviation not in _embeddings:
        csv_path, ids_path, embeddings_path = _species_files(species)
        descriptions: dict[str, str] = {}
        for line in csv_path.read_text().splitlines():
            gene_id, _, description = line.partition(",")
            descriptions[gene_id] = description
        gene_ids = [
            str(gene_id)
            for gene_id in numpy.load(ids_path, allow_pickle=True)
        ]
        import torch

        _embeddings[species.abbreviation] = {
            "gene_ids": gene_ids,
            "descriptions": [descriptions.get(g, "") for g in gene_ids],
            # from_numpy shares memory, so similarity() skips a copy
            "embeddings": torch.from_numpy(numpy.load(embeddings_path)),
        }
    return _embeddings[species.abbreviation]


@lru_cache(maxsize=256)
def _encode_query(query: str) -> Any:
    return _get_model().encode_query(query)


def preload() -> None:
    """Load the model and every available species' embeddings."""
    with _lock:
        _get_model()
    for species in SEMANTIC_SPECIES.values():
        if _has_data(species):
            with _lock:
                _get_embeddings(species)
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
def list_semantic_species() -> list[SemanticSpeciesResponse]:
    """Species that currently support semantic search."""
    return [
        SemanticSpeciesResponse(
            abbreviation=species.abbreviation,
            scientific_name=species.scientific_name,
        )
        for species in SEMANTIC_SPECIES.values()
        if _has_data(species)
    ]


# Plain ``def`` (not ``async def``): model loading and encoding are
# blocking, so FastAPI runs this in its threadpool.
@router.get("", response_model=list[SemanticSearchHit])
def semantic_search(
    species: str = Query(description="Taxon abbreviation, e.g. potra"),
    query: str = Query(min_length=1),
    number_of_results: int = Query(default=10, ge=1),
) -> list[SemanticSearchHit]:
    selected = SEMANTIC_SPECIES.get(species)
    if selected is None or not _has_data(selected):
        raise HTTPException(
            status_code=404,
            detail=f"Semantic search is not available for '{species}'",
        )

    with _lock:
        model = _get_model()
        data = _get_embeddings(selected)
    query_embedding = _encode_query(query.strip())

    similarities = model.similarity(
        query_embedding, data["embeddings"]
    ).squeeze(0)
    count = min(number_of_results, len(data["gene_ids"]))
    top = similarities.argsort(descending=True)[:count].tolist()
    return [
        SemanticSearchHit(
            gene_id=data["gene_ids"][index],
            description=data["descriptions"][index],
            similarity=similarities[index].item(),
        )
        for index in top
    ]
