#! /usr/bin/env python

from math import nan
import resource
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, cast

import duckdb
import networkx
import statsmodels # type: ignore
from scipy.stats import fisher_exact # type: ignore
import statsmodels.stats # type: ignore
import statsmodels.stats.multitest  # type: ignore

from plantgenie_api import SafeDuckDbConnection  # type: ignore


def propagate_genes_towards_roots(graph: networkx.DiGraph) -> None:
    for node in networkx.topological_sort(graph):
        for parent in graph.successors(node):
            graph.nodes[parent]["tags"] |= graph.nodes[node]["tags"]


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

non_significant_genes: Set[str] = all_genes - significant_genes

# print((significant_genes))
print(len(significant_genes))
print(len(non_significant_genes))
# sys.exit(1)

go_graph: networkx.DiGraph = networkx.DiGraph()

with SafeDuckDbConnection(
    "/opt/pg-application-data/plantgenie-backend.db"
) as connection:
    query_relation = connection.sql(
        "SELECT * FROM go_nodes WHERE go_type = 'biological_process'"
    )
    arrow_table = query_relation.arrow(batch_size=100)

    for batch in arrow_table.to_batches():
        for row in batch.to_pylist():
            go_graph.add_node(row["id"], **row, tags=set())

    query_relation = connection.sql("SELECT * FROM go_edges")
    arrow_table = query_relation.arrow(100)

    for batch in arrow_table.to_batches():
        for row in batch.to_pylist():
            if not(row["go_from"] in go_graph and row["go_to"] in go_graph):
                continue

            go_graph.add_edge(
                row["go_from"], row["go_to"], relation=row["relationship"]
            )

with duckdb.connect("/opt/pg-application-data/plantgenie-backend.db") as connection:
    # query_relation = connection.sql(
    #     "SELECT external_gene_name as gene_id, replace(go_id, ':', '_') AS go_term FROM read_csv('~/Desktop/Picab02_go_ids.csv')"
    # )
    query_relation = connection.sql(
        "SELECT * FROM go_terms_per_gene WHERE genome_id = 1"
    )
    arrow_table = query_relation.project("gene_id", "go_term").arrow(10)
    total_missing = 0
    for batch in arrow_table.to_batches():
        for row in batch.to_pylist():
            if row["gene_id"] not in all_genes:
                continue
            node = go_graph.nodes.get(row["go_term"])

            if node:
                node["tags"].add(row["gene_id"])
            else:
                total_missing += 1

    print(total_missing)

# nodes_to_remove = []
# for node, node_data in go_graph.nodes.items():
#     node_id = cast(str, node_data.get("id"))
#     node_tags = cast(Set[str], node_data.get("tags", set()))
#     if len(node_tags) == 0:
#         nodes_to_remove.append(node)

propagate_genes_towards_roots(go_graph)

nodes_to_remove = []
for node, node_data in go_graph.nodes.items():
    node_id = cast(str, node_data.get("id"))
    node_tags = cast(Set[str], node_data.get("tags", set()))
    if len(node_tags) < 1: # should be the default nodeSize param of topGOData object?
        nodes_to_remove.append(node)
    elif go_graph.in_degree(node_id) == 0 and go_graph.out_degree(node_id) == 0:
        nodes_to_remove.append(node)

graph_size_before = len(go_graph.nodes)

for node in nodes_to_remove:
    go_graph.remove_node(node)

graph_size_after = len(go_graph.nodes)

print(f"before: {graph_size_before} and after: {graph_size_after}")


topological_sort = networkx.topological_sort(go_graph)  # type: ignore[attr-defined]

number_of_nodes = 0
leaf_nodes = 0
non_leaf_nodes = 0
root_nodes = 0
for x in topological_sort:
    if go_graph.in_degree(x) == 0:
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

P_VALUE_THRESHOLD = 0.05
print(f"P_VALUE_THRESHOLD = {P_VALUE_THRESHOLD}")


nodes_p_values: Dict[str, float] = {
    cast(str, x): nan for x in go_graph.nodes
}

for sorted_node_id in go_graph.nodes:
    sorted_node_id = cast(str, sorted_node_id)
    sorted_node = go_graph.nodes.get(sorted_node_id, {})
    node_genes: Set[str] = sorted_node.get("tags", set())
    contigency_table = [
        [
            len(significant_genes & node_genes),
            len(non_significant_genes & node_genes)
        ],
        [
            len(significant_genes & (all_genes - node_genes)),
            len(non_significant_genes & (all_genes - node_genes)),
        ],
    ]
    # we need one-sided test here because we want a gene being differentially expressed
    # increases the probability of being associated with the GO term
    result = fisher_exact(contigency_table, alternative="greater")
    nodes_p_values[sorted_node_id] = result.pvalue

memusage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print(memusage)

nodes_sorted_by_pvalue = sorted(
    nodes_p_values, key=lambda x: nodes_p_values[x]
)
sorted_pvalues = [nodes_p_values[x] for x in nodes_sorted_by_pvalue]
adjusted_pvalues = statsmodels.stats.multitest.multipletests(
    sorted_pvalues,
    alpha=P_VALUE_THRESHOLD,
    method="fdr_bh",
    is_sorted=True,
    returnsorted=False,
)[1].tolist()

significant_go_terms = [
    node_id
    for (node_id, p_value) in zip(nodes_sorted_by_pvalue, adjusted_pvalues)
    if p_value <= P_VALUE_THRESHOLD
]

print(len(significant_go_terms))


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

    return [x for x in node_p_values if ranks[x] <= max_rank]

# significant_go_terms = benjamini_hochberg_fdr(nodes_p_values, fdr=P_VALUE_THRESHOLD)

# for node_id in significant_go_terms:
#     node = go_graph.nodes.get(node_id)
#     # print(node)
#     node_genes: Set[str] = node.get("tags", set())
#     contigency_table = [
#         [
#             len(significant_genes.intersection(node_genes)),
#             len(non_significant_genes.intersection(node_genes)),
#         ],
#         [
#             len(
#                 significant_genes.intersection(
#                     all_genes.difference(node_genes)
#                 )
#             ),
#             len(
#                 non_significant_genes.intersection(
#                     all_genes.difference(node_genes)
#                 )
#             ),
#         ],
#     ]
#     print(node.get('id'), contigency_table)

significant_go_terms_clause = ",\n        ".join(
    [f"('{x}')" for x in significant_go_terms]
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
