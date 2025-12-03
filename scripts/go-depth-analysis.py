from collections import deque
from pathlib import Path

import networkx

from plantgenie_api import SafeDuckDbConnection  # type: ignore


def shortest_distance_to_root(G, node):
    visited = set([node])
    queue = deque([(node, 0)])

    while queue:
        current, dist = queue.popleft()

        preds = list(G.successors(current))
        print(f"current node: {current}")
        print(preds)

        if not preds:
            return dist

        for p in preds:
            if p not in visited:
                visited.add(p)
                queue.append((p, dist + 1))

    return None


def longest_distance_to_root(G, node):
    preds = list(G.successors(node))

    if not preds:
        return 0

    longest = 0
    for p in preds:
        d = longest_distance_to_root(G, p)
        if d > longest:
            longest = d

    return 1 + longest


GENES_INPUT_PATH = (
    Path(__file__).parent / "pine_genes_in_A_compartment.txt"
)

GENES_OUTPUT_PATH = (
    Path(__file__).parent / "pine_genes_in_A_compartment_depths.tsv"
)

with open(GENES_INPUT_PATH) as f:
    input_genes = set([line.strip() for line in f])

go_graph: networkx.DiGraph = networkx.DiGraph()

with SafeDuckDbConnection(
    "/opt/pg-application-data/plantgenie-backend.db"
) as connection:
    query_relation = connection.sql(
        "SELECT * FROM go_nodes WHERE go_type = 'biological_process' AND starts_with(go_description, 'obsolete') = false"
    )
    arrow_table = query_relation.arrow(batch_size=100)

    for batch in arrow_table.to_batches():
        for row in batch.to_pylist():
            go_graph.add_node(row["id"], **row, tags=set())

    query_relation = connection.sql("SELECT * FROM go_edges")
    arrow_table = query_relation.arrow(100)

    for batch in arrow_table.to_batches():
        for row in batch.to_pylist():
            if not (
                row["go_from"] in go_graph and row["go_to"] in go_graph
            ):
                continue

            go_graph.add_edge(
                row["go_from"], row["go_to"], relation=row["relationship"]
            )

with SafeDuckDbConnection(
    "/opt/pg-application-data/plantgenie-backend.db"
) as connection:
    query_relation = connection.sql(
        "SELECT * FROM go_terms_per_gene WHERE genome_id = 2"
    )
    arrow_table = query_relation.project("gene_id", "go_term").arrow(10)

    total = 0
    total_missing = 0
    for batch in arrow_table.to_batches():
        for row in batch.to_pylist():
            if row["gene_id"] not in input_genes:
                continue
            node = go_graph.nodes.get(row["go_term"])

            if node:
                node["tags"].add(row["gene_id"])
            else:
                total_missing += 1
            total += 1

    print(total_missing, total)

nodes_with_genes = [
    node
    for node, node_data in go_graph.nodes.items()
    if len(node_data["tags"]) != 0
]

node_distances_shortest = {
    x: shortest_distance_to_root(go_graph, x) for x in nodes_with_genes
}

node_distances_longest = {
    x: longest_distance_to_root(go_graph, x) for x in nodes_with_genes
}

with open(GENES_OUTPUT_PATH, "w") as f:
    print("node_id\tshortest_path\tlongest_path", file=f, end="\n")
    for node in nodes_with_genes:
        print(
            node,
            node_distances_shortest[node],
            node_distances_longest[node],
            file=f,
            sep="\t",
            end="\n",
        )
