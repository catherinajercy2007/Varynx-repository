"""Platform adapter for Day62 behavioral security decision bridge."""

from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from app.security_decision_bridge import (
    BehavioralSecurityDecisionBridge,
    SecurityDecisionSnapshot,
)


class SecurityDecisionBridgePlatformAdapter:
    """Platform-facing adapter for the behavioral security decision bridge."""

    def __init__(
        self,
        bridge: BehavioralSecurityDecisionBridge | None = None,
    ) -> None:
        self._bridge = (
            bridge
            if bridge is not None
            else BehavioralSecurityDecisionBridge()
        )

    @staticmethod
    def _serialize_snapshot(
        snapshot: SecurityDecisionSnapshot,
    ) -> dict:
        data = asdict(snapshot)
        data["evidence"] = list(snapshot.evidence)
        return data

    def evaluate(
        self,
        *,
        agent_id: str,
        projected_score: float,
        direction: str,
        slope: float,
        confidence: str,
        evidence: Iterable[str] | None = None,
    ) -> SecurityDecisionSnapshot:
        """Evaluate predictive evidence into a security decision."""
        return self._bridge.evaluate(
            agent_id=agent_id,
            projected_score=projected_score,
            direction=direction,
            slope=slope,
            confidence=confidence,
            evidence=evidence,
        )

    def evaluate_serialized(
        self,
        *,
        agent_id: str,
        projected_score: float,
        direction: str,
        slope: float,
        confidence: str,
        evidence: Iterable[str] | None = None,
    ) -> dict:
        """Evaluate and return a JSON-friendly decision mapping."""
        snapshot = self.evaluate(
            agent_id=agent_id,
            projected_score=projected_score,
            direction=direction,
            slope=slope,
            confidence=confidence,
            evidence=evidence,
        )

        return self._serialize_snapshot(snapshot)

    def latest(
        self,
        agent_id: str,
    ) -> SecurityDecisionSnapshot | None:
        """Return the latest decision for an agent."""
        return self._bridge.latest(agent_id)

    def latest_serialized(
        self,
        agent_id: str,
    ) -> dict | None:
        """Return the latest decision as a JSON-friendly mapping."""
        snapshot = self.latest(agent_id)

        if snapshot is None:
            return None

        return self._serialize_snapshot(snapshot)

    def history(
        self,
        agent_id: str,
    ) -> list[SecurityDecisionSnapshot]:
        """Return the decision history for an agent."""
        return self._bridge.history(agent_id)

    def history_serialized(
        self,
        agent_id: str,
    ) -> list[dict]:
        """Return decision history as JSON-friendly mappings."""
        return [
            self._serialize_snapshot(snapshot)
            for snapshot in self.history(agent_id)
        ]

    def snapshot_all(
        self,
    ) -> dict[str, SecurityDecisionSnapshot]:
        """Return all latest decisions."""
        return self._bridge.snapshot_all()

    def snapshot_all_serialized(
        self,
    ) -> dict[str, dict]:
        """Return all latest decisions in serialized form."""
        return {
            agent_id: self._serialize_snapshot(snapshot)
            for agent_id, snapshot in self.snapshot_all().items()
        }

    def reset(
        self,
        agent_id: str | None = None,
    ) -> None:
        """Reset one agent or all bridge state."""
        self._bridge.reset(agent_id)

    @property
    def bridge(self) -> BehavioralSecurityDecisionBridge:
        """Return the underlying decision bridge."""
        return self._bridge


__all__ = [
    "SecurityDecisionBridgePlatformAdapter",
]