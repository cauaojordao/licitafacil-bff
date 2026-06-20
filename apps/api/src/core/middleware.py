"""Middlewares da aplicação."""

import time
import uuid
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse
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

        except Exception:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "Erro ao processar requisição",
                extra_fields={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                },
                exc_info=True,
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware para rate limiting global por IP."""

    def __init__(self, app: Any, limit_per_minute: int = 60) -> None:
        super().__init__(app)
        self.limit_per_minute = limit_per_minute
        self.requests: dict[str, list[datetime]] = defaultdict(list)

    def _clean_old_requests(self, ip: str, now: datetime) -> None:
        """Remove requisições antigas da janela de tempo."""
        cutoff = now - timedelta(minutes=1)
        self.requests[ip] = [
            req_time for req_time in self.requests[ip] if req_time > cutoff
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = datetime.utcnow()

        self._clean_old_requests(client_ip, now)

        if len(self.requests[client_ip]) >= self.limit_per_minute:
            logger.warning(
                "Rate limit excedido",
                extra_fields={
                    "client_ip": client_ip,
                    "path": request.url.path,
                    "limit": self.limit_per_minute,
                },
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit excedido. Máximo de "
                    f"{self.limit_per_minute} requisições por minuto."
                },
            )

        self.requests[client_ip].append(now)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limit_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.limit_per_minute - len(self.requests[client_ip])
        )

        return response
