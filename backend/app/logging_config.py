import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from pythonjsonlogger import jsonlogger

from app.middleware.request_id import get_request_id


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Форматтер для структурированного JSON-логирования."""

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["level"] = record.levelname.upper()
        log_record["timestamp"] = datetime.now(timezone.utc).isoformat()
        log_record["service"] = "psychology-api"
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        if not log_record.get("request_id"):
            log_record["request_id"] = get_request_id()


def setup_logging(log_level: str = "INFO") -> None:
    """Настраивает глобальное логирование: JSON в stdout/stderr."""
    
    # Форматтер для обычных сообщений (stdout)
    json_formatter = CustomJsonFormatter(
        "%(timestamp)s %(level)s %(service)s %(name)s %(message)s %(request_id)s"
    )
    
    # Форматтер для ошибок (stderr) — тот же, но отдельный хендлер
    error_formatter = CustomJsonFormatter(
        "%(timestamp)s %(level)s %(service)s %(name)s %(message)s %(request_id)s %(exc_info)s"
    )

    # Хендлер для INFO и ниже → stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.addFilter(lambda record: record.levelno < logging.ERROR)
    stdout_handler.setFormatter(json_formatter)

    # Хендлер для ERROR и выше → stderr
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(error_formatter)

    # Корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.handlers = []  # Очистка существующих
    root_logger.addHandler(stdout_handler)
    root_logger.addHandler(stderr_handler)
    root_logger.propagate = False

    # Отключение избыточных логов сторонних библиотек
    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Возвращает логгер с предустановленным именем сервиса."""
    logger = logging.getLogger(name)
    return logger