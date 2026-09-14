"""
Varynx Day 60 - Predictive Runtime Integration

Purpose:
    Integrate predictive security recommendations into a runtime-facing
    decision envelope.

Architectural boundary:
    This module consumes predictive intelligence and prepares a runtime
    control request.

It does NOT:
    - directly authorize actions
    - directly block agents
    - modify authorization policy
    - modify adaptive_response.py
    - execute hypothetical actions
    - infer malicious intent
    - replace the existing risk engine

Execution remains an explicit downstream responsibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable


SCORE_MIN = 0.0
SCORE_MAX = 100.0

RUNTIME_PENDING = "PENDING"
RUNTIME_READY = "READY"
RUNTIME_ESCALATED = "ESCALATED"

CONTROL_MAINTAIN = "MAINTAIN"
CONTROL_INCREASE_MONITORING = "INCREASE_MONITORING"
CONTROL_REDUCE_SCOPE = "REDUCE_SCOPE"
CONTROL_STEP_UP_VERIFICATION = "STEP_UP_VERIFICATION"
CONTROL_HUMAN_REVIEW = "REQUEST_HUMAN_REVIEW"
CONTROL_PREEMPTIVE_BLOCK = "PREEMPTIVE_BLOCK"

DIRECTION_IMPROVING = "IMPROVING"
DIRECTION_STABLE = "STABLE"
DIRECTION_DETERIORATING = "DETERIORATING"
DIRECTION_INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

CONFIDENCE_LOW = "LOW"
CONFIDENCE_MODERATE = "MODERATE"
CONFIDENCE_HIGH = "HIGH"


_ALLOWED_CONTROLS = {
    CONTROL_MAINTAIN,
    CONTROL_INCREASE_MONITORING,
    CONTROL_REDUCE_SCOPE,
    CONTROL_STEP_UP_VERIFICATION,
    CONTROL_HUMAN_REVIEW,
    CONTROL_PREEMPTIVE_BLOCK,
}

_ALLOWED_DIRECTIONS = {
    DIRECTION_IMPROVING,
    DIRECTION_STABLE,
    DIRECTION_DETERIORATING,
    DIRECTION_INSUFFICIENT_DATA,
}

_ALLOWED_CONFIDENCE = {
    CONFIDENCE_LOW,
    CONFIDENCE_MODERATE,
    CONFIDENCE_HIGH,
}

_ALLOWED_RUNTIME_STATES = {
    RUNTIME_PENDING,
    RUNTIME_READY,
    RUNTIME_ESCALATED,
}


def _validate_agent_id(agent_id: str) -> str:
    if not isinstance(agent_id, str) or not agent_id.strip():
        raise ValueError("agent_id must be a non-empty string")

    return agent_id.strip()


def _validate_score(
    value: float,
    field_name: str = "score",
) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{field_name} must be numeric"
        ) from exc

    if not isfinite(value):
        raise ValueError(
            f"{field_name} must be finite"
        )

    if not SCORE_MIN <= value <= SCORE_MAX:
        raise ValueError(
            f"{field_name} must be between "
            f"{SCORE_MIN} and {SCORE_MAX}"
        )

    return value


def _validate_slope(value: float) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "slope must be numeric"
        ) from exc

    if not isfinite(value):
        raise ValueError(
            "slope must be finite"
        )

    return value


def _validate_control(control: str) -> str:
    if not isinstance(control, str):
        raise ValueError(
            "recommendation must be a string"
        )

    normalized = control.strip().upper()

    if normalized not in _ALLOWED_CONTROLS:
        raise ValueError(
            f"Unsupported control recommendation: {control}"
        )

    return normalized


def _validate_direction(direction: str) -> str:
    if not isinstance(direction, str):
        raise ValueError(
            "direction must be a string"
        )

    normalized = direction.strip().upper()

    if normalized not in _ALLOWED_DIRECTIONS:
        raise ValueError(
            f"Unsupported direction: {direction}"
        )

    return normalized


def _validate_confidence(confidence: str) -> str:
    if not isinstance(confidence, str):
        raise ValueError(
            "confidence must be a string"
        )

    normalized = confidence.strip().upper()

    if normalized not in _ALLOWED_CONFIDENCE:
        raise ValueError(
            f"Unsupported confidence: {confidence}"
        )

    return normalized


def _validate_evidence(
    evidence: Iterable[str] | None,
) -> tuple[str, ...]:
    if evidence is None:
        return ()

    try:
        values = tuple(evidence)
    except TypeError as exc:
        raise ValueError(
            "evidence must be iterable"
        ) from exc

    normalized: list[str] = []

    for index, item in enumerate(values):
        if not isinstance(item, str):
            raise ValueError(
                f"evidence[{index}] must be a string"
            )

        text = item.strip()

        if text:
            normalized.append(text)

    return tuple(normalized)


def determine_runtime_state(
    recommendation: str,
) -> str:
    """
    Convert a predictive recommendation into a runtime integration state.

    This does not execute the recommendation.
    """
    recommendation = _validate_control(
        recommendation
    )

    if recommendation in {
        CONTROL_HUMAN_REVIEW,
        CONTROL_PREEMPTIVE_BLOCK,
    }:
        return RUNTIME_ESCALATED

    return RUNTIME_READY


def requires_explicit_execution(
    recommendation: str,
) -> bool:
    """
    Return whether the recommendation requires a downstream execution
    decision.

    All recommendations remain advisory at this layer.
    """
    recommendation = _validate_control(
        recommendation
    )

    # Every predictive recommendation requires an explicit downstream
    # runtime action. This function makes that boundary machine-readable.
    return True


def build_runtime_evidence(
    projected_score: float,
    direction: str,
    slope: float,
    confidence: str,
    recommendation: str,
    runtime_state: str,
) -> list[str]:
    """Build deterministic runtime integration evidence."""
    projected_score = _validate_score(
        projected_score,
        "projected_score",
    )

    direction = _validate_direction(
        direction
    )

    slope = _validate_slope(
        slope
    )

    confidence = _validate_confidence(
        confidence
    )

    recommendation = _validate_control(
        recommendation
    )

    if runtime_state not in _ALLOWED_RUNTIME_STATES:
        raise ValueError(
            f"Unsupported runtime state: {runtime_state}"
        )

    return [
        f"Projected security score: {projected_score:.2f}",
        f"Behavioral direction: {direction}",
        f"Trajectory slope: {slope:.2f}",
        f"Forecast confidence: {confidence}",
        f"Predictive recommendation: {recommendation}",
        f"Runtime integration state: {runtime_state}",
        "Recommendation remains pending downstream execution",
    ]


@dataclass(frozen=True)
class PredictiveRuntimeDecision:
    """
    Immutable runtime-facing predictive decision envelope.
    """

    agent_id: str
    projected_score: float
    direction: str
    slope: float
    confidence: str
    recommendation: str
    runtime_state: str
    execution_required: bool
    evidence: tuple[str, ...]


class PredictiveRuntimeIntegration:
    """
    Runtime-facing integration layer for predictive intelligence.

    The class stores the latest predictive runtime envelope for each agent.
    It never executes the recommended control.
    """

    def __init__(self) -> None:
        self._latest: dict[
            str,
            PredictiveRuntimeDecision,
        ] = {}

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
        """
        Prepare a predictive runtime decision envelope.

        No security control is executed here.
        """
        agent_id = _validate_agent_id(
            agent_id
        )

        projected_score = _validate_score(
            projected_score,
            "projected_score",
        )

        direction = _validate_direction(
            direction
        )

        slope = _validate_slope(
            slope
        )

        confidence = _validate_confidence(
            confidence
        )

        recommendation = _validate_control(
            recommendation
        )

        runtime_state = determine_runtime_state(
            recommendation
        )

        execution_required = requires_explicit_execution(
            recommendation
        )

        supplied_evidence = _validate_evidence(
            evidence
        )

        generated_evidence = build_runtime_evidence(
            projected_score=projected_score,
            direction=direction,
            slope=slope,
            confidence=confidence,
            recommendation=recommendation,
            runtime_state=runtime_state,
        )

        combined_evidence = tuple(
            generated_evidence
        ) + supplied_evidence

        decision = PredictiveRuntimeDecision(
            agent_id=agent_id,
            projected_score=projected_score,
            direction=direction,
            slope=slope,
            confidence=confidence,
            recommendation=recommendation,
            runtime_state=runtime_state,
            execution_required=execution_required,
            evidence=combined_evidence,
        )

        self._latest[agent_id] = decision

        return decision

    def latest(
        self,
        agent_id: str,
    ) -> PredictiveRuntimeDecision | None:
        """Return the latest runtime decision for an agent."""
        agent_id = _validate_agent_id(
            agent_id
        )

        return self._latest.get(agent_id)

    def snapshot_all(
        self,
    ) -> tuple[PredictiveRuntimeDecision, ...]:
        """Return all latest runtime decisions."""
        return tuple(
            self._latest.values()
        )

    def reset(
        self,
        agent_id: str | None = None,
    ) -> None:
        """Reset one agent or all runtime integration state."""
        if agent_id is None:
            self._latest.clear()
            return

        agent_id = _validate_agent_id(
            agent_id
        )

        self._latest.pop(
            agent_id,
            None,
        )


__all__ = [
    "SCORE_MIN",
    "SCORE_MAX",
    "RUNTIME_PENDING",
    "RUNTIME_READY",
    "RUNTIME_ESCALATED",
    "CONTROL_MAINTAIN",
    "CONTROL_INCREASE_MONITORING",
    "CONTROL_REDUCE_SCOPE",
    "CONTROL_STEP_UP_VERIFICATION",
    "CONTROL_HUMAN_REVIEW",
    "CONTROL_PREEMPTIVE_BLOCK",
    "DIRECTION_IMPROVING",
    "DIRECTION_STABLE",
    "DIRECTION_DETERIORATING",
    "DIRECTION_INSUFFICIENT_DATA",
    "CONFIDENCE_LOW",
    "CONFIDENCE_MODERATE",
    "CONFIDENCE_HIGH",
    "PredictiveRuntimeDecision",
    "PredictiveRuntimeIntegration",
    "determine_runtime_state",
    "requires_explicit_execution",
    "build_runtime_evidence",
]