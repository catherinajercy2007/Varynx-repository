"""
Platform adapter for Day 58 predictive trust and risk forecasting.

This module exposes the deterministic Day 58 forecasting engine through
a platform-safe API boundary.

The adapter:
- preserves the core forecasting semantics,
- provides API-safe serialization,
- exposes current and historical forecast state,
- keeps agent state isolated,
- supports reset operations,
- performs no authorization, enforcement, or security decisions.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Sequence

from app.predictive_forecast import (
    PredictiveForecastEngine,
    PredictiveForecastSnapshot,
)


class PredictiveForecastPlatformAdapter:
    """Platform-facing adapter for predictive forecast analysis."""

    def __init__(
        self,
        engine: PredictiveForecastEngine | None = None,
        *,
        horizon: int = 2,
        tolerance: float = 10.0,
    ) -> None:
        self._engine = engine or PredictiveForecastEngine(
            horizon=horizon,
            tolerance=tolerance,
        )

    @staticmethod
    def _serialize_snapshot(
        snapshot: PredictiveForecastSnapshot | None,
    ) -> dict[str, Any] | None:
        """Convert a forecast snapshot into an API-safe dictionary."""
        if snapshot is None:
            return None

        payload = asdict(snapshot)

        payload["observations"] = list(snapshot.observations)
        payload["evidence"] = list(snapshot.evidence)

        return payload

    def add_observation(
        self,
        agent_id: str,
        value: float,
    ) -> PredictiveForecastSnapshot:
        """Add one observation and return the resulting forecast."""
        return self._engine.add_observation(
            agent_id=agent_id,
            value=value,
        )

    def add_observation_serialized(
        self,
        agent_id: str,
        value: float,
    ) -> dict[str, Any]:
        """Add one observation and return an API-safe forecast."""
        snapshot = self.add_observation(agent_id, value)

        serialized = self._serialize_snapshot(snapshot)

        if serialized is None:
            raise RuntimeError("forecast snapshot serialization failed")

        return serialized

    def add_observations(
        self,
        agent_id: str,
        observations: Sequence[float],
    ) -> PredictiveForecastSnapshot:
        """Add multiple observations and return the resulting forecast."""
        return self._engine.add_observations(
            agent_id=agent_id,
            observations=observations,
        )

    def add_observations_serialized(
        self,
        agent_id: str,
        observations: Sequence[float],
    ) -> dict[str, Any]:
        """Add multiple observations and return an API-safe forecast."""
        snapshot = self.add_observations(agent_id, observations)

        serialized = self._serialize_snapshot(snapshot)

        if serialized is None:
            raise RuntimeError("forecast snapshot serialization failed")

        return serialized

    def forecast(
        self,
        agent_id: str,
    ) -> PredictiveForecastSnapshot:
        """Calculate the current forecast for an agent."""
        return self._engine.forecast(agent_id)

    def forecast_serialized(
        self,
        agent_id: str,
    ) -> dict[str, Any]:
        """Calculate and serialize the current forecast."""
        snapshot = self.forecast(agent_id)

        serialized = self._serialize_snapshot(snapshot)

        if serialized is None:
            raise RuntimeError("forecast snapshot serialization failed")

        return serialized

    def latest(
        self,
        agent_id: str,
    ) -> PredictiveForecastSnapshot | None:
        """Return the latest forecast snapshot for an agent."""
        return self._engine.latest(agent_id)

    def latest_serialized(
        self,
        agent_id: str,
    ) -> dict[str, Any] | None:
        """Return the latest forecast snapshot in API-safe form."""
        return self._serialize_snapshot(
            self.latest(agent_id)
        )

    def history(
        self,
        agent_id: str,
    ) -> tuple[float, ...]:
        """Return chronological observations for an agent."""
        return self._engine.get_history(agent_id)

    def history_count(
        self,
        agent_id: str,
    ) -> int:
        """Return the number of observations recorded for an agent."""
        return len(self.history(agent_id))

    def snapshot_all(
        self,
    ) -> tuple[PredictiveForecastSnapshot, ...]:
        """Return the latest forecast for every tracked agent."""
        return self._engine.snapshot_all()

    def snapshot_all_serialized(self) -> list[dict[str, Any]]:
        """Return all latest forecasts in API-safe form."""
        return [
            serialized
            for snapshot in self.snapshot_all()
            if (serialized := self._serialize_snapshot(snapshot)) is not None
        ]

    def reset(
        self,
        agent_id: str | None = None,
    ) -> None:
        """Reset one agent or all forecasting state."""
        self._engine.reset(agent_id)

    @property
    def engine(self) -> PredictiveForecastEngine:
        """Expose the underlying deterministic forecasting engine."""
        return self._engine


__all__ = [
    "PredictiveForecastPlatformAdapter",
]