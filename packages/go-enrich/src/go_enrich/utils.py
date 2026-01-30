from typing import Iterator, Tuple
from pathlib import Path


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
