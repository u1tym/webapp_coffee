from datetime import datetime
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")


def now_jst() -> datetime:
    return datetime.now(JST)


def to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(JST).isoformat(timespec="seconds")
