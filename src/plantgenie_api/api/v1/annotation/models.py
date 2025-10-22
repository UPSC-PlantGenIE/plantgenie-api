from typing import List, Optional

from pydantic import Field

from plantgenie_api.models import PlantGenieModel


class GeneAnnotation(PlantGenieModel):
    gene_id: str = Field(alias="geneId", validation_alias="gene_id")
    gene_name: Optional[str] = Field(
        alias="geneName", validation_alias="gene_name"
    )
    description: Optional[str]


class AnnotationsRequest(PlantGenieModel):
    species: str
    gene_ids: List[str] = Field(
        alias="geneIds", validation_alias="gene_ids"
    )


class AnnotationsResponse(PlantGenieModel):
    results: List[GeneAnnotation]
