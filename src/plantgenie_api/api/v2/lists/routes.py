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
        "SELECT g.list_id, g.name, g.description, g.annotation_id, g.taxon_name, g.created_at, "
        "COUNT(m.gene_id) AS gene_count "
        "FROM gene_lists g "
        "LEFT JOIN gene_list_members m ON g.list_id = m.list_id "
        "GROUP BY g.list_id"
    ) as cursor:
        rows = await cursor.fetchall()
    return {
        "lists": [
            {
                "listId": r[0],
                "name": r[1],
                "description": r[2],
                "annotationId": r[3],
                "taxonName": r[4],
                "createdAt": r[5],
                "geneCount": r[6],
            }
            for r in rows
        ]
    }


@router.post("", status_code=201, response_model=CreateListResponse)
async def create_list(
    body: CreateListRequest, conn: SqliteDep
) -> CreateListResponse:
    list_id = secrets.token_hex(8)
    await conn.execute(
        "INSERT INTO gene_lists (list_id, name, description, annotation_id, taxon_name) "
        "VALUES (?, ?, ?, ?, ?)",
        (list_id, body.name, body.description, body.annotation_id, body.taxon_name),
    )
    await conn.commit()
    return CreateListResponse(account_id="stub", list_id=list_id)


@router.get("/{list_id}")
async def get_list(list_id: str, conn: SqliteDep) -> dict:
    async with conn.execute(
        "SELECT g.list_id, g.name, g.description, g.annotation_id, g.taxon_name, g.created_at, "
        "COUNT(m.gene_id) AS gene_count "
        "FROM gene_lists g "
        "LEFT JOIN gene_list_members m ON g.list_id = m.list_id "
        "WHERE g.list_id = ? "
        "GROUP BY g.list_id",
        (list_id,),
    ) as cursor:
        row = await cursor.fetchone()
    if row is None:
        raise HTTPException(
            status_code=404, detail=f"List '{list_id}' not found"
        )
    async with conn.execute(
        "SELECT gene_id FROM gene_list_members "
        "WHERE list_id = ? ORDER BY added_at, gene_id",
        (list_id,),
    ) as cursor:
        member_rows = await cursor.fetchall()
    return {
        "listId": row[0],
        "name": row[1],
        "description": row[2],
        "annotationId": row[3],
        "taxonName": row[4],
        "createdAt": row[5],
        "geneCount": row[6],
        "memberGeneIds": [r[0] for r in member_rows],
    }


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
