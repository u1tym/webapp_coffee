from datetime import date

import psycopg
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, StrictInt, StrictStr, field_validator

from app.db import get_db
from app.services import vault

router = APIRouter()


class VaultOperationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: StrictStr
    direction: StrictStr
    amount: StrictInt
    reason_date: date

    @field_validator("reason_date", mode="before")
    @classmethod
    def reason_date_must_be_text(cls, value: object) -> object:
        # 数値（UNIX 時刻として解釈される）などを受け付けず、"YYYY-MM-DD" の文字列だけにする
        if not isinstance(value, str):
            raise ValueError("reason_date は YYYY-MM-DD の文字列で指定してください。")
        return value


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
