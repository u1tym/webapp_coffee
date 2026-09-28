"""直近 1 か月分の CSV 出力（REQ-025）。"""

import csv
import io
import re
from datetime import datetime

import psycopg
from fastapi.testclient import TestClient

from app.services import drinks, people, price, summary_csv
from app.services.summary_csv import HEADER
from app.timeutil import JST, months_before, now_jst


def _parse(body: bytes) -> list[list[str]]:
    assert body.startswith(b"\xef\xbb\xbf")
    text = body.decode("utf-8-sig")
    return list(csv.reader(io.StringIO(text, newline="")))


def _backdate_drink(conn: psycopg.Connection, drink_id: int, recorded_at: datetime) -> None:
    conn.execute(
        "UPDATE coffee_ledger.drinks SET recorded_at = %s WHERE id = %s",
        (recorded_at, drink_id),
    )


# --- months_before ---


def test_months_before_same_day() -> None:
    value = datetime(2026, 9, 28, 10, 0, tzinfo=JST)
    assert months_before(value, 1) == datetime(2026, 8, 28, 10, 0, tzinfo=JST)


def test_months_before_year_rollover() -> None:
    value = datetime(2026, 1, 15, 9, 30, tzinfo=JST)
    assert months_before(value, 1) == datetime(2025, 12, 15, 9, 30, tzinfo=JST)


def test_months_before_clamps_to_shorter_month() -> None:
    value = datetime(2026, 3, 31, 12, 0, tzinfo=JST)
    assert months_before(value, 1) == datetime(2026, 2, 28, 12, 0, tzinfo=JST)


# --- CSV 出力（直近 1 か月）---


def test_csv_1month_excludes_older_events_but_keeps_running_totals(
    conn: psycopg.Connection,
) -> None:
    person_id = int(people.register_person(conn, "山田")["id"])
    price.set_cup_price(conn, 100)

    old_drink = drinks.record_drink(conn, person_id)
    _backdate_drink(conn, int(old_drink["id"]), months_before(now_jst(), 2))

    drinks.record_drink(conn, person_id)

    _, body_all = summary_csv.build_summary_csv(conn)
    assert len(_parse(body_all)) - 1 == 2

    _, body_1month = summary_csv.build_summary_csv(conn, "1month")
    rows = _parse(body_1month)
    assert rows[0] == HEADER
    data = rows[1:]
    assert len(data) == 1
    assert data[0][1] == "飲む"
    assert data[0][9:12] == ["200", "0", "0"]


def test_csv_1month_no_events_is_header_only(conn: psycopg.Connection) -> None:
    filename, body = summary_csv.build_summary_csv(conn, "1month")
    assert re.fullmatch(r"coffee-ledger-1month-\d{8}-\d{6}\.csv", filename)
    assert body == ("﻿" + ",".join(HEADER) + "\r\n").encode("utf-8")


def test_csv_range_query_1month(client: TestClient) -> None:
    response = client.get("/summary/csv?range=1month")
    assert response.status_code == 200
    assert re.fullmatch(
        r'attachment; filename="coffee-ledger-1month-\d{8}-\d{6}\.csv"',
        response.headers["content-disposition"],
    )


def test_csv_range_query_invalid(client: TestClient) -> None:
    response = client.get("/summary/csv?range=bogus")
    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "入力が正しくありません。",
        }
    }
