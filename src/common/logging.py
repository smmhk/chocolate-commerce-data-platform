"""Shared, Kestra-friendly logging helpers for ingestion pipelines.

Logs are sent to stdout, which Kestra can capture from Python tasks.
Avoid writing raw API payloads, credentials, or customer information to logs.
"""

import logging
import os
import re
import sys
import traceback
from contextlib import contextmanager
from pathlib import Path
from time import monotonic
from uuid import uuid4


_SECRET_ENV_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "API_KEY", "AUTH", "CREDENTIAL", "PRIVATE_KEY")


def _safe_error_message(error):
    """Report a useful one-line error summary without dumping payloads/SQL parameters.

    This is a best-effort scrubber, not a guarantee. Do not log sensitive data
    intentionally, and review exception formats before enabling verbose logs.
    """
    # SQLAlchemy often appends complete SQL and parameter values on later lines.
    message = str(error).splitlines()[0].strip() or "(no error message)"

    # Replace configured secrets before applying generic masking patterns.
    for key, value in os.environ.items():
        if any(marker in key.upper() for marker in _SECRET_ENV_MARKERS):
            if value and len(value) >= 4:
                message = message.replace(value, "[REDACTED]")

    message = re.sub(r"(?i)\b(?:postgres(?:ql)?|https?)://\S+", "[REDACTED_URL]", message)
    message = re.sub(r"(?i)\bbearer\s+\S+", "Bearer [REDACTED]", message)
    message = re.sub(
        r"(?i)\b(password|access[_-]?token|api[_-]?key|secret|authorization)\s*[:=]\s*[^\s,;]+",
        r"\1=[REDACTED]",
        message,
    )
    return message[:400] + ("..." if len(message) > 400 else "")


def _error_locations(error):
    """Show failing file, line and function without exposing traceback arguments."""
    frames = traceback.extract_tb(error.__traceback__)[-8:]
    return " -> ".join(
        f"{Path(frame.filename).name}:{frame.lineno}({frame.name})" for frame in frames
    ) or "(unavailable)"


@contextmanager
def log_stage(logger, stage, **context):
    details = " ".join(f"{key}={value}" for key, value in context.items())
    started = monotonic()
    logger.info("stage=%s status=started %s", stage, details)
    try:
        yield
    except Exception as error:
        logger.error(
            "stage=%s status=failed %s error_type=%s error_message=%r "
            "error_location=%s elapsed_seconds=%.3f",
            stage, details, type(error).__name__, _safe_error_message(error),
            _error_locations(error), monotonic() - started,
        )
        raise
    else:
        logger.info(
            "stage=%s status=completed %s elapsed_seconds=%.3f",
            stage, details, monotonic() - started,
        )


def run_metadata():
    return (
        os.getenv("PIPELINE_ORCHESTRATOR", "local"),
        os.getenv("PIPELINE_RUN_ID") or str(uuid4()),
    )


def run_cli(run, **kwargs):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
        stream=sys.stdout,
        force=True,  # Ensure this formatting also applies when libraries add handlers.
    )
    try:
        run(**kwargs)
    except Exception as error:
        logging.getLogger(run.__module__).error(
            "status=failed error_type=%s error_message=%r error_location=%s",
            type(error).__name__, _safe_error_message(error), _error_locations(error),
        )
        # Nonzero exit lets Kestra mark the Python task as FAILED.
        # Do not re-raise here: raw exception tracebacks may expose SQL parameters.
        raise SystemExit(1) from None
