"""
Varynx Day 68 - Runtime Audit Query.

Provides simple querying of recorded runtime security decisions.

This module does not calculate risk, create security decisions,
authorize actions, or execute enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


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
    Stores, retrieves, and queries runtime security audit evidence.
    """

    def __init__(self) -> None:
        self._records: Dict[str, RuntimeDecisionAuditRecord] = {}

    def record(
        self,
        agent_id: str,
        decision: str,
        evidence: Optional[List[str]] = None,
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

    def get_evidence(
        self,
        agent_id: str,
    ) -> List[str]:
        record = self.get(agent_id)

        if record is None:
            return []

        return list(record.evidence)

    def query_by_decision(
        self,
        decision: str,
    ) -> List[RuntimeDecisionAuditRecord]:
        if not isinstance(decision, str) or not decision.strip():
            raise ValueError("decision must be a non-empty string")

        normalized = decision.strip().upper()

        return [
            record
            for record in self._records.values()
            if record.decision == normalized
        ]

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        return {
            agent_id: record.to_dict()
            for agent_id, record in self._records.items()
        }

    def clear(self) -> None:
        self._records.clear()