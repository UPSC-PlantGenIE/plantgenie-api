import sqlite3
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from plantgenie_api.main import app
from plantgenie_api.sqlite import bootstrap_sqlite


@pytest.fixture(scope="package", autouse=True)
def anyio_backend():
    return "asyncio"


@pytest.fixture
def sqlite_conn(tmp_path: Path):
    db_path = tmp_path / "userdata.sqlite"
    bootstrap_sqlite(db_path)
    app.state.APP_ENVIRONMENT = {"SQLITE_PATH": str(db_path)}
    conn = sqlite3.connect(str(db_path))
    yield conn
    conn.close()


@pytest.fixture
async def async_client(sqlite_conn: sqlite3.Connection):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
