from datetime import date
from typing import List, Optional

from pydantic import Field

from plantgenie_api.models import PlantGenieModel



class AvailableGenome(PlantGenieModel):
    genome_id: int = Field(alias="id")
    species_id: int = Field(alias="speciesId")
    species_name: str = Field(alias="speciesName")
    version: str
    publication_date: Optional[date] = Field(alias="publicationDate")
    doi: Optional[str]



class AvailableGenomesResponse(PlantGenieModel):
    genomes: List[AvailableGenome]
