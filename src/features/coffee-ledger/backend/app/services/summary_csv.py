import csv
import io
from datetime import datetime
from typing import Any

import psycopg

from app.logging_setup import get_logger
from app.services import summary
from app.timeutil import JST, now_jst

log = get_logger()

HEADER = [
    "日時",
    "種類",
    "名前",
    "金額",
    "入出金",
    "事由",
    "事由の日付",
    "修正前の額",
    "修正後の額",
    "未徴収",
    "徴収済み",
    "金庫",
]

EVENT_LABELS = {
    "drink_recorded": "飲む",
    "drink_cancelled": "飲用の取り消し",
    "payment_recorded": "支払",
    "payment_cancelled": "支払の取り消し",
    "safe_deposited": "金庫収納",
    "vault_operated": "金庫操作",
    "unpaid_adjusted": "未払い修正",
}

DIRECTION_LABELS = {"deposit": "入金", "withdrawal": "出金"}


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _row(entry: dict[str, Any]) -> list[str]:
    occurred_at = datetime.fromisoformat(entry["occurred_at"]).astimezone(JST)
    return [
        occurred_at.strftime("%Y-%m-%d %H:%M:%S"),
        EVENT_LABELS.get(entry["event_type"], entry["event_type"]),
        _text(entry["name"]),
        _text(entry["amount"]),
        DIRECTION_LABELS.get(entry["direction"] or "", ""),
        _text(entry["reason"]),
        _text(entry["reason_date"]),
        _text(entry["previous_amount"]),
        _text(entry["new_amount"]),
        _text(entry["uncollected_amount"]),
        _text(entry["collected_amount"]),
        _text(entry["vault_amount"]),
    ]


def build_summary_csv(conn: psycopg.Connection) -> tuple[str, bytes]:
    """金銭の動きを古い順の CSV にする。戻り値は（ファイル名, UTF-8 BOM 付きの本文）。"""
    log.info("CSV出力要求")
    entries = list(reversed(summary.get_summary(conn)["entries"]))
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(HEADER)
    for entry in entries:
        writer.writerow(_row(entry))
    filename = now_jst().strftime("coffee-ledger-%Y%m%d-%H%M%S.csv")
    log.info("CSV出力成功 filename=%s rows=%s", filename, len(entries))
    return filename, ("﻿" + buffer.getvalue()).encode("utf-8")
