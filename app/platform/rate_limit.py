"""Rate-limit configuration and monitoring for the Varynx platform.

This module provides validated configuration and observability counters.
It does not enforce request limits or replace runtime authorization.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from threading import Lock


def _read_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ValueError(
        f"{name} must be a boolean value "
        "(true/false, yes/no, on/off, or 1/0)"
    )


def _read_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


@dataclass(frozen=True)
class RateLimitConfig:
    """Validated rate-limit policy settings.

    Enforcement is disabled by default until an existing request-processing
    boundary is explicitly integrated with a limiter.
    """

    enabled: bool = False
    max_requests: int = 60
    window_seconds: int = 60

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise ValueError("enabled must be a boolean")

        for name, value in (
            ("max_requests", self.max_requests),
            ("window_seconds", self.window_seconds),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer")
            if value <= 0:
                raise ValueError(f"{name} must be positive")

    @classmethod
    def from_environment(cls) -> "RateLimitConfig":
        """Load settings from VARYNX_RATE_LIMIT_* environment variables."""
        return cls(
            enabled=_read_bool("VARYNX_RATE_LIMIT_ENABLED", False),
            max_requests=_read_int(
                "VARYNX_RATE_LIMIT_MAX_REQUESTS", 60
            ),
            window_seconds=_read_int(
                "VARYNX_RATE_LIMIT_WINDOW_SECONDS", 60
            ),
        )

    def to_dict(self) -> dict[str, bool | int]:
        return {
            "enabled": self.enabled,
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
        }


class RateLimitMonitor:
    """Thread-safe counters for outcomes reported by a future limiter."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._requests_allowed = 0
        self._requests_limited = 0

    def record_request(self, allowed: bool) -> None:
        """Record a known outcome; this method does not enforce a limit."""
        if not isinstance(allowed, bool):
            raise ValueError("allowed must be a boolean")

        with self._lock:
            if allowed:
                self._requests_allowed += 1
            else:
                self._requests_limited += 1

    def snapshot(
        self, config: RateLimitConfig | None = None
    ) -> dict[str, object]:
        """Return a consistent, serialization-safe monitoring snapshot."""
        active_config = config or RateLimitConfig.from_environment()

        with self._lock:
            allowed = self._requests_allowed
            limited = self._requests_limited

        return {
            "configuration": active_config.to_dict(),
            "enforcement_integrated": False,
            "requests_allowed": allowed,
            "requests_limited": limited,
            "requests_observed": allowed + limited,
        }


_MONITOR = RateLimitMonitor()


def get_rate_limit_config() -> RateLimitConfig:
    """Read the current rate-limit settings from the environment."""
    return RateLimitConfig.from_environment()


def get_rate_limit_monitor() -> RateLimitMonitor:
    """Return the process-wide rate-limit monitoring counters."""
    return _MONITOR
