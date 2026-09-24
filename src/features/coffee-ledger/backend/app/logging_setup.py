import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

from app.config import BACKEND_DIR, log_backup_count, log_max_bytes
from app.timeutil import JST

LOGGER_NAME = "coffee_ledger"
LOG_DIR = BACKEND_DIR / "log"
LOG_FILE = LOG_DIR / "coffee-ledger.log"

_LEVEL_LABELS = {
    logging.DEBUG: "DBG",
    logging.INFO: "INF",
    logging.WARNING: "WRN",
    logging.ERROR: "ERR",
    logging.CRITICAL: "ERR",
}


class _JstFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, JST).strftime("%Y-%m-%d %H:%M:%S")
        label = _LEVEL_LABELS.get(record.levelno, "INF")
        line = f"{timestamp} {label} {record.getMessage()}"
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


def setup_logging() -> None:
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=log_max_bytes(),
        backupCount=log_backup_count(),
        encoding="utf-8",
    )
    handler.setFormatter(_JstFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)
