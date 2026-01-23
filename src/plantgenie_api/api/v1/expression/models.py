from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import Field

from plantgenie_api.models import PlantGenieModel


class ExpressionRequest(PlantGenieModel):
    experiment_id: int
    gene_ids: List[str] = Field(min_length=1)


class ExpressionResponse(PlantGenieModel):
    gene_ids: List[str]
    samples: List[str]
    values: List[float]
    units: Optional[Literal["tpm", "vst"]] = Field(default=None)
    missing_gene_ids: List[str] = Field(default=[])


class Experiment(PlantGenieModel):
    experiment_id: int
    species_id: int
    genome_id: int
    experiment_title: str
    species_name: str
    genome_version: str


class AvailableExperimentsResponse(PlantGenieModel):
    experiments: List[Experiment]
