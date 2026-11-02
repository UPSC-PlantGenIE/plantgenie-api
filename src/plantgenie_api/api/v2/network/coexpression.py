from __future__ import annotations

import numpy as np


class TooManyEdges(ValueError):
    pass


def profile_matrix(rows: list[list[float | None]]) -> np.ndarray:
    matrix = np.array(
        [
            [np.nan if value is None else value for value in row]
            for row in rows
        ],
        dtype=np.float64,
    )
    if matrix.size == 0:
        return matrix.astype(np.float32)
    means = np.nanmean(
        np.where(np.isnan(matrix).all(axis=1, keepdims=True), 0.0, matrix),
        axis=1,
        keepdims=True,
    )
    centred = np.where(np.isnan(matrix), means, matrix) - means
    norms = np.linalg.norm(centred, axis=1, keepdims=True)
    return np.divide(
        centred, norms, out=np.zeros_like(centred), where=norms > 1e-12
    ).astype(np.float32)


def correlated_pairs(
    matrix: np.ndarray, limit: int | None = None, chunk: int = 512
) -> dict[tuple[int, int], float]:
    count = len(matrix)
    pairs: dict[tuple[int, int], float] = {}
    columns = np.arange(count)
    for start in range(0, count, chunk):
        rows = np.arange(start, min(start + chunk, count))
        scores = matrix[rows] @ matrix.T
        keep = (columns[None, :] > rows[:, None]) & (scores > 0)
        row_indices, column_indices = np.nonzero(keep)
        if limit is not None and len(pairs) + len(row_indices) > limit:
            raise TooManyEdges(
                f"The selection produces more than {limit} edges. "
                "Select fewer genes."
            )
        for row, column in zip(
            row_indices.tolist(), column_indices.tolist(), strict=True
        ):
            pairs[(int(rows[row]), column)] = min(
                float(scores[row, column]), 1.0
            )
    return pairs


def expression_pairs(
    gene_ids: list[str],
    rows: list[list[float | None]],
    limit: int | None = None,
) -> dict[tuple[str, str], float]:
    if len(gene_ids) < 2:
        return {}
    pairs = correlated_pairs(profile_matrix(rows), limit)
    return {
        (gene_ids[first], gene_ids[second]): round(score, 4)
        for (first, second), score in pairs.items()
    }
