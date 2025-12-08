import os
from contextlib import asynccontextmanager

from dotenv import dotenv_values

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from plantgenie_api.dependencies import backend_config
from plantgenie_api.models import (
    AvailableGenome,
    AvailableGenomesResponse,
    AvailableSpecies,
    AvailableSpeciesResponse,
)

from plantgenie_api.api.v1.blast.routes import router as blast_router
from plantgenie_api.api.v1.genome.routes import router as genome_router
from plantgenie_api.api.v1.expression.routes import (
    router as expression_router,
)
from plantgenie_api.api.v1.annotation.routes import (
    router as annotation_router,
)

from shared.db import SafeDuckDbConnection


@asynccontextmanager
async def lifespan(app: FastAPI):
    required_environmental_variables = [
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
    ]

    print("Here are the missing variables!")
    print(missing_variables)

    print(backend_config)
    if len(missing_variables) > 0:
        raise RuntimeError(
            f"Missing environmental variables must be defined: {", ".join(missing_variables)}"
        )

    yield

    pass


app = FastAPI(
    root_path="/api",
    title="UPSC PlantGenIE API",
    version="0.0.1",
    description="Backend for the PlantGenIE React Frontend",
    lifespan=lifespan,
)

app.add_middleware(  # type: ignore[bad-argument-type]
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # Allow all origins (change this to specific origins in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app.include_router(router=genome_router, prefix="/api")
app.include_router(router=blast_router, prefix="/v1")
app.include_router(router=genome_router, prefix="/v1")
app.include_router(router=expression_router, prefix="/v1")
app.include_router(router=annotation_router, prefix="/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to the PlantGenIE API!"}


@app.get("/available-species")
async def get_available_species() -> AvailableSpeciesResponse:
    with SafeDuckDbConnection(
        f"{backend_config.get("DATA_PATH")}/{backend_config.get("DATABASE_NAME")}",
        allowed_directories=[backend_config.get("DATA_PATH")],
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
    # with duckdb.connect(DATABASE_PATH, read_only=True) as connection:
    #     query_relation = connection.sql("select * from species;")

    #     return AvailableSpeciesResponse(
    #         species=[
    #             AvailableSpecies(
    #                 **{
    #                     k: v
    #                     for k, v in zip(
    #                         AvailableSpecies.model_fields.keys(), result
    #                     )
    #                 }
    #             )
    #             for result in query_relation.fetchall()
    #         ]
    #     )


@app.get("/available-genomes")
async def get_available_genomes() -> AvailableGenomesResponse:
    with SafeDuckDbConnection(
        f"{backend_config.get("DATA_PATH")}/{backend_config.get("DATABASE_NAME")}",
        allowed_directories=[backend_config.get("DATA_PATH")],
        read_only=True,
    ) as connection:
        query_relation = connection.sql(
            "select * from genomes join species on (genomes.species_id = species.id);"
        ).project(
            "id",
            "species_id",
            "species_name",
            "version",
            "publication_date",
            "doi",
        )
        print(query_relation)

        return AvailableGenomesResponse(
            genomes=[
                AvailableGenome(
                    **{
                        k: v
                        for k, v in zip(
                            AvailableGenome.model_fields.keys(), result
                        )
                    }
                )
                for result in query_relation.fetchall()
            ]
        )
