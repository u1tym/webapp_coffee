import psycopg
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, StrictInt, StrictStr

from app.db import get_db
from app.services import unpaid

router = APIRouter()


class UnpaidAdjustmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_amount: StrictInt
    reason: StrictStr


@router.post("/people/{person_id}/unpaid-adjustments", status_code=201)
def post_unpaid_adjustment(
    person_id: int,
    body: UnpaidAdjustmentCreate,
    conn: psycopg.Connection = Depends(get_db),
) -> dict[str, object]:
    return unpaid.create_unpaid_adjustment(
        conn,
        person_id,
        body.new_amount,
        body.reason,
    )
