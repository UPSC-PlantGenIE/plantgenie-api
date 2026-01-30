from __future__ import annotations

import sys
from math import nan
from pathlib import Path
from typing import Annotated, Dict, List, Set, TextIO, cast

import networkx
import typer
from scipy.stats import fisher_exact

from go_enrich.utils import (
    background_genes_file,
    gene_to_go_term_mapping_file,
    go_edges_file,
    go_terms_file,
    target_genes_file,
)


def benjamini_hochberg_fdr(
    node_p_values: Dict[str, float], fdr: float = 0.01
) -> List[str]:
    ranks = {
        key: rank
        for (rank, key) in enumerate(
            sorted(node_p_values, key=lambda x: node_p_values[x]), start=1
        )
    }

    imq = {
        key: (ranks[key] / len(node_p_values)) * fdr
        for key in node_p_values
    }

    smaller_pvalues = dict(
        filter(lambda item: item[1] < imq[item[0]], node_p_values.items())
    )

    # max_key, max_value = max(smaller_pvalues.items(), key=lambda x: x[1])
    max_key = max(smaller_pvalues.keys(), key=lambda x: node_p_values[x])

    max_rank = ranks[max_key]

    # return [x for x in node_p_values if ranks[x] <= max_rank]
    return sorted(
        (x for x in node_p_values if ranks[x] <= max_rank),
        key=lambda x: node_p_values[x],
    )


def propagate_genes_towards_roots(graph: networkx.DiGraph) -> None:
    for node in networkx.topological_sort(graph):  # type: ignore
        for parent in graph.successors(node):
            graph.nodes[parent]["genes"] |= graph.nodes[node]["genes"]


def read_gene_set(path: Path) -> Set[str]:
    with path.open() as f:
        return {line.strip() for line in f if line.strip()}


def main(
    target: Annotated[
        Path,
        typer.Argument(
            default=...,
            help="Path to the target gene set, line-delimited file of gene IDs",
        ),
    ],
    background: Annotated[
        Path,
        typer.Argument(
            default=...,
            help="Path to the background gene set, line-delimited file of gene IDs",
        ),
    ],
    go_nodes: Annotated[
        Path,
        typer.Argument(
            default=...,
            help="Path to line-delimited list of GO terms to use in the analysis",
        ),
    ],
    go_edges: Annotated[
        Path,
        typer.Argument(
            default=...,
            help="Path to tab-delimited pairs of GO terms (from_term -> to_term) to use in the analysis",
        ),
    ],
    gene_to_go_term_mapping: Annotated[
        Path,
        typer.Argument(
            default=...,
            help="Path to the file containing a single-line mapping of gene IDs to GO terms",
        ),
    ],
    base_fdr: Annotated[
        float,
        typer.Option(
            help="The base false discovery rate for p-value correction",
        ),
    ] = 0.01,
    min_genes_per_node: Annotated[
        int,
        typer.Option(
            help="The minimum number of genes required for a node to be considered"
        ),
    ] = 1,
    output: Annotated[
        Path | None,
        typer.Option(
            help="A path to write the output, will write to stdout if not specified"
        ),
    ] = None,
):
    output_handler: TextIO = (
        open(output, "w") if isinstance(output, Path) else sys.stdout
    )

    # with output_handler:
    #     print(
    #         f"target path = {target.as_posix()} exists? {target.exists()}",
    #         file=output_handler,
    #     )
    #     print(
    #         f"background path = {background.as_posix()} exists? {background.exists()}",
    #         file=output_handler,
    #     )

    # --- load gene sets ---
    significant_genes: Set[str] = {g for g in target_genes_file(target)}
    all_genes: Set[str] = {g for g in background_genes_file(background)}
    # significant_genes = read_gene_set(target)
    # all_genes = read_gene_set(background)

    non_significant_genes = all_genes - significant_genes

    # --- build GO graph ---
    go_graph: networkx.DiGraph[str] = networkx.DiGraph()

    for go_term in go_terms_file(go_nodes):
        go_graph.add_node(go_term, genes=set())

    for go_from, go_to in go_edges_file(go_edges):
        if (go_from in go_graph) and (go_to in go_graph):
            go_graph.add_edge(go_from, go_to)

    for gene_id, go_term in gene_to_go_term_mapping_file(
        gene_to_go_term_mapping
    ):
        if gene_id not in all_genes:
            continue

        if go_term not in go_graph:
            continue

        node = go_graph.nodes.get(go_term)

        node["genes"].add(gene_id)

    # --- propagate genes up the DAG ---
    propagate_genes_towards_roots(go_graph)

    # --- prune nodes ---
    nodes_to_remove = []
    for node, data in go_graph.nodes.items():
        genes_for_node = cast(Set[str], data.get("genes", set()))
        if len(genes_for_node) < min_genes_per_node:
            nodes_to_remove.append(node)

    for node in nodes_to_remove:
        go_graph.remove_node(node)

    # --- Fisher exact test ---
    node_pvalues: Dict[str, float] = {node: nan for node in go_graph.nodes}

    for node_id in go_graph.nodes:
        node_genes: Set[str] = go_graph.nodes[node_id]["genes"]

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

        _, pvalue = fisher_exact(contingency_table, alternative="greater")
        node_pvalues[node_id] = pvalue

    significant_go_terms = benjamini_hochberg_fdr(
        node_pvalues, fdr=base_fdr
    )

    # --- output ---
    with output_handler:
        for term in significant_go_terms:
            print(term, file=output_handler)


if __name__ == "__main__":
    typer.run(main)
