from typing import List

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class PlantGenieModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True, alias_generator=to_camel, extra="forbid"
    )


class AvailableSpecies(PlantGenieModel):
    species_id: int = Field(alias="id")
    species_name: str = Field(alias="speciesName")
    species_abbreviation: str = Field(alias="speciesAbbreviation")
    avatar_path: str = Field(alias="avatarPath")


class AvailableSpeciesResponse(PlantGenieModel):
    species: List[AvailableSpecies]
