from datetime import date
from typing import Annotated

from neo4j.time import Date as Neo4jDate
from pydantic import BeforeValidator

from plantgenie_api.models import PlantGenieModel


def to_native(v: object) -> object:
    return v.to_native() if isinstance(v, Neo4jDate) else v


NativeDate = Annotated[date, BeforeValidator(to_native)]


class Taxon(PlantGenieModel):
    id: int
    scientific_name: str
    abbreviation: str
    alias: str | None = None
    common_name: str | None = None


class TaxaResponse(PlantGenieModel):
    taxa: list[Taxon]


class Assembly(PlantGenieModel):
    id: str
    version: str
    version_name: str | None = None
    published: bool
    publication_date: NativeDate | None = None
    doi: str | None = None
    taxon_abbreviation: str


class AssembliesResponse(PlantGenieModel):
    assemblies: list[Assembly]


class Annotation(PlantGenieModel):
    id: str
    version: str
    gene_count: int
    is_default: bool
    assembly_id: str


class AnnotationDetail(Annotation):
    taxon_abbreviation: str
    taxon_scientific_name: str


class AnnotationsResponse(PlantGenieModel):
    annotations: list[Annotation]
