from typing import Annotated
from fastapi import APIRouter, File, UploadFile

from plantgenie_api import SafeDuckDbConnection
from plantgenie_api.api.v1 import BACKEND_DATA_PATH, DATABASE_PATH
from plantgenie_api.api.v1.enrichment.models import (
    GenesToGoRequest,
    GenesToGoResponse,
)

router = APIRouter(prefix="/v1/enrichment")


@router.get(path="/")
async def root():
    pass


@router.post(path="/genes-to-go-terms")
async def genes_to_go_terms(
    request: GenesToGoRequest,
) -> GenesToGoResponse:

    # count number of genes from gene list for each go term (non-zero)
    return GenesToGoResponse(go_terms_list=[])


@router.post(path="/go-enrichment-analysis")
async def gene_ontology_enrichment_analysis(
    target_genes: UploadFile, background_genes: UploadFile
):
    pass
