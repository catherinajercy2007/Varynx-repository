"""
Varynx Predictive Security Signal
Day 56 - Predictive Behavioral Control Foundation

Purpose:
    Generate a deterministic, explainable forward-looking security signal
    from observed behavioral and security indicators.

This module does NOT:
    - infer malicious intent
    - execute hypothetical actions
    - authorize actions
    - block agents
    - replace the existing risk engine
    - replace adaptive response

It provides a predictive signal only.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional, Tuple


SCORE_MIN = 0.0
SCORE_MAX = 100.0

SIGNAL_LEVELS = (
    "LOW",
    "MODERATE",
    "HIGH",
    "CRITICAL",
)

TRAJECTORIES = (
    "IMPROVING",
    "STABLE",
    "DETERIORATING",
)

CONFIDENCE_LEVELS = (
    "LOW",
    "MODERATE",
    "HIGH",
)

DEFAULT_WEIGHTS = {
    "behavioral_deviation": 0.25,
    "trust_decline": 0.20,
    "state_instability": 0.20,
    "consequence_exposure": 0.20,
    "behavioral_acceleration": 0.15,
}


def _validate_score(value: float, name: str) -> float:
    """Validate a score in the range 0-100."""

    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")

    value = float(value)

    if value < SCORE_MIN or value > SCORE_MAX:
        raise ValueError(
            f"{name} must be between "
            f"{SCORE_MIN} and {SCORE_MAX}"
        )

    return value


def _validate_weights(
    weights: Mapping[str, float],
) -> Dict[str, float]:
    """Validate predictive signal weights."""

    if not isinstance(weights, Mapping):
        raise TypeError("weights must be a mapping")

    if not weights:
        raise ValueError("weights must not be empty")

    normalized: Dict[str, float] = {}

    for name, weight in weights.items():

        if not isinstance(name, str):
            raise TypeError("weight names must be strings")

        if not isinstance(weight, (int, float)):
            raise TypeError(
                f"weight for {name} must be numeric"
            )

        weight = float(weight)

        if weight < 0:
            raise ValueError(
                f"weight for {name} must not be negative"
            )

        normalized[name] = weight

    total = sum(normalized.values())

    if total <= 0:
        raise ValueError(
            "weights must contain a positive total"
        )

    return normalized


def classify_signal(score: float) -> str:
    """
    Classify predictive security signal.

    <20   LOW
    <40   MODERATE
    <70   HIGH
    >=70  CRITICAL
    """

    score = _validate_score(score, "score")

    if score < 20:
        return "LOW"

    if score < 40:
        return "MODERATE"

    if score < 70:
        return "HIGH"

    return "CRITICAL"


def calculate_trajectory(
    previous_score: float,
    current_score: float,
    tolerance: float = 5.0,
) -> str:
    """
    Determine predictive security trajectory.
    """

    previous_score = _validate_score(
        previous_score,
        "previous_score",
    )

    current_score = _validate_score(
        current_score,
        "current_score",
    )

    if not isinstance(tolerance, (int, float)):
        raise TypeError("tolerance must be numeric")

    tolerance = float(tolerance)

    if tolerance < 0:
        raise ValueError(
            "tolerance must not be negative"
        )

    delta = current_score - previous_score

    if delta > tolerance:
        return "DETERIORATING"

    if delta < -tolerance:
        return "IMPROVING"

    return "STABLE"


def calculate_acceleration(
    previous_score: float,
    current_score: float,
    older_score: Optional[float] = None,
) -> float:
    """
    Calculate the predictive security movement.

    The Day 56 signal uses the change between observations.

    With two observations:

        current - previous

    When an older observation is supplied, the function intentionally
    uses the movement from older to current. This keeps the public
    helper simple, deterministic, bounded, and consistent with the
    Day 56 predictive signal semantics.
    """

    previous_score = _validate_score(
        previous_score,
        "previous_score",
    )

    current_score = _validate_score(
        current_score,
        "current_score",
    )

    if older_score is None:
        result = current_score - previous_score
    else:
        older_score = _validate_score(
            older_score,
            "older_score",
        )

        result = current_score - older_score

    return max(
        -100.0,
        min(100.0, result),
    )


def calculate_confidence(
    observation_count: int,
) -> str:
    """
    Determine confidence from available observations.

    1 observation  -> LOW
    2 observations -> MODERATE
    3+ observations -> HIGH
    """

    if not isinstance(observation_count, int):
        raise TypeError(
            "observation_count must be an integer"
        )

    if observation_count < 1:
        raise ValueError(
            "observation_count must be at least 1"
        )

    if observation_count >= 3:
        return "HIGH"

    if observation_count == 2:
        return "MODERATE"

    return "LOW"


def calculate_predictive_signal(
    dimensions: Mapping[str, float],
    weights: Optional[Mapping[str, float]] = None,
) -> float:
    """
    Calculate weighted predictive security signal.

    Missing dimensions are excluded and remaining weights are
    renormalized.
    """

    if not isinstance(dimensions, Mapping):
        raise TypeError(
            "dimensions must be a mapping"
        )

    if not dimensions:
        raise ValueError(
            "dimensions must not be empty"
        )

    active_weights = _validate_weights(
        weights or DEFAULT_WEIGHTS
    )

    weighted_total = 0.0
    weight_total = 0.0

    for name, weight in active_weights.items():

        if name not in dimensions:
            continue

        score = _validate_score(
            dimensions[name],
            f"dimensions[{name}]",
        )

        weighted_total += score * weight
        weight_total += weight

    if weight_total <= 0:
        raise ValueError(
            "No valid predictive dimensions were supplied"
        )

    result = weighted_total / weight_total

    return max(
        SCORE_MIN,
        min(SCORE_MAX, result),
    )


def build_predictive_evidence(
    dimensions: Mapping[str, float],
    trajectory: str,
) -> Tuple[str, ...]:
    """
    Generate deterministic explanatory evidence.
    """

    if trajectory not in TRAJECTORIES:
        raise ValueError(
            f"Unknown trajectory: {trajectory}"
        )

    evidence: List[str] = []

    for name, score in dimensions.items():

        score = _validate_score(
            score,
            f"dimensions[{name}]",
        )

        if score >= 70:
            evidence.append(
                f"{name} is strongly elevated"
            )

        elif score >= 40:
            evidence.append(
                f"{name} is moderately elevated"
            )

    if trajectory == "DETERIORATING":
        evidence.append(
            "Security signal trajectory is deteriorating"
        )

    elif trajectory == "IMPROVING":
        evidence.append(
            "Security signal trajectory is improving"
        )

    else:
        evidence.append(
            "Security signal trajectory is stable"
        )

    return tuple(evidence)


@dataclass(frozen=True)
class PredictiveSecuritySnapshot:
    """
    Immutable predictive security result.
    """

    agent_id: str
    predictive_score: float
    signal_level: str
    trajectory: str
    confidence: str
    dimensions: Tuple[Tuple[str, float], ...]
    evidence: Tuple[str, ...]
    observation_count: int


class PredictiveSecurityEngine:
    """
    Deterministic predictive security signal engine.

    Prediction history is maintained independently for each agent.
    """

    def __init__(
        self,
        weights: Optional[Mapping[str, float]] = None,
    ) -> None:

        self._weights = _validate_weights(
            weights or DEFAULT_WEIGHTS
        )

        self._history: Dict[
            str,
            List[PredictiveSecuritySnapshot],
        ] = {}

    def predict(
        self,
        *,
        agent_id: str,
        dimensions: Mapping[str, float],
        consequence_exposure: Optional[float] = None,
    ) -> PredictiveSecuritySnapshot:
        """
        Generate a predictive security snapshot.
        """

        if not isinstance(agent_id, str):
            raise TypeError(
                "agent_id must be a string"
            )

        if not agent_id.strip():
            raise ValueError(
                "agent_id must not be empty"
            )

        if not isinstance(dimensions, Mapping):
            raise TypeError(
                "dimensions must be a mapping"
            )

        normalized = dict(dimensions)

        if consequence_exposure is not None:
            normalized["consequence_exposure"] = (
                consequence_exposure
            )

        if not normalized:
            raise ValueError(
                "dimensions must not be empty"
            )

        for name, value in normalized.items():
            _validate_score(
                value,
                f"dimensions[{name}]",
            )

        previous_history = self._history.get(
            agent_id,
            [],
        )

        previous_score = (
            previous_history[-1].predictive_score
            if previous_history
            else None
        )

        predictive_score = calculate_predictive_signal(
            normalized,
            self._weights,
        )

        if previous_score is None:
            trajectory = "STABLE"
        else:
            trajectory = calculate_trajectory(
                previous_score,
                predictive_score,
            )

        observation_count = (
            len(previous_history) + 1
        )

        confidence = calculate_confidence(
            observation_count
        )

        evidence = build_predictive_evidence(
            normalized,
            trajectory,
        )

        snapshot = PredictiveSecuritySnapshot(
            agent_id=agent_id,
            predictive_score=predictive_score,
            signal_level=classify_signal(
                predictive_score
            ),
            trajectory=trajectory,
            confidence=confidence,
            dimensions=tuple(
                sorted(
                    (
                        str(name),
                        float(value),
                    )
                    for name, value
                    in normalized.items()
                )
            ),
            evidence=evidence,
            observation_count=observation_count,
        )

        self._history.setdefault(
            agent_id,
            [],
        ).append(snapshot)

        return snapshot

    def history(
        self,
        agent_id: str,
    ) -> Tuple[PredictiveSecuritySnapshot, ...]:
        """Return immutable prediction history."""

        if not isinstance(agent_id, str):
            raise TypeError(
                "agent_id must be a string"
            )

        return tuple(
            self._history.get(
                agent_id,
                [],
            )
        )

    def latest(
        self,
        agent_id: str,
    ) -> Optional[PredictiveSecuritySnapshot]:
        """Return latest prediction."""

        history = self.history(agent_id)

        if not history:
            return None

        return history[-1]

    def history_count(
        self,
        agent_id: str,
    ) -> int:
        """Return prediction count."""

        return len(
            self.history(agent_id)
        )

    def reset(
        self,
        agent_id: Optional[str] = None,
    ) -> None:
        """
        Reset prediction history.

        If agent_id is provided, reset only that agent.
        Otherwise reset all agents.
        """

        if agent_id is None:
            self._history.clear()
            return

        if not isinstance(agent_id, str):
            raise TypeError(
                "agent_id must be a string"
            )

        self._history.pop(
            agent_id,
            None,
        )


__all__ = [
    "SCORE_MIN",
    "SCORE_MAX",
    "SIGNAL_LEVELS",
    "TRAJECTORIES",
    "CONFIDENCE_LEVELS",
    "DEFAULT_WEIGHTS",
    "PredictiveSecuritySnapshot",
    "PredictiveSecurityEngine",
    "calculate_predictive_signal",
    "calculate_trajectory",
    "calculate_acceleration",
    "calculate_confidence",
    "classify_signal",
    "build_predictive_evidence",
]