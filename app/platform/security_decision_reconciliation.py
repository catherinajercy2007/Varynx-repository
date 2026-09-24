"""Platform adapter for Day63 security decision reconciliation."""

from dataclasses import asdict
from typing import Any

from app.security_decision_reconciliation import (
    SecurityDecisionReconciliation,
)


class SecurityDecisionReconciliationPlatformAdapter:
    """Platform-facing adapter for security decision reconciliation."""

    def __init__(self) -> None:
        self._latest: dict[str, SecurityDecisionReconciliation] = {}
        self._history: dict[str, list[SecurityDecisionReconciliation]] = {}

    @staticmethod
    def _serialize(
        snapshot: SecurityDecisionReconciliation,
    ) -> dict[str, Any]:
        data = asdict(snapshot)

        if isinstance(data.get("evidence"), tuple):
            data["evidence"] = list(data["evidence"])

        return data

    def reconcile(
        self,
        *,
        snapshot: SecurityDecisionReconciliation,
    ) -> SecurityDecisionReconciliation:
        """Store an already-created reconciliation snapshot."""

        if not isinstance(snapshot, SecurityDecisionReconciliation):
            raise TypeError(
                "snapshot must be a SecurityDecisionReconciliation instance"
            )

        self._latest[snapshot.agent_id] = snapshot
        self._history.setdefault(snapshot.agent_id, []).append(snapshot)

        return snapshot

    def serialized(
        self,
        *,
        snapshot: SecurityDecisionReconciliation,
    ) -> dict[str, Any]:
        """Store and serialize a reconciliation snapshot."""

        return self._serialize(self.reconcile(snapshot=snapshot))

    def latest(
        self,
        agent_id: str,
    ) -> SecurityDecisionReconciliation | None:
        """Return the latest reconciliation for an agent."""

        return self._latest.get(agent_id)

    def latest_serialized(
        self,
        agent_id: str,
    ) -> dict[str, Any] | None:
        """Return the latest reconciliation as a dictionary."""

        snapshot = self.latest(agent_id)

        if snapshot is None:
            return None

        return self._serialize(snapshot)

    def history(
        self,
        agent_id: str,
    ) -> tuple[SecurityDecisionReconciliation, ...]:
        """Return reconciliation history for an agent."""

        return tuple(self._history.get(agent_id, ()))

    def history_serialized(
        self,
        agent_id: str,
    ) -> tuple[dict[str, Any], ...]:
        """Return reconciliation history as dictionaries."""

        return tuple(
            self._serialize(snapshot)
            for snapshot in self.history(agent_id)
        )

    def snapshot_all(
        self,
    ) -> tuple[SecurityDecisionReconciliation, ...]:
        """Return all latest reconciliation snapshots."""

        return tuple(self._latest.values())

    def snapshot_all_serialized(
        self,
    ) -> tuple[dict[str, Any], ...]:
        """Return all latest snapshots as dictionaries."""

        return tuple(
            self._serialize(snapshot)
            for snapshot in self.snapshot_all()
        )

    def reset(self) -> None:
        """Clear all platform reconciliation state."""

        self._latest.clear()
        self._history.clear()


__all__ = [
    "SecurityDecisionReconciliationPlatformAdapter",
]