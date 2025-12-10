from pathlib import Path

import pytest

from shared.db import SafeDuckDbConnection


@pytest.fixture(scope="session")
def allowed_path():
    return Path(__file__).parent.resolve()


@pytest.fixture(scope="session")
def selectable_file(allowed_path: Path):
    file_to_write = allowed_path / "test_example.txt"
    file_to_write.write_text("id\tcontent\n1\tYou got it\n")
    yield file_to_write
    file_to_write.unlink()

@pytest.fixture(scope="session")
def safe_database_connection(allowed_path: Path):
    with SafeDuckDbConnection(
        ":memory:",
        read_only=False,
        allowed_directories=[allowed_path.resolve().as_posix()],
    ) as connection:
        yield connection
