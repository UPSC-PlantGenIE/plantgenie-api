from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict
from datetime import date

from pydantic.alias_generators import to_camel


class PlantGenieModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="forbid")


class GeneAnnotation(PlantGenieModel):
    chromosome_id: str = Field(alias="chromosomeId")
    gene_id: str = Field(alias="geneId")
    # tool: Optional[str]
    evalue: Optional[float]
    score: Optional[float]
    seed_ortholog: Optional[str] = Field(alias="seedOrtholog")
    description: Optional[str]
    preferred_name: Optional[str] = Field(alias="preferredName")


class AnnotationsRequest(PlantGenieModel):
    species: str
    gene_ids: List[str] = Field(alias="geneIds")


class AnnotationsResponse(PlantGenieModel):
    results: List[GeneAnnotation]


class GeneInfo(PlantGenieModel):
    chromosome_id: str
    gene_id: str

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


class GeneList(BaseModel):
    species: str
    experiment: str
    gene_ids: List[str] = Field(alias="geneIds")

    def gene_ids_to_gene_infos(self) -> List[GeneInfo]:
        return [GeneInfo.split_from_request(gene_id) for gene_id in self.gene_ids]


class SampleInfo(PlantGenieModel):
    experiment: str
    sample_id: int = Field(alias="sampleId")
    reference: str
    sequencing_id: str = Field(alias="sequencingId")
    condition: str


class ExpressionRequest(PlantGenieModel):
    species: str
    experiment_id: int = Field(alias="experimentId")
    gene_ids: List[str] = Field(alias="geneIds", default=[])


class ExpressionResponse(PlantGenieModel):
    genes: List[GeneInfo]
    samples: List[SampleInfo]
    values: List[float]


class GenesResponse(PlantGenieModel):
    results: List[GeneAnnotation]


class GenomeSequence(PlantGenieModel):
    species: str
    version: str
    chromosome: str
    begin: int
    end: int
    sequence: str


class GenomeSequenceRequest(PlantGenieModel):
    species: str = Field(description="species to query")
    version: str = Field(description="genome version for the given species")
    chromosome: str = Field(description="chromosome to extract")
    begin: int = Field(description="starting index (inclusive)")
    end: int = Field(description="ending index (inclusive)")


class GenomeSequenceResponse(PlantGenieModel):
    name: str
    sequence: str


class AvailableChromosomesRequest(PlantGenieModel):
    species: str
    version: str


class AvailableChromosomesResponse(PlantGenieModel):
    chromosomes: List[str]


class AvailableSpecies(PlantGenieModel):
    species_id: int = Field(alias="id")
    species_name: str = Field(alias="speciesName")
    species_abbreviation: str = Field(alias="speciesAbbreviation")
    avatar_path: str = Field(alias="avatarPath")


class AvailableSpeciesResponse(PlantGenieModel):
    species: List[AvailableSpecies]


class AvailableGenome(PlantGenieModel):
    genome_id: int = Field(alias="id")
    species_id: int = Field(alias="speciesId")
    species_name: str = Field(alias="speciesName")
    version: str
    publication_date: Optional[date] = Field(alias="publicationDate")
    doi: Optional[str]


class AvailableGenomesResponse(PlantGenieModel):
    genomes: List[AvailableGenome]
