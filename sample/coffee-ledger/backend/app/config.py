import os
from pathlib import Path

from dotenv import load_dotenv

_BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_BACKEND_DIR / ".env", override=True)


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if value is None or value == "":
        raise RuntimeError(f"環境変数 {name} が設定されていません。")
    return value


def db_connect_kwargs() -> dict[str, str | int]:
    return {
        "host": require_env("Server"),
        "dbname": require_env("Database"),
        "port": int(require_env("Port")),
        "user": require_env("Username"),
        "password": require_env("Password"),
    }


def cors_origins() -> list[str]:
    raw = require_env("CORS_ORIGINS")
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    if not origins or "*" in origins:
        raise RuntimeError("CORS_ORIGINS には具体的なオリジンを指定してください。")
    return origins
