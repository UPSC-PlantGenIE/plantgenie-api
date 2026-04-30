import secrets

from fastapi import APIRouter, HTTPException

from plantgenie_api.api.v2.lists.models import (
    CreateListRequest,
    CreateListResponse,
    PatchListRequest,
)
from plantgenie_api.dependencies import SqliteDep

router = APIRouter(prefix="/lists", tags=["v2", "lists"])


@router.get("")
async def retrieve_lists(conn: SqliteDep) -> dict:
    async with conn.execute(
        "SELECT list_id, name, annotation_id FROM gene_lists"
    ) as cursor:
        rows = await cursor.fetchall()
    return {
        "lists": [
            {"listId": r[0], "name": r[1], "annotationId": r[2]}
            for r in rows
        ]
    }


@router.post("", status_code=201, response_model=CreateListResponse)
async def create_list(
    body: CreateListRequest, conn: SqliteDep
) -> CreateListResponse:
    list_id = secrets.token_hex(8)
    await conn.execute(
        "INSERT INTO gene_lists (list_id, name, annotation_id) "
        "VALUES (?, ?, ?)",
        (list_id, body.name, body.annotation_id),
    )
    await conn.commit()
    return CreateListResponse(account_id="stub", list_id=list_id)


@router.get("/{list_id}")
async def get_list(list_id: str, conn: SqliteDep) -> dict:
    async with conn.execute(
        "SELECT list_id, name, annotation_id FROM gene_lists "
        "WHERE list_id = ?",
        (list_id,),
    ) as cursor:
        row = await cursor.fetchone()
    if row is None:
        raise HTTPException(
            status_code=404, detail=f"List '{list_id}' not found"
        )
    return {"listId": row[0], "name": row[1], "annotationId": row[2]}


@router.patch("/{list_id}")
async def patch_list(
    list_id: str, body: PatchListRequest, conn: SqliteDep
) -> dict:
    if body.add_gene_ids:
        await conn.executemany(
            "INSERT OR IGNORE INTO gene_list_members "
            "(list_id, gene_id) VALUES (?, ?)",
            [(list_id, g) for g in body.add_gene_ids],
        )
    if body.remove_gene_ids:
        await conn.executemany(
            "DELETE FROM gene_list_members "
            "WHERE list_id = ? AND gene_id = ?",
            [(list_id, g) for g in body.remove_gene_ids],
        )
    await conn.commit()
    return {"listId": list_id}
