from datetime import date
from typing import Any

import psycopg

from app.errors import conflict, validation_error
from app.logging_setup import get_logger
from app.services import balances, operations
from app.timeutil import now_jst, to_iso

log = get_logger()


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


def create_vault_operation(
    conn: psycopg.Connection,
    reason: str | None,
    direction: str | None,
    amount: int | None,
    reason_date: date | None,
) -> dict[str, Any]:
    log.info(
        "金庫操作要求 direction=%s amount=%s reason_date=%s reason=%s",
        direction, amount, reason_date, reason,
    )
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
    log.info("金庫操作判定 direction=%s amount=%s vault_amount=%s", direction, amount, current_vault)
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
    log.info("金庫操作成功 vault_operation_id=%s direction=%s amount=%s", row["id"], row["direction"], row["amount"])
    return _serialize(row)
