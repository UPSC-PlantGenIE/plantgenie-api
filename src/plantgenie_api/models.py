from typing import List, Optional

from pydantic import BaseModel, Field


class PlantGenieBase(BaseModel):
    pass


class AnnotationsRequest(PlantGenieBase):
    species: str
    gene_ids: List[str] = Field(alias="geneIds")


class GeneAnnotation(PlantGenieBase):
    gene_id: str = Field(alias="geneId")
    preferred_name: str = Field(alias="preferredName")
    evalue: Optional[float]
    score: Optional[float]
    seed_ortholog: Optional[str]
    description: Optional[str]
