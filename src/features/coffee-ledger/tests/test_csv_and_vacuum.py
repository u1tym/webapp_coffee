"""金銭の動きの CSV 出力（REQ-023）と DB の整理（REQ-022）。"""

import csv
import io
import re
from collections.abc import Iterator
from datetime import date

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from app.config import db_connect_kwargs
from app.services import collection, drinks, payments, people, price, summary, summary_csv, unpaid, vault
from app.services.maintenance import TABLES
from app.services.summary_csv import HEADER


def _parse(body: bytes) -> list[list[str]]:
    assert body.startswith(b"\xef\xbb\xbf")
    text = body.decode("utf-8-sig")
    assert "\r\n" in text
    return list(csv.reader(io.StringIO(text, newline="")))


# --- CSV 出力 ---


def test_csv_header_only_without_events(conn: psycopg.Connection) -> None:
    filename, body = summary_csv.build_summary_csv(conn)
    assert re.fullmatch(r"coffee-ledger-\d{8}-\d{6}\.csv", filename)
    assert body == ("﻿" + ",".join(HEADER) + "\r\n").encode("utf-8")


def test_csv_rows_are_oldest_first_and_match_summary(conn: psycopg.Connection) -> None:
    person_id = int(people.register_person(conn, "山田")["id"])
    price.set_cup_price(conn, 100)
    drinks.record_drink(conn, person_id)
    payments.record_payment(conn, person_id, 100)
    collection.create_safe_deposit(conn)
    vault.create_vault_operation(conn, "豆の購入, 500g", "withdrawal", 60, date(2026, 9, 24))
    unpaid.create_unpaid_adjustment(conn, person_id, 20, '端数の "調整"\n2 行目')

    _, body = summary_csv.build_summary_csv(conn)
    rows = _parse(body)
    assert rows[0] == HEADER
    data = rows[1:]
    assert [r[1] for r in data] == ["飲む", "支払", "金庫収納", "金庫操作", "未払い修正"]
    assert all(re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", r[0]) for r in data)
    assert data[0][2:4] == ["山田", "100"]
    assert data[3][2:7] == ["", "60", "出金", "豆の購入, 500g", "2026-09-24"]
    assert data[4][3] == ""
    assert data[4][5] == '端数の "調整"\n2 行目'
    assert data[4][7:9] == ["0", "20"]

    entries = list(reversed(summary.get_summary(conn)["entries"]))
    assert [r[9:12] for r in data] == [
        [str(e["uncollected_amount"]), str(e["collected_amount"]), str(e["vault_amount"])]
        for e in entries
    ]
    assert [r[9:12] for r in data] == [
        ["100", "0", "0"],
        ["0", "100", "0"],
        ["0", "0", "100"],
        ["0", "0", "40"],
        ["20", "0", "40"],
    ]


def test_csv_api_headers(client: TestClient) -> None:
    response = client.get("/summary/csv", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert re.fullmatch(
        r'attachment; filename="coffee-ledger-\d{8}-\d{6}\.csv"',
        response.headers["content-disposition"],
    )
    assert response.headers["cache-control"] == "no-store"
    assert "content-disposition" in response.headers["access-control-expose-headers"].lower()
    assert _parse(response.content) == [HEADER]


def test_csv_is_not_recorded_in_operation_logs(client: TestClient, conn: psycopg.Connection) -> None:
    client.get("/summary/csv")
    row = conn.execute("SELECT count(*) AS n FROM coffee_ledger.operation_logs").fetchone()
    assert row is not None and row["n"] == 0


# --- DB の整理 ---
# VACUUM は別の接続・トランザクション外で動くため、テーブルを TRUNCATE してロックする conn フィクスチャとは併用しない。


@pytest.fixture
def plain_client() -> Iterator[TestClient]:
    from app.main import app as fastapi_app

    with TestClient(fastapi_app, raise_server_exceptions=False) as test_client:
        yield test_client


def _autocommit() -> psycopg.Connection:
    return psycopg.connect(**db_connect_kwargs(), row_factory=dict_row, autocommit=True)


def _snapshot(connection: psycopg.Connection) -> dict[str, int]:
    return {
        table: int(
            connection.execute(f"SELECT count(*) AS n FROM coffee_ledger.{table}").fetchone()["n"]
        )
        for table in TABLES
    }


def test_vacuum_updates_statistics_and_keeps_data(plain_client: TestClient) -> None:
    with _autocommit() as observer:
        before = _snapshot(observer)
        response = plain_client.post("/maintenance/vacuum")
        assert response.status_code == 200
        assert isinstance(response.json()["elapsed_seconds"], float)
        assert _snapshot(observer) == before
        stats = observer.execute(
            """
            SELECT relname, last_vacuum, last_analyze
            FROM pg_stat_user_tables
            WHERE schemaname = 'coffee_ledger'
            """
        ).fetchall()
    by_table = {s["relname"]: s for s in stats}
    assert set(by_table) == set(TABLES)
    assert all(s["last_vacuum"] is not None and s["last_analyze"] is not None for s in stats)


def test_vacuum_rejected_while_another_is_running(plain_client: TestClient) -> None:
    with _autocommit() as holder:
        holder.execute("SELECT pg_advisory_lock(hashtext('coffee_ledger.maintenance_vacuum'))")
        try:
            response = plain_client.post("/maintenance/vacuum")
        finally:
            holder.execute("SELECT pg_advisory_unlock(hashtext('coffee_ledger.maintenance_vacuum'))")
    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "VACUUM_IN_PROGRESS",
            "message": "DB の整理を実行中です。しばらくしてからやり直してください。",
        }
    }
    assert plain_client.post("/maintenance/vacuum").status_code == 200
