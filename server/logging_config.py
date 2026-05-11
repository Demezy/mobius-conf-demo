"""structured logging setup — JSON to stdout, context-aware via contextvars.

Bind per-request fields (`request_id`, `session_id`, `machine_id`) once at the
request boundary and every subsequent `log.info(...)` from that request emits
them automatically. Canonical field names match CLAUDE.md.
"""
from __future__ import annotations

import logging
import sys
from typing import Any

import structlog


def configure_logging() -> None:
    """Configure structlog to emit JSON to stdout. Idempotent."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> Any:
    """Return a structlog logger. Pass module name for grep-friendliness."""
    return structlog.get_logger(name) if name else structlog.get_logger()


def bind_request_context(**kwargs: Any) -> None:
    """Bind values into the current request's logging context."""
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_request_context() -> None:
    """Clear contextvars at the end of a request to avoid leakage."""
    structlog.contextvars.clear_contextvars()
