from fastapi import APIRouter

from plantgenie_api import BACKEND_DATA_PATH
from plantgenie_api.api.v1.annotation.routes import (
    router as annotation_router,
)
from plantgenie_api.api.v1.blast.routes import router as blast_router
from plantgenie_api.api.v1.enrichment.routes import (
    router as enrichment_router,
)
from plantgenie_api.api.v1.expression.routes import (
    router as expression_router,
)
from plantgenie_api.api.v1.genome.routes import router as genome_router
from plantgenie_api.api.v1.models import (
    AvailableSpecies,
    AvailableSpeciesResponse,
)
from plantgenie_api.dependencies import DatabaseDep

DATABASE_PATH = BACKEND_DATA_PATH / "plantgenie-backend.db"

v1_router = APIRouter(prefix="/v1", tags=["v1"])

v1_router.include_router(annotation_router)
v1_router.include_router(blast_router)
v1_router.include_router(enrichment_router)
v1_router.include_router(expression_router)
v1_router.include_router(genome_router)


@v1_router.get("/available-species", tags=["species"])
async def get_available_species(
    db_connection: DatabaseDep,
) -> AvailableSpeciesResponse:
    return AvailableSpeciesResponse(
        species=[
            AvailableSpecies(
                **{
                    k: v
                    for k, v in zip(
                        AvailableSpecies.model_fields.keys(), result
                    )
                }
            )
            for result in db_connection.sql(
                "SELECT * FROM species;"
            ).fetchall()
        ]
    )
