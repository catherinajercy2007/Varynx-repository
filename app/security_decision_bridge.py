"""
Varynx Day 62 - Behavioral Security Decision Bridge.

This module translates unified behavioral and predictive intelligence
into a deterministic security decision recommendation.

Architectural boundary:
- Does not authorize actions.
- Does not execute controls.
- Does not replace adaptive_response.py.
- Does not modify authorization policy.
- Does not infer malicious intent.
- Does not create a universal security score.

The bridge consumes structured evidence produced by the behavioral
intelligence and predictive layers and produces an explainable
security decision recommendation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional


SCORE_MIN = 0.0
SCORE_MAX = 100.0

CONFIDENCE_LOW = "LOW"
CONFIDENCE_MODERATE = "MODERATE"
CONFIDENCE_HIGH = "HIGH"

DIRECTION_IMPROVING = "IMPROVING"
DIRECTION_STABLE = "STABLE"
DIRECTION_DETERIORATING = "DETERIORATING"

DECISION_ALLOW = "ALLOW"
DECISION_MONITOR = "MONITOR"
DECISION_STEP_UP = "STEP_UP_VERIFICATION"
DECISION_REDUCE_SCOPE = "REDUCE_SCOPE"
DECISION_HUMAN_REVIEW = "HUMAN_REVIEW"
DECISION_BLOCK = "BLOCK"

DECISION_PRIORITY = {
    DECISION_ALLOW: 10,
    DECISION_MONITOR: 20,
    DECISION_STEP_UP: 40,
    DECISION_REDUCE_SCOPE: 50,
    DECISION_HUMAN_REVIEW: 70,
    DECISION_BLOCK: 100,
}


def _validate_score(value: float, name: str) -> float:
    """Validate and normalize a security score."""

    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc

    if not SCORE_MIN <= numeric <= SCORE_MAX:
        raise ValueError(
            f"{name} must be between {SCORE_MIN} and {SCORE_MAX}"
        )

    return numeric


def _validate_text(value: str, name: str) -> str:
    """Validate required text fields."""

    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")

    return value.strip()


def _validate_confidence(value: str) -> str:
    """Validate confidence classification."""

    value = _validate_text(value, "confidence").upper()

    allowed = {
        CONFIDENCE_LOW,
        CONFIDENCE_MODERATE,
        CONFIDENCE_HIGH,
    }

    if value not in allowed:
        raise ValueError(f"Unsupported confidence level: {value}")

    return value


def _validate_direction(value: str) -> str:
    """Validate trajectory direction."""

    value = _validate_text(value, "direction").upper()

    allowed = {
        DIRECTION_IMPROVING,
        DIRECTION_STABLE,
        DIRECTION_DETERIORATING,
    }

    if value not in allowed:
        raise ValueError(f"Unsupported direction: {value}")

    return value


def _validate_evidence(
    evidence: Optional[Iterable[str]],
) -> List[str]:
    """Return a defensive evidence list."""

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


def classify_security_decision(
    projected_score: float,
    direction: str,
    confidence: str,
) -> str:
    """
    Convert predictive security evidence into a decision recommendation.

    The decision is intentionally conservative when confidence is low.
    """

    score = _validate_score(projected_score, "projected_score")
    direction = _validate_direction(direction)
    confidence = _validate_confidence(confidence)

    # Low projected concern.
    if score < 20:
        return DECISION_ALLOW

    # Moderate concern.
    if score < 40:
        if direction == DIRECTION_DETERIORATING:
            return DECISION_MONITOR

        return DECISION_ALLOW

    # High concern.
    if score < 70:
        if direction == DIRECTION_DETERIORATING:
            if confidence == CONFIDENCE_HIGH:
                return DECISION_REDUCE_SCOPE

            return DECISION_STEP_UP

        if confidence == CONFIDENCE_LOW:
            return DECISION_MONITOR

        return DECISION_STEP_UP

    # Critical concern.
    if direction == DIRECTION_DETERIORATING:
        if confidence == CONFIDENCE_HIGH:
            return DECISION_BLOCK

        return DECISION_HUMAN_REVIEW

    if confidence == CONFIDENCE_HIGH:
        return DECISION_HUMAN_REVIEW

    return DECISION_STEP_UP


def calculate_decision_priority(
    projected_score: float,
    slope: float,
    decision: str,
) -> float:
    """
    Calculate decision priority.

    This is a decision-ordering value, not a security risk score.
    """

    score = _validate_score(projected_score, "projected_score")

    try:
        slope_value = float(slope)
    except (TypeError, ValueError) as exc:
        raise ValueError("slope must be numeric") from exc

    decision = _validate_text(decision, "decision").upper()

    if decision not in DECISION_PRIORITY:
        raise ValueError(f"Unsupported decision: {decision}")

    escalation_pressure = max(0.0, slope_value)

    priority = score + (escalation_pressure * 2.0)

    # Ensure stronger decision classes retain their ordering.
    priority = max(
        priority,
        float(DECISION_PRIORITY[decision]),
    )

    return min(SCORE_MAX, priority)


def build_decision_evidence(
    projected_score: float,
    direction: str,
    confidence: str,
    decision: str,
    source_evidence: Optional[Iterable[str]] = None,
) -> List[str]:
    """Build explainable evidence for a decision recommendation."""

    score = _validate_score(projected_score, "projected_score")
    direction = _validate_direction(direction)
    confidence = _validate_confidence(confidence)
    decision = _validate_text(decision, "decision").upper()

    evidence = [
        f"Projected security score: {score:.2f}",
        f"Behavioral direction: {direction}",
        f"Prediction confidence: {confidence}",
        f"Recommended security decision: {decision}",
    ]

    evidence.extend(_validate_evidence(source_evidence))

    return evidence


@dataclass(frozen=True)
class SecurityDecisionSnapshot:
    """Immutable behavioral security decision recommendation."""

    agent_id: str
    projected_score: float
    direction: str
    slope: float
    confidence: str
    decision: str
    priority: float
    evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_text(self.agent_id, "agent_id")
        _validate_score(self.projected_score, "projected_score")
        _validate_direction(self.direction)
        _validate_confidence(self.confidence)
        _validate_text(self.decision, "decision")

        try:
            float(self.slope)
        except (TypeError, ValueError) as exc:
            raise ValueError("slope must be numeric") from exc

        if self.decision not in DECISION_PRIORITY:
            raise ValueError(
                f"Unsupported decision: {self.decision}"
            )

        _validate_score(self.priority, "priority")

        _validate_evidence(self.evidence)


class BehavioralSecurityDecisionBridge:
    """
    Stateful bridge between predictive intelligence and security decisions.

    State is isolated per agent.
    """

    def __init__(self) -> None:
        self._history: Dict[str, List[SecurityDecisionSnapshot]] = {}
        self._latest: Dict[str, SecurityDecisionSnapshot] = {}

    def evaluate(
        self,
        *,
        agent_id: str,
        projected_score: float,
        direction: str,
        slope: float,
        confidence: str,
        evidence: Optional[Iterable[str]] = None,
    ) -> SecurityDecisionSnapshot:
        """Create a deterministic security decision recommendation."""

        agent_id = _validate_text(agent_id, "agent_id")

        projected_score = _validate_score(
            projected_score,
            "projected_score",
        )

        direction = _validate_direction(direction)
        confidence = _validate_confidence(confidence)

        try:
            slope = float(slope)
        except (TypeError, ValueError) as exc:
            raise ValueError("slope must be numeric") from exc

        decision = classify_security_decision(
            projected_score=projected_score,
            direction=direction,
            confidence=confidence,
        )

        priority = calculate_decision_priority(
            projected_score=projected_score,
            slope=slope,
            decision=decision,
        )

        decision_evidence = build_decision_evidence(
            projected_score=projected_score,
            direction=direction,
            confidence=confidence,
            decision=decision,
            source_evidence=evidence,
        )

        snapshot = SecurityDecisionSnapshot(
            agent_id=agent_id,
            projected_score=projected_score,
            direction=direction,
            slope=slope,
            confidence=confidence,
            decision=decision,
            priority=priority,
            evidence=tuple(decision_evidence),
        )

        self._history.setdefault(agent_id, []).append(snapshot)
        self._latest[agent_id] = snapshot

        return snapshot

    def latest(
        self,
        agent_id: str,
    ) -> Optional[SecurityDecisionSnapshot]:
        """Return the latest decision for an agent."""

        agent_id = _validate_text(agent_id, "agent_id")
        return self._latest.get(agent_id)

    def history(
        self,
        agent_id: str,
    ) -> List[SecurityDecisionSnapshot]:
        """Return a defensive copy of agent decision history."""

        agent_id = _validate_text(agent_id, "agent_id")
        return list(self._history.get(agent_id, []))

    def snapshot_all(self) -> Dict[str, SecurityDecisionSnapshot]:
        """Return a defensive copy of latest decisions."""

        return dict(self._latest)

    def reset(self, agent_id: Optional[str] = None) -> None:
        """Reset one agent or the complete bridge state."""

        if agent_id is None:
            self._history.clear()
            self._latest.clear()
            return

        agent_id = _validate_text(agent_id, "agent_id")

        self._history.pop(agent_id, None)
        self._latest.pop(agent_id, None)