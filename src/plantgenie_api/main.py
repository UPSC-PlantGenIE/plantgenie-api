from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from plantgenie_api.api.v1.annotation.routes import (
    router as annotation_router,
)
from plantgenie_api.api.v1.blast.routes import router as blast_router
from plantgenie_api.api.v1.expression.routes import (
    router as expression_router,
)
from plantgenie_api.api.v1.enrichment.routes import (
    router as enrichment_router,
)
from plantgenie_api.api.v1.genome.routes import router as genome_router
from plantgenie_api.dependencies import DatabaseDep, lifespan
from plantgenie_api.models import (
    AvailableSpecies,
    AvailableSpeciesResponse,
)

app = FastAPI(
    root_path="/api",
    title="UPSC PlantGenIE API",
    version="0.0.1",
    description="Backend for the PlantGenIE React Frontend",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=[
        "*"
    ],  # Allow all origins (change this to specific origins in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router=blast_router, prefix="/v1")
app.include_router(router=genome_router, prefix="/v1")
app.include_router(router=expression_router, prefix="/v1")
app.include_router(router=annotation_router, prefix="/v1")
app.include_router(router=enrichment_router, prefix="/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to the PlantGenIE API!"}


@app.get("/available-species")
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
