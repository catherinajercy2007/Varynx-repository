"""
Varynx Day 64 - Security Decision Runtime Handoff.

Provides a platform-facing adapter around the Day 63 security decision
reconciliation layer.

The adapter prepares a validated runtime handoff envelope.

It does not authorize, execute, block, or modify security policy.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Optional

from app.security_decision_reconciliation import (
    SecurityDecisionReconciliation,
)


def _serialize_reconciliation(
    reconciliation: SecurityDecisionReconciliation,
) -> dict[str, Any]:
    """Convert a reconciliation snapshot into a JSON-safe mapping."""
    data = asdict(reconciliation)

    data["evidence"] = list(reconciliation.evidence)

    return data


class SecurityDecisionRuntimeHandoffPlatformAdapter:
    """
    Platform-facing Day 64 runtime handoff adapter.

    The adapter stores the latest reconciled decision for each agent and
    converts it into a runtime-facing, serialization-safe envelope.

    No runtime control is executed here.
    """

    def __init__(
        self,
        reconciliation: Optional[
            SecurityDecisionReconciliation
        ] = None,
    ) -> None:
        self._latest: dict[
            str,
            dict[str, Any],
        ] = {}

        if reconciliation is not None:
            self.handoff(reconciliation)

    def handoff(
        self,
        reconciliation: SecurityDecisionReconciliation,
    ) -> dict[str, Any]:
        """
        Prepare a runtime handoff envelope from a reconciled decision.
        """
        if not isinstance(
            reconciliation,
            SecurityDecisionReconciliation,
        ):
            raise TypeError(
                "reconciliation must be a "
                "SecurityDecisionReconciliation"
            )

        serialized = _serialize_reconciliation(reconciliation)

        envelope = {
            "agent_id": reconciliation.agent_id,
            "reconciled_decision": (
                reconciliation.reconciled_decision
            ),
            "reconciliation_status": (
                reconciliation.reconciliation_status
            ),
            "projected_score": (
                reconciliation.projected_score
            ),
            "direction": reconciliation.direction,
            "slope": reconciliation.slope,
            "confidence": reconciliation.confidence,
            "consequence_score": (
                reconciliation.consequence_score
            ),
            "deviation_score": (
                reconciliation.deviation_score
            ),
            "evidence": list(reconciliation.evidence),
            "reconciliation": serialized,
            "runtime_handoff": True,
            "execution_required": True,
        }

        self._latest[reconciliation.agent_id] = dict(envelope)

        return dict(envelope)

    def latest(
        self,
        agent_id: str,
    ) -> Optional[dict[str, Any]]:
        """Return the latest runtime handoff for an agent."""
        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError(
                "agent_id must be a non-empty string"
            )

        snapshot = self._latest.get(agent_id.strip())

        if snapshot is None:
            return None

        return dict(snapshot)

    def snapshot_all(
        self,
    ) -> dict[str, dict[str, Any]]:
        """Return all latest runtime handoffs."""
        return {
            agent_id: dict(snapshot)
            for agent_id, snapshot in self._latest.items()
        }

    def snapshot_all_serialized(
        self,
    ) -> dict[str, dict[str, Any]]:
        """Return JSON-friendly copies of all handoffs."""
        return self.snapshot_all()

    def reset(
        self,
        agent_id: Optional[str] = None,
    ) -> None:
        """Reset one agent or all runtime handoff state."""
        if agent_id is None:
            self._latest.clear()
            return

        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError(
                "agent_id must be a non-empty string"
            )

        self._latest.pop(agent_id.strip(), None)