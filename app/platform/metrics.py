"""
Lightweight in-process metrics for the Varynx platform.

This is intentionally dependency-free. It provides a foundation that can
later be exported to Prometheus, OpenTelemetry, or another observability
system without coupling the security engine to a specific vendor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from time import perf_counter


@dataclass
class PlatformMetrics:
    """Thread-safe lightweight application metrics."""

    requests_total: int = 0
    requests_successful: int = 0
    requests_failed: int = 0
    total_request_seconds: float = 0.0
    _lock: Lock = field(
        default_factory=Lock,
        repr=False,
    )

    def record_request(
        self,
        duration_seconds: float,
        successful: bool,
    ) -> None:
        """Record one completed request."""

        if duration_seconds < 0:
            raise ValueError(
                "duration_seconds cannot be negative"
            )

        with self._lock:
            self.requests_total += 1
            self.total_request_seconds += duration_seconds

            if successful:
                self.requests_successful += 1
            else:
                self.requests_failed += 1

    def observe(
        self,
        successful: bool,
        operation,
    ):
        """
        Execute an operation and automatically record its duration.

        The original exception is deliberately re-raised so platform
        instrumentation never hides application failures.
        """

        start = perf_counter()

        try:
            result = operation()
            self.record_request(
                perf_counter() - start,
                successful=True,
            )
            return result

        except Exception:
            self.record_request(
                perf_counter() - start,
                successful=False,
            )
            raise

    @property
    def average_latency_seconds(self) -> float:
        """Return average request latency."""

        with self._lock:
            if self.requests_total == 0:
                return 0.0

            return (
                self.total_request_seconds
                / self.requests_total
            )

    def snapshot(self) -> dict[str, float | int]:
        """Return a serializable metrics snapshot."""

        with self._lock:
            return {
                "requests_total": self.requests_total,
                "requests_successful": self.requests_successful,
                "requests_failed": self.requests_failed,
                "total_request_seconds": self.total_request_seconds,
                "average_latency_seconds": (
                    self.total_request_seconds
                    / self.requests_total
                    if self.requests_total
                    else 0.0
                ),
            }


_METRICS = PlatformMetrics()


def get_metrics() -> PlatformMetrics:
    """Return the process-wide metrics collector."""

    return _METRICS