"""Platform adapter for Day59 predictive control recommendations."""

from dataclasses import asdict
from typing import Any, Optional

from app.predictive_control import PredictiveControlEngine


class PredictiveControlPlatformAdapter:
    """Expose Day59 predictive control through the platform layer.

    The adapter exposes recommendation generation and state inspection.
    It does not execute or enforce the recommendation.
    """

    def __init__(
        self,
        engine: Optional[PredictiveControlEngine] = None,
        *,
        high_threshold: float = 60.0,
        critical_threshold: float = 80.0,
        deterioration_slope: float = 5.0,
    ) -> None:
        self._engine = (
            engine
            if engine is not None
            else PredictiveControlEngine(
                high_threshold=high_threshold,
                critical_threshold=critical_threshold,
                deterioration_slope=deterioration_slope,
            )
        )

    @staticmethod
    def _serialize_snapshot(
        snapshot: Any,
    ) -> dict[str, Any] | None:
        if snapshot is None:
            return None

        data = asdict(snapshot)

        for key, value in tuple(data.items()):
            if isinstance(value, tuple):
                data[key] = list(value)

        return data

    def recommend(
        self,
        agent_id: str,
        projected_score: float,
        direction: str,
        slope: float,
        confidence: str,
    ) -> Any:
        """Generate a predictive control recommendation."""
        return self._engine.recommend(
            agent_id,
            projected_score,
            direction,
            slope,
            confidence,
        )

    def recommend_serialized(
        self,
        agent_id: str,
        projected_score: float,
        direction: str,
        slope: float,
        confidence: str,
    ) -> dict[str, Any]:
        """Generate a JSON-friendly predictive control recommendation."""
        snapshot = self.recommend(
            agent_id,
            projected_score,
            direction,
            slope,
            confidence,
        )

        serialized = self._serialize_snapshot(snapshot)

        if serialized is None:
            return {}

        return serialized

    def latest(self, agent_id: str) -> Any:
        """Return the latest recommendation for one agent."""
        return self._engine.latest(agent_id)

    def latest_serialized(
        self,
        agent_id: str,
    ) -> dict[str, Any] | None:
        """Return the latest recommendation as a mapping."""
        return self._serialize_snapshot(
            self._engine.latest(agent_id)
        )

    def snapshot_all(self) -> tuple[Any, ...]:
        """Return the latest recommendation for every agent."""
        return self._engine.snapshot_all()

    def snapshot_all_serialized(self) -> list[dict[str, Any]]:
        """Return all latest recommendations as mappings."""
        return [
            serialized
            for snapshot in self.snapshot_all()
            if (serialized := self._serialize_snapshot(snapshot))
            is not None
        ]

    def reset(self, agent_id: str | None = None) -> None:
        """Reset one agent or all recommendation state."""
        self._engine.reset(agent_id)

    @property
    def engine(self) -> PredictiveControlEngine:
        """Return the underlying Day59 core engine."""
        return self._engine


__all__ = ["PredictiveControlPlatformAdapter"]