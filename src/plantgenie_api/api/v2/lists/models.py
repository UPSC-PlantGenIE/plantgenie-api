from datetime import datetime
from typing import List, Optional

from pydantic import Field

from plantgenie_api.models import PlantGenieModel


class CreateListRequest(PlantGenieModel):
    account_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    annotation_id: str
    taxon_name: str


class CreateListResponse(PlantGenieModel):
    account_id: str
    list_id: str


class PatchListRequest(PlantGenieModel):
    add_gene_ids: Optional[List[str]] = None
    remove_gene_ids: Optional[List[str]] = None


class GeneList(PlantGenieModel):
    list_id: str
    name: str
    description: Optional[str] = None
    annotation_id: str
    taxon_name: str
    created_at: datetime
    gene_count: int = Field(ge=0)


class GetListsResponse(PlantGenieModel):
    lists: List[GeneList]


class GeneListWithMember(GeneList):
    member_gene_ids: List[str]
