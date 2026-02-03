from __future__ import annotations

import sys
from math import nan
from pathlib import Path
from typing import (
    Annotated,
    Dict,
    Set,
    TextIO,
    cast,
)

import networkx
import typer

from go_enrich.methods import EnrichmentMethod, enrichment_methods
from go_enrich.utils import (
    background_genes_file,
    gene_to_go_term_mapping_file,
    go_edges_file,
    go_terms_file,
    target_genes_file,
    benjamini_hochberg_fdr
)


def propagate_genes_towards_roots(graph: networkx.DiGraph) -> None:
    for node in networkx.topological_sort(graph):  # type: ignore
        for parent in graph.successors(node):
            graph.nodes[parent]["genes"] |= graph.nodes[node]["genes"]


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
    method: Annotated[
        EnrichmentMethod,
        typer.Option(
            help="Method to be used for testing GO enrichment, default GO term independence"
        ),
    ] = EnrichmentMethod.independent,
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

    # --- load gene sets ---
    significant_genes: Set[str] = {g for g in target_genes_file(target)}
    all_genes: Set[str] = {g for g in background_genes_file(background)}

    # non_significant_genes = all_genes - significant_genes

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

    enrichment_test = enrichment_methods[method]
    node_pvalues: Dict[str, float] = {node: nan for node in go_graph.nodes}

    for node_id in go_graph.nodes:
        node_pvalues[node_id] = enrichment_test(
            node_id, go_graph, significant_genes, all_genes
        )

    significant_go_terms = benjamini_hochberg_fdr(
        node_pvalues, fdr=base_fdr
    )

    # --- output ---
    with output_handler:
        for term in significant_go_terms:
            print(term, file=output_handler)


if __name__ == "__main__":
    typer.run(main)
