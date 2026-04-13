from fastapi import APIRouter

from plantgenie_api.api.v1.genome.models import (
    AvailableGenome,
    AvailableGenomesResponse,
)
from plantgenie_api.dependencies import DatabaseDep

router = APIRouter(prefix="/genome")


@router.get(path="/available-genomes", tags=["v1", "genome"])
async def get_available_genomes(
    db_connection: DatabaseDep,
) -> AvailableGenomesResponse:
    query_relation = db_connection.sql(
        "SELECT * FROM genomes JOIN species ON (genomes.species_id = species.id);"
    ).project(
        "id", "species_id", "species_name", "version", "publication_date", "doi"
    )

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
