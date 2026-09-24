from typing import Any

import psycopg
from fastapi import APIRouter, Depends

from app.db import get_db
from app.services import operations

router = APIRouter()


@router.get("/operation-logs")
def get_operation_logs(
    conn: psycopg.Connection = Depends(get_db),
) -> dict[str, list[dict[str, Any]]]:
    return {"operation_logs": operations.list_operation_logs(conn)}
