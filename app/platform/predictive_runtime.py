"""Platform adapter for Day60 predictive runtime integration."""

from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from app.predictive_runtime import (
    PredictiveRuntimeDecision,
    PredictiveRuntimeIntegration,
)


class PredictiveRuntimePlatformAdapter:
    """Platform-facing adapter for predictive runtime decision envelopes.

    This adapter exposes the existing Day60 runtime integration layer through
    platform-friendly methods and JSON-serializable representations.

    It does not execute, authorize, block, or enforce any recommendation.
    """

    def __init__(
        self,
        integration: PredictiveRuntimeIntegration | None = None,
    ) -> None:
        self._integration = (
            integration
            if integration is not None
            else PredictiveRuntimeIntegration()
        )

    @staticmethod
    def _serialize_decision(
        decision: PredictiveRuntimeDecision,
    ) -> dict:
        data = asdict(decision)
        data["evidence"] = list(decision.evidence)
        return data

    def prepare_decision(
        self,
        agent_id: str,
        projected_score: float,
        direction: str,
        slope: float,
        confidence: str,
        recommendation: str,
        evidence: Iterable[str] | None = None,
    ) -> PredictiveRuntimeDecision:
        """Prepare and store a runtime-facing predictive decision."""
        return self._integration.prepare_decision(
            agent_id=agent_id,
            projected_score=projected_score,
            direction=direction,
            slope=slope,
            confidence=confidence,
            recommendation=recommendation,
            evidence=evidence,
        )

    def prepare_decision_serialized(
        self,
        agent_id: str,
        projected_score: float,
        direction: str,
        slope: float,
        confidence: str,
        recommendation: str,
        evidence: Iterable[str] | None = None,
    ) -> dict:
        """Prepare a decision and return a JSON-friendly mapping."""
        decision = self.prepare_decision(
            agent_id=agent_id,
            projected_score=projected_score,
            direction=direction,
            slope=slope,
            confidence=confidence,
            recommendation=recommendation,
            evidence=evidence,
        )
        return self._serialize_decision(decision)

    def latest(
        self,
        agent_id: str,
    ) -> PredictiveRuntimeDecision | None:
        """Return the latest runtime decision for an agent."""
        return self._integration.latest(agent_id)

    def latest_serialized(
        self,
        agent_id: str,
    ) -> dict | None:
        """Return the latest decision as a JSON-friendly mapping."""
        decision = self.latest(agent_id)

        if decision is None:
            return None

        return self._serialize_decision(decision)

    def snapshot_all(
        self,
    ) -> tuple[PredictiveRuntimeDecision, ...]:
        """Return all latest runtime decisions."""
        return self._integration.snapshot_all()

    def snapshot_all_serialized(self) -> list[dict]:
        """Return all latest decisions as JSON-friendly mappings."""
        return [
            self._serialize_decision(decision)
            for decision in self.snapshot_all()
        ]

    def reset(
        self,
        agent_id: str | None = None,
    ) -> None:
        """Reset one agent or all runtime integration state."""
        self._integration.reset(agent_id)

    @property
    def integration(self) -> PredictiveRuntimeIntegration:
        """Return the underlying runtime integration instance."""
        return self._integration


__all__ = [
    "PredictiveRuntimePlatformAdapter",
]