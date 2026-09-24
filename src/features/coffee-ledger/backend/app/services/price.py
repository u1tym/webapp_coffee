from typing import Any

import psycopg

from app.errors import validation_error
from app.logging_setup import get_logger
from app.services import operations
from app.timeutil import now_jst, to_iso

log = get_logger()


def get_cup_price(conn: psycopg.Connection) -> dict[str, Any]:
    row = conn.execute(
        "SELECT amount, updated_at FROM coffee_ledger.cup_price WHERE id = 1"
    ).fetchone()
    if row is None:
        return {"amount": None, "updated_at": None}
    return {"amount": row["amount"], "updated_at": to_iso(row["updated_at"])}


def set_cup_price(conn: psycopg.Connection, amount: int) -> dict[str, Any]:
    log.info("一杯単価保存要求 amount=%s", amount)
    if not isinstance(amount, int) or isinstance(amount, bool) or amount < 1:
        raise validation_error()
    existing = conn.execute(
        "SELECT amount FROM coffee_ledger.cup_price WHERE id = 1 FOR UPDATE"
    ).fetchone()
    now = now_jst()
    if existing is None:
        conn.execute(
            """
            INSERT INTO coffee_ledger.cup_price (id, amount, updated_at)
            VALUES (1, %s, %s)
            """,
            (amount, now),
        )
        operations.add_operation_log(conn, "cup_price_registered", {"amount": amount})
        log.info("一杯単価登録成功 amount=%s", amount)
    else:
        previous = int(existing["amount"])
        conn.execute(
            """
            UPDATE coffee_ledger.cup_price
            SET amount = %s, updated_at = %s
            WHERE id = 1
            """,
            (amount, now),
        )
        operations.add_operation_log(
            conn,
            "cup_price_updated",
            {"amount": amount, "previous_amount": previous},
        )
        log.info("一杯単価変更成功 previous_amount=%s amount=%s", previous, amount)
    return get_cup_price(conn)
