from pathlib import Path

import duckdb
from fastapi import APIRouter

from plantgenie_api import ENV_DATA_PATH
from plantgenie_api.api.v1.genome.models import (
    AvailableGenome,
    AvailableGenomesResponse,
)

DATA_PATH = (
    Path(ENV_DATA_PATH)
    if ENV_DATA_PATH
    else Path(__file__).parent.parent / "example_data"
)

DATABASE_PATH = DATA_PATH / "plantgenie-backend.db"


router = APIRouter(prefix="/genome")


@router.get(path="/available-genomes")
async def get_available_genomes() -> AvailableGenomesResponse:
    # CREATE TABLE
    # species (
    #   id INT64 PRIMARY KEY,
    #   species_name VARCHAR NOT NULL,
	# 	species_alias VARCHAR,
	# 	species_abbreviation VARCHAR,
	# 	avatar_path VARCHAR
	# );
    # CREATE TABLE
    # genomes (
    #     id INT64 PRIMARY KEY,
    #     species_id INT64 REFERENCES species (id),
    #     version VARCHAR NOT NULL,
    #     version_name VARCHAR,
    #     published BOOLEAN,
    #     publication_date DATE,
    #     doi VARCHAR
    # );
    with duckdb.connect(DATABASE_PATH, read_only=True) as connection:
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
