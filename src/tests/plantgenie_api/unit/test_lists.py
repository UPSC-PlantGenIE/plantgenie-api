import hashlib
import sqlite3

import pytest
from httpx import AsyncClient

ADA = "1111111111111111"
BOB = "2222222222222222"
CARL = "3333333333333333"


def given_account(conn: sqlite3.Connection, account_id: str) -> str:
    account_hash = hashlib.sha256(account_id.encode()).hexdigest()
    conn.execute(
        "INSERT OR IGNORE INTO accounts (account_hash) VALUES (?)",
        (account_hash,),
    )
    conn.commit()
    return account_hash


def given_account_with_list(
    conn: sqlite3.Connection, account_id: str, list_id: str, name: str
):
    account_hash = given_account(conn, account_id)
    conn.execute(
        "INSERT INTO gene_lists "
        "(list_id, name, annotation_id, taxon_name, account_hash) "
        "VALUES (?, ?, ?, ?, ?)",
        (list_id, name, "arath-Araport11", "Arabidopsis thaliana", account_hash),
    )
    conn.commit()


@pytest.fixture
def auth_headers(sqlite_conn: sqlite3.Connection) -> dict[str, str]:
    given_account(sqlite_conn, CARL)
    return {"Authorization": f"Bearer {CARL}"}


@pytest.mark.anyio
async def test_create_list_stores_the_owning_account(
    async_client: AsyncClient,
    sqlite_conn: sqlite3.Connection,
):
    created = await async_client.post("/v2/accounts")
    account_id = created.json()["accountId"]

    await async_client.post(
        "/v2/lists",
        headers={"Authorization": f"Bearer {account_id}"},
        json={
            "name": "My list",
            "annotationId": "arath-Araport11",
            "taxonName": "Arabidopsis thaliana",
        },
    )

    row = sqlite_conn.execute("SELECT account_hash FROM gene_lists").fetchone()
    assert row[0] == hashlib.sha256(account_id.encode()).hexdigest()


@pytest.mark.anyio
async def test_lists_are_scoped_to_the_account(
    async_client: AsyncClient,
    sqlite_conn: sqlite3.Connection,
):
    given_account_with_list(sqlite_conn, ADA, "ada-1", "Ada's list")
    given_account_with_list(sqlite_conn, BOB, "bob-1", "Bob's list")

    adas_response = await async_client.get(
        "/v2/lists", headers={"Authorization": f"Bearer {ADA}"}
    )
    bobs_response = await async_client.get(
        "/v2/lists", headers={"Authorization": f"Bearer {BOB}"}
    )

    assert [list_["name"] for list_ in adas_response.json()["lists"]] == [
        "Ada's list"
    ]
    assert [list_["name"] for list_ in bobs_response.json()["lists"]] == [
        "Bob's list"
    ]


@pytest.mark.anyio
async def test_a_list_is_only_visible_to_its_owner(
    async_client: AsyncClient,
    sqlite_conn: sqlite3.Connection,
):
    given_account_with_list(sqlite_conn, ADA, "ada-1", "Ada's list")
    given_account(sqlite_conn, BOB)

    adas_response = await async_client.get(
        "/v2/lists/ada-1", headers={"Authorization": f"Bearer {ADA}"}
    )
    bobs_response = await async_client.get(
        "/v2/lists/ada-1", headers={"Authorization": f"Bearer {BOB}"}
    )

    assert adas_response.status_code == 200
    assert bobs_response.status_code == 404


@pytest.mark.anyio
async def test_a_list_can_only_be_deleted_by_its_owner(
    async_client: AsyncClient,
    sqlite_conn: sqlite3.Connection,
):
    given_account_with_list(sqlite_conn, ADA, "ada-1", "Ada's list")
    given_account(sqlite_conn, BOB)

    bobs_response = await async_client.delete(
        "/v2/lists/ada-1", headers={"Authorization": f"Bearer {BOB}"}
    )
    adas_response = await async_client.delete(
        "/v2/lists/ada-1", headers={"Authorization": f"Bearer {ADA}"}
    )

    assert bobs_response.status_code == 404
    assert adas_response.status_code == 204


