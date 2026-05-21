from typing import List, Optional
from plantgenie_api.models import PlantGenieModel


class SemanticSearchRequest(PlantGenieModel):
    taxon: str
    query: str
    n: int = 10


class SemanticSearchHit(PlantGenieModel):
    gene_id: str
    description: Optional[str]
    score: float


class SemanticSearchResponse(PlantGenieModel):
    results: List[SemanticSearchHit]