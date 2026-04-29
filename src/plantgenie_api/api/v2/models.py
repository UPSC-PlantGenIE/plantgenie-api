from datetime import date
from typing import Annotated, List, Optional

from pydantic import BeforeValidator

from plantgenie_api.models import PlantGenieModel


def _to_native(v):
    return v.to_native() if hasattr(v, "to_native") else v


NativeDate = Annotated[date, BeforeValidator(_to_native)]


class Taxon(PlantGenieModel):
    id: int
    scientific_name: str
    abbreviation: str
    alias: Optional[str] = None
    common_name: Optional[str] = None


class TaxaResponse(PlantGenieModel):
    taxa: List[Taxon]


class Assembly(PlantGenieModel):
    id: str
    version: str
    version_name: Optional[str] = None
    published: bool
    publication_date: Optional[NativeDate] = None
    doi: Optional[str] = None
    taxon_abbreviation: str


class AssembliesResponse(PlantGenieModel):
    assemblies: List[Assembly]


class Annotation(PlantGenieModel):
    id: str
    version: str
    gene_count: int
    is_default: bool
    assembly_id: str


class AnnotationsResponse(PlantGenieModel):
    annotations: List[Annotation]


class CreateListRequest(PlantGenieModel):
    name: str
    annotation_id: str
    account_id: Optional[str] = None
    description: Optional[str] = None


class CreateListResponse(PlantGenieModel):
    account_id: str
    list_id: str
