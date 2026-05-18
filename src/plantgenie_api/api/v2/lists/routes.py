import secrets

from fastapi import APIRouter, HTTPException, Response

from plantgenie_api.api.v2.lists.models import (
    CreateListRequest,
    CreateListResponse,
    GeneList,
    GeneListWithMember,
    GetListsResponse,
    PatchListRequest,
)
from plantgenie_api.dependencies import SqliteDep

router = APIRouter(prefix="/lists", tags=["v2", "lists"])


@router.get("")
async def retrieve_lists(conn: SqliteDep) -> GetListsResponse:
    async with conn.execute(
        "SELECT g.list_id, g.name, g.description, g.annotation_id, g.taxon_name, g.created_at, "
        "COUNT(m.gene_id) AS gene_count "
        "FROM gene_lists g "
        "LEFT JOIN gene_list_members m ON g.list_id = m.list_id "
        "GROUP BY g.list_id"
    ) as cursor:
        rows = await cursor.fetchall()
    return GetListsResponse(
        lists=[
            GeneList(
                list_id=r[0],
                name=r[1],
                description=r[2],
                annotation_id=r[3],
                taxon_name=r[4],
                created_at=r[5],
                gene_count=r[6],
            )
            for r in rows
        ]
    )


@router.post("", status_code=201)
async def create_list(
    body: CreateListRequest, conn: SqliteDep
) -> CreateListResponse:
    list_id = secrets.token_hex(8)
    await conn.execute(
        "INSERT INTO gene_lists (list_id, name, description, annotation_id, taxon_name) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            list_id,
            body.name,
            body.description,
            body.annotation_id,
            body.taxon_name,
        ),
    )
    await conn.commit()
    return CreateListResponse(account_id="stub", list_id=list_id)


@router.get("/{list_id}")
async def get_list(list_id: str, conn: SqliteDep) -> GeneListWithMember:
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
    return GeneListWithMember(
        list_id=row[0],
        name=row[1],
        description=row[2],
        annotation_id=row[3],
        taxon_name=row[4],
        created_at=row[5],
        gene_count=row[6],
        member_gene_ids=[r[0] for r in member_rows],
    )


@router.delete("/{list_id}", status_code=204)
async def delete_list(list_id: str, conn: SqliteDep) -> Response:
    async with conn.execute(
        "SELECT 1 FROM gene_lists WHERE list_id = ?", (list_id,)
    ) as cursor:
        row = await cursor.fetchone()
    if row is None:
        raise HTTPException(
            status_code=404, detail=f"List '{list_id}' not found"
        )
    await conn.execute(
        "DELETE FROM gene_list_members WHERE list_id = ?", (list_id,)
    )
    await conn.execute("DELETE FROM gene_lists WHERE list_id = ?", (list_id,))
    await conn.commit()
    return Response(status_code=204)


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
