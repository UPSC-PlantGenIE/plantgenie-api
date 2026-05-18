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
            "taxonName": "Arabidopsis thaliana",
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
        json={"name": "First", "annotationId": "arath-Araport11", "taxonName": "Arabidopsis thaliana"},
    )
    r2 = await async_client.post(
        "/v2/lists",
        json={"name": "Second", "annotationId": "arath-Araport11", "taxonName": "Arabidopsis thaliana"},
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
            "taxonName": "Arabidopsis thaliana",
        },
    )
    list_id = create.json()["listId"]

    response = await async_client.get(f"/v2/lists/{list_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["listId"] == list_id
    assert body["name"] == "My list"
    assert body["annotationId"] == "arath-Araport11"
    assert body["taxonName"] == "Arabidopsis thaliana"
    assert body["geneCount"] == 0
    assert body["createdAt"] is not None
    assert body["memberGeneIds"] == []


@pytest.mark.anyio
async def test_get_list_returns_member_gene_ids_after_patch(
    async_client: AsyncClient,
):
    create = await async_client.post(
        "/v2/lists",
        json={
            "name": "My list",
            "annotationId": "arath-Araport11",
            "taxonName": "Arabidopsis thaliana",
        },
    )
    list_id = create.json()["listId"]

    await async_client.patch(
        f"/v2/lists/{list_id}",
        json={"addGeneIds": ["AT1G01010", "AT1G01020"]},
    )

    response = await async_client.get(f"/v2/lists/{list_id}")
    body = response.json()
    assert body["memberGeneIds"] == ["AT1G01010", "AT1G01020"]
    assert body["geneCount"] == 2


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
            "taxonName": "Arabidopsis thaliana",
        },
    )
    list_id = response.json()["listId"]

    row = sqlite_conn.execute(
        "SELECT name, annotation_id, taxon_name FROM gene_lists "
        "WHERE list_id = ?",
        (list_id,),
    ).fetchone()

    assert row is not None
    assert row == ("Persisted", "arath-Araport11", "Arabidopsis thaliana")


@pytest.mark.anyio
async def test_get_list_returns_404_when_missing(
    async_client: AsyncClient,
):
    response = await async_client.get("/v2/lists/does-not-exist")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_lists_returns_all_lists(
    async_client: AsyncClient,
):
    await async_client.post(
        "/v2/lists",
        json={"name": "First", "annotationId": "arath-Araport11", "taxonName": "Arabidopsis thaliana"},
    )
    await async_client.post(
        "/v2/lists",
        json={"name": "Second", "annotationId": "arath-Araport11", "taxonName": "Arabidopsis thaliana"},
    )

    response = await async_client.get("/v2/lists")

    assert response.status_code == 200
    body = response.json()
    names = [item["name"] for item in body["lists"]]
    assert "First" in names
    assert "Second" in names


@pytest.mark.anyio
async def test_delete_list_returns_204_for_existing_list(
    async_client: AsyncClient,
):
    create = await async_client.post(
        "/v2/lists",
        json={
            "name": "Doomed",
            "annotationId": "arath-Araport11",
            "taxonName": "Arabidopsis thaliana",
        },
    )
    list_id = create.json()["listId"]

    response = await async_client.delete(f"/v2/lists/{list_id}")

    assert response.status_code == 204


@pytest.mark.anyio
async def test_delete_list_makes_subsequent_get_return_404(
    async_client: AsyncClient,
):
    create = await async_client.post(
        "/v2/lists",
        json={
            "name": "Doomed",
            "annotationId": "arath-Araport11",
            "taxonName": "Arabidopsis thaliana",
        },
    )
    list_id = create.json()["listId"]

    await async_client.delete(f"/v2/lists/{list_id}")
    response = await async_client.get(f"/v2/lists/{list_id}")

    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_list_cascades_to_members(
    async_client: AsyncClient,
    sqlite_conn: sqlite3.Connection,
):
    create = await async_client.post(
        "/v2/lists",
        json={
            "name": "Doomed",
            "annotationId": "arath-Araport11",
            "taxonName": "Arabidopsis thaliana",
        },
    )
    list_id = create.json()["listId"]
    await async_client.patch(
        f"/v2/lists/{list_id}",
        json={"addGeneIds": ["AT1G01010", "AT1G01020"]},
    )

    await async_client.delete(f"/v2/lists/{list_id}")

    rows = sqlite_conn.execute(
        "SELECT COUNT(*) FROM gene_list_members WHERE list_id = ?",
        (list_id,),
    ).fetchone()
    assert rows[0] == 0


@pytest.mark.anyio
async def test_delete_list_returns_404_when_missing(
    async_client: AsyncClient,
):
    response = await async_client.delete("/v2/lists/does-not-exist")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_patch_list_adds_genes(
    async_client: AsyncClient,
    sqlite_conn: sqlite3.Connection,
):
    create = await async_client.post(
        "/v2/lists",
        json={"name": "My list", "annotationId": "arath-Araport11", "taxonName": "Arabidopsis thaliana"},
    )
    list_id = create.json()["listId"]

    response = await async_client.patch(
        f"/v2/lists/{list_id}",
        json={"addGeneIds": ["AT1G01010", "AT1G01020"]},
    )

    assert response.status_code == 200
    rows = sqlite_conn.execute(
        "SELECT gene_id FROM gene_list_members "
        "WHERE list_id = ? ORDER BY gene_id",
        (list_id,),
    ).fetchall()
    assert [r[0] for r in rows] == ["AT1G01010", "AT1G01020"]
