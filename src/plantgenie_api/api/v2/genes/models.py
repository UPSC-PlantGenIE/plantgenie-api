from plantgenie_api.models import PlantGenieModel


class LookupGenesRequest(PlantGenieModel):
    annotation_id: str
    gene_ids: list[str]


class LookupGene(PlantGenieModel):
    gene_id: str
    name: str | None = None
    description: str | None = None


class LookupGenesResponse(PlantGenieModel):
    found: list[LookupGene]
    not_found: list[str]


class GeneDetail(PlantGenieModel):
    gene_id: str
    name: str | None = None
    description: str | None = None
    chromosome: str | None = None
    start_position: int | None = None
    end_position: int | None = None
    strand: str | None = None


class GoTerm(PlantGenieModel):
    id: str
    name: str | None = None
    namespace: str | None = None


class ArabidopsisHit(PlantGenieModel):
    gene_id: str
    name: str | None = None
    description: str | None = None
    evalue: float
    bitscore: float
