from typing import Literal, List

from pydantic import BaseModel, Field

GoNodeType = Literal[
    "biological_process",
    "molecular_function",
    "cellular_component",
]


class GoEnrichPipelineArgs(BaseModel):
    target_path: str
    background_path: str
    genome_id: int
    method: Literal["classic"] = Field(
        default="classic"
    )  # ... others to be added ... #
    node_types: List[GoNodeType] = Field(
        min_length=1, default=["biological_process"]
    )
    base_fdr: float = Field(lt=1, gt=0, default=0.01)
    min_genes_per_node: int = Field(gt=0, default=1)
