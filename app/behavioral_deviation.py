"""
Varynx Day 48
Behavioral Deviation Detection Engine

This module detects deviation between an agent's current behavioral
profile and its established behavioral baseline.

Design principles:
- deterministic
- explainable
- bounded
- evidence-oriented
- independent of authorization decisions
- independent of adaptive response
- does not infer malicious intent
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Dict, Iterable, List, Mapping, Optional


DEVIATION_MIN = 0.0
DEVIATION_MAX = 100.0

DEFAULT_WEIGHTS: Dict[str, float] = {
    "action_deviation": 0.25,
    "resource_deviation": 0.20,
    "context_deviation": 0.20,
    "authorization_deviation": 0.20,
    "temporal_deviation": 0.15,
}

DEVIATION_LEVELS = (
    "NONE",
    "LOW",
    "MODERATE",
    "HIGH",
    "CRITICAL",
)


def _validate_score(value: float, field_name: str) -> float:
    """Validate a bounded deviation dimension."""
    if not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be numeric")

    value = float(value)

    if value < DEVIATION_MIN or value > DEVIATION_MAX:
        raise ValueError(
            f"{field_name} must be between "
            f"{DEVIATION_MIN} and {DEVIATION_MAX}"
        )

    return value


def _validate_weights(weights: Mapping[str, float]) -> Dict[str, float]:
    """Validate and normalize deviation weights."""
    if not weights:
        raise ValueError("weights cannot be empty")

    validated = {}

    for name, weight in weights.items():
        if not isinstance(weight, (int, float)):
            raise TypeError(f"Weight for {name} must be numeric")

        weight = float(weight)

        if weight < 0:
            raise ValueError(f"Weight for {name} cannot be negative")

        validated[name] = weight

    total = sum(validated.values())

    if total <= 0:
        raise ValueError("Weight total must be greater than zero")

    return {
        name: weight / total
        for name, weight in validated.items()
    }


def calculate_deviation(
    baseline: float,
    current: float,
) -> float:
    """
    Calculate absolute behavioral deviation.

    Both baseline and current are represented on a 0-100 scale.

    The result is the absolute distance between the two values.
    """
    baseline = _validate_score(baseline, "baseline")
    current = _validate_score(current, "current")

    return abs(current - baseline)


def calculate_relative_deviation(
    baseline: float,
    current: float,
) -> float:
    """
    Calculate relative deviation normalized to a 0-100 scale.

    A baseline of zero is handled deterministically:
    - current == 0 -> 0 deviation
    - current > 0  -> 100 deviation
    """
    baseline = _validate_score(baseline, "baseline")
    current = _validate_score(current, "current")

    if baseline == 0:
        return 0.0 if current == 0 else 100.0

    deviation = abs(current - baseline) / baseline * 100.0

    return max(
        DEVIATION_MIN,
        min(DEVIATION_MAX, deviation),
    )


def aggregate_deviation(
    dimensions: Mapping[str, float],
    weights: Optional[Mapping[str, float]] = None,
) -> float:
    """
    Calculate a weighted behavioral deviation score.

    Missing dimensions are excluded and the remaining weights are
    renormalized.

    No dimensions produces zero deviation.
    """
    if not dimensions:
        return 0.0

    selected = {}

    for name, value in dimensions.items():
        selected[name] = _validate_score(value, name)

    if weights is None:
        weights = DEFAULT_WEIGHTS

    normalized_weights = _validate_weights(weights)

    applicable = {
        name: value
        for name, value in selected.items()
        if name in normalized_weights
    }

    if not applicable:
        return 0.0

    applicable_weights = {
        name: normalized_weights[name]
        for name in applicable
    }

    weight_total = sum(applicable_weights.values())

    return sum(
        applicable[name] * applicable_weights[name]
        for name in applicable
    ) / weight_total


def classify_deviation(score: float) -> str:
    """Classify a deviation score into an explainable band."""
    score = _validate_score(score, "score")

    if score < 20:
        return "NONE"

    if score < 40:
        return "LOW"

    if score < 60:
        return "MODERATE"

    if score < 80:
        return "HIGH"

    return "CRITICAL"


def identify_deviation_evidence(
    dimensions: Mapping[str, float],
    threshold: float = 40.0,
) -> List[str]:
    """
    Convert dimension scores into human-readable evidence.

    This function describes observed deviation. It does not claim
    malicious intent.
    """
    threshold = _validate_score(threshold, "threshold")

    evidence = []

    labels = {
        "action_deviation": "Action pattern changed",
        "resource_deviation": "Resource usage pattern changed",
        "context_deviation": "Execution context changed",
        "authorization_deviation": "Authorization behavior changed",
        "temporal_deviation": "Temporal activity pattern changed",
    }

    for name, value in dimensions.items():
        value = _validate_score(value, name)

        if value >= threshold:
            label = labels.get(
                name,
                f"{name.replace('_', ' ').capitalize()} detected",
            )

            evidence.append(
                f"{label} (deviation={value:.2f})"
            )

    return evidence


@dataclass(frozen=True)
class DeviationSnapshot:
    """Immutable representation of one deviation evaluation."""

    agent_id: str
    deviation_score: float
    deviation_level: str
    dimensions: Dict[str, float]
    evidence: List[str]
    update_index: int


class BehavioralDeviationDetector:
    """
    Stateful behavioral deviation detector.

    The detector maintains a baseline for each agent and evaluates
    future observations against that baseline.

    It deliberately does not:
    - authorize requests
    - block agents
    - modify trust
    - trigger adaptive response
    - infer attacker intent
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

        self._baselines: Dict[str, Dict[str, float]] = {}
        self._snapshots: Dict[str, List[DeviationSnapshot]] = {}
        self._update_counts: Dict[str, int] = {}

    def set_baseline(
        self,
        agent_id: str,
        dimensions: Mapping[str, float],
    ) -> None:
        """Set or replace the behavioral baseline for an agent."""
        if not agent_id or not isinstance(agent_id, str):
            raise ValueError("agent_id must be a non-empty string")

        if not dimensions:
            raise ValueError("dimensions cannot be empty")

        validated = {
            name: _validate_score(value, name)
            for name, value in dimensions.items()
        }

        self._baselines[agent_id] = validated

    def get_baseline(
        self,
        agent_id: str,
    ) -> Optional[Dict[str, float]]:
        """Return a defensive copy of an agent baseline."""
        baseline = self._baselines.get(agent_id)

        if baseline is None:
            return None

        return dict(baseline)

    def detect(
        self,
        agent_id: str,
        current_dimensions: Mapping[str, float],
    ) -> DeviationSnapshot:
        """
        Compare current behavioral dimensions with the stored baseline.
        """
        if not agent_id or not isinstance(agent_id, str):
            raise ValueError("agent_id must be a non-empty string")

        if not current_dimensions:
            raise ValueError("current_dimensions cannot be empty")

        baseline = self._baselines.get(agent_id)

        if baseline is None:
            raise ValueError(
                f"No behavioral baseline exists for agent '{agent_id}'"
            )

        validated_current = {
            name: _validate_score(value, name)
            for name, value in current_dimensions.items()
        }

        dimensions = {}

        for name, current_value in validated_current.items():
            if name not in baseline:
                continue

            dimensions[name] = calculate_deviation(
                baseline[name],
                current_value,
            )

        score = aggregate_deviation(
            dimensions,
            self.weights,
        )

        level = classify_deviation(score)

        evidence = identify_deviation_evidence(
            dimensions,
            self.evidence_threshold,
        )

        index = self._update_counts.get(agent_id, 0) + 1
        self._update_counts[agent_id] = index

        snapshot = DeviationSnapshot(
            agent_id=agent_id,
            deviation_score=round(score, 4),
            deviation_level=level,
            dimensions=dict(dimensions),
            evidence=list(evidence),
            update_index=index,
        )

        self._snapshots.setdefault(agent_id, []).append(snapshot)

        return snapshot

    def history(
        self,
        agent_id: str,
    ) -> List[DeviationSnapshot]:
        """Return deviation evaluation history."""
        return list(self._snapshots.get(agent_id, []))

    def latest(
        self,
        agent_id: str,
    ) -> Optional[DeviationSnapshot]:
        """Return the most recent deviation evaluation."""
        history = self._snapshots.get(agent_id, [])

        if not history:
            return None

        return history[-1]

    def reset(
        self,
        agent_id: Optional[str] = None,
    ) -> None:
        """
        Reset detector state.

        If agent_id is supplied, only that agent is reset.
        Otherwise all detector state is cleared.
        """
        if agent_id is None:
            self._baselines.clear()
            self._snapshots.clear()
            self._update_counts.clear()
            return

        self._baselines.pop(agent_id, None)
        self._snapshots.pop(agent_id, None)
        self._update_counts.pop(agent_id, None)