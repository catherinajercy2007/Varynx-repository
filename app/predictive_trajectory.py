"""
Varynx Day 57 - Predictive Behavioral Trajectory

Purpose:
    Analyze the direction and stability of an agent's behavioral security
    observations over time.

Architectural boundary:
    This module describes behavioral trajectory. It does not:
    - authorize actions
    - block agents
    - modify adaptive response
    - infer malicious intent
    - predict exact attacker behavior
    - replace the existing risk engine
    - create a new global Varynx risk score
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Mapping, Sequence


SCORE_MIN = 0.0
SCORE_MAX = 100.0

DEFAULT_STABILITY_TOLERANCE = 5.0
DEFAULT_MIN_OBSERVATIONS = 2

DIRECTION_IMPROVING = "IMPROVING"
DIRECTION_STABLE = "STABLE"
DIRECTION_DETERIORATING = "DETERIORATING"
DIRECTION_INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

STABILITY_STABLE = "STABLE"
STABILITY_VARIABLE = "VARIABLE"

TRAJECTORY_IMPROVING = DIRECTION_IMPROVING
TRAJECTORY_STABLE = DIRECTION_STABLE
TRAJECTORY_DETERIORATING = DIRECTION_DETERIORATING


def _validate_score(value: float, field_name: str = "score") -> float:
    """Validate and normalize a security score."""
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


def _validate_tolerance(value: float) -> float:
    """Validate trajectory tolerance."""
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("tolerance must be numeric") from exc

    if not isfinite(value):
        raise ValueError("tolerance must be finite")

    if value < 0:
        raise ValueError("tolerance must be non-negative")

    return value


def _validate_min_observations(value: int) -> int:
    """Validate minimum observation count."""
    if isinstance(value, bool):
        raise ValueError("min_observations must be an integer")

    try:
        value = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("min_observations must be an integer") from exc

    if value < 2:
        raise ValueError("min_observations must be at least 2")

    return value


def _validate_history(
    observations: Iterable[float],
) -> list[float]:
    """Validate a sequence of behavioral observations."""
    if observations is None:
        raise ValueError("observations cannot be None")

    try:
        values = list(observations)
    except TypeError as exc:
        raise ValueError("observations must be iterable") from exc

    return [
        _validate_score(value, f"observation[{index}]")
        for index, value in enumerate(values)
    ]


def calculate_slope(
    observations: Sequence[float],
) -> float:
    """
    Calculate the average change between the first and last observation.

    Positive slope:
        Increasing signal.

    Negative slope:
        Decreasing signal.

    Zero:
        No net change.

    The function assumes observations are ordered chronologically.
    """
    values = _validate_history(observations)

    if len(values) < 2:
        return 0.0

    return (values[-1] - values[0]) / (len(values) - 1)


def calculate_mean_change(
    observations: Sequence[float],
) -> float:
    """
    Calculate the mean signed change between consecutive observations.
    """
    values = _validate_history(observations)

    if len(values) < 2:
        return 0.0

    changes = [
        values[index] - values[index - 1]
        for index in range(1, len(values))
    ]

    return sum(changes) / len(changes)


def calculate_volatility(
    observations: Sequence[float],
) -> float:
    """
    Calculate mean absolute change between consecutive observations.

    Higher values indicate more behavioral movement.
    """
    values = _validate_history(observations)

    if len(values) < 2:
        return 0.0

    changes = [
        abs(values[index] - values[index - 1])
        for index in range(1, len(values))
    ]

    return sum(changes) / len(changes)


def classify_direction(
    slope: float,
    tolerance: float = DEFAULT_STABILITY_TOLERANCE,
) -> str:
    """
    Classify trajectory direction from the observed slope.

    |slope| <= tolerance:
        STABLE

    slope < -tolerance:
        IMPROVING

    slope > tolerance:
        DETERIORATING

    For predictive security signals, an increasing score is treated as
    deterioration because larger signal values represent greater security
    concern.
    """
    slope = float(slope)
    tolerance = _validate_tolerance(tolerance)

    if not isfinite(slope):
        raise ValueError("slope must be finite")

    if abs(slope) <= tolerance:
        return DIRECTION_STABLE

    if slope > tolerance:
        return DIRECTION_DETERIORATING

    return DIRECTION_IMPROVING


def classify_stability(
    volatility: float,
    tolerance: float = DEFAULT_STABILITY_TOLERANCE,
) -> str:
    """
    Describe whether the trajectory is stable or variable.
    """
    volatility = float(volatility)
    tolerance = _validate_tolerance(tolerance)

    if not isfinite(volatility):
        raise ValueError("volatility must be finite")

    if volatility <= tolerance:
        return STABILITY_STABLE

    return STABILITY_VARIABLE


def calculate_direction_confidence(
    observations: Sequence[float],
    slope: float,
    tolerance: float = DEFAULT_STABILITY_TOLERANCE,
) -> str:
    """
    Estimate confidence in trajectory direction from observation count
    and directional separation.

    This is confidence in the observed trajectory calculation, not
    confidence that a future event will actually occur.
    """
    values = _validate_history(observations)
    tolerance = _validate_tolerance(tolerance)

    if len(values) < 2:
        return "LOW"

    magnitude = abs(float(slope))

    if len(values) >= 5 and magnitude > tolerance * 2:
        return "HIGH"

    if len(values) >= 3 and magnitude > tolerance:
        return "MODERATE"

    return "LOW"


def build_trajectory_evidence(
    observations: Sequence[float],
    slope: float,
    volatility: float,
    direction: str,
    stability: str,
) -> list[str]:
    """Build deterministic evidence describing the calculated trajectory."""
    values = _validate_history(observations)

    evidence: list[str] = [
        f"Observed {len(values)} chronological behavioral observations",
        f"Trajectory slope: {float(slope):.2f}",
        f"Mean absolute change: {float(volatility):.2f}",
        f"Trajectory direction: {direction}",
        f"Trajectory stability: {stability}",
    ]

    if len(values) >= 2:
        evidence.append(
            f"Initial observation: {values[0]:.2f}"
        )
        evidence.append(
            f"Latest observation: {values[-1]:.2f}"
        )

    return evidence


@dataclass(frozen=True)
class BehavioralTrajectorySnapshot:
    """
    Immutable trajectory result for one agent.
    """

    agent_id: str
    observations: tuple[float, ...]
    observation_count: int
    initial_value: float | None
    latest_value: float | None
    slope: float
    mean_change: float
    volatility: float
    direction: str
    stability: str
    confidence: str
    evidence: tuple[str, ...]


class PredictiveBehavioralTrajectory:
    """
    Stateful per-agent trajectory analyzer.

    The class stores chronological observations and generates deterministic
    trajectory snapshots.

    It intentionally does not perform security control actions.
    """

    def __init__(
        self,
        tolerance: float = DEFAULT_STABILITY_TOLERANCE,
        min_observations: int = DEFAULT_MIN_OBSERVATIONS,
    ) -> None:
        self.tolerance = _validate_tolerance(tolerance)
        self.min_observations = _validate_min_observations(
            min_observations
        )

        self._history: dict[str, list[float]] = {}
        self._latest: dict[str, BehavioralTrajectorySnapshot] = {}

    def add_observation(
        self,
        agent_id: str,
        value: float,
    ) -> BehavioralTrajectorySnapshot:
        """Add one chronological observation and calculate a snapshot."""
        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError("agent_id must be a non-empty string")

        normalized_agent_id = agent_id.strip()
        normalized_value = _validate_score(value)

        self._history.setdefault(normalized_agent_id, []).append(
            normalized_value
        )

        snapshot = self.analyze(normalized_agent_id)
        return snapshot

    def add_observations(
        self,
        agent_id: str,
        observations: Iterable[float],
    ) -> BehavioralTrajectorySnapshot:
        """Add multiple observations in chronological order."""
        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError("agent_id must be a non-empty string")

        normalized_agent_id = agent_id.strip()
        values = _validate_history(observations)

        self._history.setdefault(normalized_agent_id, []).extend(values)

        return self.analyze(normalized_agent_id)

    def analyze(
        self,
        agent_id: str,
    ) -> BehavioralTrajectorySnapshot:
        """Analyze the current trajectory for an agent."""
        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError("agent_id must be a non-empty string")

        normalized_agent_id = agent_id.strip()
        observations = tuple(self._history.get(normalized_agent_id, []))

        if len(observations) < self.min_observations:
            snapshot = BehavioralTrajectorySnapshot(
                agent_id=normalized_agent_id,
                observations=observations,
                observation_count=len(observations),
                initial_value=(
                    observations[0] if observations else None
                ),
                latest_value=(
                    observations[-1] if observations else None
                ),
                slope=0.0,
                mean_change=0.0,
                volatility=0.0,
                direction=DIRECTION_INSUFFICIENT_DATA,
                stability=STABILITY_STABLE,
                confidence="LOW",
                evidence=(
                    f"Insufficient observations: "
                    f"{len(observations)}/{self.min_observations}",
                ),
            )

            self._latest[normalized_agent_id] = snapshot
            return snapshot

        slope = calculate_slope(observations)
        mean_change = calculate_mean_change(observations)
        volatility = calculate_volatility(observations)

        direction = classify_direction(
            slope,
            self.tolerance,
        )

        stability = classify_stability(
            volatility,
            self.tolerance,
        )

        confidence = calculate_direction_confidence(
            observations,
            slope,
            self.tolerance,
        )

        evidence = build_trajectory_evidence(
            observations,
            slope,
            volatility,
            direction,
            stability,
        )

        snapshot = BehavioralTrajectorySnapshot(
            agent_id=normalized_agent_id,
            observations=observations,
            observation_count=len(observations),
            initial_value=observations[0],
            latest_value=observations[-1],
            slope=slope,
            mean_change=mean_change,
            volatility=volatility,
            direction=direction,
            stability=stability,
            confidence=confidence,
            evidence=tuple(evidence),
        )

        self._latest[normalized_agent_id] = snapshot
        return snapshot

    def get_history(self, agent_id: str) -> tuple[float, ...]:
        """Return chronological observations for an agent."""
        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError("agent_id must be a non-empty string")

        return tuple(self._history.get(agent_id.strip(), []))

    def latest(
        self,
        agent_id: str,
    ) -> BehavioralTrajectorySnapshot | None:
        """Return the latest calculated snapshot."""
        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError("agent_id must be a non-empty string")

        return self._latest.get(agent_id.strip())

    def snapshot_all(
        self,
    ) -> tuple[BehavioralTrajectorySnapshot, ...]:
        """Return latest snapshots for all tracked agents."""
        return tuple(self._latest.values())

    def reset(self, agent_id: str | None = None) -> None:
        """
        Reset one agent or the entire trajectory state.
        """
        if agent_id is None:
            self._history.clear()
            self._latest.clear()
            return

        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError("agent_id must be a non-empty string")

        normalized_agent_id = agent_id.strip()

        self._history.pop(normalized_agent_id, None)
        self._latest.pop(normalized_agent_id, None)


__all__ = [
    "SCORE_MIN",
    "SCORE_MAX",
    "DEFAULT_STABILITY_TOLERANCE",
    "DEFAULT_MIN_OBSERVATIONS",
    "DIRECTION_IMPROVING",
    "DIRECTION_STABLE",
    "DIRECTION_DETERIORATING",
    "DIRECTION_INSUFFICIENT_DATA",
    "STABILITY_STABLE",
    "STABILITY_VARIABLE",
    "TRAJECTORY_IMPROVING",
    "TRAJECTORY_STABLE",
    "TRAJECTORY_DETERIORATING",
    "BehavioralTrajectorySnapshot",
    "PredictiveBehavioralTrajectory",
    "calculate_slope",
    "calculate_mean_change",
    "calculate_volatility",
    "classify_direction",
    "classify_stability",
    "calculate_direction_confidence",
    "build_trajectory_evidence",
]