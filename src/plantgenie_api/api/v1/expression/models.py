from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import Field

from plantgenie_api.models import PlantGenieModel


class ExpressionRequest(PlantGenieModel):
    experiment_id: int
    gene_ids: List[str] = Field(min_length=1)


class ExpressionResponse(PlantGenieModel):
    genes: List[str]
    samples: List[str]
    values: List[float]
    units: Optional[Literal["tpm", "vst"]] = Field(default=None)
    missing_gene_ids: Optional[List[str]] = Field(default=[])
