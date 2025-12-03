#! /usr/bin/env python

from math import nan
import resource
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, cast

import networkx
from scipy.stats import fisher_exact  # type: ignore

from plantgenie_api import SafeDuckDbConnection  # type: ignore


def get_descendants_iter(g: networkx.DiGraph, n: str) -> set[str]:
    succ = set(g.successors(n))
    if not succ:
        return {n}
    return set().union({n}, *(get_descendants_iter(g, y) for y in succ))


def upper_induced_graph(
    node_id: str, starting_graph: networkx.DiGraph
) -> networkx.Graph:
    return networkx.induced_subgraph(
        starting_graph,
        get_descendants_iter(starting_graph, node_id) - {node_id},
    )


working_directory = Path(__file__).parent
sig_genes_file_path = (
    working_directory / "Spruce_list_cold_270OG_DEG_Jamie.txt"
)
# background_genes_file_path = (
#     working_directory
#     / "picab_cold_stress_roots_background_full_experiment.tsv"
# )
background_genes_file_path = (
    working_directory / "background_spruce_half_exp.txt"
)

with open(sig_genes_file_path) as f:
    significant_genes = set([line.strip() for line in f])

with open(background_genes_file_path) as f:
    all_genes = set([line.strip() for line in f])

non_significant_genes: Set[str] = all_genes.difference(significant_genes)

# print((significant_genes))
print(len(significant_genes))
print(len(non_significant_genes))
# sys.exit(1)

go_graph: networkx.DiGraph = networkx.DiGraph()

with SafeDuckDbConnection(
    "/opt/pg-application-data/plantgenie-backend.db"
) as connection:
    query_relation = connection.sql("SELECT * FROM go_nodes WHERE go_type = 'biological_process'")
    arrow_table = query_relation.arrow(batch_size=100)

    for batch in arrow_table.to_batches():
        for row in batch.to_pylist():
            go_graph.add_node(row["id"], **row, tags=set())

    query_relation = connection.sql("SELECT * FROM go_edges")
    arrow_table = query_relation.arrow(100)

    for batch in arrow_table.to_batches():
        for row in batch.to_pylist():
            go_graph.add_edge(
                row["go_from"], row["go_to"], relation=row["relationship"]
            )

    query_relation = connection.sql(
        "SELECT * FROM go_terms_per_gene WHERE genome_id = 1"
    )
    arrow_table = query_relation.project("gene_id", "go_term").arrow(10)
    total_missing = 0
    for batch in arrow_table.to_batches():
        for row in batch.to_pylist():
            node = go_graph.nodes.get(row["go_term"])

            if node:
                node["tags"].add(row["gene_id"])
            else:
                # print(row['go_term'])
                total_missing += 1

    print(total_missing)

nodes_to_remove = []
for node, node_data in go_graph.nodes.items():
    node_id = cast(str, node_data.get("id"))
    node_tags = cast(Set[str], node_data.get("tags", set()))
    if len(node_tags) == 0:
        nodes_to_remove.append(node)

for node in nodes_to_remove:
    go_graph.remove_node(node)

topological_sort = networkx.topological_sort(go_graph)  # type: ignore[attr-defined]

number_of_nodes = 0
leaf_nodes = 0
non_leaf_nodes = 0
root_nodes = 0
for x in topological_sort:
    if go_graph.in_degree(x) == 0:
        # print(x)
        leaf_nodes += 1
    else:
        non_leaf_nodes += 1

    if go_graph.out_degree(x) == 0:
        root_nodes += 1
    number_of_nodes += 1

print(f"nodes: {number_of_nodes}")
print(f"leaves: {leaf_nodes}")
print(f"inner: {non_leaf_nodes}")
print(f"roots: {root_nodes}")

P_VALUE_THRESHOLD = 0.01 / number_of_nodes
# P_VALUE_THRESHOLD = 0.01
print(f"P_VALUE_THRESHOLD = {P_VALUE_THRESHOLD}")


marked_genes: Dict[str, Set[str]] = {x: set() for x in go_graph.nodes}

nodes_p_values: Dict[str, float] = {
    cast(str, x): nan for x in go_graph.nodes
}

topological_sort = networkx.topological_sort(go_graph)  # type: ignore[attr-defined]

for sorted_node_id in topological_sort:
    sorted_node_id = cast(str, sorted_node_id)
    # print(f"working on {sorted_node_id}")
    sorted_node = go_graph.nodes.get(sorted_node_id, {})
    node_genes: Set[str] = sorted_node.get("tags", set())
    node_genes.difference_update(marked_genes[sorted_node_id])
    contigency_table = [
        [
            len(significant_genes.intersection(node_genes)),
            len(non_significant_genes.intersection(node_genes)),
        ],
        [
            len(
                significant_genes.intersection(
                    all_genes.difference(node_genes)
                )
            ),
            len(
                non_significant_genes.intersection(
                    all_genes.difference(node_genes)
                )
            ),
        ],
    ]
    # nodes_p_values[sorted_node_id] = fisher_exact(contigency_table)
    odds_ratio, p_value = fisher_exact(contigency_table)
    nodes_p_values[sorted_node_id] = p_value
    if p_value is not None and p_value <= P_VALUE_THRESHOLD:
        print(
            f"{sorted_node_id}: p_value = {p_value} and threshold = {P_VALUE_THRESHOLD}"
        )
        for node in upper_induced_graph(sorted_node_id, go_graph).nodes:
            marked_genes[cast(str, node)] = marked_genes[
                cast(str, node)
            ].union(node_genes)


memusage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print(memusage)

significant_go_terms_clause = ",\n        ".join(
    [
        f"('{x}')"
        for x in nodes_p_values
        if nodes_p_values.get(x, nan) <= P_VALUE_THRESHOLD
    ]
)

# values_clause = ",\n        ".join(
#     f"('{term}')" for term in significant_go_terms
# )

query = f"""
WITH significant_go_terms(go_id) AS (
    VALUES
        {significant_go_terms_clause}
)
SELECT
    g.id,
    g.go_description
FROM go_nodes AS g
JOIN significant_go_terms AS s
    ON g.id = s.go_id;
"""

print(query)
with SafeDuckDbConnection(
    "/opt/pg-application-data/plantgenie-backend.db"
) as connection:
    query_relation = connection.sql(query)
    results = query_relation.fetchall()

for term, description in results:
    print(f"{term}\t{description}")
