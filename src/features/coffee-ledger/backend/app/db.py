import asyncio
from collections.abc import Awaitable, Callable

import psycopg
from fastapi import Request
from psycopg.rows import dict_row
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import db_connect_kwargs


def connect() -> psycopg.Connection:
    return psycopg.connect(**db_connect_kwargs(), row_factory=dict_row)


def get_db(request: Request) -> psycopg.Connection:
    return request.state.db


class DbSessionMiddleware(BaseHTTPMiddleware):
    """要求ごとに接続を開き、成功ならコミット、失敗ならロールバックする。"""

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
