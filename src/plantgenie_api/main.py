import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from shared.config import backend_config
from shared.services.database import SafeDuckDbConnection

from plantgenie_api.api.v1.annotation.routes import (
    router as annotation_router,
)
from plantgenie_api.api.v1.blast.routes import router as blast_router
from plantgenie_api.api.v1.expression.routes import (
    router as expression_router,
)
from plantgenie_api.api.v1.genome.routes import router as genome_router
from plantgenie_api.models import (
    AvailableSpecies,
    AvailableSpeciesResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    required_environmental_variables = [
        "DATA_PATH",
        "DATABASE_NAME",
        "OS_AUTH_TYPE",
        "OS_AUTH_URL",
        "OS_IDENTITY_API_VERSION",
        "OS_REGION_NAME",
        "OS_INTERFACE",
        "OS_APPLICATION_CREDENTIAL_ID",
        "OS_APPLICATION_CREDENTIAL_SECRET",
    ]

    missing_variables = [
        value
        for value in required_environmental_variables
        if os.environ.get(value) is None
        and backend_config.get(value) is None
    ]

    if len(missing_variables) > 0:
        raise RuntimeError(
            f"Missing environmental variables must be defined: {", ".join(missing_variables)}"
        )

    yield


app = FastAPI(
    root_path="/api",
    title="UPSC PlantGenIE API",
    version="0.0.1",
    description="Backend for the PlantGenIE React Frontend",
    lifespan=lifespan,
)

# app.add_middleware(  # type: ignore[bad-argument-type]
#     CORSMiddleware,
#     allow_origins=[
#         "*"
#     ],  # Allow all origins (change this to specific origins in production)
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
app.include_router(router=blast_router, prefix="/v1")
app.include_router(router=genome_router, prefix="/v1")
app.include_router(router=expression_router, prefix="/v1")
app.include_router(router=annotation_router, prefix="/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to the PlantGenIE API!"}


@app.get("/available-species")
async def get_available_species() -> AvailableSpeciesResponse:
    DATA_DIRECTORY: Optional[str] = backend_config.get("DATA_PATH")

    with SafeDuckDbConnection(
        f"{backend_config.get("DATA_PATH")}/{backend_config.get("DATABASE_NAME")}",
        allowed_directories=[DATA_DIRECTORY] if DATA_DIRECTORY else None,
        read_only=True,
    ) as connection:
        query_relation = connection.sql("select * from species;")

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
                for result in query_relation.fetchall()
            ]
        )