@pytest.mark.anyio
async def test_a_list_can_only_be_patched_by_its_owner(
    async_client: AsyncClient,
    sqlite_conn: sqlite3.Connection,
):
    given_account_with_list(sqlite_conn, ADA, "ada-1", "Ada's list")
    given_account(sqlite_conn, BOB)

    bobs_response = await async_client.patch(
        "/v2/lists/ada-1",
        headers={"Authorization": f"Bearer {BOB}"},
        json={"addGeneIds": ["AT1G01010"]},
    )
    adas_response = await async_client.patch(
        "/v2/lists/ada-1",
        headers={"Authorization": f"Bearer {ADA}"},
        json={"addGeneIds": ["AT1G01020"]},
    )

    assert bobs_response.status_code == 404
    assert adas_response.status_code == 200
    rows = sqlite_conn.execute(
        "SELECT gene_id FROM gene_list_members WHERE list_id = ?", ("ada-1",)
    ).fetchall()
    assert [r[0] for r in rows] == ["AT1G01020"]


@pytest.mark.anyio
async def test_create_list_401s_without_a_bearer(async_client: AsyncClient):
    response = await async_client.post(
        "/v2/lists",
        json={
            "name": "My list",
            "annotationId": "arath-Araport11",
            "taxonName": "Arabidopsis thaliana",
        },
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_create_list_401s_for_an_unknown_account(
    async_client: AsyncClient,
):
    response = await async_client.post(
        "/v2/lists",
        headers={"Authorization": "Bearer 9999999999999999"},
        json={
            "name": "My list",
            "annotationId": "arath-Araport11",
            "taxonName": "Arabidopsis thaliana",
        },
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_create_list_returns_account_and_list_ids(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
):
    response = await async_client.post(
        "/v2/lists",
        headers=auth_headers,
        json={
            "name": "My list",
            "annotationId": "arath-Araport11",
            "taxonName": "Arabidopsis thaliana",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["listId"]


@pytest.mark.anyio
async def test_create_list_generates_unique_list_ids(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
):
    r1 = await async_client.post(
        "/v2/lists",
        headers=auth_headers,
        json={"name": "First", "annotationId": "arath-Araport11", "taxonName": "Arabidopsis thaliana"},
    )
    r2 = await async_client.post(
        "/v2/lists",
        headers=auth_headers,
        json={"name": "Second", "annotationId": "arath-Araport11", "taxonName": "Arabidopsis thaliana"},
    )
    assert r1.json()["listId"] != r2.json()["listId"]


@pytest.mark.anyio
async def test_get_list_returns_a_created_list(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
):
    create = await async_client.post(
        "/v2/lists",
        headers=auth_headers,
        json={
            "name": "My list",
            "annotationId": "arath-Araport11",
            "taxonName": "Arabidopsis thaliana",
        },
    )
    list_id = create.json()["listId"]

    response = await async_client.get(f"/v2/lists/{list_id}", headers=auth_headers)

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
    auth_headers: dict[str, str],
):
    create = await async_client.post(
        "/v2/lists",
        headers=auth_headers,
        json={
            "name": "My list",
            "annotationId": "arath-Araport11",
            "taxonName": "Arabidopsis thaliana",
        },
    )
    list_id = create.json()["listId"]

    await async_client.patch(
        f"/v2/lists/{list_id}",
        headers=auth_headers,
        json={"addGeneIds": ["AT1G01010", "AT1G01020"]},
    )

    response = await async_client.get(f"/v2/lists/{list_id}", headers=auth_headers)
    body = response.json()
    assert body["memberGeneIds"] == ["AT1G01010", "AT1G01020"]
    assert body["geneCount"] == 2


@pytest.mark.anyio
async def test_create_list_persists_to_sqlite(
    async_client: AsyncClient,
    sqlite_conn: sqlite3.Connection,
    auth_headers: dict[str, str],
):
    response = await async_client.post(
        "/v2/lists",
        headers=auth_headers,
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
    auth_headers: dict[str, str],
):
    response = await async_client.get(
        "/v2/lists/does-not-exist", headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_lists_returns_all_of_my_lists(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
):
    await async_client.post(
        "/v2/lists",
        headers=auth_headers,
        json={"name": "First", "annotationId": "arath-Araport11", "taxonName": "Arabidopsis thaliana"},
    )
    await async_client.post(
        "/v2/lists",
        headers=auth_headers,
        json={"name": "Second", "annotationId": "arath-Araport11", "taxonName": "Arabidopsis thaliana"},
    )

    response = await async_client.get("/v2/lists", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    names = [item["name"] for item in body["lists"]]
    assert "First" in names
    assert "Second" in names


@pytest.mark.anyio
async def test_delete_list_returns_204_for_existing_list(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
):
    create = await async_client.post(
        "/v2/lists",
        headers=auth_headers,
        json={
            "name": "Doomed",
            "annotationId": "arath-Araport11",
            "taxonName": "Arabidopsis thaliana",
        },
    )
    list_id = create.json()["listId"]

    response = await async_client.delete(f"/v2/lists/{list_id}", headers=auth_headers)

    assert response.status_code == 204


@pytest.mark.anyio
async def test_delete_list_makes_subsequent_get_return_404(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
):
    create = await async_client.post(
        "/v2/lists",
        headers=auth_headers,
        json={
            "name": "Doomed",
            "annotationId": "arath-Araport11",
            "taxonName": "Arabidopsis thaliana",
        },
    )
    list_id = create.json()["listId"]

    await async_client.delete(f"/v2/lists/{list_id}", headers=auth_headers)
    response = await async_client.get(f"/v2/lists/{list_id}", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_list_cascades_to_members(
    async_client: AsyncClient,
    sqlite_conn: sqlite3.Connection,
    auth_headers: dict[str, str],
):
    create = await async_client.post(
        "/v2/lists",
        headers=auth_headers,
        json={
            "name": "Doomed",
            "annotationId": "arath-Araport11",
            "taxonName": "Arabidopsis thaliana",
        },
    )
    list_id = create.json()["listId"]
    await async_client.patch(
        f"/v2/lists/{list_id}",
        headers=auth_headers,
        json={"addGeneIds": ["AT1G01010", "AT1G01020"]},
    )

    await async_client.delete(f"/v2/lists/{list_id}", headers=auth_headers)

    rows = sqlite_conn.execute(
        "SELECT COUNT(*) FROM gene_list_members WHERE list_id = ?",
        (list_id,),
    ).fetchone()
    assert rows[0] == 0


@pytest.mark.anyio
async def test_delete_list_returns_404_when_missing(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
):
    response = await async_client.delete(
        "/v2/lists/does-not-exist", headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_patch_list_adds_genes(
    async_client: AsyncClient,
    sqlite_conn: sqlite3.Connection,
    auth_headers: dict[str, str],
):
    create = await async_client.post(
        "/v2/lists",
        headers=auth_headers,
        json={"name": "My list", "annotationId": "arath-Araport11", "taxonName": "Arabidopsis thaliana"},
    )
    list_id = create.json()["listId"]

    response = await async_client.patch(
        f"/v2/lists/{list_id}",
        headers=auth_headers,
        json={"addGeneIds": ["AT1G01010", "AT1G01020"]},
    )

    assert response.status_code == 200
    rows = sqlite_conn.execute(
        "SELECT gene_id FROM gene_list_members "
        "WHERE list_id = ? ORDER BY gene_id",
        (list_id,),
    ).fetchall()
    assert [r[0] for r in rows] == ["AT1G01010", "AT1G01020"]
