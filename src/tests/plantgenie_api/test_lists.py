import sqlite3

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_create_list_returns_account_and_list_ids(
    async_client: AsyncClient,
):
    response = await async_client.post(
        "/v2/lists",
        json={
            "name": "My list",
            "annotationId": "arath-Araport11",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["accountId"]
    assert body["listId"]


@pytest.mark.anyio
async def test_create_list_generates_unique_list_ids(
    async_client: AsyncClient,
):
    r1 = await async_client.post(
        "/v2/lists",
        json={"name": "First", "annotationId": "arath-Araport11"},
    )
    r2 = await async_client.post(
        "/v2/lists",
        json={"name": "Second", "annotationId": "arath-Araport11"},
    )
    assert r1.json()["listId"] != r2.json()["listId"]
    assert r1.json()["accountId"] is not None
    assert r2.json()["accountId"] is not None


@pytest.mark.anyio
async def test_get_list_returns_a_created_list(
    async_client: AsyncClient,
):
    create = await async_client.post(
        "/v2/lists",
        json={
            "name": "My list",
            "annotationId": "arath-Araport11",
        },
    )
    list_id = create.json()["listId"]

    response = await async_client.get(f"/v2/lists/{list_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["listId"] == list_id
    assert body["name"] == "My list"
    assert body["annotationId"] == "arath-Araport11"


@pytest.mark.anyio
async def test_create_list_persists_to_sqlite(
    async_client: AsyncClient,
    sqlite_conn: sqlite3.Connection,
):
    response = await async_client.post(
        "/v2/lists",
        json={
            "name": "Persisted",
            "annotationId": "arath-Araport11",
        },
    )
    list_id = response.json()["listId"]

    row = sqlite_conn.execute(
        "SELECT name, annotation_id FROM gene_lists "
        "WHERE list_id = ?",
        (list_id,),
    ).fetchone()

    assert row is not None
    assert row == ("Persisted", "arath-Araport11")


@pytest.mark.anyio
async def test_get_list_returns_404_when_missing(
    async_client: AsyncClient,
):
    response = await async_client.get("/v2/lists/does-not-exist")
    assert response.status_code == 404
