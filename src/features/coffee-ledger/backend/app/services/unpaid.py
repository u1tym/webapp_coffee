from typing import Any

import psycopg

from app.errors import conflict, validation_error
from app.logging_setup import get_logger
from app.services import balances, operations, people
from app.timeutil import now_jst, to_iso

log = get_logger()


def _serialize(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "person_id": row["person_id"],
        "previous_amount": int(row["previous_amount"]),
        "new_amount": int(row["new_amount"]),
        "reason": row["reason"],
        "occurred_at": to_iso(row["occurred_at"]),
    }


def create_unpaid_adjustment(
    conn: psycopg.Connection,
    person_id: int,
    new_amount: int | None,
    reason: str | None,
) -> dict[str, Any]:
    log.info("未払い修正要求 person_id=%s new_amount=%s reason=%s", person_id, new_amount, reason)
    if not isinstance(new_amount, int) or isinstance(new_amount, bool) or new_amount < 0:
        raise validation_error()
    if reason is None or not isinstance(reason, str):
        raise validation_error()
    trimmed = reason.strip()
    if trimmed == "" or len(trimmed) > 200:
        raise validation_error()

    person = people.get_person_row(conn, person_id, for_update=True)
    previous_amount = balances.unpaid_amount(conn, person_id)
    if new_amount == previous_amount:
        log.info("未払い修正判定 person_id=%s current=%s new_amount=%s", person_id, previous_amount, new_amount)
        raise conflict(
            "UNPAID_AMOUNT_UNCHANGED",
            "現在の未払い代金と同じ額には修正できません。",
        )
    row = conn.execute(
        """
        INSERT INTO coffee_ledger.unpaid_adjustments
            (person_id, previous_amount, new_amount, reason, occurred_at)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, person_id, previous_amount, new_amount, reason, occurred_at
        """,
        (person_id, previous_amount, new_amount, trimmed, now_jst()),
    ).fetchone()
    if row is None:
        raise RuntimeError("未払い修正の記録に失敗しました。")
    operations.add_operation_log(
        conn,
        "unpaid_adjusted",
        {
            "unpaid_adjustment_id": row["id"],
            "person_id": person_id,
            "name": person["name"],
            "previous_amount": int(row["previous_amount"]),
            "new_amount": int(row["new_amount"]),
            "reason": row["reason"],
        },
    )
    log.info("未払い修正成功 person_id=%s previous_amount=%s new_amount=%s", person_id, previous_amount, new_amount)
    return _serialize(row)
