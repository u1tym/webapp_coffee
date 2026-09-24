from typing import Any

import psycopg

from app.errors import conflict, not_found, validation_error
from app.logging_setup import get_logger
from app.services import balances, operations, people
from app.timeutil import now_jst, to_iso

log = get_logger()


def _serialize_payment(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "person_id": row["person_id"],
        "amount": row["amount"],
        "recorded_at": to_iso(row["recorded_at"]),
        "cancelled": row["cancelled_at"] is not None,
        "cancelled_at": to_iso(row["cancelled_at"]),
    }


def list_payments(conn: psycopg.Connection, person_id: int) -> list[dict[str, Any]]:
    people.get_person_row(conn, person_id)
    rows = conn.execute(
        """
        SELECT id, person_id, amount, recorded_at, cancelled_at
        FROM coffee_ledger.payments
        WHERE person_id = %s
        ORDER BY recorded_at DESC, id DESC
        """,
        (person_id,),
    ).fetchall()
    return [_serialize_payment(row) for row in rows]


def record_payment(
    conn: psycopg.Connection, person_id: int, amount: int
) -> dict[str, Any]:
    log.info("支払要求 person_id=%s amount=%s", person_id, amount)
    if not isinstance(amount, int) or isinstance(amount, bool) or amount < 1:
        raise validation_error()
    person = people.get_person_row(conn, person_id, for_update=True)
    unpaid = balances.unpaid_amount(conn, person_id)
    if unpaid == 0 or amount > unpaid:
        log.info("支払判定 person_id=%s amount=%s unpaid=%s", person_id, amount, unpaid)
        raise conflict(
            "PAYMENT_EXCEEDS_UNPAID",
            "支払額が未払い代金を超えています。",
        )
    row = conn.execute(
        """
        INSERT INTO coffee_ledger.payments (person_id, amount, recorded_at)
        VALUES (%s, %s, %s)
        RETURNING id, person_id, amount, recorded_at, cancelled_at
        """,
        (person_id, amount, now_jst()),
    ).fetchone()
    if row is None:
        raise RuntimeError("支払の記録に失敗しました。")
    operations.add_operation_log(
        conn,
        "payment_recorded",
        {
            "person_id": person_id,
            "name": person["name"],
            "payment_id": row["id"],
            "amount": row["amount"],
        },
    )
    log.info("支払記録成功 person_id=%s payment_id=%s amount=%s unpaid_before=%s", person_id, row["id"], amount, unpaid)
    return _serialize_payment(row)


def cancel_payment(
    conn: psycopg.Connection, person_id: int, payment_id: int
) -> dict[str, Any]:
    log.info("支払取消要求 person_id=%s payment_id=%s", person_id, payment_id)
    person = people.get_person_row(conn, person_id, for_update=True)
    row = conn.execute(
        """
        SELECT id, person_id, amount, recorded_at, cancelled_at
        FROM coffee_ledger.payments
        WHERE id = %s
        FOR UPDATE
        """,
        (payment_id,),
    ).fetchone()
    if row is None or row["person_id"] != person_id:
        raise not_found()
    if row["cancelled_at"] is not None:
        raise conflict("ALREADY_CANCELLED", "既に取り消されています。")
    updated = conn.execute(
        """
        UPDATE coffee_ledger.payments
        SET cancelled_at = %s
        WHERE id = %s
        RETURNING id, person_id, amount, recorded_at, cancelled_at
        """,
        (now_jst(), payment_id),
    ).fetchone()
    if updated is None:
        raise not_found()
    operations.add_operation_log(
        conn,
        "payment_cancelled",
        {
            "person_id": person_id,
            "name": person["name"],
            "payment_id": updated["id"],
            "amount": updated["amount"],
        },
    )
    log.info("支払取消成功 person_id=%s payment_id=%s amount=%s", person_id, payment_id, updated["amount"])
    return _serialize_payment(updated)
