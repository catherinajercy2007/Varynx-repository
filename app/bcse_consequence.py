"""
Varynx Day 52
BCSE Security Consequence Estimation.

This module estimates potential security consequences associated with
a counterfactual behavioral scenario.

The estimator is:
- bounded
- deterministic
- explainable
- evidence-driven
- context-aware where supplied context permits

It does NOT:
- predict exact attacker behavior
- infer malicious intent
- execute hypothetical actions
- authorize requests
- block agents
- trigger adaptive response
- claim probabilistic attack certainty
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional


SCORE_MIN = 0.0
SCORE_MAX = 100.0

DEFAULT_WEIGHTS: Dict[str, float] = {
    "confidentiality": 0.25,
    "integrity": 0.20,
    "availability": 0.15,
    "scope": 0.15,
    "privilege": 0.15,
    "persistence": 0.10,
}

CONSEQUENCE_LEVELS = (
    "NONE",
    "LOW",
    "MODERATE",
    "HIGH",
    "CRITICAL",
)

CONFIDENCE_LEVELS = (
    "LOW",
    "MODERATE",
    "HIGH",
)


def _validate_score(
    value: float,
    field_name: str,
) -> float:
    """Validate a normalized 0-100 score."""
    if not isinstance(value, (int, float)):
        raise TypeError(
            f"{field_name} must be numeric"
        )

    value = float(value)

    if value < SCORE_MIN or value > SCORE_MAX:
        raise ValueError(
            f"{field_name} must be between "
            f"{SCORE_MIN} and {SCORE_MAX}"
        )

    return value


def _validate_text(
    value: str,
    field_name: str,
) -> str:
    """Validate required text."""
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string"
        )

    if not value.strip():
        raise ValueError(
            f"{field_name} must be non-empty"
        )

    return value


def _validate_weights(
    weights: Mapping[str, float],
) -> Dict[str, float]:
    """Validate and normalize consequence weights."""
    if not weights:
        raise ValueError(
            "weights cannot be empty"
        )

    validated = {}

    for name, weight in weights.items():
        if not isinstance(weight, (int, float)):
            raise TypeError(
                f"Weight for {name} must be numeric"
            )

        weight = float(weight)

        if weight < 0:
            raise ValueError(
                f"Weight for {name} cannot be negative"
            )

        validated[name] = weight

    total = sum(validated.values())

    if total <= 0:
        raise ValueError(
            "Weight total must be greater than zero"
        )

    return {
        name: weight / total
        for name, weight in validated.items()
    }


def aggregate_consequence(
    dimensions: Mapping[str, float],
    weights: Optional[Mapping[str, float]] = None,
) -> float:
    """
    Calculate a weighted potential consequence score.

    Missing dimensions are excluded and the remaining weights are
    renormalized.

    This is a consequence magnitude, not an attack probability.
    """
    if not dimensions:
        return 0.0

    validated_dimensions = {
        name: _validate_score(value, name)
        for name, value in dimensions.items()
    }

    normalized_weights = _validate_weights(
        weights or DEFAULT_WEIGHTS
    )

    applicable = {
        name: value
        for name, value in validated_dimensions.items()
        if name in normalized_weights
    }

    if not applicable:
        return 0.0

    applicable_weights = {
        name: normalized_weights[name]
        for name in applicable
    }

    weight_total = sum(
        applicable_weights.values()
    )

    return sum(
        applicable[name] * applicable_weights[name]
        for name in applicable
    ) / weight_total


def classify_consequence(
    score: float,
) -> str:
    """Classify potential consequence magnitude."""
    score = _validate_score(
        score,
        "score",
    )

    if score < 20:
        return "NONE"

    if score < 40:
        return "LOW"

    if score < 60:
        return "MODERATE"

    if score < 80:
        return "HIGH"

    return "CRITICAL"


def classify_confidence(
    evidence_count: int,
    assumption_count: int,
) -> str:
    """
    Classify estimator confidence based on available evidence and
    explicit assumptions.

    More direct evidence increases confidence.
    More assumptions reduce confidence.
    """
    if not isinstance(
        evidence_count,
        int,
    ):
        raise TypeError(
            "evidence_count must be an integer"
        )

    if not isinstance(
        assumption_count,
        int,
    ):
        raise TypeError(
            "assumption_count must be an integer"
        )

    if evidence_count < 0:
        raise ValueError(
            "evidence_count cannot be negative"
        )

    if assumption_count < 0:
        raise ValueError(
            "assumption_count cannot be negative"
        )

    if (
        evidence_count >= 3
        and assumption_count <= 1
    ):
        return "HIGH"

    if (
        evidence_count >= 1
        and assumption_count <= 3
    ):
        return "MODERATE"

    return "LOW"


def identify_consequence_evidence(
    dimensions: Mapping[str, float],
    threshold: float = 40.0,
) -> List[str]:
    """
    Produce human-readable consequence evidence.

    Evidence describes potential impact. It does not assert that
    the impact will definitely occur.
    """
    threshold = _validate_score(
        threshold,
        "threshold",
    )

    labels = {
        "confidentiality": (
            "Potential confidentiality impact"
        ),
        "integrity": (
            "Potential integrity impact"
        ),
        "availability": (
            "Potential availability impact"
        ),
        "scope": (
            "Potential scope expansion"
        ),
        "privilege": (
            "Potential privilege impact"
        ),
        "persistence": (
            "Potential persistence impact"
        ),
    }

    evidence = []

    for name, value in dimensions.items():
        value = _validate_score(
            value,
            name,
        )

        if value >= threshold:
            evidence.append(
                f"{labels.get(name, name)} "
                f"(magnitude={value:.2f})"
            )

    return evidence


@dataclass(frozen=True)
class ConsequenceEstimate:
    """
    Immutable BCSE security consequence estimate.

    The estimate describes potential consequence magnitude and
    confidence. It is not a security decision.
    """

    scenario_id: str
    consequence_score: float
    consequence_level: str
    confidence: str
    dimensions: Dict[str, float]
    evidence: List[str] = field(
        default_factory=list
    )
    assumptions: List[str] = field(
        default_factory=list
    )


class SecurityConsequenceEstimator:
    """
    Deterministic BCSE consequence estimator.

    It consumes normalized consequence dimensions and produces an
    explainable consequence estimate.
    """

    def __init__(
        self,
        weights: Optional[Mapping[str, float]] = None,
        evidence_threshold: float = 40.0,
    ) -> None:
        self.weights = _validate_weights(
            weights or DEFAULT_WEIGHTS
        )

        self.evidence_threshold = _validate_score(
            evidence_threshold,
            "evidence_threshold",
        )

    def estimate(
        self,
        scenario_id: str,
        dimensions: Mapping[str, float],
        *,
        evidence: Optional[List[str]] = None,
        assumptions: Optional[List[str]] = None,
    ) -> ConsequenceEstimate:
        """
        Estimate potential security consequence magnitude.
        """
        scenario_id = _validate_text(
            scenario_id,
            "scenario_id",
        )

        if not dimensions:
            raise ValueError(
                "dimensions cannot be empty"
            )

        validated_dimensions = {
            name: _validate_score(
                value,
                name,
            )
            for name, value in dimensions.items()
        }

        evidence_list = list(
            evidence or []
        )

        assumptions_list = list(
            assumptions or []
        )

        score = aggregate_consequence(
            validated_dimensions,
            self.weights,
        )

        level = classify_consequence(
            score
        )

        confidence = classify_confidence(
            len(evidence_list),
            len(assumptions_list),
        )

        generated_evidence = (
            identify_consequence_evidence(
                validated_dimensions,
                self.evidence_threshold,
            )
        )

        combined_evidence = (
            evidence_list
            + generated_evidence
        )

        return ConsequenceEstimate(
            scenario_id=scenario_id,
            consequence_score=round(
                score,
                4,
            ),
            consequence_level=level,
            confidence=confidence,
            dimensions=dict(
                validated_dimensions
            ),
            evidence=combined_evidence,
            assumptions=list(
                assumptions_list
            ),
        )