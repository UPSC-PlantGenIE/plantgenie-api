"""
Keep Gene embeddings in Neo4j in sync with gene descriptions.

Finds Gene nodes that are new, have a changed description, or were embedded
with a different model, embeds each distinct description once, and writes the
vector back to every node that uses that description. The semantic search
endpoint (``plantgenie_api.semanticsearch``) reads these vectors through the
``gene_desc_embedding`` vector index.

Usage:
  python -m plantgenie_api.embeddings_worker --once --max-batches 1   # test: one batch, then exit
  python -m plantgenie_api.embeddings_worker --once                   # one full pass, then exit
  python -m plantgenie_api.embeddings_worker                          # run forever, a pass every --interval seconds

Environment variables: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD (required),
NEO4J_DATABASE (default neo4j), DATA_PATH (model cache, see
semanticsearch.configure_model_cache), EMBEDDING_BATCH (descriptions per
batch, default 500) and EMBEDDING_WRITE_CHUNK (descriptions per write
transaction, default 10; keeps each transaction under Neo4j's memory limit).
"""

import argparse
import logging
import os
import time

from neo4j import GraphDatabase

from plantgenie_api.semanticsearch import (
    EMBEDDING_DIMENSIONS as DIMENSIONS,
    INDEX_NAME,
    MODEL_NAME,
    configure_model_cache,
)

log = logging.getLogger("embeddings_worker")


# --- Configuration ---------------------------------------------------------
URI = os.environ["NEO4J_URI"]
USER = os.environ["NEO4J_USER"]
PASSWORD = os.environ["NEO4J_PASSWORD"]
DATABASE = os.environ.get("NEO4J_DATABASE", "neo4j")

BATCH = int(os.environ.get("EMBEDDING_BATCH", "500"))
WRITE_CHUNK = int(os.environ.get("EMBEDDING_WRITE_CHUNK", "10"))


# --- Cypher ----------------------------------------------------------------
FIND_STALE = """
MATCH (g:Gene)
WHERE g.description IS NOT NULL AND trim(g.description) <> ''
  AND (g.embedding IS NULL
       OR g.embeddedDescription IS NULL
       OR g.embeddedDescription <> g.description
       OR g.embeddingModel IS NULL
       OR g.embeddingModel <> $model)
WITH g.description AS description, collect(elementId(g)) AS eids
RETURN description, eids
LIMIT $batch
"""

# Writes only if the description is still the text that was embedded,
# so an edit made mid-run is picked up again on the next pass.
WRITE_BACK = """
UNWIND $rows AS r
UNWIND r.eids AS eid
MATCH (g:Gene) WHERE elementId(g) = eid AND g.description = r.description
CALL db.create.setNodeVectorProperty(g, 'embedding', r.embedding)
SET g.embeddedDescription = r.description,
    g.embeddingModel = $model,
    g.embeddedAt = datetime()
RETURN count(g) AS written
"""

CREATE_INDEX = f"""
CREATE VECTOR INDEX {INDEX_NAME} IF NOT EXISTS
FOR (g:Gene) ON g.embedding
OPTIONS {{indexConfig: {{
  `vector.dimensions`: {DIMENSIONS},
  `vector.similarity_function`: 'cosine'
}}}}
"""

CHECK_INDEX = """
SHOW VECTOR INDEXES YIELD name, options
WHERE name = $name
RETURN options.indexConfig['vector.dimensions'] AS dims
"""

# --- Embedding model -------------------------------------------------------
_model = None

def load_model():
    global _model
    if _model is None:
        # Must run before the import: HuggingFace reads HF_HOME on import.
        configure_model_cache()
        from sentence_transformers import SentenceTransformer
        log.info("Loading model %s", MODEL_NAME)
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed(texts):
    model = load_model()
    return model.encode(texts, convert_to_numpy=True)

# --- Worker ----------------------------------------------------------------
def ensure_index(driver):
    driver.execute_query(CREATE_INDEX, database_=DATABASE)
    records = driver.execute_query(CHECK_INDEX, name=INDEX_NAME, database_=DATABASE).records
    dims = records[0]["dims"] if records else None
    if dims != DIMENSIONS:
        raise RuntimeError(
            f"Index {INDEX_NAME} has {dims} dimensions, expected {DIMENSIONS}. "
            f"Drop it (DROP INDEX {INDEX_NAME}) and restart the worker."
        )


def run_once(driver, max_batches=None):
    texts_done = nodes_done = batches = 0
    while max_batches is None or batches < max_batches:
        rows = driver.execute_query(
            FIND_STALE, model=MODEL_NAME, batch=BATCH, database_=DATABASE
        ).records
        if not rows:
            break

        texts = [r["description"] for r in rows]
        vectors = embed(texts)
        if len(vectors) != len(texts):
            raise RuntimeError(f"embed() returned {len(vectors)} vectors for {len(texts)} texts")
        if len(vectors[0]) != DIMENSIONS:
            raise RuntimeError(f"embed() returned {len(vectors[0])}-dim vectors, expected {DIMENSIONS}")

        payload = [
            {"description": r["description"], "eids": r["eids"],
             "embedding": [float(x) for x in v]}
            for r, v in zip(rows, vectors)
        ]
        # Write in small chunks to stay under Neo4j's transaction memory limit.
        written = 0
        for i in range(0, len(payload), WRITE_CHUNK):
            result = driver.execute_query(
                WRITE_BACK, rows=payload[i:i + WRITE_CHUNK], model=MODEL_NAME,
                database_=DATABASE,
            )
            written += result.records[0]["written"]

        batches += 1
        texts_done += len(rows)
        nodes_done += written
        log.info("batch %d: %d texts -> %d genes (total %d texts, %d genes)",
                 batches, len(rows), written, texts_done, nodes_done)
    return texts_done, nodes_done


def main():
    parser = argparse.ArgumentParser(description="Sync Gene embeddings in Neo4j.")
    parser.add_argument("--once", action="store_true", help="run one pass and exit")
    parser.add_argument("--max-batches", type=int, default=None, help="stop after N batches (for testing)")
    parser.add_argument("--interval", type=int, default=300, help="seconds between passes")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    with GraphDatabase.driver(URI, auth=(USER, PASSWORD)) as driver:
        driver.verify_connectivity()
        ensure_index(driver)

        while True:
            try:
                texts, nodes = run_once(driver, args.max_batches)
                if texts:
                    log.info("pass complete: %d texts, %d genes updated", texts, nodes)
                else:
                    log.info("nothing to update")
            except Exception:
                if args.once:
                    raise
                log.exception("pass failed; retrying after %d s", args.interval)

            if args.once:
                break
            time.sleep(args.interval)


if __name__ == "__main__":
    main()