"""
Varynx Day 66 - Runtime Decision Audit Evidence.

Provides a small platform-facing audit record for runtime security
decisions.

This module does not calculate risk, create security decisions,
authorize actions, or execute enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class RuntimeDecisionAuditRecord:
    """Audit record for a runtime security decision."""

    agent_id: str
    decision: str
    evidence: tuple[str, ...]
    recorded_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "decision": self.decision,
            "evidence": list(self.evidence),
            "recorded_at": self.recorded_at,
        }


class RuntimeDecisionAudit:
    """
    Stores runtime security decision audit evidence.

    Enforcement remains outside this class.
    """

    def __init__(self) -> None:
        self._records: Dict[str, RuntimeDecisionAuditRecord] = {}

    def record(
        self,
        agent_id: str,
        decision: str,
        evidence: Optional[list[str]] = None,
    ) -> RuntimeDecisionAuditRecord:

        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError("agent_id must be a non-empty string")

        if not isinstance(decision, str) or not decision.strip():
            raise ValueError("decision must be a non-empty string")

        if evidence is None:
            evidence = []

        if not isinstance(evidence, list):
            raise ValueError("evidence must be a list")

        record = RuntimeDecisionAuditRecord(
            agent_id=agent_id.strip(),
            decision=decision.strip().upper(),
            evidence=tuple(evidence),
            recorded_at=datetime.now(timezone.utc).isoformat(),
        )

        self._records[record.agent_id] = record

        return record

    def get(
        self,
        agent_id: str,
    ) -> Optional[RuntimeDecisionAuditRecord]:
        return self._records.get(agent_id)

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        return {
            agent_id: record.to_dict()
            for agent_id, record in self._records.items()
        }

    def clear(self) -> None:
        self._records.clear()