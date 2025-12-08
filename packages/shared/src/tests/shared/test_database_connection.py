from pathlib import Path

import pytest
from duckdb import (
    InvalidInputException,
    PermissionException,
    DuckDBPyConnection,
)


def test_can_access_allowed_dir(
    selectable_file: Path, safe_database_connection: DuckDBPyConnection
):
    assert selectable_file.exists()
    filepath_as_str = selectable_file.resolve().as_posix()
    safe_database_connection.sql(
        f"SELECT * FROM read_csv_auto('{filepath_as_str}')"
    )


def test_cannot_access_disallowed_dir(
    safe_database_connection: DuckDBPyConnection,
):
    with pytest.raises(PermissionException):
        safe_database_connection.sql(
            "SELECT * FROM read_csv_auto('/etc/passwd')"
        )


def test_cannot_modify_configuration(
    safe_database_connection: DuckDBPyConnection,
):
    with pytest.raises(InvalidInputException):
        safe_database_connection.sql("SET lock_configuration = false")
