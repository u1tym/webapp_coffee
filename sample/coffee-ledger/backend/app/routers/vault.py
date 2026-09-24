from datetime import date

import psycopg
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, StrictInt

from app.db import get_db
from app.services import vault

router = APIRouter()


class VaultOperationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str
    direction: str
    amount: StrictInt
    reason_date: date


@router.get("/vault-operations")
def get_vault_operations(
    conn: psycopg.Connection = Depends(get_db),
) -> dict[str, list[dict[str, object]]]:
    return {"vault_operations": vault.list_vault_operations(conn)}


@router.post("/vault-operations", status_code=201)
def post_vault_operation(
    body: VaultOperationCreate,
    conn: psycopg.Connection = Depends(get_db),
) -> dict[str, object]:
    return vault.create_vault_operation(
        conn,
        body.reason,
        body.direction,
        body.amount,
        body.reason_date,
    )
