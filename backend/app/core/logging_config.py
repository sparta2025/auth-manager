"""
Structured JSON logging.

Правило logging.md:
  - Структурированный вывод (JSON в production, human-readable в dev)
  - НИКОГДА не логировать пароли, токены, PII
  - Каждый лог содержит: timestamp, level, logger, message, extra context

Использование:
    from app.core.logging_config import get_logger
    log = get_logger(__name__)
    log.info("User logged in", extra={"user_id": user.id, "ip": ip})
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Форматирует логи в JSON — удобно для CloudWatch, Datadog, Loki."""

    # Поля, которые НИКОГДА не должны попасть в лог (OWASP A09)
    SENSITIVE = frozenset({
        "password", "password_hash", "token", "access_token",
        "refresh_token", "secret", "secret_salt", "smtp_password",
        "authorization", "cookie", "otp", "totp_secret",
    })

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts":      datetime.now(timezone.utc).isoformat(),
            "level":   record.levelname,
            "logger":  record.name,
            "message": record.getMessage(),
        }

        # Добавляем extra-поля, фильтруя чувствительные
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in (
                "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "name",
                "message", "taskName",
            ):
                continue
            if key.lower() in self.SENSITIVE:
                payload[key] = "***REDACTED***"
            else:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


class HumanFormatter(logging.Formatter):
    """Читаемый формат для локальной разработки."""
    COLORS = {
        "DEBUG":    "\033[36m",
        "INFO":     "\033[32m",
        "WARNING":  "\033[33m",
        "ERROR":    "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        return (
            f"{color}[{ts}] {record.levelname:<8}{self.RESET} "
            f"{record.name}: {record.getMessage()}"
        )


def configure_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
    """
    Настраивает корневой логгер.
    json_logs=True в production, False в dev.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    formatter: logging.Formatter = (
        JSONFormatter() if json_logs else HumanFormatter()
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

    # Снижаем шум от сторонних библиотек
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Возвращает именованный логгер. Использовать во всех модулях."""
    return logging.getLogger(name)


# Инициализация при импорте
_json = os.getenv("LOG_FORMAT", "human").lower() == "json"
_level = os.getenv("LOG_LEVEL", "INFO")
configure_logging(log_level=_level, json_logs=_json)
