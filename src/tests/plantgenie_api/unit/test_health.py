from pathlib import Path

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_health_200s_when_the_data_is_marked_ready(
    async_client: AsyncClient, tmp_path: Path
):
    (tmp_path / ".data-ready").touch()

    response = await async_client.get("/v2/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.anyio
async def test_health_503s_without_the_marker(async_client: AsyncClient):
    response = await async_client.get("/v2/health")

    assert response.status_code == 503
