"""Structlog configuration for Enterprise QA Assistant."""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from src.infra.config.settings import get_settings


def add_app_info(logger: Any, method_name: str, event_dict: dict) -> dict:
    """Add application info to log context."""
    settings = get_settings()
    event_dict["app_name"] = settings.APP_NAME
    event_dict["app_version"] = settings.APP_VERSION
    event_dict["env"] = settings.ENV
    return event_dict


def configure_logging() -> None:
    """Configure structlog with JSON output and request context."""

    settings = get_settings()

    # Determine log level
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Shared processors for both stdlib and structlog
    shared_processors: list[Processor] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        add_app_info,
    ]

    # Configure structlog
    structlog.configure(
        processors=shared_processors
        + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)
