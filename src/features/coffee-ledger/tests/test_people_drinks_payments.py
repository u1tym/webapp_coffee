"""人・飲用・支払・未払い修正の業務ロジック（REQ-003〜006、REQ-012〜014、REQ-016）。"""

import psycopg
import pytest

from app.errors import AppError
from app.services import balances, drinks, payments, people, price, unpaid


def _error_code(excinfo: pytest.ExceptionInfo[AppError]) -> str:
    return excinfo.value.code


def _person(conn: psycopg.Connection, name: str = "山田") -> int:
    return int(people.register_person(conn, name)["id"])


# --- 人 ---


def test_register_person_trims_name_and_appends_display_order(conn: psycopg.Connection) -> None:
    first = people.register_person(conn, "  山田  ")
    second = people.register_person(conn, "佐藤")
    assert first["name"] == "山田"
    assert (first["display_order"], second["display_order"]) == (1, 2)
    assert first["unpaid_amount"] == 0
    assert first["last_drink"] is None


def test_register_person_rejects_duplicate_including_deactivated(conn: psycopg.Connection) -> None:
    person_id = _person(conn)
    people.deactivate_person(conn, person_id)
    with pytest.raises(AppError) as excinfo:
        people.register_person(conn, "山田")
    assert _error_code(excinfo) == "NAME_DUPLICATE"


@pytest.mark.parametrize("name", ["", "   ", "あ" * 101])
def test_register_person_rejects_invalid_name(conn: psycopg.Connection, name: str) -> None:
    with pytest.raises(AppError) as excinfo:
        people.register_person(conn, name)
    assert _error_code(excinfo) == "VALIDATION_ERROR"


def test_register_person_accepts_100_chars(conn: psycopg.Connection) -> None:
    assert people.register_person(conn, "あ" * 100)["name"] == "あ" * 100


def test_deactivate_hides_from_active_list_and_rejects_twice(conn: psycopg.Connection) -> None:
    a = _person(conn, "山田")
    b = _person(conn, "佐藤")
    result = people.deactivate_person(conn, a)
    assert result["deactivated"] is True
    assert [p["id"] for p in people.list_people(conn, "active")] == [b]
    assert [p["id"] for p in people.list_people(conn, "all")] == [a, b]
    with pytest.raises(AppError) as excinfo:
        people.deactivate_person(conn, a)
    assert _error_code(excinfo) == "ALREADY_DEACTIVATED"


def test_list_people_rejects_unknown_scope(conn: psycopg.Connection) -> None:
    with pytest.raises(AppError) as excinfo:
        people.list_people(conn, "deactivated")
    assert _error_code(excinfo) == "VALIDATION_ERROR"


def test_display_order_is_renumbered_from_one(conn: psycopg.Connection) -> None:
    a, b, c = _person(conn, "A"), _person(conn, "B"), _person(conn, "C")
    people.deactivate_person(conn, b)
    result = people.update_display_order(conn, [c, a, b])
    assert [(p["id"], p["display_order"]) for p in result] == [(c, 1), (a, 2), (b, 3)]
    assert [p["id"] for p in people.list_people(conn, "active")] == [c, a]


def test_display_order_rejects_mismatch_duplicates_and_empty(conn: psycopg.Connection) -> None:
    a, b = _person(conn, "A"), _person(conn, "B")
    with pytest.raises(AppError) as excinfo:
        people.update_display_order(conn, [a])
    assert _error_code(excinfo) == "DISPLAY_ORDER_MISMATCH"
    with pytest.raises(AppError) as excinfo:
        people.update_display_order(conn, [a, b, 999])
    assert _error_code(excinfo) == "DISPLAY_ORDER_MISMATCH"
    for invalid in ([], [a, a]):
        with pytest.raises(AppError) as excinfo:
            people.update_display_order(conn, invalid)
        assert _error_code(excinfo) == "VALIDATION_ERROR"


# --- 飲用 ---


def test_drink_copies_current_price_and_price_change_does_not_affect_it(
    conn: psycopg.Connection,
) -> None:
    person_id = _person(conn)
    price.set_cup_price(conn, 100)
    drink = drinks.record_drink(conn, person_id)
    price.set_cup_price(conn, 150)
    drinks.record_drink(conn, person_id)
    assert drink["unit_price"] == 100
    assert [d["unit_price"] for d in drinks.list_drinks(conn, person_id)] == [150, 100]
    assert balances.unpaid_amount(conn, person_id) == 250
    assert people.get_person(conn, person_id)["last_drink"]["cancelled"] is False


def test_drink_rejected_without_price_or_when_deactivated(conn: psycopg.Connection) -> None:
    person_id = _person(conn)
    with pytest.raises(AppError) as excinfo:
        drinks.record_drink(conn, person_id)
    assert _error_code(excinfo) == "CUP_PRICE_MISSING"
    price.set_cup_price(conn, 100)
    people.deactivate_person(conn, person_id)
    with pytest.raises(AppError) as excinfo:
        drinks.record_drink(conn, person_id)
    assert _error_code(excinfo) == "PERSON_DEACTIVATED"


def test_drink_for_missing_person_is_not_found(conn: psycopg.Connection) -> None:
    price.set_cup_price(conn, 100)
    with pytest.raises(AppError) as excinfo:
        drinks.record_drink(conn, 999)
    assert excinfo.value.status_code == 404


