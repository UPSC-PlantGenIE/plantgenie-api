from datetime import datetime

from pydantic import Field

from plantgenie_api.models import PlantGenieModel


class CreateListRequest(PlantGenieModel):
    name: str
    description: str | None = None
    annotation_id: str
    taxon_name: str


class CreateListResponse(PlantGenieModel):
    list_id: str


class PatchListRequest(PlantGenieModel):
    name: str | None = Field(default=None, min_length=1)
    add_gene_ids: list[str] | None = None
    remove_gene_ids: list[str] | None = None


MAX_RANDOM_GENES = 100


class RandomGenesRequest(PlantGenieModel):
    count: int = Field(ge=1, le=MAX_RANDOM_GENES)


class RandomGenesResponse(PlantGenieModel):
    added: int = Field(ge=0)


class GeneList(PlantGenieModel):
    list_id: str
    name: str
    description: str | None = None
    annotation_id: str
    taxon_name: str
    created_at: datetime
    gene_count: int = Field(ge=0)


class GetListsResponse(PlantGenieModel):
    lists: list[GeneList]


class GeneListWithMember(GeneList):
    member_gene_ids: list[str]
