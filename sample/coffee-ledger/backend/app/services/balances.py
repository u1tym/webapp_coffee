import psycopg


def unpaid_amount(conn: psycopg.Connection, person_id: int) -> int:
    drinks = conn.execute(
        """
        SELECT COALESCE(SUM(unit_price), 0) AS total
        FROM coffee_ledger.drinks
        WHERE person_id = %s AND cancelled_at IS NULL
        """,
        (person_id,),
    ).fetchone()
    payments = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM coffee_ledger.payments
        WHERE person_id = %s AND cancelled_at IS NULL
        """,
        (person_id,),
    ).fetchone()
    adjustments = conn.execute(
        """
        SELECT COALESCE(SUM(new_amount - previous_amount), 0) AS total
        FROM coffee_ledger.unpaid_adjustments
        WHERE person_id = %s
        """,
        (person_id,),
    ).fetchone()
    drink_total = int(drinks["total"]) if drinks else 0
    payment_total = int(payments["total"]) if payments else 0
    adjustment_total = int(adjustments["total"]) if adjustments else 0
    unpaid = drink_total - payment_total + adjustment_total
    return unpaid if unpaid > 0 else 0


def collected_amount(conn: psycopg.Connection) -> int:
    last = conn.execute(
        """
        SELECT deposited_at
        FROM coffee_ledger.safe_deposits
        ORDER BY deposited_at DESC
        LIMIT 1
        """
    ).fetchone()
    if last is None:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM coffee_ledger.payments
            WHERE cancelled_at IS NULL
            """
        ).fetchone()
    else:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM coffee_ledger.payments
            WHERE cancelled_at IS NULL AND recorded_at > %s
            """,
            (last["deposited_at"],),
        ).fetchone()
    return int(row["total"]) if row else 0


def uncollected_amount(conn: psycopg.Connection) -> int:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(GREATEST(person_unpaid, 0)), 0) AS total
        FROM (
            SELECT
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
                ), 0) AS person_unpaid
            FROM coffee_ledger.people p
        ) amounts
        """
    ).fetchone()
    total = int(row["total"]) if row else 0
    return total if total > 0 else 0


def vault_amount(conn: psycopg.Connection) -> int:
    deposits = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM coffee_ledger.safe_deposits
        """
    ).fetchone()
    ops = conn.execute(
        """
        SELECT
            COALESCE(SUM(amount) FILTER (WHERE direction = 'deposit'), 0) AS deposits,
            COALESCE(SUM(amount) FILTER (WHERE direction = 'withdrawal'), 0) AS withdrawals
        FROM coffee_ledger.vault_operations
        """
    ).fetchone()
    deposited = int(deposits["total"]) if deposits else 0
    incoming = int(ops["deposits"]) if ops else 0
    outgoing = int(ops["withdrawals"]) if ops else 0
    total = deposited + incoming - outgoing
    return total if total > 0 else 0


def lock_vault_cash(conn: psycopg.Connection) -> None:
    conn.execute("SELECT pg_advisory_xact_lock(hashtext('coffee_ledger.vault_cash'))")
