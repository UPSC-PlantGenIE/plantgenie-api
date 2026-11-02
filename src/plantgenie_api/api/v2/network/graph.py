from __future__ import annotations

from dataclasses import dataclass

from plantgenie_api.api.v2.network.coexpression import (
    TooManyEdges,
    expression_pairs,
)
from plantgenie_api.api.v2.network.models import (
    GraphEdge,
    GraphNode,
    GraphResponse,
)


@dataclass(frozen=True)
class ExpressionProfiles:
    gene_ids: list[str]
    rows: list[list[float | None]]


def build_graph(
    nodes: list[GraphNode],
    profiles: list[ExpressionProfiles],
    max_edges: int,
) -> GraphResponse:
    best: dict[tuple[str, str], float] = {}
    for experiment in profiles:
        pairs = expression_pairs(
            experiment.gene_ids, experiment.rows, max_edges
        )
        for pair, score in pairs.items():
            best[pair] = max(best.get(pair, 0.0), score)
        if len(best) > max_edges:
            raise TooManyEdges(
                f"The selection produces more than {max_edges} edges. "
                "Select fewer genes."
            )
    return GraphResponse(
        nodes=nodes,
        edges=[
            GraphEdge(source=source, target=target, score=score)
            for (source, target), score in best.items()
        ],
    )
