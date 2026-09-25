"""
Varynx Day 65 - Runtime Security Decision Enforcement Boundary.

This module accepts a validated security decision and prepares it
for the existing runtime security gateway.

Day 65 does not calculate risk or create a new security decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


DECISION_ALLOW = "ALLOW"
DECISION_MONITOR = "MONITOR"
DECISION_STEP_UP = "STEP_UP_VERIFICATION"
DECISION_REDUCE_SCOPE = "REDUCE_SCOPE"
DECISION_HUMAN_REVIEW = "HUMAN_REVIEW"
DECISION_BLOCK = "BLOCK"


ALLOWED_DECISIONS = {
    DECISION_ALLOW,
    DECISION_MONITOR,
    DECISION_STEP_UP,
    DECISION_REDUCE_SCOPE,
    DECISION_HUMAN_REVIEW,
    DECISION_BLOCK,
}


@dataclass(frozen=True)
class RuntimeSecurityRequest:
    """Validated runtime security request."""

    agent_id: str
    decision: str
    evidence: tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "decision": self.decision,
            "evidence": list(self.evidence),
        }


class RuntimeSecurityDecisionEnforcementBoundary:
    """
    Day 65 runtime enforcement boundary.

    It validates and stores the security decision.
    Actual enforcement remains outside this class.
    """

    def __init__(self) -> None:
        self._requests: Dict[str, RuntimeSecurityRequest] = {}

    def create_request(
        self,
        agent_id: str,
        decision: str,
        evidence: Optional[list[str]] = None,
    ) -> RuntimeSecurityRequest:

        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError(
                "agent_id must be a non-empty string"
            )

        if not isinstance(decision, str):
            raise ValueError("decision must be a string")

        decision = decision.strip().upper()

        if decision not in ALLOWED_DECISIONS:
            raise ValueError(
                f"Unsupported security decision: {decision}"
            )

        if evidence is None:
            evidence = []

        if not isinstance(evidence, list):
            raise ValueError("evidence must be a list")

        request = RuntimeSecurityRequest(
            agent_id=agent_id.strip(),
            decision=decision,
            evidence=tuple(evidence),
        )

        self._requests[request.agent_id] = request

        return request

    def get_request(
        self,
        agent_id: str,
    ) -> Optional[RuntimeSecurityRequest]:
        return self._requests.get(agent_id)

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        return {
            agent_id: request.to_dict()
            for agent_id, request in self._requests.items()
        }

    def clear(self) -> None:
        self._requests.clear()