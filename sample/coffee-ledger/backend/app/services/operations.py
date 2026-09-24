from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from app.timeutil import now_jst, to_iso


def add_operation_log(
    conn: psycopg.Connection,
    operation_type: str,
    payload: dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO coffee_ledger.operation_logs (occurred_at, operation_type, payload)
        VALUES (%s, %s, %s)
        """,
        (now_jst(), operation_type, Jsonb(payload)),
    )


def list_operation_logs(conn: psycopg.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, occurred_at, operation_type, payload
        FROM coffee_ledger.operation_logs
        ORDER BY occurred_at DESC, id DESC
        """
    ).fetchall()
    return [
        {
            "id": row["id"],
            "occurred_at": to_iso(row["occurred_at"]),
            "operation_type": row["operation_type"],
            "payload": row["payload"],
        }
        for row in rows
    ]
