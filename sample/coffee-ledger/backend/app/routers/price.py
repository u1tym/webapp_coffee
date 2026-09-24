from typing import Any

import psycopg
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, StrictInt

from app.db import get_db
from app.services import price

router = APIRouter()


class CupPriceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: StrictInt


@router.get("/cup-price")
def get_cup_price(conn: psycopg.Connection = Depends(get_db)) -> dict[str, Any]:
    return price.get_cup_price(conn)


@router.put("/cup-price")
def put_cup_price(
    body: CupPriceUpdate,
    conn: psycopg.Connection = Depends(get_db),
) -> dict[str, Any]:
    return price.set_cup_price(conn, body.amount)
