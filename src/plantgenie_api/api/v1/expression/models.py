from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import Field

from plantgenie_api.models import PlantGenieModel


class GeneInfo(PlantGenieModel):
    chromosome_id: str = Field(alias="chromosomeId")
    gene_id: str = Field(alias="geneId")

    @staticmethod
    def split_from_request(gene_id_request: str) -> GeneInfo:
        """
        Gene IDs normally come in like this:
            {chromosome_id}_{gene_id}

        The gene_id part has no '_' inside of it, so it works to split on '_' and take
        the last one for the gene_id and join the chromosome_id part on '_' and return it.
        """
        gene_id_split = gene_id_request.split("_")

        if len(gene_id_split) < 2:
            raise IndexError(
                f"gene_id: {gene_id_request} split on '_' not at least length 2"
            )

        return GeneInfo(
            chromosome_id="_".join(gene_id_split[:-1]), gene_id=gene_id_split[-1]
        )

    @staticmethod
    def split_gene_ids_from_request(gene_ids: List[str]) -> List[GeneInfo]:
        return [GeneInfo.split_from_request(gene_id) for gene_id in gene_ids]


class SampleInfo(PlantGenieModel):
    experiment: str
    sample_id: int = Field(alias="sampleId")
    reference: str
    sequencing_id: str = Field(alias="sequencingId")
    condition: str


class ExpressionRequest(PlantGenieModel):
    experiment_id: int = Field(alias="experimentId")
    gene_ids: List[str] = Field(alias="geneIds", default=[])


class ExpressionResponse(PlantGenieModel):
    genes: List[str]
    samples: List[str]
    values: List[float]
    units: Optional[Literal["tpm", "vst"]] = Field(default=None)
    missing_gene_ids: List[str] = Field(alias="missingGeneIds", default=[])
