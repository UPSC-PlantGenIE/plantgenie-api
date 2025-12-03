from typing import List

from pydantic import Field

from plantgenie_api.models import PlantGenieModel


EnrichmentBaseModel = PlantGenieModel


class GenesToGoRequest(PlantGenieModel):
    gene_list: List[str]


class GenesToGoResponse(PlantGenieModel):
    go_terms_list: List[str]


class GeneOntologyEnrichmentResponse(PlantGenieModel):
    job_id: str = Field(alias="jobId", validation_alias="job_id")
