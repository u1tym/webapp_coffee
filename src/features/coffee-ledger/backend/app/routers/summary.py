from typing import Any

import psycopg
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.db import get_db
from app.errors import validation_error
from app.services import summary, summary_csv

router = APIRouter()


@router.get("/summary")
def get_summary(conn: psycopg.Connection = Depends(get_db)) -> dict[str, Any]:
    return summary.get_summary(conn)


@router.get("/summary/csv")
def get_summary_csv(
    range: str | None = Query(default=None),
    conn: psycopg.Connection = Depends(get_db),
) -> Response:
    if range is not None and range != "1month":
        raise validation_error()
    filename, body = summary_csv.build_summary_csv(conn, range)
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )
