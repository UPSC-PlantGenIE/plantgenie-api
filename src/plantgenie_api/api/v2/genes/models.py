from typing import List, Optional

from plantgenie_api.models import PlantGenieModel


class LookupGenesRequest(PlantGenieModel):
    annotation_id: str
    gene_ids: List[str]


class LookupGene(PlantGenieModel):
    gene_id: str
    name: Optional[str] = None
    description: Optional[str] = None


class LookupGenesResponse(PlantGenieModel):
    found: List[LookupGene]
    not_found: List[str]
