import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

from loguru import logger


def setup_logging(
    level: str = "INFO", json_format: bool = True, log_file: Optional[str] = None
) -> None:
    """Configure loguru for local development and Google Cloud Run."""
    # Remove default handler
    logger.remove()

    # Check if running in Cloud Run
    is_cloud_run = os.getenv("K_SERVICE") is not None

    if is_cloud_run:
        # Cloud Run: structured JSON logging to stdout.
        #
        # The sink must be a callable that accepts a Loguru message object
        # and writes it directly. Do NOT use format= with a callable — Loguru
        # treats the return value of format callables as a format string template
        # and calls format_map() on it, which breaks on JSON keys like "severity".
        # Passing the callable as the sink bypasses format_map entirely.
        _severity_mapping = {
            "TRACE": "DEBUG",
            "DEBUG": "DEBUG",
            "INFO": "INFO",
            "SUCCESS": "INFO",
            "WARNING": "WARNING",
            "ERROR": "ERROR",
            "CRITICAL": "CRITICAL",
        }

        def _json_sink(message: Any) -> None:
            record = message.record
            log_entry: dict = {
                "severity": _severity_mapping.get(record["level"].name, "INFO"),
                "message": record["message"],
                "timestamp": record["time"].isoformat(),
                "logger": record["name"],
                "module": record["module"],
                "function": record["function"],
                "line": record["line"],
            }

            if record.get("extra"):
                log_entry["extra"] = {
                    k: v for k, v in record["extra"].items() if k != "name"
                }

            if record.get("exception") and record["exception"] is not None:
                exc = record["exception"]
                log_entry["exception"] = {
                    "type": exc.type.__name__ if exc.type else None,
                    "value": str(exc.value) if exc.value else None,
                }

            sys.stdout.write(json.dumps(log_entry) + "\n")
            sys.stdout.flush()

        logger.add(
            _json_sink,
            level=level.upper(),
            backtrace=True,
            diagnose=False,  # diagnose=True leaks locals into logs — off in prod
        )
    else:
        # Local development: Use colored output to stderr
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level> | <level>{extra}</level>",
            level=level.upper(),
            colorize=True,
        )

        # Optional: Add file logging for local development
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            if json_format:
                logger.add(
                    str(log_file),  # Convert to string for type checking
                    level=level.upper(),
                    serialize=True,
                    rotation="10 MB",
                    retention="7 days",
                    compression="gz",
                    backtrace=True,
                    diagnose=True,
                )
            else:
                logger.add(
                    str(log_file),  # Convert to string for type checking
                    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                    level=level.upper(),
                    rotation="10 MB",
                    retention="7 days",
                    compression="gz",
                )


def get_logger(name: Optional[str] = None):  # type: ignore[no-untyped-def]
    """Get a logger instance for the given name."""
    if name:
        return logger.bind(name=name)
    return logger
