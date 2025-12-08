from pathlib import Path

import duckdb
from fastapi import APIRouter

from plantgenie_api import ENV_DATA_PATH
from plantgenie_api.dependencies import backend_config
from plantgenie_api.api.v1.genome.models import (
    AvailableGenome,
    AvailableGenomesResponse,
)

from shared.db import SafeDuckDbConnection

DATA_PATH = (
    Path(ENV_DATA_PATH)
    if ENV_DATA_PATH
    else Path(__file__).parent.parent / "example_data"
)

DATABASE_PATH = DATA_PATH / "plantgenie-backend.db"


router = APIRouter(prefix="/genome")


@router.get(path="/available-genomes", tags=["v1", "genome"])
async def get_available_genomes() -> AvailableGenomesResponse:
    with SafeDuckDbConnection(
        f"{backend_config.get("DATA_PATH")}/{backend_config.get("DATABASE_NAME")}",
        allowed_directories=[backend_config.get("DATA_PATH")],
        read_only=True,
    ) as connection:
        query_relation = connection.sql(
            "SELECT * FROM genomes JOIN species ON (genomes.species_id = species.id);"
        ).project(
            "id", "species_id", "species_name", "version", "publication_date", "doi"
        )
        print(query_relation)

        return AvailableGenomesResponse(
            genomes=[
                AvailableGenome(
                    **{
                        k: v
                        for k, v in zip(AvailableGenome.model_fields.keys(), result)
                    }
                )
                for result in query_relation.fetchall()
            ]
        )
