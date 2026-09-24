import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env", override=True)


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if value is None or value == "":
        raise RuntimeError(f"環境変数 {name} が設定されていません。")
    return value


def require_int_env(name: str) -> int:
    raw = require_env(name)
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"環境変数 {name} は整数で指定してください。") from exc


def db_connect_kwargs() -> dict[str, str | int]:
    return {
        "host": require_env("DB_SERVER"),
        "port": require_int_env("DB_PORT"),
        "dbname": require_env("DB_DATABASE"),
        "user": require_env("DB_USERNAME"),
        "password": require_env("DB_PASSWORD"),
    }


def cors_origins() -> list[str]:
    raw = require_env("CORS_ORIGINS")
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    if not origins or "*" in origins:
        raise RuntimeError("CORS_ORIGINS には具体的なオリジンを指定してください。")
    return origins


def log_max_bytes() -> int:
    return require_int_env("LOG_MAX_BYTES")


def log_backup_count() -> int:
    return require_int_env("LOG_BACKUP_COUNT")


def validate_settings() -> None:
    db_connect_kwargs()
    cors_origins()
    log_max_bytes()
    log_backup_count()
