import json
import os
import sys
from pathlib import Path
from typing import Optional

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
        # Cloud Run: Use structured JSON logging to stdout
        def json_formatter(record):
            """Format log record as JSON for Cloud Run."""
            severity_mapping = {
                "TRACE": "DEBUG",
                "DEBUG": "DEBUG",
                "INFO": "INFO",
                "SUCCESS": "INFO",
                "WARNING": "WARNING",
                "ERROR": "ERROR",
                "CRITICAL": "CRITICAL",
            }

            log_entry = {
                "severity": severity_mapping.get(record["level"].name, "INFO"),
                "message": record["message"],
                "timestamp": record["time"].isoformat(),
                "logger": record["name"],
                "module": record["module"],
                "function": record["function"],
                "line": record["line"],
            }

            if record.get("extra"):
                log_entry["extra"] = record["extra"]

            if record.get("exception"):
                log_entry["exception"] = {
                    "type": record["exception"].type.__name__,
                    "value": str(record["exception"].value),
                    "traceback": record["exception"].traceback,
                }

            return json.dumps(log_entry) + "\n"

        logger.add(
            sys.stdout,
            format=json_formatter,
            level=level.upper(),
            backtrace=True,
            diagnose=True,
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


def get_logger(name: Optional[str] = None):
    """Get a logger instance for the given name."""
    if name:
        return logger.bind(name=name)
    return logger
