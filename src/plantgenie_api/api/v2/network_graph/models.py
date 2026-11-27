import numpy as np
from pydantic import Field

from plantgenie_api.models import PlantGenieModel


class CorrelationRequest(PlantGenieModel):
    gene_ids: list[str] = Field(min_length=1)


class CorrelationValue(PlantGenieModel):
    gene_pair: tuple[str,str]
    correlation: float


class CorrelationResponse(PlantGenieModel):
    experiment_id: str
    gene_ids: list[str]
    missing_gene_ids: list[str] = Field(default=[])
    correlation_values: list[CorrelationValue]





def expression_to_array(
    values: list[list[float | None]],
) -> np.ndarray:
    return np.array(
        [
            [np.nan if value is None else value for value in row]
            for row in values],
        dtype=np.float64,
    )


#Minimum periods are 3, that means the genes should have at least 3 expression values to participate in the calculation. 
def pairwise_pearson(
    expression: np.ndarray, min_periods: int = 3
) -> np.ndarray:
    is_valid = (~np.isnan(expression)).astype(np.float64)
    gene_means = np.nanmean(expression, axis=1, keepdims=True)
    deviations = np.nan_to_num(expression - gene_means)

    overlap = is_valid @ is_valid.T
    deviation_sums = deviations @ is_valid.T
    squared_deviation_sums = (deviations**2) @ is_valid.T
    deviation_products = deviations @ deviations.T

    with np.errstate(divide="ignore", invalid="ignore"):
        covariance = (
            deviation_products
            - deviation_sums * deviation_sums.T / overlap
        )
        variance = squared_deviation_sums - deviation_sums**2 / overlap
        correlations = covariance / np.sqrt(variance * variance.T)

    correlations[overlap < min_periods] = np.nan
    return correlations




def compute_correlation_values(
    expression: np.ndarray,
    gene_ids: list[str],
    threshold: float = 0.6,
    min_periods: int = 3,
) -> list[CorrelationValue]:
    correlations = pairwise_pearson(expression, min_periods=min_periods)
    row_indices, column_indices = np.nonzero(np.triu(correlations > threshold, k=1))
    
    return [
        CorrelationValue(
            gene_pair=(gene_ids[row_index], gene_ids[column_index]),
            correlation=float(correlations[row_index, column_index]),)
        for row_index, column_index in zip(row_indices, column_indices)
    ]
