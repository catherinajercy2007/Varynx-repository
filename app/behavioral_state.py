"""
Varynx Day 47
Behavioral State Modeling

This module maintains a deterministic behavioral state profile for
autonomous AI agents.

Day 46 introduced Dynamic Behavioral Trust.

Day 47 introduces a behavioral state representation that describes
the current behavioral characteristics of an agent independently from
authorization and adaptive-response decisions.

Architectural boundary
----------------------
This module does NOT:
- authorize actions
- calculate adaptive-response decisions
- replace the existing risk engine
- infer malicious intent
- implement BCSE
- make unrestricted predictions

It provides structured behavioral state information that later
components can consume.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import isfinite
from typing import Any, Mapping


STATE_MIN = 0.0
STATE_MAX = 100.0
NEUTRAL_STATE = 50.0


DEFAULT_STATE_WEIGHTS: dict[str, float] = {
    "action_consistency": 0.20,
    "resource_consistency": 0.20,
    "context_consistency": 0.15,
    "authorization_consistency": 0.15,
    "temporal_consistency": 0.10,
    "behavioral_stability": 0.20,
}


def _number(value: Any, *, name: str) -> float:
    """Validate and convert a numeric value."""

    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")

    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{name} must be numeric"
        ) from exc

    if not isfinite(number):
        raise ValueError(
            f"{name} must be finite"
        )

    return number


def _clamp(
    value: float,
    minimum: float = STATE_MIN,
    maximum: float = STATE_MAX,
) -> float:
    return max(
        minimum,
        min(maximum, value),
    )


def _validate_agent_id(agent_id: str) -> str:
    if not isinstance(agent_id, str):
        raise TypeError(
            "agent_id must be a string"
        )

    normalized = agent_id.strip()

    if not normalized:
        raise ValueError(
            "agent_id must not be empty"
        )

    return normalized


def _validate_timestamp(
    timestamp: datetime | None,
) -> datetime:
    if timestamp is None:
        return datetime.now(timezone.utc)

    if not isinstance(timestamp, datetime):
        raise TypeError(
            "timestamp must be a datetime"
        )

    if timestamp.tzinfo is None:
        raise ValueError(
            "timestamp must be timezone-aware"
        )

    return timestamp.astimezone(timezone.utc)


def _validate_dimensions(
    dimensions: Mapping[str, Any] | None,
) -> dict[str, float]:
    """
    Validate behavioral state dimensions.

    Dimension values use:

        0   = strongly unstable / inconsistent
        50  = neutral
        100 = strongly stable / consistent
    """

    if dimensions is None:
        return {}

    if not isinstance(dimensions, Mapping):
        raise TypeError(
            "dimensions must be a mapping"
        )

    result: dict[str, float] = {}

    for key, raw_value in dimensions.items():

        if not isinstance(key, str):
            raise TypeError(
                "dimension names must be strings"
            )

        name = key.strip()

        if not name:
            raise ValueError(
                "dimension names must not be empty"
            )

        value = _number(
            raw_value,
            name=f"dimensions[{name!r}]",
        )

        if not STATE_MIN <= value <= STATE_MAX:
            raise ValueError(
                f"dimensions[{name!r}] must be between "
                f"{STATE_MIN} and {STATE_MAX}"
            )

        result[name] = value

    return result


def _validate_weights(
    weights: Mapping[str, Any],
) -> dict[str, float]:

    if not isinstance(weights, Mapping):
        raise TypeError(
            "weights must be a mapping"
        )

    result: dict[str, float] = {}

    for key, raw_value in weights.items():

        if not isinstance(key, str):
            raise TypeError(
                "weight names must be strings"
            )

        value = _number(
            raw_value,
            name=f"weights[{key!r}]",
        )

        if value < 0.0:
            raise ValueError(
                f"weights[{key!r}] cannot be negative"
            )

        result[key] = value

    if not result:
        raise ValueError(
            "weights must not be empty"
        )

    if sum(result.values()) <= 0.0:
        raise ValueError(
            "weights must have a positive total"
        )

    return result


def aggregate_behavioral_state(
    dimensions: Mapping[str, Any] | None,
    weights: Mapping[str, Any] | None = None,
) -> float:
    """
    Produce one bounded behavioral-state stability score.

    Missing dimensions are excluded from the denominator rather than
    being interpreted as negative behavioral evidence.
    """

    validated_dimensions = _validate_dimensions(
        dimensions
    )

    if not validated_dimensions:
        return NEUTRAL_STATE

    selected_weights = _validate_weights(
        weights or DEFAULT_STATE_WEIGHTS
    )

    numerator = 0.0
    denominator = 0.0

    for dimension, value in validated_dimensions.items():

        weight = selected_weights.get(
            dimension
        )

        if weight is None or weight <= 0.0:
            continue

        numerator += value * weight
        denominator += weight

    if denominator <= 0.0:
        return NEUTRAL_STATE

    return round(
        _clamp(
            numerator / denominator
        ),
        4,
    )


def calculate_deviation(
    current_score: float,
    reference_score: float,
) -> float:
    """
    Calculate absolute deviation from a reference state.

    Result range:

        0   = no deviation
        100 = maximum possible deviation
    """

    current = _number(
        current_score,
        name="current_score",
    )

    reference = _number(
        reference_score,
        name="reference_score",
    )

    if not STATE_MIN <= current <= STATE_MAX:
        raise ValueError(
            "current_score must be between 0 and 100"
        )

    if not STATE_MIN <= reference <= STATE_MAX:
        raise ValueError(
            "reference_score must be between 0 and 100"
        )

    return round(
        abs(current - reference),
        4,
    )


def calculate_stability(
    scores: list[float] | tuple[float, ...],
) -> float:
    """
    Calculate behavioral stability from a sequence of scores.

    Stability is derived from score dispersion.

    A perfectly stable sequence has stability 100.

    A maximally dispersed sequence approaches stability 0.
    """

    if not isinstance(scores, (list, tuple)):
        raise TypeError(
            "scores must be a list or tuple"
        )

    if not scores:
        return NEUTRAL_STATE

    validated = []

    for index, score in enumerate(scores):
        value = _number(
            score,
            name=f"scores[{index}]",
        )

        if not STATE_MIN <= value <= STATE_MAX:
            raise ValueError(
                f"scores[{index}] must be between 0 and 100"
            )

        validated.append(value)

    if len(validated) == 1:
        return 100.0

    mean = sum(validated) / len(validated)

    mean_absolute_deviation = (
        sum(
            abs(score - mean)
            for score in validated
        )
        / len(validated)
    )

    stability = STATE_MAX - (
        mean_absolute_deviation * 2.0
    )

    return round(
        _clamp(stability),
        4,
    )


def classify_behavioral_state(
    stability_score: float,
) -> str:
    """
    Convert behavioral stability into an interpretable state.
    """

    score = _number(
        stability_score,
        name="stability_score",
    )

    if not STATE_MIN <= score <= STATE_MAX:
        raise ValueError(
            "stability_score must be between 0 and 100"
        )

    if score >= 80.0:
        return "STABLE"

    if score >= 60.0:
        return "MOSTLY_STABLE"

    if score >= 40.0:
        return "VARIABLE"

    if score >= 20.0:
        return "UNSTABLE"

    return "HIGHLY_UNSTABLE"


@dataclass(frozen=True)
class BehavioralStateSnapshot:
    """
    Immutable behavioral-state representation.
    """

    agent_id: str
    state_score: float
    state_class: str
    dimensions: dict[str, float]
    stability_score: float
    deviation_from_reference: float
    timestamp: str
    update_index: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class _BehavioralState:
    agent_id: str
    state_score: float = NEUTRAL_STATE
    stability_score: float = NEUTRAL_STATE
    reference_score: float = NEUTRAL_STATE
    update_index: int = 0
    history_scores: list[float] | None = None
    last_timestamp: datetime | None = None


class BehavioralStateModel:
    """
    Stateful deterministic behavioral state model.

    Each agent receives an independent behavioral state.

    The model maintains:
    - current state score
    - behavioral stability
    - reference state
    - update history
    - immutable snapshots
    """

    def __init__(
        self,
        *,
        weights: Mapping[str, Any] | None = None,
        history_window: int = 10,
        reference_score: float = NEUTRAL_STATE,
    ) -> None:

        self.weights = _validate_weights(
            weights or DEFAULT_STATE_WEIGHTS
        )

        if isinstance(history_window, bool):
            raise ValueError(
                "history_window must be an integer"
            )

        if not isinstance(history_window, int):
            raise TypeError(
                "history_window must be an integer"
            )

        if history_window <= 0:
            raise ValueError(
                "history_window must be greater than zero"
            )

        self.history_window = history_window

        self.reference_score = _number(
            reference_score,
            name="reference_score",
        )

        if not STATE_MIN <= self.reference_score <= STATE_MAX:
            raise ValueError(
                "reference_score must be between 0 and 100"
            )

        self._states: dict[
            str,
            _BehavioralState,
        ] = {}

        self._snapshots: dict[
            str,
            list[BehavioralStateSnapshot],
        ] = {}

    def _get_or_create(
        self,
        agent_id: str,
    ) -> _BehavioralState:

        if agent_id not in self._states:

            self._states[agent_id] = _BehavioralState(
                agent_id=agent_id,
                reference_score=self.reference_score,
                history_scores=[],
            )

        return self._states[agent_id]

    def update(
        self,
        agent_id: str,
        dimensions: Mapping[str, Any] | None,
        *,
        timestamp: datetime | None = None,
        reference_score: float | None = None,
    ) -> BehavioralStateSnapshot:

        normalized_agent_id = _validate_agent_id(
            agent_id
        )

        validated_dimensions = _validate_dimensions(
            dimensions
        )

        current_time = _validate_timestamp(
            timestamp
        )

        state = self._get_or_create(
            normalized_agent_id
        )

        if (
            state.last_timestamp is not None
            and current_time < state.last_timestamp
        ):
            raise ValueError(
                "timestamp cannot move backwards"
            )

        current_score = aggregate_behavioral_state(
            validated_dimensions,
            self.weights,
        )

        history = state.history_scores or []

        history.append(current_score)

        if len(history) > self.history_window:
            history = history[
                -self.history_window:
            ]

        state.history_scores = history

        stability_score = calculate_stability(
            history
        )

        reference = (
            state.reference_score
            if reference_score is None
            else _number(
                reference_score,
                name="reference_score",
            )
        )

        if not STATE_MIN <= reference <= STATE_MAX:
            raise ValueError(
                "reference_score must be between 0 and 100"
            )

        state.reference_score = reference

        deviation = calculate_deviation(
            current_score,
            reference,
        )

        state.state_score = current_score
        state.stability_score = stability_score
        state.update_index += 1
        state.last_timestamp = current_time

        snapshot = BehavioralStateSnapshot(
            agent_id=normalized_agent_id,
            state_score=state.state_score,
            state_class=classify_behavioral_state(
                state.stability_score
            ),
            dimensions=dict(
                validated_dimensions
            ),
            stability_score=state.stability_score,
            deviation_from_reference=deviation,
            timestamp=current_time.isoformat(),
            update_index=state.update_index,
        )

        self._snapshots.setdefault(
            normalized_agent_id,
            [],
        ).append(snapshot)

        return snapshot

    def get_state_score(
        self,
        agent_id: str,
    ) -> float:

        normalized_agent_id = _validate_agent_id(
            agent_id
        )

        state = self._states.get(
            normalized_agent_id
        )

        if state is None:
            return NEUTRAL_STATE

        return state.state_score

    def get_stability(
        self,
        agent_id: str,
    ) -> float:

        normalized_agent_id = _validate_agent_id(
            agent_id
        )

        state = self._states.get(
            normalized_agent_id
        )

        if state is None:
            return NEUTRAL_STATE

        return state.stability_score

    def get_snapshot(
        self,
        agent_id: str,
    ) -> BehavioralStateSnapshot | None:

        normalized_agent_id = _validate_agent_id(
            agent_id
        )

        snapshots = self._snapshots.get(
            normalized_agent_id,
            [],
        )

        if not snapshots:
            return None

        return snapshots[-1]

    def get_history(
        self,
        agent_id: str,
    ) -> tuple[BehavioralStateSnapshot, ...]:

        normalized_agent_id = _validate_agent_id(
            agent_id
        )

        return tuple(
            self._snapshots.get(
                normalized_agent_id,
                [],
            )
        )

    def reset(
        self,
        agent_id: str,
    ) -> None:

        normalized_agent_id = _validate_agent_id(
            agent_id
        )

        self._states.pop(
            normalized_agent_id,
            None,
        )

        self._snapshots.pop(
            normalized_agent_id,
            None,
        )


__all__ = [
    "STATE_MIN",
    "STATE_MAX",
    "NEUTRAL_STATE",
    "DEFAULT_STATE_WEIGHTS",
    "BehavioralStateSnapshot",
    "BehavioralStateModel",
    "aggregate_behavioral_state",
    "calculate_deviation",
    "calculate_stability",
    "classify_behavioral_state",
]