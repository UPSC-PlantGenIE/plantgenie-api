from pydantic import Field

from plantgenie_api.models import PlantGenieModel


class GraphRequest(PlantGenieModel):
    list_id: str
    gene_ids: list[str] | None = None
    experiment_ids: list[str] = Field(default_factory=list, max_length=50)


class GraphNode(PlantGenieModel):
    id: str
    description: str


class GraphEdge(PlantGenieModel):
    source: str
    target: str
    score: float


class GraphResponse(PlantGenieModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
