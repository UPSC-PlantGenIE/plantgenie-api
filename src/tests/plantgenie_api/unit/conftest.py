import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from plantgenie_api.dependencies import get_neo4j_session
from plantgenie_api.main import app
from plantgenie_api.sqlite import bootstrap_sqlite


class FakeNeo4jRecord:
    def __init__(self, data: dict):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]


class FakeNeo4jResult:
    def __init__(self, records: list[dict]):
        self._records = [FakeNeo4jRecord(r) for r in records]

    def __aiter__(self):
        async def gen():
            for r in self._records:
                yield r

        return gen()


class FakeNeo4jSession:
    def __init__(self):
        self.next_records: list[dict] = []
        self.last_query: str | None = None
        self.last_params: dict | None = None

    async def run(self, query: str, **params):
        self.last_query = query
        self.last_params = params
        return FakeNeo4jResult(self.next_records)


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


@pytest.fixture
def neo4j_session() -> Generator[FakeNeo4jSession, None, None]:
    session = FakeNeo4jSession()

    async def override():
        yield session

    app.dependency_overrides[get_neo4j_session] = override
    yield session
    app.dependency_overrides.pop(get_neo4j_session, None)
