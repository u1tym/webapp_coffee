from datetime import datetime
from typing import Any

import psycopg

from app.services import balances
from app.timeutil import to_iso


def _entry(
    *,
    occurred_at: datetime,
    event_type: str,
    amount: int | None,
    person_id: int | None = None,
    name: str | None = None,
    direction: str | None = None,
    reason: str | None = None,
    reason_date: str | None = None,
    previous_amount: int | None = None,
    new_amount: int | None = None,
    sort_id: int,
) -> dict[str, Any]:
    return {
        "occurred_at": occurred_at,
        "event_type": event_type,
        "person_id": person_id,
        "name": name,
        "amount": amount,
        "direction": direction,
        "reason": reason,
        "reason_date": reason_date,
        "previous_amount": previous_amount,
        "new_amount": new_amount,
        "sort_id": sort_id,
    }


def _collect_events(conn: psycopg.Connection) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    drinks = conn.execute(
        """
        SELECT d.id, d.person_id, p.name, d.unit_price, d.recorded_at, d.cancelled_at
        FROM coffee_ledger.drinks d
        JOIN coffee_ledger.people p ON p.id = d.person_id
        """
    ).fetchall()
    for row in drinks:
        events.append(
            _entry(
                occurred_at=row["recorded_at"],
                event_type="drink_recorded",
                amount=int(row["unit_price"]),
                person_id=row["person_id"],
                name=row["name"],
                sort_id=row["id"],
            )
        )
        if row["cancelled_at"] is not None:
            events.append(
                _entry(
                    occurred_at=row["cancelled_at"],
                    event_type="drink_cancelled",
                    amount=int(row["unit_price"]),
                    person_id=row["person_id"],
                    name=row["name"],
                    sort_id=row["id"],
                )
            )
    payments = conn.execute(
        """
        SELECT pay.id, pay.person_id, p.name, pay.amount, pay.recorded_at, pay.cancelled_at
        FROM coffee_ledger.payments pay
        JOIN coffee_ledger.people p ON p.id = pay.person_id
        """
    ).fetchall()
    for row in payments:
        events.append(
            _entry(
                occurred_at=row["recorded_at"],
                event_type="payment_recorded",
                amount=int(row["amount"]),
                person_id=row["person_id"],
                name=row["name"],
                sort_id=row["id"],
            )
        )
        if row["cancelled_at"] is not None:
            events.append(
                {
                    **_entry(
                        occurred_at=row["cancelled_at"],
                        event_type="payment_cancelled",
                        amount=int(row["amount"]),
                        person_id=row["person_id"],
                        name=row["name"],
                        sort_id=row["id"],
                    ),
                    "payment_recorded_at": row["recorded_at"],
                }
            )
    deposits = conn.execute(
        """
        SELECT id, amount, deposited_at
        FROM coffee_ledger.safe_deposits
        """
    ).fetchall()
    for row in deposits:
        events.append(
            _entry(
                occurred_at=row["deposited_at"],
                event_type="safe_deposited",
                amount=int(row["amount"]),
                sort_id=row["id"],
            )
        )
    ops = conn.execute(
        """
        SELECT id, reason, direction, amount, reason_date, entered_at
        FROM coffee_ledger.vault_operations
        """
    ).fetchall()
    for row in ops:
        reason_date = row["reason_date"]
        events.append(
            _entry(
                occurred_at=row["entered_at"],
                event_type="vault_operated",
                amount=int(row["amount"]),
                direction=row["direction"],
                reason=row["reason"],
                reason_date=(
                    reason_date.isoformat()
                    if hasattr(reason_date, "isoformat")
                    else str(reason_date)
                ),
                sort_id=row["id"],
            )
        )
    adjustments = conn.execute(
        """
        SELECT ua.id, ua.person_id, p.name, ua.previous_amount, ua.new_amount,
               ua.reason, ua.occurred_at
        FROM coffee_ledger.unpaid_adjustments ua
        JOIN coffee_ledger.people p ON p.id = ua.person_id
        """
    ).fetchall()
    for row in adjustments:
        events.append(
            _entry(
                occurred_at=row["occurred_at"],
                event_type="unpaid_adjusted",
                amount=None,
                person_id=row["person_id"],
                name=row["name"],
                reason=row["reason"],
                previous_amount=int(row["previous_amount"]),
                new_amount=int(row["new_amount"]),
                sort_id=row["id"],
            )
        )
    events.sort(key=lambda item: (item["occurred_at"], item["event_type"], item["sort_id"]))
    return events


def get_summary(conn: psycopg.Connection) -> dict[str, Any]:
    events = _collect_events(conn)
    uncollected = 0
    collected = 0
    vault = 0
    last_deposit_at: datetime | None = None
    rows: list[dict[str, Any]] = []
    for event in events:
        event_type = event["event_type"]
        amount = event["amount"]
        if event_type == "drink_recorded":
            uncollected += amount
        elif event_type == "drink_cancelled":
            uncollected -= amount
        elif event_type == "payment_recorded":
            uncollected -= amount
            collected += amount
        elif event_type == "payment_cancelled":
            uncollected += amount
            recorded_at = event["payment_recorded_at"]
            if last_deposit_at is None or recorded_at > last_deposit_at:
                collected -= amount
        elif event_type == "safe_deposited":
            vault += amount
            collected = 0
            last_deposit_at = event["occurred_at"]
        elif event_type == "vault_operated":
            if event["direction"] == "deposit":
                vault += amount
            else:
                vault -= amount
        elif event_type == "unpaid_adjusted":
            uncollected += int(event["new_amount"]) - int(event["previous_amount"])
        if uncollected < 0:
            uncollected = 0
        if collected < 0:
            collected = 0
        if vault < 0:
            vault = 0
        rows.append(
            {
                "occurred_at": to_iso(event["occurred_at"]),
                "event_type": event_type,
                "person_id": event["person_id"],
                "name": event["name"],
                "amount": amount,
                "direction": event["direction"],
                "reason": event["reason"],
                "reason_date": event["reason_date"],
                "previous_amount": event.get("previous_amount"),
                "new_amount": event.get("new_amount"),
                "uncollected_amount": uncollected,
                "collected_amount": collected,
                "vault_amount": vault,
            }
        )
    rows.reverse()
    return {
        "uncollected_amount": balances.uncollected_amount(conn),
        "collected_amount": balances.collected_amount(conn),
        "vault_amount": balances.vault_amount(conn),
        "entries": rows,
    }
