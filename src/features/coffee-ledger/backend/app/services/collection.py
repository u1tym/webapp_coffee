from typing import Any

import psycopg

from app.errors import conflict
from app.logging_setup import get_logger
from app.services import balances, operations
from app.timeutil import now_jst, to_iso

log = get_logger()


def get_collection(conn: psycopg.Connection) -> dict[str, int]:
    return {
        "collected_amount": balances.collected_amount(conn),
        "uncollected_amount": balances.uncollected_amount(conn),
        "vault_amount": balances.vault_amount(conn),
    }


def list_safe_deposits(conn: psycopg.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, amount, deposited_at
        FROM coffee_ledger.safe_deposits
        ORDER BY deposited_at DESC, id DESC
        """
    ).fetchall()
    return [
        {
            "id": row["id"],
            "amount": row["amount"],
            "deposited_at": to_iso(row["deposited_at"]),
        }
        for row in rows
    ]


def create_safe_deposit(conn: psycopg.Connection) -> dict[str, Any]:
    log.info("金庫収納要求")
    balances.lock_vault_cash(conn)
    collected = balances.collected_amount(conn)
    log.info("金庫収納判定 collected_amount=%s", collected)
    if collected == 0:
        raise conflict("COLLECTED_AMOUNT_ZERO", "徴収済み金額が 0 のため金庫収納できません。")
    row = conn.execute(
        """
        INSERT INTO coffee_ledger.safe_deposits (amount, deposited_at)
        VALUES (%s, %s)
        RETURNING id, amount, deposited_at
        """,
        (collected, now_jst()),
    ).fetchone()
    if row is None:
        raise RuntimeError("金庫収納の記録に失敗しました。")
    operations.add_operation_log(
        conn,
        "safe_deposited",
        {"safe_deposit_id": row["id"], "amount": row["amount"]},
    )
    log.info("金庫収納成功 safe_deposit_id=%s amount=%s", row["id"], row["amount"])
    return {
        "id": row["id"],
        "amount": row["amount"],
        "deposited_at": to_iso(row["deposited_at"]),
    }
