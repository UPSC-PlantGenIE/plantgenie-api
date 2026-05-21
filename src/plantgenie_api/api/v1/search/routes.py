import numpy as np
from fastapi import APIRouter, HTTPException

from plantgenie_api.api.v1.search.models import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchHit,
)
from plantgenie_api.dependencies import (
    DatabaseDep,
    EmbeddingModelDep,
    SearchIndexDep,
)

router = APIRouter(prefix="/search", tags=["v1", "search"])


@router.post("", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    db_connection: DatabaseDep,
    embedding_model: EmbeddingModelDep,
    search_index: SearchIndexDep,
) -> SemanticSearchResponse:
    

    taxon = request.taxon.lower().strip()
    if taxon not in search_index:
        raise HTTPException(
            status_code=404, 
            detail=f"No semantic search index found for taxon: '{request.taxon}'"
        )

    taxon_data = search_index[taxon]
    embeddings = taxon_data["embeddings"]  # numpy matrix
    gene_ids = taxon_data["gene_ids"]      # numpy array

    query_text = f"Represent this sentence for searching relevant passages: {request.query}"
    query_embedding = embedding_model.encode(query_text, convert_to_numpy=True)

    dot_products = np.dot(embeddings, query_embedding)
    matrix_norms = np.linalg.norm(embeddings, axis=1)
    query_norm = np.linalg.norm(query_embedding)
    
    matrix_norms = np.where(matrix_norms == 0, 1e-9, matrix_norms)
    query_norm = query_norm if query_norm > 0 else 1e-9
    
    similarities = dot_products / (matrix_norms * query_norm)

    top_indices = np.argsort(similarities)[::-1][:request.n]

    top_gene_ids = [str(gene_ids[idx]) for idx in top_indices]
    top_scores = [float(similarities[idx]) for idx in top_indices]

    query = """
        SELECT g.feature_id, a.description 
        FROM gff g
        LEFT JOIN annotations a ON g.feature_id = a.feature_id
        WHERE g.feature_id = ANY(?)
    """
    db_results = db_connection.execute(query, [top_gene_ids]).fetchall()
    description_map = {row[0]: row[1] for row in db_results}

    hits = []
    for gene_id, score in zip(top_gene_ids, top_scores):
        hits.append(
            SemanticSearchHit(
                gene_id=gene_id,
                description=description_map.get(gene_id, "No description available in database"),
                score=score
            )
        )

    return SemanticSearchResponse(results=hits)