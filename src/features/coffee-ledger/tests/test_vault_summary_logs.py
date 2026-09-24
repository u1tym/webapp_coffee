"""金庫・集計・操作記録（REQ-009〜011、REQ-017、REQ-018、REQ-020）。"""

from datetime import date

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.errors import AppError
from app.services import collection, drinks, operations, payments, people, price, summary, unpaid, vault


def _setup_person_with_drinks(conn: psycopg.Connection, count: int, unit: int = 100) -> int:
    person_id = int(people.register_person(conn, "山田")["id"])
    price.set_cup_price(conn, unit)
    for _ in range(count):
        drinks.record_drink(conn, person_id)
    return person_id


# --- 徴収済み金額と金庫収納 ---


def test_collected_amount_resets_after_safe_deposit(conn: psycopg.Connection) -> None:
    person_id = _setup_person_with_drinks(conn, 3)
    payments.record_payment(conn, person_id, 100)
    payments.record_payment(conn, person_id, 50)
    assert collection.get_collection(conn) == {
        "collected_amount": 150,
        "uncollected_amount": 150,
        "vault_amount": 0,
    }
    deposit = collection.create_safe_deposit(conn)
    assert deposit["amount"] == 150
    assert collection.get_collection(conn)["collected_amount"] == 0
    assert collection.get_collection(conn)["vault_amount"] == 150
    payments.record_payment(conn, person_id, 30)
    assert collection.get_collection(conn)["collected_amount"] == 30
    assert [d["amount"] for d in collection.list_safe_deposits(conn)] == [150]


def test_safe_deposit_rejected_when_collected_is_zero(conn: psycopg.Connection) -> None:
    with pytest.raises(AppError) as excinfo:
        collection.create_safe_deposit(conn)
    assert excinfo.value.code == "COLLECTED_AMOUNT_ZERO"


def test_cancelling_deposited_payment_does_not_reduce_collected(conn: psycopg.Connection) -> None:
    person_id = _setup_person_with_drinks(conn, 3)
    old_payment = payments.record_payment(conn, person_id, 100)["id"]
    collection.create_safe_deposit(conn)
    new_payment = payments.record_payment(conn, person_id, 50)["id"]
    payments.cancel_payment(conn, person_id, old_payment)
    assert collection.get_collection(conn)["collected_amount"] == 50
    payments.cancel_payment(conn, person_id, new_payment)
    assert collection.get_collection(conn)["collected_amount"] == 0


# --- 金庫操作 ---


def test_vault_operations_change_vault_amount(conn: psycopg.Connection) -> None:
    vault.create_vault_operation(conn, "寄付", "deposit", 1000, date(2026, 9, 1))
    result = vault.create_vault_operation(conn, "  豆の購入 ", "withdrawal", 400, date(2026, 9, 2))
    assert result["reason"] == "豆の購入"
    assert result["reason_date"] == "2026-09-02"
    assert collection.get_collection(conn)["vault_amount"] == 600


def test_vault_withdrawal_cannot_exceed_vault_amount(conn: psycopg.Connection) -> None:
    vault.create_vault_operation(conn, "寄付", "deposit", 100, date(2026, 9, 1))
    with pytest.raises(AppError) as excinfo:
        vault.create_vault_operation(conn, "豆", "withdrawal", 101, date(2026, 9, 1))
    assert excinfo.value.code == "VAULT_AMOUNT_EXCEEDED"
    vault.create_vault_operation(conn, "豆", "withdrawal", 100, date(2026, 9, 1))
    assert collection.get_collection(conn)["vault_amount"] == 0


@pytest.mark.parametrize(
    ("reason", "direction", "amount"),
    [("", "deposit", 1), ("あ" * 201, "deposit", 1), ("事由", "move", 1), ("事由", "deposit", 0)],
)
def test_vault_operation_rejects_invalid_input(
    conn: psycopg.Connection, reason: str, direction: str, amount: int
) -> None:
    with pytest.raises(AppError) as excinfo:
        vault.create_vault_operation(conn, reason, direction, amount, date(2026, 9, 1))
    assert excinfo.value.code == "VALIDATION_ERROR"


# --- 集計 ---


def test_summary_accumulates_events_oldest_first_and_returns_newest_first(
    conn: psycopg.Connection,
) -> None:
    person_id = _setup_person_with_drinks(conn, 2)  # 飲用 100 × 2
    payment_id = payments.record_payment(conn, person_id, 150)["id"]
    collection.create_safe_deposit(conn)  # 150 を金庫へ
    payments.cancel_payment(conn, person_id, payment_id)  # 収納済みの支払の取り消し
    vault.create_vault_operation(conn, "豆", "withdrawal", 100, date(2026, 9, 1))
    unpaid.create_unpaid_adjustment(conn, person_id, 50, "調整")

    result = summary.get_summary(conn)
    rows = list(reversed(result["entries"]))
    assert [r["event_type"] for r in rows] == [
        "drink_recorded",
        "drink_recorded",
        "payment_recorded",
        "safe_deposited",
        "payment_cancelled",
        "vault_operated",
        "unpaid_adjusted",
    ]
    assert [(r["uncollected_amount"], r["collected_amount"], r["vault_amount"]) for r in rows] == [
        (100, 0, 0),
        (200, 0, 0),
        (50, 150, 0),
        (50, 0, 150),
        (200, 0, 150),  # 収納後の取り消しなので徴収済みは減らない
        (200, 0, 50),
        (50, 0, 50),
    ]
    assert rows[-1]["previous_amount"] == 200
    assert rows[-1]["new_amount"] == 50
    assert rows[-1]["amount"] is None
    assert (result["uncollected_amount"], result["collected_amount"], result["vault_amount"]) == (
        50,
        0,
        50,
    )


