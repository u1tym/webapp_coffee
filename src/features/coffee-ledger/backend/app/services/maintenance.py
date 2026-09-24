import time
from typing import Any

from app.db import connect_autocommit
from app.errors import conflict
from app.logging_setup import get_logger

log = get_logger()

TABLES = [
    "people",
    "cup_price",
    "drinks",
    "payments",
    "unpaid_adjustments",
    "safe_deposits",
    "vault_operations",
    "operation_logs",
]

_LOCK_KEY = "coffee_ledger.maintenance_vacuum"


def vacuum() -> dict[str, Any]:
    """台帳の全テーブルに VACUUM (ANALYZE) を実行する。VACUUM はトランザクション外でしか動かない。"""
    log.info("DB整理要求 tables=%s", ",".join(TABLES))
    with connect_autocommit() as conn:
        row = conn.execute(
            "SELECT pg_try_advisory_lock(hashtext(%s)) AS locked", (_LOCK_KEY,)
        ).fetchone()
        if row is None or not row["locked"]:
            raise conflict(
                "VACUUM_IN_PROGRESS",
                "DB の整理を実行中です。しばらくしてからやり直してください。",
            )
        try:
            started = time.monotonic()
            conn.execute(
                "VACUUM (ANALYZE) "
                + ", ".join(f"coffee_ledger.{table}" for table in TABLES)
            )
            elapsed = round(time.monotonic() - started, 1)
        finally:
            conn.execute("SELECT pg_advisory_unlock(hashtext(%s))", (_LOCK_KEY,))
    log.info("DB整理成功 elapsed_seconds=%s", elapsed)
    return {"elapsed_seconds": elapsed}
