from pathlib import Path
from typing import Dict, Iterator, List, Tuple


def target_genes_file(file_path: Path) -> Iterator[str]:
    with open(file_path) as f:
        for line in f:
            if line:
                yield line.strip()


def background_genes_file(file_path: Path) -> Iterator[str]:
    with open(file_path) as f:
        for line in f:
            if line:
                yield line.strip()


def go_terms_file(file_path: Path) -> Iterator[str]:
    with open(file_path) as f:
        for line in f:
            if line:
                yield line.strip()


def go_edges_file(file_path: Path) -> Iterator[Tuple[str, str]]:
    with open(file_path) as f:
        for line in f:
            node_pair = line.strip().split()

            if len(node_pair) != 2:
                raise TypeError(
                    f"Format requires two GO terms per line separated by whitespace, received: {line}"
                )

            yield (node_pair[0], node_pair[1])


def gene_to_go_term_mapping_file(
    file_path: Path,
) -> Iterator[Tuple[str, str]]:
    with open(file_path) as f:
        for line in f:
            node_pair = line.strip().split()

            if len(node_pair) != 2:
                raise TypeError(
                    f"Format requires a gene id and go term per line separated by whitespace, received: {line}"
                )

            yield (node_pair[0], node_pair[1])


def benjamini_hochberg_fdr(
    node_p_values: Dict[str, float], fdr: float = 0.01
) -> List[str]:
    ranks: Dict[str, float] = {
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

    return sorted(
        (x for x in node_p_values if ranks[x] <= max_rank),
        key=lambda x: node_p_values[x],
    )