def test_summary_is_empty_without_events(conn: psycopg.Connection) -> None:
    people.register_person(conn, "山田")
    result = summary.get_summary(conn)
    assert result["entries"] == []


# --- 操作記録 ---


def test_operation_logs_record_every_operation_type(conn: psycopg.Connection) -> None:
    a = int(people.register_person(conn, "A")["id"])
    b = int(people.register_person(conn, "B")["id"])
    people.update_display_order(conn, [b, a])
    price.set_cup_price(conn, 100)
    price.set_cup_price(conn, 120)
    drink_id = drinks.record_drink(conn, a)["id"]
    drinks.record_drink(conn, a)
    drinks.cancel_drink(conn, a, drink_id)
    payment_id = payments.record_payment(conn, a, 20)["id"]
    payments.cancel_payment(conn, a, payment_id)
    payments.record_payment(conn, a, 10)
    collection.create_safe_deposit(conn)
    vault.create_vault_operation(conn, "豆", "withdrawal", 5, date(2026, 9, 1))
    unpaid.create_unpaid_adjustment(conn, a, 0, "精算")
    people.deactivate_person(conn, b)

    logs = operations.list_operation_logs(conn)
    types = {log["operation_type"] for log in logs}
    assert types == {
        "person_registered",
        "person_deactivated",
        "display_order_changed",
        "cup_price_registered",
        "cup_price_updated",
        "drink_recorded",
        "drink_cancelled",
        "payment_recorded",
        "payment_cancelled",
        "safe_deposited",
        "vault_operated",
        "unpaid_adjusted",
    }
    assert logs[0]["operation_type"] == "person_deactivated"  # 新しい順
    by_type = {log["operation_type"]: log["payload"] for log in logs}
    assert by_type["cup_price_updated"] == {"amount": 120, "previous_amount": 100}
    assert by_type["display_order_changed"] == {"person_ids": [b, a]}
    assert by_type["vault_operated"]["reason_date"] == "2026-09-01"
    assert by_type["unpaid_adjusted"]["previous_amount"] == 110
    assert by_type["unpaid_adjusted"]["name"] == "A"


# --- API 経由（エラー応答の形、失敗時に何も残らないこと） ---


def _count(conn: psycopg.Connection, table: str) -> int:
    row = conn.execute(f"SELECT count(*) AS n FROM coffee_ledger.{table}").fetchone()
    return int(row["n"]) if row else 0


def test_api_success_and_error_shapes(client: TestClient) -> None:
    created = client.post("/people", json={"name": "山田"})
    assert created.status_code == 201
    person_id = created.json()["id"]

    assert client.put("/cup-price", json={"amount": 100}).status_code == 200
    assert client.post(f"/people/{person_id}/drinks").status_code == 201

    over = client.post(f"/people/{person_id}/payments", json={"amount": 101})
    assert over.status_code == 409
    assert over.json() == {
        "error": {"code": "PAYMENT_EXCEEDS_UNPAID", "message": "支払額が未払い代金を超えています。"}
    }

    for body in ({"amount": 1.0}, {"amount": "1"}, {"amount": True}, {"amount": 1, "x": 1}, {}):
        invalid = client.post(f"/people/{person_id}/payments", json=body)
        assert invalid.status_code == 400, body
        assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"

    assert client.get("/people/abc").status_code == 400
    missing = client.get("/people/999")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "NOT_FOUND"

    bad_date = client.post(
        "/vault-operations",
        json={"reason": "豆", "direction": "deposit", "amount": 1, "reason_date": "2026-13-01"},
    )
    assert bad_date.status_code == 400
    numeric_date = client.post(
        "/vault-operations",
        json={"reason": "豆", "direction": "deposit", "amount": 1, "reason_date": 1758000000},
    )
    assert numeric_date.status_code == 400
    good_date = client.post(
        "/vault-operations",
        json={"reason": " 豆 ", "direction": "deposit", "amount": 1, "reason_date": "2026-09-24"},
    )
    assert good_date.status_code == 201
    assert good_date.json()["reason_date"] == "2026-09-24"
    assert good_date.json()["reason"] == "豆"
    assert client.get("/vault-operations").status_code == 405


def test_api_failure_leaves_no_records(client: TestClient, conn: psycopg.Connection) -> None:
    person_id = client.post("/people", json={"name": "山田"}).json()["id"]
    before = (_count(conn, "drinks"), _count(conn, "operation_logs"))

    response = client.post(f"/people/{person_id}/drinks")  # 単価未登録で拒否
    assert response.status_code == 409
    assert (_count(conn, "drinks"), _count(conn, "operation_logs")) == before


def test_api_rolls_back_partial_writes_on_unexpected_error(
    client: TestClient, conn: psycopg.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.services import operations as operations_service

    def broken_log(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("操作記録の書き込みに失敗")

    monkeypatch.setattr(operations_service, "add_operation_log", broken_log)
    response = client.post("/people", json={"name": "山田"})
    assert response.status_code == 500
    assert response.json() == {"error": {"code": "INTERNAL_ERROR", "message": "処理に失敗しました。"}}
    assert _count(conn, "people") == 0
