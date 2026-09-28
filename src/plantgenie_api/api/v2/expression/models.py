from pydantic import Field

from plantgenie_api.models import PlantGenieModel


class Experiment(PlantGenieModel):
    id: str
    name: str
    description: str | None = None
    unit: str
    sample_count: int


class ExperimentsResponse(PlantGenieModel):
    experiments: list[Experiment]


class ExpressionRequest(PlantGenieModel):
    gene_ids: list[str] = Field(min_length=1)


class ExpressionSample(PlantGenieModel):
    id: str
    group: int
    order: int


class ExpressionResponse(PlantGenieModel):
    experiment_id: str
    unit: str
    samples: list[ExpressionSample]
    gene_ids: list[str]
    values: list[list[float | None]]
    missing_gene_ids: list[str] = Field(default=[])
