"""Platform adapter for Day61 unified behavioral pipeline."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.unified_behavioral_pipeline import (
    UnifiedBehavioralPipeline,
)


class UnifiedBehavioralPipelinePlatformAdapter:
    """Platform-facing adapter for the unified behavioral pipeline."""

    def __init__(
        self,
        pipeline: UnifiedBehavioralPipeline | None = None,
    ) -> None:
        self._pipeline = (
            pipeline
            if pipeline is not None
            else UnifiedBehavioralPipeline()
        )

    @staticmethod
    def _serialize(value: Any) -> Any:
        if hasattr(value, "__dataclass_fields__"):
            data = asdict(value)

            for key, item in data.items():
                if isinstance(item, tuple):
                    data[key] = list(item)

            return data

        if isinstance(value, tuple):
            return [
                UnifiedBehavioralPipelinePlatformAdapter._serialize(
                    item
                )
                for item in value
            ]

        return value

    def evaluate(
        self,
        agent_id: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Evaluate an agent through the unified behavioral pipeline."""
        return self._pipeline.evaluate(
            agent_id,
            *args,
            **kwargs,
        )

    def evaluate_serialized(
        self,
        agent_id: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Evaluate and return a JSON-friendly representation."""
        result = self.evaluate(
            agent_id,
            *args,
            **kwargs,
        )
        return self._serialize(result)

    def latest(
        self,
        agent_id: str,
    ) -> Any:
        """Return the latest pipeline result for an agent."""
        return self._pipeline.latest(agent_id)

    def latest_serialized(
        self,
        agent_id: str,
    ) -> Any:
        """Return the latest result in serialized form."""
        result = self.latest(agent_id)

        if result is None:
            return None

        return self._serialize(result)

    def snapshot_all(self) -> Any:
        """Return all latest pipeline results."""
        return self._pipeline.snapshot_all()

    def snapshot_all_serialized(self) -> Any:
        """Return all latest results in serialized form."""
        return self._serialize(
            self._pipeline.snapshot_all()
        )

    def reset(
        self,
        agent_id: str | None = None,
    ) -> None:
        """Reset one agent or all pipeline state."""
        self._pipeline.reset(agent_id)

    @property
    def pipeline(self) -> UnifiedBehavioralPipeline:
        """Return the underlying pipeline."""
        return self._pipeline


__all__ = [
    "UnifiedBehavioralPipelinePlatformAdapter",
]