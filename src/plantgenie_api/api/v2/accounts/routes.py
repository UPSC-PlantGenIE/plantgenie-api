import secrets

from fastapi import APIRouter

from plantgenie_api.api.v2.accounts.models import CreateAccountResponse
from plantgenie_api.dependencies import (
    AccountDep,
    SqliteDep,
    hash_account_id,
)

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", status_code=201, response_model=CreateAccountResponse)
async def create_account(conn: SqliteDep) -> CreateAccountResponse:
    account_id = f"{secrets.randbelow(10**16):016d}"

    await conn.execute(
        "INSERT INTO accounts (account_hash) VALUES (?)",
        (hash_account_id(account_id),),
    )
    await conn.commit()

    return CreateAccountResponse(account_id=account_id)


@router.get("/me")
async def get_account_me(account_hash: AccountDep):
    return None
