from typing import Any

import psycopg
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, StrictInt

from app.db import get_db
from app.services import payments

router = APIRouter()


class PaymentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: StrictInt


@router.get("/people/{person_id}/payments")
def get_payments(
    person_id: int,
    conn: psycopg.Connection = Depends(get_db),
) -> dict[str, list[dict[str, Any]]]:
    return {"payments": payments.list_payments(conn, person_id)}


@router.post("/people/{person_id}/payments", status_code=201)
def post_payment(
    person_id: int,
    body: PaymentCreate,
    conn: psycopg.Connection = Depends(get_db),
) -> dict[str, Any]:
    return payments.record_payment(conn, person_id, body.amount)


@router.post("/people/{person_id}/payments/{payment_id}/cancel")
def post_cancel_payment(
    person_id: int,
    payment_id: int,
    conn: psycopg.Connection = Depends(get_db),
) -> dict[str, Any]:
    return payments.cancel_payment(conn, person_id, payment_id)
