from typing import List, Optional

from plantgenie_api.models import PlantGenieModel


class CreateListRequest(PlantGenieModel):
    account_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    annotation_id: str


class CreateListResponse(PlantGenieModel):
    account_id: str
    list_id: str


class PatchListRequest(PlantGenieModel):
    add_gene_ids: Optional[List[str]] = None
    remove_gene_ids: Optional[List[str]] = None
