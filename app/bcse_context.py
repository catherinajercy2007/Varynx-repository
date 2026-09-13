"""
Day 53 - Context-Aware BCSE Modeling.

This module adjusts a Day 52 security consequence estimate using
explicit security-context modifiers.

Design principles:
- deterministic
- bounded
- explainable
- evidence-driven
- context-aware
- testable
- no authorization decisions
- no malicious-intent inference
- no hypothetical execution
- no exact attacker-behavior prediction
"""

from dataclasses import dataclass
from typing import Dict, Mapping, Optional


CONTEXT_MIN = 0.0
CONTEXT_MAX = 100.0

SCORE_MIN = 0.0
SCORE_MAX = 100.0

DEFAULT_CONTEXT_WEIGHTS = {
    "resource_sensitivity": 0.25,
    "privilege_context": 0.20,
    "scope_context": 0.20,
    "environment_context": 0.15,
    "persistence_context": 0.20,
}

CONTEXT_LEVELS = (
    "LOW",
    "MODERATE",
    "HIGH",
    "CRITICAL",
)


def _validate_score(value: float, name: str) -> float:
    """Validate a bounded 0-100 score."""
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")

    value = float(value)

    if value < SCORE_MIN or value > SCORE_MAX:
        raise ValueError(f"{name} must be between 0 and 100")

    return value


def _validate_context(context: Mapping[str, float]) -> Dict[str, float]:
    """Validate and normalize context dimensions."""
    if not isinstance(context, Mapping):
        raise TypeError("context must be a mapping")

    validated = {}

    for dimension, value in context.items():
        if not isinstance(dimension, str) or not dimension.strip():
            raise ValueError("context dimension names must be non-empty strings")

        validated[dimension] = _validate_score(
            value,
            f"context[{dimension}]",
        )

    return validated


def _validate_weights(
    weights: Mapping[str, float],
) -> Dict[str, float]:
    """Validate context weights."""
    if not isinstance(weights, Mapping):
        raise TypeError("weights must be a mapping")

    validated = {}

    for dimension, weight in weights.items():
        if not isinstance(weight, (int, float)):
            raise TypeError(f"weight for {dimension} must be numeric")

        weight = float(weight)

        if weight < 0:
            raise ValueError(f"weight for {dimension} cannot be negative")

        validated[dimension] = weight

    if not validated:
        raise ValueError("at least one weight is required")

    if sum(validated.values()) <= 0:
        raise ValueError("weight sum must be greater than zero")

    return validated


def classify_context(score: float) -> str:
    """
    Classify contextual consequence.

    Thresholds intentionally mirror the bounded BCSE consequence
    interpretation used in Day 52.
    """
    score = _validate_score(score, "context_score")

    if score < 20:
        return "LOW"

    if score < 40:
        return "MODERATE"

    if score < 70:
        return "HIGH"

    return "CRITICAL"


def calculate_context_index(
    context: Mapping[str, float],
    weights: Optional[Mapping[str, float]] = None,
) -> float:
    """
    Calculate a deterministic 0-100 contextual sensitivity index.

    Missing dimensions are excluded and the remaining weights are
    renormalized.
    """
    context = _validate_context(context)

    if not context:
        return 0.0

    weights = _validate_weights(
        weights or DEFAULT_CONTEXT_WEIGHTS
    )

    weighted_sum = 0.0
    weight_sum = 0.0

    for dimension, value in context.items():
        if dimension not in weights:
            continue

        weight = weights[dimension]

        weighted_sum += value * weight
        weight_sum += weight

    if weight_sum == 0:
        return 0.0

    score = weighted_sum / weight_sum

    return round(
        max(CONTEXT_MIN, min(CONTEXT_MAX, score)),
        4,
    )


def calculate_context_modifier(context_index: float) -> float:
    """
    Convert a contextual sensitivity index into a bounded multiplier.

    0 context  -> 0.50x
    50 context -> 1.00x
    100 context -> 1.50x

    This keeps context influential but bounded.
    """
    context_index = _validate_score(
        context_index,
        "context_index",
    )

    modifier = 0.50 + (context_index / 100.0)

    return round(
        max(0.50, min(1.50, modifier)),
        4,
    )


