from typing import Any

import psycopg
from psycopg.errors import UniqueViolation

from app.errors import conflict, not_found, validation_error
from app.services import balances, operations
from app.timeutil import now_jst, to_iso


def _last_drink_from_row(row: dict[str, Any]) -> dict[str, Any] | None:
    drink_id = row.get("last_drink_id")
    if drink_id is None:
        return None
    return {
        "id": drink_id,
        "recorded_at": to_iso(row.get("last_drink_recorded_at")),
        "cancelled": row.get("last_drink_cancelled_at") is not None,
    }


def _serialize_person(
    row: dict[str, Any],
    *,
    unpaid: int,
    last_drink: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "display_order": row["display_order"],
        "deactivated": row["deactivated_at"] is not None,
        "deactivated_at": to_iso(row["deactivated_at"]),
        "unpaid_amount": unpaid,
        "last_drink": last_drink,
    }


_PERSON_LIST_SQL = """
SELECT
    p.id,
    p.name,
    p.display_order,
    p.deactivated_at,
    GREATEST(
        COALESCE((
            SELECT SUM(d.unit_price)
            FROM coffee_ledger.drinks d
            WHERE d.person_id = p.id AND d.cancelled_at IS NULL
        ), 0)
        -
        COALESCE((
            SELECT SUM(pay.amount)
            FROM coffee_ledger.payments pay
            WHERE pay.person_id = p.id AND pay.cancelled_at IS NULL
        ), 0)
        +
        COALESCE((
            SELECT SUM(ua.new_amount - ua.previous_amount)
            FROM coffee_ledger.unpaid_adjustments ua
            WHERE ua.person_id = p.id
        ), 0),
        0
    ) AS unpaid_amount,
    ld.id AS last_drink_id,
    ld.recorded_at AS last_drink_recorded_at,
    ld.cancelled_at AS last_drink_cancelled_at
FROM coffee_ledger.people p
LEFT JOIN LATERAL (
    SELECT id, recorded_at, cancelled_at
    FROM coffee_ledger.drinks
    WHERE person_id = p.id
    ORDER BY recorded_at DESC, id DESC
    LIMIT 1
) ld ON TRUE
"""


def list_people(conn: psycopg.Connection, scope: str) -> list[dict[str, Any]]:
    if scope not in ("active", "all"):
        raise validation_error()
    sql = _PERSON_LIST_SQL
    if scope == "active":
        sql += " WHERE p.deactivated_at IS NULL"
    sql += " ORDER BY p.display_order ASC"
    rows = conn.execute(sql).fetchall()
    return [
        _serialize_person(
            row,
            unpaid=int(row["unpaid_amount"]),
            last_drink=_last_drink_from_row(row),
        )
        for row in rows
    ]


def get_person_row(
    conn: psycopg.Connection, person_id: int, *, for_update: bool = False
) -> dict[str, Any]:
    sql = """
        SELECT id, name, display_order, deactivated_at
        FROM coffee_ledger.people
        WHERE id = %s
    """
    if for_update:
        sql += " FOR UPDATE"
    row = conn.execute(sql, (person_id,)).fetchone()
    if row is None:
        raise not_found()
    return row


def _fetch_last_drink(
    conn: psycopg.Connection, person_id: int
) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT id, recorded_at, cancelled_at
        FROM coffee_ledger.drinks
        WHERE person_id = %s
        ORDER BY recorded_at DESC, id DESC
        LIMIT 1
        """,
        (person_id,),
    ).fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "recorded_at": to_iso(row["recorded_at"]),
        "cancelled": row["cancelled_at"] is not None,
    }


def get_person(conn: psycopg.Connection, person_id: int) -> dict[str, Any]:
    row = get_person_row(conn, person_id)
    return _serialize_person(
        row,
        unpaid=balances.unpaid_amount(conn, person_id),
        last_drink=_fetch_last_drink(conn, person_id),
    )


def register_person(conn: psycopg.Connection, name: str | None) -> dict[str, Any]:
    if name is None or not isinstance(name, str):
        raise validation_error()
    trimmed = name.strip()
    if trimmed == "" or len(trimmed) > 100:
        raise validation_error()
    conn.execute("LOCK TABLE coffee_ledger.people IN EXCLUSIVE MODE")
    existing = conn.execute(
        "SELECT 1 FROM coffee_ledger.people WHERE name = %s",
        (trimmed,),
    ).fetchone()
    if existing is not None:
        raise conflict("NAME_DUPLICATE", "同じ名前の人が既に登録されています。")
    next_order = conn.execute(
        "SELECT COALESCE(MAX(display_order), 0) + 1 AS next_order FROM coffee_ledger.people"
    ).fetchone()
    display_order = int(next_order["next_order"]) if next_order else 1
    try:
        row = conn.execute(
            """
            INSERT INTO coffee_ledger.people (name, display_order)
            VALUES (%s, %s)
            RETURNING id, name, display_order, deactivated_at
            """,
            (trimmed, display_order),
        ).fetchone()
    except UniqueViolation as exc:
        raise conflict("NAME_DUPLICATE", "同じ名前の人が既に登録されています。") from exc
    if row is None:
        raise RuntimeError("人の登録に失敗しました。")
    operations.add_operation_log(
        conn,
        "person_registered",
        {"person_id": row["id"], "name": row["name"]},
    )
    return _serialize_person(row, unpaid=0, last_drink=None)


def deactivate_person(conn: psycopg.Connection, person_id: int) -> dict[str, Any]:
    row = get_person_row(conn, person_id, for_update=True)
    if row["deactivated_at"] is not None:
        raise conflict("ALREADY_DEACTIVATED", "既に利用停止しています。")
    updated = conn.execute(
        """
        UPDATE coffee_ledger.people
        SET deactivated_at = %s
        WHERE id = %s
        RETURNING id, name, display_order, deactivated_at
        """,
        (now_jst(), person_id),
    ).fetchone()
    if updated is None:
        raise not_found()
    operations.add_operation_log(
        conn,
        "person_deactivated",
        {"person_id": updated["id"], "name": updated["name"]},
    )
    return get_person(conn, person_id)


def update_display_order(
    conn: psycopg.Connection, person_ids: list[int]
) -> list[dict[str, Any]]:
    if not person_ids:
        raise validation_error()
    if len(person_ids) != len(set(person_ids)):
        raise validation_error()
    conn.execute("LOCK TABLE coffee_ledger.people IN EXCLUSIVE MODE")
    existing = conn.execute("SELECT id FROM coffee_ledger.people").fetchall()
    existing_ids = {row["id"] for row in existing}
    if existing_ids != set(person_ids):
        raise conflict(
            "DISPLAY_ORDER_MISMATCH",
            "表示順の対象が登録済みの人と一致しません。",
        )
    max_row = conn.execute(
        "SELECT COALESCE(MAX(display_order), 0) AS max_order FROM coffee_ledger.people"
    ).fetchone()
    offset = int(max_row["max_order"]) if max_row else 0
    conn.execute(
        "UPDATE coffee_ledger.people SET display_order = display_order + %s",
        (offset + 1,),
    )
    for index, person_id in enumerate(person_ids, start=1):
        conn.execute(
            "UPDATE coffee_ledger.people SET display_order = %s WHERE id = %s",
            (index, person_id),
        )
    operations.add_operation_log(
        conn,
        "display_order_changed",
        {"person_ids": person_ids},
    )
    return list_people(conn, "all")
