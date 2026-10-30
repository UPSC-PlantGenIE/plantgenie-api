import pytest
from httpx import AsyncClient

from plantgenie_api.dependencies import lifespan
from plantgenie_api.main import app


@pytest.mark.anyio
async def test_root(async_client: AsyncClient):
    response = await async_client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the PlantGenIE API!"}


@pytest.mark.anyio
async def test_v1_routes_are_not_served(async_client: AsyncClient):
    response = await async_client.get("/v1/blast/version")

    assert response.status_code == 404


@pytest.mark.parametrize(
    "variable", ["CELERY_BROKER_URL", "CELERY_RESULT_BACKEND"]
)
@pytest.mark.anyio
async def test_startup_requires_celery_settings(
    monkeypatch: pytest.MonkeyPatch, variable: str
):
    monkeypatch.delenv(variable, raising=False)

    with pytest.raises(RuntimeError, match=variable):
        async with lifespan(app):
            pass
