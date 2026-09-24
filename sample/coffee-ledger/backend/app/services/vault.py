from datetime import date
from typing import Any

import psycopg

from app.errors import conflict, validation_error
from app.services import balances, operations
from app.timeutil import now_jst, to_iso


def _serialize(row: dict[str, Any]) -> dict[str, Any]:
    reason_date = row["reason_date"]
    return {
        "id": row["id"],
        "reason": row["reason"],
        "direction": row["direction"],
        "amount": int(row["amount"]),
        "reason_date": reason_date.isoformat() if hasattr(reason_date, "isoformat") else str(reason_date),
        "entered_at": to_iso(row["entered_at"]),
    }


def list_vault_operations(conn: psycopg.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, reason, direction, amount, reason_date, entered_at
        FROM coffee_ledger.vault_operations
        ORDER BY entered_at DESC, id DESC
        """
    ).fetchall()
    return [_serialize(row) for row in rows]


def create_vault_operation(
    conn: psycopg.Connection,
    reason: str | None,
    direction: str | None,
    amount: int | None,
    reason_date: date | None,
) -> dict[str, Any]:
    if reason is None or not isinstance(reason, str):
        raise validation_error()
    trimmed = reason.strip()
    if trimmed == "" or len(trimmed) > 200:
        raise validation_error()
    if direction not in ("deposit", "withdrawal"):
        raise validation_error()
    if not isinstance(amount, int) or isinstance(amount, bool) or amount < 1:
        raise validation_error()
    if reason_date is None or not isinstance(reason_date, date):
        raise validation_error()

    balances.lock_vault_cash(conn)
    current_vault = balances.vault_amount(conn)
    if direction == "withdrawal" and amount > current_vault:
        raise conflict(
            "VAULT_AMOUNT_EXCEEDED",
            "出金額が金庫金額を超えています。",
        )
    row = conn.execute(
        """
        INSERT INTO coffee_ledger.vault_operations
            (reason, direction, amount, reason_date, entered_at)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, reason, direction, amount, reason_date, entered_at
        """,
        (trimmed, direction, amount, reason_date, now_jst()),
    ).fetchone()
    if row is None:
        raise RuntimeError("金庫操作の記録に失敗しました。")
    operations.add_operation_log(
        conn,
        "vault_operated",
        {
            "vault_operation_id": row["id"],
            "direction": row["direction"],
            "amount": row["amount"],
            "reason": row["reason"],
            "reason_date": row["reason_date"].isoformat(),
        },
    )
    return _serialize(row)
