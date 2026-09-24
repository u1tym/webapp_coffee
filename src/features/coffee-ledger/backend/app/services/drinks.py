from typing import Any

import psycopg

from app.errors import conflict, not_found
from app.logging_setup import get_logger
from app.services import balances, operations, people, price
from app.timeutil import now_jst, to_iso

log = get_logger()


def _serialize_drink(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "person_id": row["person_id"],
        "unit_price": row["unit_price"],
        "recorded_at": to_iso(row["recorded_at"]),
        "cancelled": row["cancelled_at"] is not None,
        "cancelled_at": to_iso(row["cancelled_at"]),
    }


def list_drinks(conn: psycopg.Connection, person_id: int) -> list[dict[str, Any]]:
    people.get_person_row(conn, person_id)
    rows = conn.execute(
        """
        SELECT id, person_id, unit_price, recorded_at, cancelled_at
        FROM coffee_ledger.drinks
        WHERE person_id = %s
        ORDER BY recorded_at DESC, id DESC
        """,
        (person_id,),
    ).fetchall()
    return [_serialize_drink(row) for row in rows]


def record_drink(conn: psycopg.Connection, person_id: int) -> dict[str, Any]:
    log.info("飲用記録要求 person_id=%s", person_id)
    person = people.get_person_row(conn, person_id, for_update=True)
    if person["deactivated_at"] is not None:
        raise conflict("PERSON_DEACTIVATED", "利用停止した人には飲用を記録できません。")
    current = price.get_cup_price(conn)
    if current["amount"] is None:
        raise conflict("CUP_PRICE_MISSING", "一杯単価が未登録です。")
    row = conn.execute(
        """
        INSERT INTO coffee_ledger.drinks (person_id, unit_price, recorded_at)
        VALUES (%s, %s, %s)
        RETURNING id, person_id, unit_price, recorded_at, cancelled_at
        """,
        (person_id, current["amount"], now_jst()),
    ).fetchone()
    if row is None:
        raise RuntimeError("飲用の記録に失敗しました。")
    operations.add_operation_log(
        conn,
        "drink_recorded",
        {
            "person_id": person_id,
            "name": person["name"],
            "drink_id": row["id"],
            "unit_price": row["unit_price"],
        },
    )
    log.info("飲用記録成功 person_id=%s drink_id=%s unit_price=%s", person_id, row["id"], row["unit_price"])
    return _serialize_drink(row)


def cancel_drink(
    conn: psycopg.Connection, person_id: int, drink_id: int
) -> dict[str, Any]:
    log.info("飲用取消要求 person_id=%s drink_id=%s", person_id, drink_id)
    person = people.get_person_row(conn, person_id, for_update=True)
    row = conn.execute(
        """
        SELECT id, person_id, unit_price, recorded_at, cancelled_at
        FROM coffee_ledger.drinks
        WHERE id = %s
        FOR UPDATE
        """,
        (drink_id,),
    ).fetchone()
    if row is None or row["person_id"] != person_id:
        raise not_found()
    if row["cancelled_at"] is not None:
        raise conflict("ALREADY_CANCELLED", "既に取り消されています。")
    unpaid = balances.unpaid_amount(conn, person_id)
    if unpaid - int(row["unit_price"]) < 0:
        raise conflict(
            "DRINK_CANCEL_WOULD_OVERPAY",
            "この飲用を取り消すと支払合計が飲用代金を超えます。",
        )
    updated = conn.execute(
        """
        UPDATE coffee_ledger.drinks
        SET cancelled_at = %s
        WHERE id = %s
        RETURNING id, person_id, unit_price, recorded_at, cancelled_at
        """,
        (now_jst(), drink_id),
    ).fetchone()
    if updated is None:
        raise not_found()
    operations.add_operation_log(
        conn,
        "drink_cancelled",
        {
            "person_id": person_id,
            "name": person["name"],
            "drink_id": updated["id"],
            "unit_price": updated["unit_price"],
        },
    )
    log.info("飲用取消成功 person_id=%s drink_id=%s unpaid_before=%s", person_id, drink_id, unpaid)
    return _serialize_drink(updated)
