"""
Health and readiness checks for the Varynx platform.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import get_platform_config


def _utc_timestamp() -> str:
    """Return a UTC timestamp suitable for health responses."""
    return datetime.now(timezone.utc).isoformat()


def health_check() -> dict[str, Any]:
    """
    Return a lightweight liveness response.

    Liveness intentionally does not require the database to be available.
    """

    config = get_platform_config()

    return {
        "status": "healthy",
        "service": config.service_name,
        "environment": config.environment,
        "timestamp": _utc_timestamp(),
    }


def _database_check(database_path: str) -> dict[str, Any]:
    """Check whether the configured SQLite database is reachable."""

    path = Path(database_path)

    if not path.exists():
        return {
            "status": "unavailable",
            "database": database_path,
            "reason": "database file does not exist",
        }

    connection = None

    try:
        connection = sqlite3.connect(
            database_path,
            timeout=2,
        )

        connection.execute("SELECT 1")

        return {
            "status": "healthy",
            "database": database_path,
        }

    except sqlite3.Error as exc:
        return {
            "status": "unavailable",
            "database": database_path,
            "reason": str(exc),
        }

    finally:
        if connection is not None:
            connection.close()


def readiness_check() -> dict[str, Any]:
    """
    Return readiness information for deployment orchestration.

    The service is ready when its configured database is reachable.
    """

    config = get_platform_config()

    database = _database_check(
        config.database_path
    )

    ready = database["status"] == "healthy"

    return {
        "status": "ready" if ready else "not_ready",
        "service": config.service_name,
        "environment": config.environment,
        "database": database,
        "timestamp": _utc_timestamp(),
    }