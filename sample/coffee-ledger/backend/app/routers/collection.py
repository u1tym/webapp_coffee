from typing import Any

import psycopg
from fastapi import APIRouter, Depends

from app.db import get_db
from app.services import collection

router = APIRouter()


@router.get("/collection")
def get_collection(conn: psycopg.Connection = Depends(get_db)) -> dict[str, int]:
    return collection.get_collection(conn)


@router.get("/safe-deposits")
def get_safe_deposits(
    conn: psycopg.Connection = Depends(get_db),
) -> dict[str, list[dict[str, Any]]]:
    return {"safe_deposits": collection.list_safe_deposits(conn)}


@router.post("/safe-deposits", status_code=201)
def post_safe_deposit(conn: psycopg.Connection = Depends(get_db)) -> dict[str, Any]:
    return collection.create_safe_deposit(conn)
