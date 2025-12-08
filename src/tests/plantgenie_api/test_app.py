import pytest
from httpx import ASGITransport, AsyncClient

from plantgenie_api.main import app


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_root(anyio_backend):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the PlantGenIE API!"}
