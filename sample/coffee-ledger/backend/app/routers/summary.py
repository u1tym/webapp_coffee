from typing import Any

import psycopg
from fastapi import APIRouter, Depends

from app.db import get_db
from app.services import summary

router = APIRouter()


@router.get("/summary")
def get_summary(conn: psycopg.Connection = Depends(get_db)) -> dict[str, Any]:
    return summary.get_summary(conn)
