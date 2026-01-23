import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Dict, Generator, List

import duckdb
from duckdb import DuckDBPyConnection
from fastapi import Depends, FastAPI, Request


@asynccontextmanager
async def lifespan(app: FastAPI):
    APP_ENVIRONMENT: Dict[str, str] = {}
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

    missing_variables: List[str] = [
        var
        for var in required_environmental_variables
        if var not in os.environ
    ]

    if missing_variables:
        raise RuntimeError(
            f"Missing environmental variables must be defined: {', '.join(missing_variables)}"
        )

    APP_ENVIRONMENT = {
        var: os.environ[var] for var in required_environmental_variables
    }

    db_path = (
        Path(APP_ENVIRONMENT["DATA_PATH"])
        / APP_ENVIRONMENT["DATABASE_NAME"]
    )

    APP_ENVIRONMENT["DATABASE_PATH"] = db_path.resolve(
        strict=True
    ).as_posix()

    connection = duckdb.connect(APP_ENVIRONMENT["DATABASE_PATH"])

    connection.execute(
        f"SET allowed_directories = ['{APP_ENVIRONMENT["DATA_PATH"]}'];"
    )

    connection.execute("SET enable_external_access = false;")

    connection.execute("SET lock_configuration = true")

    app.state.APP_ENVIRONMENT = APP_ENVIRONMENT

    yield


def get_environment(request: Request) -> dict[str, str]:
    return request.app.state.APP_ENVIRONMENT


def get_blast_path(request: Request) -> Path:
    return (
        Path(request.app.state.APP_ENVIRONMENT["DATA_PATH"])
        / "pg-service-blast"
    )


def get_db_connection(
    request: Request,
) -> Generator[DuckDBPyConnection, None, None]:
    """
    Creates a SafeDuckDbConnection context for dependency injection.
    Yields the active connection and ensures it closes after the request.
    """

    with duckdb.connect(
        request.app.state.APP_ENVIRONMENT["DATABASE_PATH"]
    ) as connection:
        yield connection


DatabaseDep = Annotated[DuckDBPyConnection, Depends(get_db_connection)]
EnvironmentDep = Annotated[Dict[str, str], Depends(get_environment)]
BlastPathDep = Annotated[Path, Depends(get_blast_path)]
