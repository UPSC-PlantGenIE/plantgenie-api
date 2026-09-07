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
    add_gene_ids: list[str] | None = None
    remove_gene_ids: list[str] | None = None


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