def test_cancel_drink_reduces_unpaid_and_rejects_twice(conn: psycopg.Connection) -> None:
    person_id = _person(conn)
    price.set_cup_price(conn, 100)
    drink_id = drinks.record_drink(conn, person_id)["id"]
    cancelled = drinks.cancel_drink(conn, person_id, drink_id)
    assert cancelled["cancelled"] is True
    assert balances.unpaid_amount(conn, person_id) == 0
    assert people.get_person(conn, person_id)["last_drink"]["cancelled"] is True
    with pytest.raises(AppError) as excinfo:
        drinks.cancel_drink(conn, person_id, drink_id)
    assert _error_code(excinfo) == "ALREADY_CANCELLED"


def test_cancel_drink_of_other_person_is_not_found(conn: psycopg.Connection) -> None:
    a, b = _person(conn, "A"), _person(conn, "B")
    price.set_cup_price(conn, 100)
    drink_id = drinks.record_drink(conn, a)["id"]
    with pytest.raises(AppError) as excinfo:
        drinks.cancel_drink(conn, b, drink_id)
    assert excinfo.value.status_code == 404


def test_cancel_drink_rejected_when_unpaid_would_go_negative(conn: psycopg.Connection) -> None:
    person_id = _person(conn)
    price.set_cup_price(conn, 100)
    drink_id = drinks.record_drink(conn, person_id)["id"]
    payments.record_payment(conn, person_id, 100)
    with pytest.raises(AppError) as excinfo:
        drinks.cancel_drink(conn, person_id, drink_id)
    assert _error_code(excinfo) == "DRINK_CANCEL_WOULD_OVERPAY"


# --- 支払 ---


def test_payment_reduces_unpaid_and_limits_amount(conn: psycopg.Connection) -> None:
    person_id = _person(conn)
    price.set_cup_price(conn, 100)
    drinks.record_drink(conn, person_id)
    drinks.record_drink(conn, person_id)
    with pytest.raises(AppError) as excinfo:
        payments.record_payment(conn, person_id, 201)
    assert _error_code(excinfo) == "PAYMENT_EXCEEDS_UNPAID"
    payments.record_payment(conn, person_id, 150)
    assert balances.unpaid_amount(conn, person_id) == 50


def test_payment_rejected_when_unpaid_is_zero_or_amount_invalid(conn: psycopg.Connection) -> None:
    person_id = _person(conn)
    with pytest.raises(AppError) as excinfo:
        payments.record_payment(conn, person_id, 1)
    assert _error_code(excinfo) == "PAYMENT_EXCEEDS_UNPAID"
    with pytest.raises(AppError) as excinfo:
        payments.record_payment(conn, person_id, 0)
    assert _error_code(excinfo) == "VALIDATION_ERROR"


def test_cancel_payment_restores_unpaid_and_rejects_twice(conn: psycopg.Connection) -> None:
    person_id = _person(conn)
    price.set_cup_price(conn, 100)
    drinks.record_drink(conn, person_id)
    payment_id = payments.record_payment(conn, person_id, 100)["id"]
    payments.cancel_payment(conn, person_id, payment_id)
    assert balances.unpaid_amount(conn, person_id) == 100
    assert payments.list_payments(conn, person_id)[0]["cancelled"] is True
    with pytest.raises(AppError) as excinfo:
        payments.cancel_payment(conn, person_id, payment_id)
    assert _error_code(excinfo) == "ALREADY_CANCELLED"


# --- 未払い修正 ---


def test_unpaid_adjustment_sets_new_amount(conn: psycopg.Connection) -> None:
    person_id = _person(conn)
    price.set_cup_price(conn, 100)
    drinks.record_drink(conn, person_id)
    result = unpaid.create_unpaid_adjustment(conn, person_id, 30, "  端数を調整  ")
    assert (result["previous_amount"], result["new_amount"]) == (100, 30)
    assert result["reason"] == "端数を調整"
    assert balances.unpaid_amount(conn, person_id) == 30
    unpaid.create_unpaid_adjustment(conn, person_id, 500, "過去分を追加")
    assert balances.unpaid_amount(conn, person_id) == 500


def test_unpaid_adjustment_rejects_same_amount_and_invalid_input(conn: psycopg.Connection) -> None:
    person_id = _person(conn)
    with pytest.raises(AppError) as excinfo:
        unpaid.create_unpaid_adjustment(conn, person_id, 0, "変更なし")
    assert _error_code(excinfo) == "UNPAID_AMOUNT_UNCHANGED"
    for new_amount, reason in [(-1, "事由"), (10, "   "), (10, "あ" * 201)]:
        with pytest.raises(AppError) as excinfo:
            unpaid.create_unpaid_adjustment(conn, person_id, new_amount, reason)
        assert _error_code(excinfo) == "VALIDATION_ERROR"


def test_uncollected_includes_deactivated_person(conn: psycopg.Connection) -> None:
    a, b = _person(conn, "A"), _person(conn, "B")
    price.set_cup_price(conn, 100)
    drinks.record_drink(conn, a)
    drinks.record_drink(conn, b)
    people.deactivate_person(conn, b)
    assert balances.uncollected_amount(conn) == 200
