import hashlib
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, AsyncGenerator, Dict, Generator, List

import aiosqlite
import duckdb
from duckdb import DuckDBPyConnection
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession

from plantgenie_api.sqlite import bootstrap_sqlite


async def get_sqlite_connection(
    request: Request,
) -> AsyncGenerator[aiosqlite.Connection, None]:
    async with aiosqlite.connect(
        request.app.state.APP_ENVIRONMENT["SQLITE_PATH"]
    ) as conn:
        yield conn


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
        "NEO4J_URI",
        "NEO4J_USER",
        "NEO4J_PASSWORD",
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

    # connection = duckdb.connect(APP_ENVIRONMENT["DATABASE_PATH"])

    with duckdb.connect(APP_ENVIRONMENT["DATABASE_PATH"]) as connection:
        connection.execute(
            f"SET allowed_directories = ['{APP_ENVIRONMENT["DATA_PATH"]}'];"
        )

        connection.execute("SET enable_external_access = false;")
        connection.execute("SET lock_configuration = true")

    app.state.APP_ENVIRONMENT = APP_ENVIRONMENT

    driver = AsyncGraphDatabase.driver(
        APP_ENVIRONMENT["NEO4J_URI"],
        auth=(
            APP_ENVIRONMENT["NEO4J_USER"],
            APP_ENVIRONMENT["NEO4J_PASSWORD"],
        ),
    )
    await driver.verify_connectivity()
    app.state.NEO4J_DRIVER = driver

    sqlite_path = (
        Path(APP_ENVIRONMENT["DATA_PATH"]) / "plantgenie-userdata.sqlite"
    )
    bootstrap_sqlite(sqlite_path)
    APP_ENVIRONMENT["SQLITE_PATH"] = sqlite_path.as_posix()

    yield

    await driver.close()


def get_environment(request: Request) -> dict[str, str]:
    return request.app.state.APP_ENVIRONMENT


def get_blast_path(request: Request) -> Path:
    return (
        Path(request.app.state.APP_ENVIRONMENT["DATA_PATH"])
        / "pg-service-blast"
    )


def get_go_enrichment_path(request: Request) -> Path:
    return (
        Path(request.app.state.APP_ENVIRONMENT["DATA_PATH"])
        / "pg-service-go-enrichment"
    )


def get_db_connection(
    request: Request,
) -> Generator[DuckDBPyConnection, None, None]:
    """
    Creates a SafeDuckDbConnection context for dependency injection.
    Yields the active connection and ensures it closes after the request.
    """

    with duckdb.connect(
        request.app.state.APP_ENVIRONMENT["DATABASE_PATH"], read_only=True
    ) as connection:
        yield connection


async def get_neo4j_session(
    request: Request,
) -> AsyncGenerator[AsyncSession, None]:
    driver: AsyncDriver = request.app.state.NEO4J_DRIVER
    async with driver.session() as session:
        yield session


def hash_account_id(account_id: str) -> str:
    return hashlib.sha256(account_id.encode()).hexdigest()


async def get_account_hash(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    if authorization is None:
        raise HTTPException(status_code=401, detail="Unknown account")

    account_hash = hash_account_id(authorization.removeprefix("Bearer "))

    async with aiosqlite.connect(
        request.app.state.APP_ENVIRONMENT["SQLITE_PATH"]
    ) as conn:
        async with conn.execute(
            "SELECT 1 FROM accounts WHERE account_hash = ?", (account_hash,)
        ) as cursor:
            row = await cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=401, detail="Unknown account")

    return account_hash


DatabaseDep = Annotated[DuckDBPyConnection, Depends(get_db_connection)]
Neo4jDep = Annotated[AsyncSession, Depends(get_neo4j_session)]
SqliteDep = Annotated[aiosqlite.Connection, Depends(get_sqlite_connection)]
EnvironmentDep = Annotated[Dict[str, str], Depends(get_environment)]
BlastPathDep = Annotated[Path, Depends(get_blast_path)]
GoEnrichmentPathDep = Annotated[Path, Depends(get_go_enrichment_path)]
AccountDep = Annotated[str, Depends(get_account_hash)]
