"""Middlewares da aplicação."""

import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.logging import get_logger, set_correlation_id

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging e rastreamento de requisições."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        set_correlation_id(correlation_id)

        start_time = time.time()
        logger.info(
            "Requisição iniciada",
            extra_fields={
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
            },
        )

        try:
            response = await call_next(request)

            duration_ms = (time.time() - start_time) * 1000

            log_level = "info" if response.status_code < 400 else "warning"
            getattr(logger, log_level)(
                "Requisição concluída",
                extra_fields={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            response.headers["X-Correlation-ID"] = correlation_id
            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Erro ao processar requisição: {str(e)}",
                extra_fields={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                },
                exc_info=True,
            )
            raise
