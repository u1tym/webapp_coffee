"""テストの土台。

開発用 DB に接続し、テストごとにテーブルを空にしてから実行し、最後にロールバックする。
テストの後に開発用 DB のデータは変わらない（実行中は対象テーブルがロックされる）。
"""

import logging
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.config import db_connect_kwargs  # noqa: E402
from app.logging_setup import LOGGER_NAME  # noqa: E402

# テストのログを開発用のログファイルへ出さない（setup_logging はハンドラがあれば何もしない）
logging.getLogger(LOGGER_NAME).addHandler(logging.NullHandler())

TABLES = [
    "operation_logs",
    "unpaid_adjustments",
    "payments",
    "drinks",
    "safe_deposits",
    "vault_operations",
    "cup_price",
    "people",
]


@pytest.fixture
def conn() -> Iterator[psycopg.Connection]:
    connection = psycopg.connect(**db_connect_kwargs(), row_factory=dict_row)
    try:
        connection.execute(
            "TRUNCATE "
            + ", ".join(f"coffee_ledger.{name}" for name in TABLES)
            + " RESTART IDENTITY CASCADE"
        )
        yield connection
    finally:
        connection.rollback()
        connection.close()


class _SavepointConnection:
    """1 要求分のコミット／ロールバックを、テストのトランザクション内のセーブポイントに置き換える。"""

    def __init__(self, connection: psycopg.Connection) -> None:
        self._connection = connection
        connection.execute("SAVEPOINT api_request")

    def __getattr__(self, name: str) -> Any:
        return getattr(self._connection, name)

    def commit(self) -> None:
        self._connection.execute("RELEASE SAVEPOINT api_request")

    def rollback(self) -> None:
        self._connection.execute("ROLLBACK TO SAVEPOINT api_request")
        self._connection.execute("RELEASE SAVEPOINT api_request")

    def close(self) -> None:
        pass


@pytest.fixture
def client(conn: psycopg.Connection, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    import app.db
    from app.main import app as fastapi_app

    monkeypatch.setattr(app.db, "connect", lambda: _SavepointConnection(conn))
    with TestClient(fastapi_app, raise_server_exceptions=False) as test_client:
        yield test_client
