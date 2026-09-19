"""
Platform adapter for Day 57 predictive behavioral trajectory analysis.

This module exposes the deterministic Day 57 trajectory engine through a
platform-safe API boundary.

The adapter:
- preserves the core trajectory engine semantics,
- provides API-safe serialization,
- exposes latest and history views,
- keeps agent state isolated,
- supports reset operations,
- performs no authorization, enforcement, or security decisions.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Sequence

from app.predictive_trajectory import (
    BehavioralTrajectorySnapshot,
    PredictiveBehavioralTrajectory,
)


class PredictiveTrajectoryPlatformAdapter:
    """Platform-facing adapter for predictive behavioral trajectory analysis."""

    def __init__(
        self,
        engine: PredictiveBehavioralTrajectory | None = None,
        *,
        tolerance: float = 1.0,
        min_observations: int = 2,
    ) -> None:
        self._engine = engine or PredictiveBehavioralTrajectory(
            tolerance=tolerance,
            min_observations=min_observations,
        )

    @staticmethod
    def _serialize_snapshot(
        snapshot: BehavioralTrajectorySnapshot | None,
    ) -> dict[str, Any] | None:
        """Convert a trajectory snapshot into an API-safe dictionary."""
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
    ) -> BehavioralTrajectorySnapshot:
        """Add one observation and return the updated trajectory snapshot."""
        return self._engine.add_observation(
            agent_id=agent_id,
            value=value,
        )

    def add_observation_serialized(
        self,
        agent_id: str,
        value: float,
    ) -> dict[str, Any]:
        """Add one observation and return an API-safe snapshot."""
        snapshot = self.add_observation(agent_id, value)

        serialized = self._serialize_snapshot(snapshot)

        if serialized is None:
            raise RuntimeError("trajectory snapshot serialization failed")

        return serialized

    def add_observations(
        self,
        agent_id: str,
        observations: Sequence[float],
    ) -> BehavioralTrajectorySnapshot:
        """Add multiple observations and return the updated snapshot."""
        return self._engine.add_observations(
            agent_id=agent_id,
            observations=observations,
        )

    def add_observations_serialized(
        self,
        agent_id: str,
        observations: Sequence[float],
    ) -> dict[str, Any]:
        """Add multiple observations and return an API-safe snapshot."""
        snapshot = self.add_observations(agent_id, observations)

        serialized = self._serialize_snapshot(snapshot)

        if serialized is None:
            raise RuntimeError("trajectory snapshot serialization failed")

        return serialized

    def analyze(
        self,
        agent_id: str,
    ) -> BehavioralTrajectorySnapshot:
        """Analyze the current trajectory for an agent."""
        return self._engine.analyze(agent_id)

    def analyze_serialized(
        self,
        agent_id: str,
    ) -> dict[str, Any]:
        """Analyze and return an API-safe trajectory snapshot."""
        snapshot = self.analyze(agent_id)

        serialized = self._serialize_snapshot(snapshot)

        if serialized is None:
            raise RuntimeError("trajectory snapshot serialization failed")

        return serialized

    def latest(
        self,
        agent_id: str,
    ) -> BehavioralTrajectorySnapshot | None:
        """Return the latest trajectory snapshot for an agent."""
        return self._engine.latest(agent_id)

    def latest_serialized(
        self,
        agent_id: str,
    ) -> dict[str, Any] | None:
        """Return the latest trajectory snapshot in API-safe form."""
        return self._serialize_snapshot(
            self.latest(agent_id)
        )

    def history(
        self,
        agent_id: str,
    ) -> tuple[float, ...]:
        """Return chronological observations for an agent."""
        snapshot = self.latest(agent_id)

        if snapshot is None:
            return ()

        return tuple(snapshot.observations)

    def history_count(
        self,
        agent_id: str,
    ) -> int:
        """Return the number of observations recorded for an agent."""
        snapshot = self.latest(agent_id)

        if snapshot is None:
            return 0

        return snapshot.observation_count

    def snapshot_all(self) -> tuple[BehavioralTrajectorySnapshot, ...]:
        """Return the latest snapshot for every tracked agent."""
        return self._engine.snapshot_all()

    def snapshot_all_serialized(self) -> list[dict[str, Any]]:
        """Return all latest snapshots in API-safe form."""
        return [
            serialized
            for snapshot in self.snapshot_all()
            if (serialized := self._serialize_snapshot(snapshot)) is not None
        ]

    def reset(self, agent_id: str | None = None) -> None:
        """Reset one agent or all trajectory state."""
        self._engine.reset(agent_id)

    @property
    def engine(self) -> PredictiveBehavioralTrajectory:
        """Expose the underlying deterministic engine."""
        return self._engine


__all__ = [
    "PredictiveTrajectoryPlatformAdapter",
]