def apply_context_to_consequence(
    consequence_score: float,
    context_index: float,
) -> float:
    """
    Apply a bounded contextual modifier to a Day 52 consequence score.

    The result remains in the 0-100 range.
    """
    consequence_score = _validate_score(
        consequence_score,
        "consequence_score",
    )

    context_index = _validate_score(
        context_index,
        "context_index",
    )

    modifier = calculate_context_modifier(context_index)

    adjusted = consequence_score * modifier

    return round(
        max(SCORE_MIN, min(SCORE_MAX, adjusted)),
        4,
    )


def identify_context_evidence(
    context: Mapping[str, float],
) -> list[str]:
    """
    Produce deterministic human-readable explanations for
    the contextual model.
    """
    context = _validate_context(context)

    evidence = []

    labels = {
        "resource_sensitivity": "Resource sensitivity",
        "privilege_context": "Privilege context",
        "scope_context": "Scope context",
        "environment_context": "Environment context",
        "persistence_context": "Persistence context",
    }

    for dimension, value in context.items():
        label = labels.get(
            dimension,
            dimension.replace("_", " ").title(),
        )

        if value >= 70:
            evidence.append(
                f"{label} is high ({value:.1f})"
            )
        elif value >= 40:
            evidence.append(
                f"{label} is moderate ({value:.1f})"
            )
        else:
            evidence.append(
                f"{label} is low ({value:.1f})"
            )

    return evidence


@dataclass(frozen=True)
class ContextAwareConsequenceEstimate:
    """
    Immutable result of context-aware consequence modeling.
    """

    scenario_id: str
    base_consequence_score: float
    context_index: float
    context_level: str
    context_modifier: float
    adjusted_consequence_score: float
    adjusted_consequence_level: str
    context: Dict[str, float]
    evidence: tuple[str, ...]


class ContextAwareConsequenceModel:
    """
    Deterministic context-aware consequence model.

    This class consumes a consequence estimate and an explicit
    security context. It does not make authorization decisions.
    """

    def __init__(self) -> None:
        self._history: Dict[
            str,
            list[ContextAwareConsequenceEstimate]
        ] = {}

    def estimate(
        self,
        scenario_id: str,
        consequence_score: float,
        context: Mapping[str, float],
        weights: Optional[Mapping[str, float]] = None,
    ) -> ContextAwareConsequenceEstimate:
        """Generate a context-aware consequence estimate."""
        if not isinstance(scenario_id, str) or not scenario_id.strip():
            raise ValueError("scenario_id must be a non-empty string")

        consequence_score = _validate_score(
            consequence_score,
            "consequence_score",
        )

        validated_context = _validate_context(context)

        context_index = calculate_context_index(
            validated_context,
            weights,
        )

        modifier = calculate_context_modifier(
            context_index
        )

        adjusted_score = apply_context_to_consequence(
            consequence_score,
            context_index,
        )

        evidence = tuple(
            identify_context_evidence(
                validated_context
            )
        )

        estimate = ContextAwareConsequenceEstimate(
            scenario_id=scenario_id,
            base_consequence_score=consequence_score,
            context_index=context_index,
            context_level=classify_context(context_index),
            context_modifier=modifier,
            adjusted_consequence_score=adjusted_score,
            adjusted_consequence_level=classify_context(
                adjusted_score
            ),
            context=dict(validated_context),
            evidence=evidence,
        )

        self._history.setdefault(
            scenario_id,
            []
        ).append(estimate)

        return estimate

    def history(
        self,
        scenario_id: str,
    ) -> tuple[ContextAwareConsequenceEstimate, ...]:
        """Return immutable history for a scenario."""
        return tuple(
            self._history.get(scenario_id, [])
        )

    def latest(
        self,
        scenario_id: str,
    ) -> Optional[ContextAwareConsequenceEstimate]:
        """Return the latest estimate for a scenario."""
        history = self._history.get(scenario_id, [])

        if not history:
            return None

        return history[-1]

    def reset(self, scenario_id: Optional[str] = None) -> None:
        """
        Reset stored estimates.

        If scenario_id is omitted, all history is cleared.
        """
        if scenario_id is None:
            self._history.clear()
            return

        self._history.pop(scenario_id, None)