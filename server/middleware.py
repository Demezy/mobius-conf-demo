"""ASGI middleware: stamp every request with a `request_id` and log lifecycle.

The `request_id` is bound into structlog contextvars so all downstream
`log.info(...)` calls from this request inherit it automatically.
"""
from __future__ import annotations

import time
import uuid
from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from logging_config import (
    bind_request_context,
    clear_request_context,
    get_logger,
)

log = get_logger("middleware.request_id")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Generate a `request_id` per request, bind to log context, log timing."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        bind_request_context(request_id=request_id)

        start = time.perf_counter()
        log.info(
            "request.start",
            method=request.method,
            path=request.url.path,
        )
        try:
            response = await call_next(request)
        except Exception:
            log.exception(
                "request.error",
                method=request.method,
                path=request.url.path,
            )
            raise
        else:
            duration_ms = (time.perf_counter() - start) * 1000.0
            log.info(
                "request.end",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )
            response.headers["x-request-id"] = request_id
            return response
        finally:
            clear_request_context()
