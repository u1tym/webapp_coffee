from typing import Any

import psycopg
from fastapi import APIRouter, Depends

from app.db import get_db
from app.services import drinks

router = APIRouter()


@router.get("/people/{person_id}/drinks")
def get_drinks(
    person_id: int,
    conn: psycopg.Connection = Depends(get_db),
) -> dict[str, list[dict[str, Any]]]:
    return {"drinks": drinks.list_drinks(conn, person_id)}


@router.post("/people/{person_id}/drinks", status_code=201)
def post_drink(
    person_id: int,
    conn: psycopg.Connection = Depends(get_db),
) -> dict[str, Any]:
    return drinks.record_drink(conn, person_id)


@router.post("/people/{person_id}/drinks/{drink_id}/cancel")
def post_cancel_drink(
    person_id: int,
    drink_id: int,
    conn: psycopg.Connection = Depends(get_db),
) -> dict[str, Any]:
    return drinks.cancel_drink(conn, person_id, drink_id)
