import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path

import psycopg
from fastapi import Request
from psycopg.rows import dict_row
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import db_connect_kwargs

_SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def connect() -> psycopg.Connection:
    return psycopg.connect(**db_connect_kwargs(), row_factory=dict_row)


def init_schema() -> None:
    with connect() as conn:
        for sql_path in sorted(_SQL_DIR.glob("*.sql")):
            script = sql_path.read_text(encoding="utf-8")
            statements = [part.strip() for part in script.split(";") if part.strip()]
            for statement in statements:
                conn.execute(statement)
        conn.commit()


def get_db(request: Request) -> psycopg.Connection:
    return request.state.db


class DbSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        conn = await asyncio.to_thread(connect)
        request.state.db = conn
        try:
            response = await call_next(request)
            if response.status_code < 400:
                await asyncio.to_thread(conn.commit)
            else:
                await asyncio.to_thread(conn.rollback)
            return response
        except Exception:
            await asyncio.to_thread(conn.rollback)
            raise
        finally:
            await asyncio.to_thread(conn.close)
