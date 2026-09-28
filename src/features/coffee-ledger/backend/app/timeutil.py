import calendar
from datetime import datetime
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")


def now_jst() -> datetime:
    return datetime.now(JST)


def to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(JST).isoformat(timespec="seconds")


def months_before(value: datetime, months: int) -> datetime:
    """`value` から `months` か月前の日時を返す（同じ日、無ければその月の末日）。"""
    total_months = value.year * 12 + (value.month - 1) - months
    year, month = divmod(total_months, 12)
    month += 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)
