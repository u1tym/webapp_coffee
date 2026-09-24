from typing import Any

import psycopg
from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.db import get_db
from app.services import summary, summary_csv

router = APIRouter()


@router.get("/summary")
def get_summary(conn: psycopg.Connection = Depends(get_db)) -> dict[str, Any]:
    return summary.get_summary(conn)


@router.get("/summary/csv")
def get_summary_csv(conn: psycopg.Connection = Depends(get_db)) -> Response:
    filename, body = summary_csv.build_summary_csv(conn)
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )
