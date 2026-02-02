from __future__ import annotations

from enum import Enum
from typing import Callable, Set, Dict, TYPE_CHECKING

import networkx
from scipy.stats import fisher_exact

TypedGraph = networkx.DiGraph

if TYPE_CHECKING:
    TypedGraph = networkx.DiGraph[str]


class EnrichmentMethod(str, Enum):
    independent = "independent"
    parent_child_union = "parent-child-union"
    parent_child_intersection = "parent-child-intersection"


EnrichmentFunction = Callable[
    [str, TypedGraph, Set[str], Set[str]],
    float,
]


def independent_enrichment_test(
    node_id: str,
    go_graph: networkx.DiGraph,
    significant_genes: Set[str],
    all_genes: Set[str],
) -> float:
    node_genes: Set[str] = go_graph.nodes[node_id]["genes"]
    non_significant_genes = all_genes - significant_genes

    contingency_table = [
        [
            len(significant_genes & node_genes),
            len(non_significant_genes & node_genes),
        ],
        [
            len(significant_genes - node_genes),
            len(non_significant_genes - node_genes),
        ],
    ]

    result = fisher_exact(contingency_table, alternative="greater")
    return result.pvalue


def parent_child_enrichment_union(
    node_id: str,
    go_graph: networkx.DiGraph,
    significant_genes: Set[str],
    all_genes: Set[str],
) -> float:
    parents = list(go_graph.successors(node_id))
    if not parents:
        return 1.0

    parent_genes: Set[str] = set()
    for p in parents:
        parent_genes |= go_graph.nodes[p]["genes"]

    parent_genes &= all_genes
    if not parent_genes:
        return 1.0

    sig_in_parent = significant_genes & parent_genes
    if not sig_in_parent:
        return 1.0

    child_genes = go_graph.nodes[node_id]["genes"] & parent_genes

    contingency_table = [
        [
            len(sig_in_parent & child_genes),
            len(sig_in_parent - child_genes),
        ],
        [
            len(parent_genes - sig_in_parent & child_genes),
            len(parent_genes - sig_in_parent - child_genes),
        ],
    ]

    result = fisher_exact(contingency_table, alternative="greater")
    return result.pvalue


def parent_child_enrichment_intersection(
    node_id: str,
    go_graph: networkx.DiGraph,
    significant_genes: Set[str],
    all_genes: Set[str],
) -> float:
    parents = list(go_graph.successors(node_id))
    if not parents:
        return 1.0

    # parent_genes: Set[str] = set()
    parent_genes = go_graph.nodes[parents[0]]["genes"].copy()
    for p in parents:
        parent_genes &= go_graph.nodes[p]["genes"]

    parent_genes &= all_genes
    if not parent_genes:
        return 1.0

    sig_in_parent = significant_genes & parent_genes
    if not sig_in_parent:
        return 1.0

    child_genes = go_graph.nodes[node_id]["genes"] & parent_genes

    contingency_table = [
        [
            len(sig_in_parent & child_genes),
            len(sig_in_parent - child_genes),
        ],
        [
            len(parent_genes - sig_in_parent & child_genes),
            len(parent_genes - sig_in_parent - child_genes),
        ],
    ]

    result = fisher_exact(contingency_table, alternative="greater")
    return result.pvalue


enrichment_methods: Dict[EnrichmentMethod, EnrichmentFunction] = {
    EnrichmentMethod.independent: independent_enrichment_test,
    EnrichmentMethod.parent_child_union: parent_child_enrichment_union,
    EnrichmentMethod.parent_child_intersection: parent_child_enrichment_intersection,
}
