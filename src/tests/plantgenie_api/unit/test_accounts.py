import hashlib
import sqlite3

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_create_account_responds_201(async_client: AsyncClient):
    response = await async_client.post("/v2/accounts")

    assert response.status_code == 201


@pytest.mark.anyio
async def test_create_account_returns_a_16_digit_id(
    async_client: AsyncClient,
):
    response = await async_client.post("/v2/accounts")

    account_id = response.json()["accountId"]
    assert len(account_id) == 16
    assert account_id.isdigit()


@pytest.mark.anyio
async def test_get_account_me_401s_on_unknown_id(
    async_client: AsyncClient,
):
    response = await async_client.get(
        "/v2/accounts/me",
        headers={"Authorization": "Bearer 0000000000000000"},
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_create_account_writes_one_row(
    async_client: AsyncClient,
    sqlite_conn: sqlite3.Connection,
):
    await async_client.post("/v2/accounts")

    rows = sqlite_conn.execute("SELECT account_hash FROM accounts").fetchall()
    assert len(rows) == 1


@pytest.mark.anyio
async def test_create_account_stores_a_hash_not_the_id(
    async_client: AsyncClient,
    sqlite_conn: sqlite3.Connection,
):
    response = await async_client.post("/v2/accounts")
    account_id = response.json()["accountId"]

    row = sqlite_conn.execute("SELECT account_hash FROM accounts").fetchone()
    assert row[0] == hashlib.sha256(account_id.encode()).hexdigest()


@pytest.mark.anyio
async def test_get_account_me_200s_for_a_created_id(
    async_client: AsyncClient,
):
    created = await async_client.post("/v2/accounts")
    account_id = created.json()["accountId"]

    response = await async_client.get(
        "/v2/accounts/me",
        headers={"Authorization": f"Bearer {account_id}"},
    )

    assert response.status_code == 200
