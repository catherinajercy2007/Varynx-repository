"""
Varynx Day 65 - Runtime Enforcement Boundary Adapter.

This module creates a controlled, immutable enforcement request from a
runtime security decision.

IMPORTANT SECURITY BOUNDARY
----------------------------
This module DOES NOT execute enforcement.

It prepares a request that an external enforcement layer may consume.

The actual enforcement mechanism remains outside this module.

Pipeline:

Behavioral Intelligence
        ->
Predictive Security
        ->
Security Decision
        ->
Runtime Security Envelope
        ->
Enforcement Boundary Adapter
        ->
External Enforcement Layer
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional
from copy import deepcopy


# ---------------------------------------------------------------------------
# Supported security decisions
# ---------------------------------------------------------------------------

DECISION_ALLOW = "ALLOW"
DECISION_MONITOR = "MONITOR"
DECISION_STEP_UP = "STEP_UP_VERIFICATION"
DECISION_REDUCE_SCOPE = "REDUCE_SCOPE"
DECISION_HUMAN_REVIEW = "HUMAN_REVIEW"
DECISION_BLOCK = "BLOCK"

VALID_DECISIONS = frozenset(
    {
        DECISION_ALLOW,
        DECISION_MONITOR,
        DECISION_STEP_UP,
        DECISION_REDUCE_SCOPE,
        DECISION_HUMAN_REVIEW,
        DECISION_BLOCK,
    }
)


# ---------------------------------------------------------------------------
# Boundary states
# ---------------------------------------------------------------------------

BOUNDARY_READY = "BOUNDARY_READY"
BOUNDARY_ESCALATED = "BOUNDARY_ESCALATED"


# ---------------------------------------------------------------------------
# Request modes
# ---------------------------------------------------------------------------

REQUEST_ONLY = "REQUEST_ONLY"


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")

    return value.strip()


def _validate_score(
    value: Optional[float],
    field_name: str,
) -> Optional[float]:
    if value is None:
        return None

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be numeric or None")

    value = float(value)

    if not 0.0 <= value <= 100.0:
        raise ValueError(f"{field_name} must be between 0 and 100")

    return value


def _validate_slope(
    value: Optional[float],
    field_name: str,
) -> Optional[float]:
    if value is None:
        return None

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be numeric or None")

    return float(value)


def _validate_decision(value: str) -> str:
    value = _validate_text(value, "decision")

    if value not in VALID_DECISIONS:
        raise ValueError(
            f"Unsupported decision: {value}. "
            f"Expected one of {sorted(VALID_DECISIONS)}"
        )

    return value


def _validate_evidence(
    evidence: Optional[Mapping[str, Any]],
) -> dict[str, Any]:
    if evidence is None:
        return {}

    if not isinstance(evidence, Mapping):
        raise TypeError("evidence must be a mapping or None")

    return deepcopy(dict(evidence))


# ---------------------------------------------------------------------------
# Boundary-state helpers
# ---------------------------------------------------------------------------


def determine_boundary_state(decision: str) -> str:
    """
    Determine whether the enforcement request represents an escalated
    security decision.

    This function does not execute the decision.
    """

    decision = _validate_decision(decision)

    if decision in {
        DECISION_HUMAN_REVIEW,
        DECISION_BLOCK,
    }:
        return BOUNDARY_ESCALATED

    return BOUNDARY_READY


def requires_external_enforcement(decision: str) -> bool:
    """
    Every decision crosses an explicit enforcement boundary.

    Even ALLOW and MONITOR are represented as requests because the adapter
    never assumes that it owns the downstream execution environment.
    """

    _validate_decision(decision)
    return True


def execution_is_performed_here() -> bool:
    """
    Explicit architectural invariant.

    Day 65 only creates an enforcement request.
    """

    return False


# ---------------------------------------------------------------------------
# Enforcement request
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EnforcementRequest:
    """
    Immutable request intended for an external enforcement layer.

    This object represents WHAT Varynx recommends.

    It does not perform the recommended action.
    """

    request_id: str
    agent_id: str
    decision: str
    boundary_state: str
    request_mode: str
    enforcement_required: bool

    projected_score: Optional[float]
    slope: Optional[float]
    confidence: Optional[str]

    reconciliation_status: Optional[str]
    consequence_score: Optional[float]
    deviation_score: Optional[float]

    evidence: dict[str, Any]


# ---------------------------------------------------------------------------
# Evidence construction
# ---------------------------------------------------------------------------


def build_enforcement_evidence(
    *,
    decision: str,
    boundary_state: str,
    projected_score: Optional[float] = None,
    slope: Optional[float] = None,
    confidence: Optional[str] = None,
    reconciliation_status: Optional[str] = None,
    consequence_score: Optional[float] = None,
    deviation_score: Optional[float] = None,
    evidence: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """
    Construct structured evidence for downstream enforcement.

    Existing evidence is preserved rather than replaced.
    """

    decision = _validate_decision(decision)
    boundary_state = _validate_text(
        boundary_state,
        "boundary_state",
    )

    result = {
        "decision": decision,
        "boundary_state": boundary_state,
        "execution_performed_here": False,
        "external_enforcement_required": True,
    }

    if projected_score is not None:
        result["projected_score"] = _validate_score(
            projected_score,
            "projected_score",
        )

    if slope is not None:
        result["slope"] = _validate_slope(
            slope,
            "slope",
        )

    if confidence is not None:
        result["confidence"] = _validate_text(
            confidence,
            "confidence",
        )

    if reconciliation_status is not None:
        result["reconciliation_status"] = _validate_text(
            reconciliation_status,
            "reconciliation_status",
        )

    if consequence_score is not None:
        result["consequence_score"] = _validate_score(
            consequence_score,
            "consequence_score",
        )

    if deviation_score is not None:
        result["deviation_score"] = _validate_score(
            deviation_score,
            "deviation_score",
        )

    if evidence:
        result["source_evidence"] = deepcopy(dict(evidence))

    return result


# ---------------------------------------------------------------------------
# Enforcement Boundary Adapter
# ---------------------------------------------------------------------------


class EnforcementBoundaryAdapter:
    """
    Converts runtime security decisions into immutable enforcement requests.

    Responsibilities
    ----------------
    - validate runtime decision data
    - create deterministic request identifiers
    - preserve evidence
    - expose explicit enforcement boundaries
    - maintain request history
    - provide latest request
    - provide defensive snapshots

    Non-responsibilities
    -------------------
    - executing BLOCK
    - executing ALLOW
    - changing authorization
    - changing adaptive response
    - changing policy
    - modifying agent permissions
    - making a malicious-intent determination
    """

    def __init__(self) -> None:
        self._history: dict[str, list[EnforcementRequest]] = {}
        self._request_counters: dict[str, int] = {}

    # ------------------------------------------------------------------
    # Request ID
    # ------------------------------------------------------------------

    def _next_request_id(self, agent_id: str) -> str:
        count = self._request_counters.get(agent_id, 0) + 1
        self._request_counters[agent_id] = count

        return f"{agent_id}-enforcement-{count}"

    # ------------------------------------------------------------------
    # Main operation
    # ------------------------------------------------------------------

    def prepare_request(
        self,
        *,
        agent_id: str,
        decision: str,
        projected_score: Optional[float] = None,
        slope: Optional[float] = None,
        confidence: Optional[str] = None,
        reconciliation_status: Optional[str] = None,
        consequence_score: Optional[float] = None,
        deviation_score: Optional[float] = None,
        evidence: Optional[Mapping[str, Any]] = None,
    ) -> EnforcementRequest:
        """
        Prepare an enforcement request.

        No external action is performed.
        """

        agent_id = _validate_text(agent_id, "agent_id")
        decision = _validate_decision(decision)

        projected_score = _validate_score(
            projected_score,
            "projected_score",
        )

        slope = _validate_slope(
            slope,
            "slope",
        )

        if confidence is not None:
            confidence = _validate_text(
                confidence,
                "confidence",
            )

        if reconciliation_status is not None:
            reconciliation_status = _validate_text(
                reconciliation_status,
                "reconciliation_status",
            )

        consequence_score = _validate_score(
            consequence_score,
            "consequence_score",
        )

        deviation_score = _validate_score(
            deviation_score,
            "deviation_score",
        )

        boundary_state = determine_boundary_state(decision)

        request = EnforcementRequest(
            request_id=self._next_request_id(agent_id),
            agent_id=agent_id,
            decision=decision,
            boundary_state=boundary_state,
            request_mode=REQUEST_ONLY,
            enforcement_required=requires_external_enforcement(
                decision
            ),
            projected_score=projected_score,
            slope=slope,
            confidence=confidence,
            reconciliation_status=reconciliation_status,
            consequence_score=consequence_score,
            deviation_score=deviation_score,
            evidence=build_enforcement_evidence(
                decision=decision,
                boundary_state=boundary_state,
                projected_score=projected_score,
                slope=slope,
                confidence=confidence,
                reconciliation_status=reconciliation_status,
                consequence_score=consequence_score,
                deviation_score=deviation_score,
                evidence=evidence,
            ),
        )

        self._history.setdefault(agent_id, []).append(request)

        return request

    # ------------------------------------------------------------------
    # State inspection
    # ------------------------------------------------------------------

    def latest(self, agent_id: str) -> Optional[EnforcementRequest]:
        agent_id = _validate_text(agent_id, "agent_id")

        requests = self._history.get(agent_id)

        if not requests:
            return None

        return requests[-1]

    def history(
        self,
        agent_id: str,
    ) -> tuple[EnforcementRequest, ...]:
        agent_id = _validate_text(agent_id, "agent_id")

        return tuple(self._history.get(agent_id, ()))

    def snapshot_all(
        self,
    ) -> dict[str, tuple[EnforcementRequest, ...]]:
        return {
            agent_id: tuple(requests)
            for agent_id, requests in self._history.items()
        }

    def reset(self, agent_id: Optional[str] = None) -> None:
        """
        Reset one agent or all adapter state.
        """

        if agent_id is None:
            self._history.clear()
            self._request_counters.clear()
            return

        agent_id = _validate_text(agent_id, "agent_id")

        self._history.pop(agent_id, None)
        self._request_counters.pop(agent_id, None)