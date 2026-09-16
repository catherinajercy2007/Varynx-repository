"""
Varynx Day 64 - Runtime Security Decision Coordinator.

This module prepares a complete runtime-facing security decision envelope
from reconciled behavioral intelligence.

Architectural boundary:
- Does not authorize requests.
- Does not execute controls.
- Does not modify authorization policy.
- Does not replace adaptive_response.py.
- Does not replace the risk engine.
- Does not execute hypothetical BCSE scenarios.
- Does not infer malicious intent.
- Does not create a universal Varynx score.

The coordinator combines decision evidence into a structured,
immutable runtime security envelope that can be consumed by
downstream enforcement components.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional


DECISION_ALLOW = "ALLOW"
DECISION_MONITOR = "MONITOR"
DECISION_STEP_UP = "STEP_UP_VERIFICATION"
DECISION_REDUCE_SCOPE = "REDUCE_SCOPE"
DECISION_HUMAN_REVIEW = "HUMAN_REVIEW"
DECISION_BLOCK = "BLOCK"

DECISIONS = {
    DECISION_ALLOW,
    DECISION_MONITOR,
    DECISION_STEP_UP,
    DECISION_REDUCE_SCOPE,
    DECISION_HUMAN_REVIEW,
    DECISION_BLOCK,
}

RUNTIME_READY = "RUNTIME_READY"
RUNTIME_ESCALATED = "RUNTIME_ESCALATED"
RUNTIME_PENDING = "RUNTIME_PENDING"

CONFIDENCE_LOW = "LOW"
CONFIDENCE_MODERATE = "MODERATE"
CONFIDENCE_HIGH = "HIGH"

CONFIDENCES = {
    CONFIDENCE_LOW,
    CONFIDENCE_MODERATE,
    CONFIDENCE_HIGH,
}

DIRECTION_IMPROVING = "IMPROVING"
DIRECTION_STABLE = "STABLE"
DIRECTION_DETERIORATING = "DETERIORATING"

DIRECTIONS = {
    DIRECTION_IMPROVING,
    DIRECTION_STABLE,
    DIRECTION_DETERIORATING,
}

SCORE_MIN = 0.0
SCORE_MAX = 100.0


def _validate_text(value: str, name: str) -> str:
    """Validate required text."""

    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")

    return value.strip()


def _validate_score(value: float, name: str) -> float:
    """Validate a bounded score."""

    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc

    if not SCORE_MIN <= numeric <= SCORE_MAX:
        raise ValueError(
            f"{name} must be between {SCORE_MIN} and {SCORE_MAX}"
        )

    return numeric


def _validate_slope(value: float) -> float:
    """Validate a numeric trajectory slope."""

    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("slope must be numeric") from exc


def _validate_decision(value: str) -> str:
    """Validate a security decision."""

    value = _validate_text(value, "decision").upper()

    if value not in DECISIONS:
        raise ValueError(f"Unsupported decision: {value}")

    return value


def _validate_confidence(value: str) -> str:
    """Validate prediction confidence."""

    value = _validate_text(value, "confidence").upper()

    if value not in CONFIDENCES:
        raise ValueError(f"Unsupported confidence: {value}")

    return value


def _validate_direction(value: str) -> str:
    """Validate behavioral direction."""

    value = _validate_text(value, "direction").upper()

    if value not in DIRECTIONS:
        raise ValueError(f"Unsupported direction: {value}")

    return value


def _validate_evidence(
    evidence: Optional[Iterable[str]],
) -> List[str]:
    """Validate and defensively copy evidence."""

    if evidence is None:
        return []

    if isinstance(evidence, (str, bytes)):
        raise ValueError("evidence must be an iterable of strings")

    result: List[str] = []

    for item in evidence:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                "evidence entries must be non-empty strings"
            )

        result.append(item.strip())

    return result


def determine_runtime_state(decision: str) -> str:
    """
    Determine the runtime readiness state.

    This does not execute the decision.
    """

    decision = _validate_decision(decision)

    if decision in {
        DECISION_HUMAN_REVIEW,
        DECISION_BLOCK,
    }:
        return RUNTIME_ESCALATED

    return RUNTIME_READY


def requires_enforcement_boundary(decision: str) -> bool:
    """
    Indicate whether the recommendation must cross an external
    enforcement boundary.

    Always returns True because this coordinator never executes
    security controls itself.
    """

    _validate_decision(decision)
    return True


def build_runtime_evidence(
    *,
    decision: str,
    reconciliation_status: str,
    projected_score: float,
    direction: str,
    confidence: str,
    consequence_score: Optional[float],
    deviation_score: Optional[float],
    source_evidence: Optional[Iterable[str]] = None,
) -> List[str]:
    """Construct explainable runtime security evidence."""

    decision = _validate_decision(decision)
    reconciliation_status = _validate_text(
        reconciliation_status,
        "reconciliation_status",
    ).upper()

    projected_score = _validate_score(
        projected_score,
        "projected_score",
    )

    direction = _validate_direction(direction)
    confidence = _validate_confidence(confidence)

    evidence = [
        f"Runtime security decision: {decision}",
        f"Reconciliation status: {reconciliation_status}",
        f"Projected security score: {projected_score:.2f}",
        f"Behavioral direction: {direction}",
        f"Prediction confidence: {confidence}",
    ]

    if consequence_score is not None:
        consequence_score = _validate_score(
            consequence_score,
            "consequence_score",
        )

        evidence.append(
            f"Consequence score: {consequence_score:.2f}"
        )

    if deviation_score is not None:
        deviation_score = _validate_score(
            deviation_score,
            "deviation_score",
        )

        evidence.append(
            f"Behavioral deviation score: {deviation_score:.2f}"
        )

    evidence.extend(_validate_evidence(source_evidence))

    return evidence


@dataclass(frozen=True)
class RuntimeSecurityEnvelope:
    """
    Immutable runtime-facing security decision envelope.

    This object is advisory and does not represent an executed action.
    """

    agent_id: str
    decision: str
    runtime_state: str
    enforcement_required: bool
    projected_score: float
    direction: str
    slope: float
    confidence: str
    reconciliation_status: str
    consequence_score: Optional[float]
    deviation_score: Optional[float]
    evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_text(self.agent_id, "agent_id")
        _validate_decision(self.decision)

        runtime_state = _validate_text(
            self.runtime_state,
            "runtime_state",
        ).upper()

        if runtime_state not in {
            RUNTIME_READY,
            RUNTIME_ESCALATED,
            RUNTIME_PENDING,
        }:
            raise ValueError(
                f"Unsupported runtime state: {runtime_state}"
            )

        if not isinstance(self.enforcement_required, bool):
            raise ValueError(
                "enforcement_required must be boolean"
            )

        _validate_score(
            self.projected_score,
            "projected_score",
        )

        _validate_direction(self.direction)
        _validate_slope(self.slope)
        _validate_confidence(self.confidence)

        _validate_text(
            self.reconciliation_status,
            "reconciliation_status",
        )

        if self.consequence_score is not None:
            _validate_score(
                self.consequence_score,
                "consequence_score",
            )

        if self.deviation_score is not None:
            _validate_score(
                self.deviation_score,
                "deviation_score",
            )

        _validate_evidence(self.evidence)


class RuntimeSecurityDecisionCoordinator:
    """
    Coordinates reconciled security recommendations into runtime envelopes.

    The coordinator is intentionally separated from enforcement.
    """

    def __init__(self) -> None:
        self._history: Dict[
            str,
            List[RuntimeSecurityEnvelope],
        ] = {}

        self._latest: Dict[
            str,
            RuntimeSecurityEnvelope,
        ] = {}

    def prepare(
        self,
        *,
        agent_id: str,
        decision: str,
        reconciliation_status: str,
        projected_score: float,
        direction: str,
        slope: float,
        confidence: str,
        consequence_score: Optional[float] = None,
        deviation_score: Optional[float] = None,
        evidence: Optional[Iterable[str]] = None,
    ) -> RuntimeSecurityEnvelope:
        """
        Prepare a runtime-facing security envelope.

        No security action is executed.
        """

        agent_id = _validate_text(agent_id, "agent_id")
        decision = _validate_decision(decision)

        reconciliation_status = _validate_text(
            reconciliation_status,
            "reconciliation_status",
        ).upper()

        projected_score = _validate_score(
            projected_score,
            "projected_score",
        )

        direction = _validate_direction(direction)
        slope = _validate_slope(slope)
        confidence = _validate_confidence(confidence)

        if consequence_score is not None:
            consequence_score = _validate_score(
                consequence_score,
                "consequence_score",
            )

        if deviation_score is not None:
            deviation_score = _validate_score(
                deviation_score,
                "deviation_score",
            )

        runtime_state = determine_runtime_state(decision)

        enforcement_required = requires_enforcement_boundary(
            decision
        )

        runtime_evidence = build_runtime_evidence(
            decision=decision,
            reconciliation_status=reconciliation_status,
            projected_score=projected_score,
            direction=direction,
            confidence=confidence,
            consequence_score=consequence_score,
            deviation_score=deviation_score,
            source_evidence=evidence,
        )

        envelope = RuntimeSecurityEnvelope(
            agent_id=agent_id,
            decision=decision,
            runtime_state=runtime_state,
            enforcement_required=enforcement_required,
            projected_score=projected_score,
            direction=direction,
            slope=slope,
            confidence=confidence,
            reconciliation_status=reconciliation_status,
            consequence_score=consequence_score,
            deviation_score=deviation_score,
            evidence=tuple(runtime_evidence),
        )

        self._history.setdefault(agent_id, []).append(envelope)
        self._latest[agent_id] = envelope

        return envelope

    def latest(
        self,
        agent_id: str,
    ) -> Optional[RuntimeSecurityEnvelope]:
        """Return the latest runtime envelope for an agent."""

        agent_id = _validate_text(agent_id, "agent_id")

        return self._latest.get(agent_id)

    def history(
        self,
        agent_id: str,
    ) -> List[RuntimeSecurityEnvelope]:
        """Return a defensive copy of runtime history."""

        agent_id = _validate_text(agent_id, "agent_id")

        return list(self._history.get(agent_id, []))

    def snapshot_all(
        self,
    ) -> Dict[str, RuntimeSecurityEnvelope]:
        """Return latest envelopes for all agents."""

        return dict(self._latest)

    def reset(
        self,
        agent_id: Optional[str] = None,
    ) -> None:
        """Reset one agent or the entire coordinator."""

        if agent_id is None:
            self._history.clear()
            self._latest.clear()
            return

        agent_id = _validate_text(agent_id, "agent_id")

        self._history.pop(agent_id, None)
        self._latest.pop(agent_id, None)