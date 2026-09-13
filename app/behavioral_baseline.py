"""
Varynx Day 49
Adaptive Behavioral Baseline Management.

This module maintains controlled behavioral baselines for autonomous
AI agents.

The baseline adapts gradually to accepted observations while
preventing high-deviation observations from immediately redefining
normal behavior.

This module does not:
- authorize requests
- block agents
- change permissions
- modify dynamic trust
- trigger adaptive response
- infer malicious intent
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional


SCORE_MIN = 0.0
SCORE_MAX = 100.0

DEFAULT_LEARNING_RATE = 0.10
DEFAULT_MAX_LEARNING_DEVIATION = 30.0


def _validate_score(value: float, field_name: str) -> float:
    """Validate a normalized behavioral value."""
    if not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be numeric")

    value = float(value)

    if value < SCORE_MIN or value > SCORE_MAX:
        raise ValueError(
            f"{field_name} must be between "
            f"{SCORE_MIN} and {SCORE_MAX}"
        )

    return value


def _validate_learning_rate(value: float) -> float:
    """Validate the baseline learning rate."""
    if not isinstance(value, (int, float)):
        raise TypeError("learning_rate must be numeric")

    value = float(value)

    if value <= 0 or value > 1:
        raise ValueError(
            "learning_rate must be greater than 0 and at most 1"
        )

    return value


def _validate_threshold(value: float) -> float:
    """Validate the maximum deviation learning threshold."""
    return _validate_score(
        value,
        "max_learning_deviation",
    )


def _validate_dimensions(
    dimensions: Mapping[str, float],
) -> Dict[str, float]:
    """Validate and copy behavioral dimensions."""
    if not dimensions:
        raise ValueError("dimensions cannot be empty")

    return {
        name: _validate_score(value, name)
        for name, value in dimensions.items()
    }


def calculate_baseline_update(
    baseline: float,
    observation: float,
    learning_rate: float = DEFAULT_LEARNING_RATE,
) -> float:
    """
    Calculate one exponentially weighted baseline update.
    """
    baseline = _validate_score(baseline, "baseline")
    observation = _validate_score(observation, "observation")
    learning_rate = _validate_learning_rate(learning_rate)

    updated = (
        (1.0 - learning_rate) * baseline
        + learning_rate * observation
    )

    return max(
        SCORE_MIN,
        min(SCORE_MAX, updated),
    )


def calculate_dimension_deviation(
    baseline: Mapping[str, float],
    observation: Mapping[str, float],
) -> Dict[str, float]:
    """
    Calculate absolute deviation for dimensions present in both
    baseline and observation.
    """
    if not baseline:
        raise ValueError("baseline cannot be empty")

    if not observation:
        raise ValueError("observation cannot be empty")

    deviations = {}

    for name, current_value in observation.items():
        if name not in baseline:
            continue

        base_value = _validate_score(
            baseline[name],
            f"baseline.{name}",
        )

        current_value = _validate_score(
            current_value,
            f"observation.{name}",
        )

        deviations[name] = abs(
            current_value - base_value
        )

    return deviations


def calculate_mean_deviation(
    baseline: Mapping[str, float],
    observation: Mapping[str, float],
) -> float:
    """
    Calculate mean absolute deviation across shared dimensions.
    """
    deviations = calculate_dimension_deviation(
        baseline,
        observation,
    )

    if not deviations:
        return 0.0

    return sum(deviations.values()) / len(deviations)


@dataclass(frozen=True)
class BaselineUpdate:
    """Immutable record describing one baseline update attempt."""

    agent_id: str
    accepted: bool
    mean_deviation: float
    previous_baseline: Dict[str, float]
    observation: Dict[str, float]
    updated_baseline: Dict[str, float]
    reason: str
    update_index: int


class AdaptiveBehavioralBaseline:
    """
    Controlled adaptive behavioral baseline manager.

    Observations are accepted for learning only when their mean
    deviation from the current baseline is within the configured
    learning threshold.
    """

    def __init__(
        self,
        learning_rate: float = DEFAULT_LEARNING_RATE,
        max_learning_deviation: float = DEFAULT_MAX_LEARNING_DEVIATION,
    ) -> None:
        self.learning_rate = _validate_learning_rate(
            learning_rate
        )

        self.max_learning_deviation = _validate_threshold(
            max_learning_deviation
        )

        self._baselines: Dict[str, Dict[str, float]] = {}
        self._history: Dict[str, List[BaselineUpdate]] = {}
        self._update_counts: Dict[str, int] = {}

    def set_baseline(
        self,
        agent_id: str,
        dimensions: Mapping[str, float],
    ) -> None:
        """Create or replace an agent baseline."""
        if not isinstance(agent_id, str) or not agent_id:
            raise ValueError(
                "agent_id must be a non-empty string"
            )

        self._baselines[agent_id] = _validate_dimensions(
            dimensions
        )

    def get_baseline(
        self,
        agent_id: str,
    ) -> Optional[Dict[str, float]]:
        """Return a defensive copy of the current baseline."""
        baseline = self._baselines.get(agent_id)

        if baseline is None:
            return None

        return dict(baseline)

    def observe(
        self,
        agent_id: str,
        observation: Mapping[str, float],
    ) -> BaselineUpdate:
        """
        Evaluate an observation and optionally adapt the baseline.
        """
        if not isinstance(agent_id, str) or not agent_id:
            raise ValueError(
                "agent_id must be a non-empty string"
            )

        baseline = self._baselines.get(agent_id)

        if baseline is None:
            raise ValueError(
                f"No baseline exists for agent '{agent_id}'"
            )

        observation = _validate_dimensions(observation)

        previous_baseline = dict(baseline)

        mean_deviation = calculate_mean_deviation(
            baseline,
            observation,
        )

        accepted = (
            mean_deviation
            <= self.max_learning_deviation
        )

        if accepted:
            updated_baseline = dict(baseline)

            for name, value in observation.items():
                if name not in baseline:
                    continue

                updated_baseline[name] = calculate_baseline_update(
                    baseline[name],
                    value,
                    self.learning_rate,
                )

            reason = (
                "Observation accepted for controlled baseline adaptation"
            )
        else:
            updated_baseline = dict(baseline)

            reason = (
                "Observation rejected because behavioral deviation "
                "exceeded the learning threshold"
            )

        self._baselines[agent_id] = updated_baseline

        index = self._update_counts.get(agent_id, 0) + 1
        self._update_counts[agent_id] = index

        result = BaselineUpdate(
            agent_id=agent_id,
            accepted=accepted,
            mean_deviation=round(mean_deviation, 4),
            previous_baseline=previous_baseline,
            observation=dict(observation),
            updated_baseline=dict(updated_baseline),
            reason=reason,
            update_index=index,
        )

        self._history.setdefault(agent_id, []).append(
            result
        )

        return result

    def history(
        self,
        agent_id: str,
    ) -> List[BaselineUpdate]:
        """Return baseline update history."""
        return list(
            self._history.get(agent_id, [])
        )

    def latest(
        self,
        agent_id: str,
    ) -> Optional[BaselineUpdate]:
        """Return the most recent update attempt."""
        history = self._history.get(agent_id, [])

        if not history:
            return None

        return history[-1]

    def reset(
        self,
        agent_id: Optional[str] = None,
    ) -> None:
        """Reset one agent or all baseline state."""
        if agent_id is None:
            self._baselines.clear()
            self._history.clear()
            self._update_counts.clear()
            return

        self._baselines.pop(agent_id, None)
        self._history.pop(agent_id, None)
        self._update_counts.pop(agent_id, None)