from pathlib import Path
from typing import List, Optional

import duckdb
from duckdb import DuckDBPyConnection


class SafeDuckDbConnection:
    def __init__(
        self,
        database_path: str | Path,
        read_only: bool = True,
        allowed_directories: Optional[List[str]] = None,
    ) -> None:
        self.database_path = database_path
        self.connection: Optional[DuckDBPyConnection] = None
        self.read_only = read_only
        self.allowed_directories = allowed_directories

    def __enter__(self) -> DuckDBPyConnection:
        self.connection = duckdb.connect(
            self.database_path, read_only=self.read_only
        )

        if self.allowed_directories is not None:
            dir_list_str = ", ".join([f"'{d}'" for d in self.allowed_directories])
            allowed_dirs_sql = f"SET allowed_directories = [{dir_list_str}];"
            self.connection.execute(allowed_dirs_sql)

        self.connection.execute("SET enable_external_access = false")
        self.connection.execute("SET lock_configuration = true")

        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.connection:
            self.connection.close()
