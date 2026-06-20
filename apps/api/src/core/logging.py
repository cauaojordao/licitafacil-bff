"""Sistema de logging estruturado com correlation ID."""

import json
import logging
import sys
from collections.abc import MutableMapping
from contextvars import ContextVar
from typing import Any

from src.core.config import settings

correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)
user_id_ctx: ContextVar[str | None] = ContextVar("user_id", default=None)


class StructuredFormatter(logging.Formatter):
    """Formatter que adiciona contexto estruturado aos logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if correlation_id := correlation_id_ctx.get():
            log_data["correlation_id"] = correlation_id

        if user_id := user_id_ctx.get():
            log_data["user_id"] = user_id

        extra_fields = getattr(record, "extra_fields", None)
        if extra_fields:
            log_data.update(extra_fields)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class ContextLogger(logging.LoggerAdapter):
    """Logger adapter que facilita adição de contexto extra."""

    def process(
        self, msg: str, kwargs: MutableMapping[str, Any]
    ) -> tuple[str, MutableMapping[str, Any]]:
        if "extra" not in kwargs:
            kwargs["extra"] = {}

        if extra_fields := kwargs.pop("extra_fields", None):
            kwargs["extra"]["extra_fields"] = extra_fields

        return msg, kwargs


def setup_logging() -> None:
    """Configura sistema de logging estruturado."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [handler]


def get_logger(name: str) -> ContextLogger:
    """Retorna logger com suporte a contexto estruturado."""
    base_logger = logging.getLogger(name)
    return ContextLogger(base_logger, {})


def set_correlation_id(correlation_id: str) -> None:
    """Define correlation ID para a requisição atual."""
    correlation_id_ctx.set(correlation_id)


def set_user_id(user_id: str) -> None:
    """Define user ID para a requisição atual."""
    user_id_ctx.set(user_id)


def get_correlation_id() -> str | None:
    """Obtém correlation ID da requisição atual."""
    return correlation_id_ctx.get()


logger = get_logger(settings.APP_NAME)
