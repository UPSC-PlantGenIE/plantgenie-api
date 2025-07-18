import os
from os import PathLike

from pathlib import Path
from typing import Optional

import duckdb
from duckdb.duckdb import DuckDBPyConnection

DUCKDB_DATABASE_BASENAME = "upsc-plantgenie.db"

ENV_DATA_PATH = os.environ.get("DATA_PATH", __file__)

BACKEND_DATA_PATH = (
    Path(ENV_DATA_PATH)
    if ENV_DATA_PATH
    else Path(__file__).parent.parent / "example_data"
)

DUCKDB_DATABASE_PATH = (
    Path(ENV_DATA_PATH) / DUCKDB_DATABASE_BASENAME
    if ENV_DATA_PATH
    else Path(__file__).parent / DUCKDB_DATABASE_BASENAME
)

class SafeDuckDbConnection:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = database_path
        self.connection: Optional[DuckDBPyConnection] = None

    def __enter__(self):
        self.connection = duckdb.connect(self.database_path, read_only=True)
        self.connection.execute(
            "SET allowed_directories = ['/srv/pg-application-data', '/opt/pg-application-data'];"
        )
        self.connection.execute("SET enable_external_access = false")
        self.connection.execute("SET lock_configuration = true")

        return self.connection;

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.connection:
            self.connection.close()
