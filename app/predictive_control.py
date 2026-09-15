"""
Varynx Day 59 - Predictive Control Decision Layer

Purpose:
    Convert predictive behavioral security evidence into a deterministic
    and explainable control recommendation.

Architectural boundary:
    This module recommends a control. It does NOT execute the control.

It does not:
    - authorize actions
    - deny actions
    - block agents
    - modify authorization policy
    - directly invoke adaptive response
    - infer malicious intent
    - execute hypothetical actions
    - replace the existing risk engine
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping


SCORE_MIN = 0.0
SCORE_MAX = 100.0

DEFAULT_HIGH_THRESHOLD = 70.0
DEFAULT_CRITICAL_THRESHOLD = 85.0
DEFAULT_DETERIORATION_SLOPE = 5.0

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

LEVEL_LOW = "LOW"
LEVEL_MODERATE = "MODERATE"
LEVEL_HIGH = "HIGH"
LEVEL_CRITICAL = "CRITICAL"


def _validate_score(
    value: float,
    field_name: str = "score",
) -> float:
    """Validate a bounded security score."""
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc

    if not isfinite(value):
        raise ValueError(f"{field_name} must be finite")

    if not SCORE_MIN <= value <= SCORE_MAX:
        raise ValueError(
            f"{field_name} must be between {SCORE_MIN} and {SCORE_MAX}"
        )

    return value


def _validate_threshold(
    value: float,
    field_name: str,
) -> float:
    """Validate a bounded threshold."""
    value = _validate_score(value, field_name)
    return value


def _validate_slope(
    value: float,
) -> float:
    """Validate trajectory slope."""
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("slope must be numeric") from exc

    if not isfinite(value):
        raise ValueError("slope must be finite")

    return value


def _validate_agent_id(agent_id: str) -> str:
    """Validate agent identifier."""
    if not isinstance(agent_id, str) or not agent_id.strip():
        raise ValueError("agent_id must be a non-empty string")

    return agent_id.strip()


def _validate_direction(direction: str) -> str:
    """Validate trajectory direction."""
    allowed = {
        DIRECTION_IMPROVING,
        DIRECTION_STABLE,
        DIRECTION_DETERIORATING,
        DIRECTION_INSUFFICIENT_DATA,
    }

    if direction not in allowed:
        raise ValueError(
            f"Unsupported direction: {direction}"
        )

    return direction


def _validate_level(level: str) -> str:
    """Validate forecast/security level."""
    allowed = {
        LEVEL_LOW,
        LEVEL_MODERATE,
        LEVEL_HIGH,
        LEVEL_CRITICAL,
    }

    if level not in allowed:
        raise ValueError(
            f"Unsupported level: {level}"
        )

    return level


def classify_signal_level(
    score: float,
) -> str:
    """
    Classify a 0-100 predictive signal.

    <20   LOW
    <40   MODERATE
    <70   HIGH
    >=70  CRITICAL
    """
    score = _validate_score(score)

    if score < 20:
        return LEVEL_LOW

    if score < 40:
        return LEVEL_MODERATE

    if score < 70:
        return LEVEL_HIGH

    return LEVEL_CRITICAL


def calculate_control_priority(
    projected_score: float,
    slope: float,
) -> float:
    """
    Calculate a bounded control-priority indicator.

    Projected security concern contributes directly.
    Positive deterioration adds urgency.

    This is a decision-support priority value, not a replacement risk
    score.
    """
    projected_score = _validate_score(
        projected_score,
        "projected_score",
    )

    slope = _validate_slope(slope)

    deterioration_bonus = max(0.0, slope) * 2.0

    priority = projected_score + deterioration_bonus

    return max(
        SCORE_MIN,
        min(SCORE_MAX, priority),
    )


def recommend_control(
    projected_score: float,
    direction: str,
    slope: float,
    confidence: str,
    current_level: str | None = None,
) -> str:
    """
    Determine a deterministic predictive control recommendation.

    The recommendation is advisory. It does not execute a security
    control.

    Rules:

    CRITICAL projected state:
        HIGH confidence + deterioration -> PREEMPTIVE_BLOCK
        otherwise -> REQUEST_HUMAN_REVIEW

    HIGH projected state:
        deterioration + moderate/high confidence -> REDUCE_SCOPE
        otherwise -> STEP_UP_VERIFICATION

    MODERATE projected state:
        deterioration -> INCREASE_MONITORING
        otherwise -> MAINTAIN

    LOW projected state:
        -> MAINTAIN
    """
    projected_score = _validate_score(
        projected_score,
        "projected_score",
    )

    direction = _validate_direction(direction)
    slope = _validate_slope(slope)

    if not isinstance(confidence, str):
        raise ValueError("confidence must be a string")

    confidence = confidence.upper()

    if confidence not in {"LOW", "MODERATE", "HIGH"}:
        raise ValueError(
            f"Unsupported confidence: {confidence}"
        )

    if current_level is None:
        current_level = classify_signal_level(
            projected_score
        )
    else:
        current_level = _validate_level(
            current_level
        )

    if direction == DIRECTION_INSUFFICIENT_DATA:
        return CONTROL_MAINTAIN

    if current_level == LEVEL_CRITICAL:
        if (
            direction == DIRECTION_DETERIORATING
            and confidence == "HIGH"
        ):
            return CONTROL_PREEMPTIVE_BLOCK

        return CONTROL_HUMAN_REVIEW

    if current_level == LEVEL_HIGH:
        if (
            direction == DIRECTION_DETERIORATING
            and confidence in {"MODERATE", "HIGH"}
        ):
            return CONTROL_REDUCE_SCOPE

        return CONTROL_STEP_UP_VERIFICATION

    if current_level == LEVEL_MODERATE:
        if direction == DIRECTION_DETERIORATING:
            return CONTROL_INCREASE_MONITORING

        return CONTROL_MAINTAIN

    return CONTROL_MAINTAIN


def build_control_evidence(
    projected_score: float,
    direction: str,
    slope: float,
    confidence: str,
    recommendation: str,
) -> list[str]:
    """Generate deterministic evidence for a recommendation."""
    projected_score = _validate_score(
        projected_score,
        "projected_score",
    )

    direction = _validate_direction(direction)
    slope = _validate_slope(slope)

    if not isinstance(confidence, str):
        raise ValueError("confidence must be a string")

    if not isinstance(recommendation, str):
        raise ValueError("recommendation must be a string")

    return [
        f"Projected security score: {projected_score:.2f}",
        f"Observed trajectory direction: {direction}",
        f"Observed trajectory slope: {slope:.2f}",
        f"Forecast confidence: {confidence}",
        f"Recommended control: {recommendation}",
        "Recommendation is advisory and does not execute the control",
    ]


@dataclass(frozen=True)
class PredictiveControlSnapshot:
    """
    Immutable predictive control recommendation.
    """

    agent_id: str
    projected_score: float
    projected_level: str
    direction: str
    slope: float
    confidence: str
    priority: float
    recommendation: str
    evidence: tuple[str, ...]


class PredictiveControlEngine:
    """
    Stateful per-agent predictive control recommendation engine.

    The engine stores the latest recommendation for each agent.

    It never executes the recommendation.
    """

    def __init__(
        self,
        high_threshold: float = DEFAULT_HIGH_THRESHOLD,
        critical_threshold: float = DEFAULT_CRITICAL_THRESHOLD,
        deterioration_slope: float = DEFAULT_DETERIORATION_SLOPE,
    ) -> None:
        self.high_threshold = _validate_threshold(
            high_threshold,
            "high_threshold",
        )

        self.critical_threshold = _validate_threshold(
            critical_threshold,
            "critical_threshold",
        )

        if self.critical_threshold <= self.high_threshold:
            raise ValueError(
                "critical_threshold must be greater than "
                "high_threshold"
            )

        self.deterioration_slope = _validate_slope(
            deterioration_slope
        )

        self._latest: dict[
            str,
            PredictiveControlSnapshot,
        ] = {}

    def recommend(
        self,
        agent_id: str,
        projected_score: float,
        direction: str,
        slope: float,
        confidence: str,
    ) -> PredictiveControlSnapshot:
        """
        Generate a recommendation without executing it.
        """
        agent_id = _validate_agent_id(agent_id)

        projected_score = _validate_score(
            projected_score,
            "projected_score",
        )

        direction = _validate_direction(direction)
        slope = _validate_slope(slope)

        projected_level = classify_signal_level(
            projected_score
        )

        # Respect configurable critical/high boundaries when supplied.
        if projected_score >= self.critical_threshold:
            projected_level = LEVEL_CRITICAL
        elif projected_score >= self.high_threshold:
            projected_level = LEVEL_HIGH
        else:
            projected_level = classify_signal_level(
                projected_score
            )

        recommendation = recommend_control(
            projected_score=projected_score,
            direction=direction,
            slope=slope,
            confidence=confidence,
            current_level=projected_level,
        )

        priority = calculate_control_priority(
            projected_score=projected_score,
            slope=slope,
        )

        evidence = build_control_evidence(
            projected_score=projected_score,
            direction=direction,
            slope=slope,
            confidence=confidence,
            recommendation=recommendation,
        )

        snapshot = PredictiveControlSnapshot(
            agent_id=agent_id,
            projected_score=projected_score,
            projected_level=projected_level,
            direction=direction,
            slope=slope,
            confidence=confidence.upper(),
            priority=priority,
            recommendation=recommendation,
            evidence=tuple(evidence),
        )

        self._latest[agent_id] = snapshot

        return snapshot

    def latest(
        self,
        agent_id: str,
    ) -> PredictiveControlSnapshot | None:
        """Return the latest recommendation."""
        agent_id = _validate_agent_id(agent_id)
        return self._latest.get(agent_id)

    def snapshot_all(
        self,
    ) -> tuple[PredictiveControlSnapshot, ...]:
        """Return all latest recommendations."""
        return tuple(self._latest.values())

    def reset(
        self,
        agent_id: str | None = None,
    ) -> None:
        """Reset one agent or all recommendation state."""
        if agent_id is None:
            self._latest.clear()
            return

        agent_id = _validate_agent_id(agent_id)
        self._latest.pop(agent_id, None)


__all__ = [
    "SCORE_MIN",
    "SCORE_MAX",
    "DEFAULT_HIGH_THRESHOLD",
    "DEFAULT_CRITICAL_THRESHOLD",
    "DEFAULT_DETERIORATION_SLOPE",
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
    "LEVEL_LOW",
    "LEVEL_MODERATE",
    "LEVEL_HIGH",
    "LEVEL_CRITICAL",
    "PredictiveControlSnapshot",
    "PredictiveControlEngine",
    "classify_signal_level",
    "calculate_control_priority",
    "recommend_control",
    "build_control_evidence",
]