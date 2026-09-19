"""
Day 56 platform integration for predictive security signals.

This adapter exposes the deterministic predictive security engine through
the platform layer while preserving the core predictive-security behavior.

The adapter does not make authorization decisions, block agents, or alter
the predictive security model.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Mapping, Optional, Tuple

from app.predictive_security import (
    PredictiveSecurityEngine,
    PredictiveSecuritySnapshot,
)


class PredictiveSecurityPlatformAdapter:
    """
    Platform-facing adapter for Day 56 predictive security signals.

    Prediction history is maintained independently for each agent by the
    underlying PredictiveSecurityEngine.
    """

    def __init__(
        self,
        engine: Optional[PredictiveSecurityEngine] = None,
    ) -> None:
        self._engine = engine or PredictiveSecurityEngine()

    @staticmethod
    def _serialize_snapshot(
        snapshot: PredictiveSecuritySnapshot,
    ) -> Dict[str, Any]:
        """
        Convert a predictive security snapshot into an API-safe dictionary.
        """

        payload = asdict(snapshot)

        payload["dimensions"] = [
            {
                "name": name,
                "value": value,
            }
            for name, value in snapshot.dimensions
        ]

        payload["evidence"] = list(snapshot.evidence)

        return payload

    def predict(
        self,
        *,
        agent_id: str,
        dimensions: Mapping[str, float],
        consequence_exposure: Optional[float] = None,
    ) -> PredictiveSecuritySnapshot:
        """
        Generate and retain a predictive security snapshot.
        """

        return self._engine.predict(
            agent_id=agent_id,
            dimensions=dimensions,
            consequence_exposure=consequence_exposure,
        )

    def predict_serialized(
        self,
        *,
        agent_id: str,
        dimensions: Mapping[str, float],
        consequence_exposure: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Generate a predictive security snapshot in API-safe form.
        """

        snapshot = self.predict(
            agent_id=agent_id,
            dimensions=dimensions,
            consequence_exposure=consequence_exposure,
        )

        return self._serialize_snapshot(snapshot)

    def latest(
        self,
        agent_id: str,
    ) -> Optional[PredictiveSecuritySnapshot]:
        """Return the latest prediction for an agent."""

        return self._engine.latest(agent_id)

    def latest_serialized(
        self,
        agent_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Return the latest prediction in API-safe form."""

        snapshot = self.latest(agent_id)

        if snapshot is None:
            return None

        return self._serialize_snapshot(snapshot)

    def history(
        self,
        agent_id: str,
    ) -> Tuple[PredictiveSecuritySnapshot, ...]:
        """Return immutable prediction history for an agent."""

        return self._engine.history(agent_id)

    def history_serialized(
        self,
        agent_id: str,
    ) -> Tuple[Dict[str, Any], ...]:
        """Return prediction history in API-safe form."""

        return tuple(
            self._serialize_snapshot(snapshot)
            for snapshot in self.history(agent_id)
        )

    def history_count(
        self,
        agent_id: str,
    ) -> int:
        """Return prediction count for an agent."""

        return self._engine.history_count(agent_id)

    def reset(
        self,
        agent_id: Optional[str] = None,
    ) -> None:
        """
        Reset predictive-security history.

        If an agent_id is supplied, only that agent's history is removed.
        If omitted, all adapter-managed predictive history is cleared.
        """

        if agent_id is None:
            self._engine.reset()
            return

        self._engine.reset(agent_id)

    @property
    def engine(self) -> PredictiveSecurityEngine:
        """Expose the underlying engine for advanced platform integration."""

        return self._engine