from typing import List, Optional

from plantgenie_api.models import PlantGenieModel


# class GeneAnnotation(PlantGenieModel):
#     chromosome_id: str = Field(alias="chromosomeId")
#     gene_id: str = Field(alias="geneId")
#     # tool: Optional[str]
#     evalue: Optional[float]
#     score: Optional[float]
#     seed_ortholog: Optional[str] = Field(alias="seedOrtholog")
#     description: Optional[str]
#     preferred_name: Optional[str] = Field(alias="preferredName")


class GeneAnnotation(PlantGenieModel):
    gene_id: str
    gene_name: Optional[str]
    description: Optional[str]


class AnnotationsRequest(PlantGenieModel):
    species: str
    gene_ids: List[str]


class AnnotationsResponse(PlantGenieModel):
    results: List[GeneAnnotation]
