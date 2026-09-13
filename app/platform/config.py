"""
Platform configuration for Varynx.

Configuration is intentionally environment-driven so the same application
can run locally, inside Docker, or in a cloud deployment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable safely."""
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _env_int(name: str, default: int) -> int:
    """Read an integer environment variable with validation."""
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(
            f"{name} must be an integer"
        ) from exc


@dataclass(frozen=True)
class PlatformConfig:
    """Runtime configuration for the Varynx platform layer."""

    service_name: str = "varynx-platform"
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    metrics_enabled: bool = True
    database_path: str = "aegisguard.db"

    @classmethod
    def from_environment(cls) -> "PlatformConfig":
        """Construct configuration from environment variables."""

        return cls(
            service_name=os.getenv(
                "VARYNX_SERVICE_NAME",
                "varynx-platform",
            ),
            environment=os.getenv(
                "VARYNX_ENVIRONMENT",
                "development",
            ),
            host=os.getenv(
                "VARYNX_HOST",
                "0.0.0.0",
            ),
            port=_env_int(
                "VARYNX_PORT",
                8000,
            ),
            log_level=os.getenv(
                "VARYNX_LOG_LEVEL",
                "INFO",
            ).upper(),
            metrics_enabled=_env_bool(
                "VARYNX_METRICS_ENABLED",
                True,
            ),
            database_path=os.getenv(
                "VARYNX_DATABASE_PATH",
                "aegisguard.db",
            ),
        )

    def as_dict(self) -> dict[str, object]:
        """Return a serialization-safe configuration representation."""

        return {
            "service_name": self.service_name,
            "environment": self.environment,
            "host": self.host,
            "port": self.port,
            "log_level": self.log_level,
            "metrics_enabled": self.metrics_enabled,
            "database_path": self.database_path,
        }


_CONFIG: PlatformConfig | None = None


def get_platform_config() -> PlatformConfig:
    """Return the process-wide platform configuration."""

    global _CONFIG

    if _CONFIG is None:
        _CONFIG = PlatformConfig.from_environment()

    return _CONFIG