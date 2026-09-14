"""
Varynx Day 58 - Predictive Trust & Risk Forecasting

Purpose:
    Project near-future behavioral security indicators from observed
    values and their measured trajectory.

Architectural boundary:
    This module does not:
    - authorize actions
    - block agents
    - modify adaptive response
    - infer malicious intent
    - execute hypothetical actions
    - replace the existing risk engine
    - claim certainty about future behavior

The forecast is a deterministic projection of observed trends.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Sequence


SCORE_MIN = 0.0
SCORE_MAX = 100.0

DEFAULT_HORIZON = 1
DEFAULT_MAX_HORIZON = 10
DEFAULT_CONFIDENCE_TOLERANCE = 5.0

FORECAST_IMPROVING = "IMPROVING"
FORECAST_STABLE = "STABLE"
FORECAST_DETERIORATING = "DETERIORATING"
FORECAST_INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

CONFIDENCE_LOW = "LOW"
CONFIDENCE_MODERATE = "MODERATE"
CONFIDENCE_HIGH = "HIGH"


def _validate_score(value: float, field_name: str = "score") -> float:
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


def _validate_horizon(value: int) -> int:
    """Validate forecast horizon."""
    if isinstance(value, bool):
        raise ValueError("horizon must be an integer")

    try:
        value = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("horizon must be an integer") from exc

    if value < 1:
        raise ValueError("horizon must be at least 1")

    if value > DEFAULT_MAX_HORIZON:
        raise ValueError(
            f"horizon must be <= {DEFAULT_MAX_HORIZON}"
        )

    return value


def _validate_tolerance(value: float) -> float:
    """Validate confidence tolerance."""
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("tolerance must be numeric") from exc

    if not isfinite(value):
        raise ValueError("tolerance must be finite")

    if value < 0:
        raise ValueError("tolerance must be non-negative")

    return value


def _validate_observations(
    observations: Sequence[float],
) -> list[float]:
    """Validate chronological observations."""
    if observations is None:
        raise ValueError("observations cannot be None")

    try:
        values = list(observations)
    except TypeError as exc:
        raise ValueError("observations must be iterable") from exc

    return [
        _validate_score(
            value,
            f"observation[{index}]",
        )
        for index, value in enumerate(values)
    ]


def calculate_slope(
    observations: Sequence[float],
) -> float:
    """
    Calculate the average directional change.

    Positive:
        security concern increasing.

    Negative:
        security concern decreasing.

    Zero:
        stable.
    """
    values = _validate_observations(observations)

    if len(values) < 2:
        return 0.0

    return (values[-1] - values[0]) / (len(values) - 1)


def calculate_volatility(
    observations: Sequence[float],
) -> float:
    """
    Calculate mean absolute movement between consecutive observations.
    """
    values = _validate_observations(observations)

    if len(values) < 2:
        return 0.0

    changes = [
        abs(values[index] - values[index - 1])
        for index in range(1, len(values))
    ]

    return sum(changes) / len(changes)


def project_value(
    current_value: float,
    slope: float,
    horizon: int = DEFAULT_HORIZON,
) -> float:
    """
    Project a future value using a bounded linear trend.

    projected = current + slope * horizon

    The result is clamped to the valid 0-100 security range.
    """
    current_value = _validate_score(
        current_value,
        "current_value",
    )

    try:
        slope = float(slope)
    except (TypeError, ValueError) as exc:
        raise ValueError("slope must be numeric") from exc

    if not isfinite(slope):
        raise ValueError("slope must be finite")

    horizon = _validate_horizon(horizon)

    projected = current_value + (slope * horizon)

    return max(
        SCORE_MIN,
        min(SCORE_MAX, projected),
    )


def classify_forecast(
    slope: float,
    tolerance: float = DEFAULT_CONFIDENCE_TOLERANCE,
) -> str:
    """
    Classify projected direction.

    Increasing security concern:
        DETERIORATING

    Small movement:
        STABLE

    Decreasing security concern:
        IMPROVING
    """
    try:
        slope = float(slope)
    except (TypeError, ValueError) as exc:
        raise ValueError("slope must be numeric") from exc

    if not isfinite(slope):
        raise ValueError("slope must be finite")

    tolerance = _validate_tolerance(tolerance)

    if abs(slope) <= tolerance:
        return FORECAST_STABLE

    if slope > tolerance:
        return FORECAST_DETERIORATING

    return FORECAST_IMPROVING


def classify_confidence(
    observation_count: int,
    slope: float,
    volatility: float,
    tolerance: float = DEFAULT_CONFIDENCE_TOLERANCE,
) -> str:
    """
    Estimate confidence in the mathematical projection.

    Confidence reflects evidence quality, not certainty that the
    projected future state will occur.
    """
    if isinstance(observation_count, bool):
        raise ValueError("observation_count must be an integer")

    try:
        count = int(observation_count)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "observation_count must be an integer"
        ) from exc

    if count < 0:
        raise ValueError("observation_count cannot be negative")

    try:
        slope = float(slope)
        volatility = float(volatility)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "slope and volatility must be numeric"
        ) from exc

    if not isfinite(slope) or not isfinite(volatility):
        raise ValueError(
            "slope and volatility must be finite"
        )

    tolerance = _validate_tolerance(tolerance)

    if count < 2:
        return CONFIDENCE_LOW

    if count >= 5 and abs(slope) > tolerance and volatility <= 20:
        return CONFIDENCE_HIGH

    if count >= 3:
        return CONFIDENCE_MODERATE

    return CONFIDENCE_LOW


def build_forecast_evidence(
    observations: Sequence[float],
    current_value: float,
    projected_value: float,
    slope: float,
    volatility: float,
    direction: str,
    confidence: str,
    horizon: int,
) -> list[str]:
    """Build deterministic evidence supporting the forecast."""
    values = _validate_observations(observations)

    return [
        f"Observed {len(values)} chronological observations",
        f"Current value: {current_value:.2f}",
        f"Forecast horizon: {horizon}",
        f"Observed slope: {slope:.2f}",
        f"Observed volatility: {volatility:.2f}",
        f"Projected value: {projected_value:.2f}",
        f"Forecast direction: {direction}",
        f"Forecast confidence: {confidence}",
        (
            "Projection is a deterministic trend extrapolation "
            "from observed behavior"
        ),
    ]


@dataclass(frozen=True)
class PredictiveForecastSnapshot:
    """
    Immutable forecast result for one behavioral indicator.
    """

    agent_id: str
    observations: tuple[float, ...]
    observation_count: int
    current_value: float | None
    projected_value: float | None
    slope: float
    volatility: float
    horizon: int
    direction: str
    confidence: str
    evidence: tuple[str, ...]


class PredictiveForecastEngine:
    """
    Stateful per-agent predictive forecasting engine.

    Each agent maintains an independent chronological observation history.
    """

    def __init__(
        self,
        horizon: int = DEFAULT_HORIZON,
        tolerance: float = DEFAULT_CONFIDENCE_TOLERANCE,
    ) -> None:
        self.horizon = _validate_horizon(horizon)
        self.tolerance = _validate_tolerance(tolerance)

        self._history: dict[str, list[float]] = {}
        self._latest: dict[str, PredictiveForecastSnapshot] = {}

    def add_observation(
        self,
        agent_id: str,
        value: float,
    ) -> PredictiveForecastSnapshot:
        """Add one observation and return the resulting forecast."""
        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError("agent_id must be a non-empty string")

        normalized_agent_id = agent_id.strip()
        normalized_value = _validate_score(value)

        self._history.setdefault(
            normalized_agent_id,
            [],
        ).append(normalized_value)

        return self.forecast(normalized_agent_id)

    def add_observations(
        self,
        agent_id: str,
        observations: Sequence[float],
    ) -> PredictiveForecastSnapshot:
        """Add chronological observations and return the forecast."""
        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError("agent_id must be a non-empty string")

        normalized_agent_id = agent_id.strip()
        values = _validate_observations(observations)

        self._history.setdefault(
            normalized_agent_id,
            [],
        ).extend(values)

        return self.forecast(normalized_agent_id)

    def forecast(
        self,
        agent_id: str,
    ) -> PredictiveForecastSnapshot:
        """Calculate the current forecast for an agent."""
        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError("agent_id must be a non-empty string")

        normalized_agent_id = agent_id.strip()

        observations = tuple(
            self._history.get(
                normalized_agent_id,
                [],
            )
        )

        if len(observations) < 2:
            snapshot = PredictiveForecastSnapshot(
                agent_id=normalized_agent_id,
                observations=observations,
                observation_count=len(observations),
                current_value=(
                    observations[-1]
                    if observations
                    else None
                ),
                projected_value=None,
                slope=0.0,
                volatility=0.0,
                horizon=self.horizon,
                direction=FORECAST_INSUFFICIENT_DATA,
                confidence=CONFIDENCE_LOW,
                evidence=(
                    f"Insufficient observations: "
                    f"{len(observations)}/2",
                ),
            )

            self._latest[normalized_agent_id] = snapshot
            return snapshot

        current_value = observations[-1]
        slope = calculate_slope(observations)
        volatility = calculate_volatility(observations)

        projected_value = project_value(
            current_value=current_value,
            slope=slope,
            horizon=self.horizon,
        )

        direction = classify_forecast(
            slope=slope,
            tolerance=self.tolerance,
        )

        confidence = classify_confidence(
            observation_count=len(observations),
            slope=slope,
            volatility=volatility,
            tolerance=self.tolerance,
        )

        evidence = build_forecast_evidence(
            observations=observations,
            current_value=current_value,
            projected_value=projected_value,
            slope=slope,
            volatility=volatility,
            direction=direction,
            confidence=confidence,
            horizon=self.horizon,
        )

        snapshot = PredictiveForecastSnapshot(
            agent_id=normalized_agent_id,
            observations=observations,
            observation_count=len(observations),
            current_value=current_value,
            projected_value=projected_value,
            slope=slope,
            volatility=volatility,
            horizon=self.horizon,
            direction=direction,
            confidence=confidence,
            evidence=tuple(evidence),
        )

        self._latest[normalized_agent_id] = snapshot
        return snapshot

    def get_history(
        self,
        agent_id: str,
    ) -> tuple[float, ...]:
        """Return chronological observations."""
        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError("agent_id must be a non-empty string")

        return tuple(
            self._history.get(
                agent_id.strip(),
                [],
            )
        )

    def latest(
        self,
        agent_id: str,
    ) -> PredictiveForecastSnapshot | None:
        """Return the latest forecast."""
        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError("agent_id must be a non-empty string")

        return self._latest.get(agent_id.strip())

    def snapshot_all(
        self,
    ) -> tuple[PredictiveForecastSnapshot, ...]:
        """Return latest forecasts for all tracked agents."""
        return tuple(self._latest.values())

    def reset(
        self,
        agent_id: str | None = None,
    ) -> None:
        """Reset one agent or all forecasting state."""
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
    "DEFAULT_HORIZON",
    "DEFAULT_MAX_HORIZON",
    "DEFAULT_CONFIDENCE_TOLERANCE",
    "FORECAST_IMPROVING",
    "FORECAST_STABLE",
    "FORECAST_DETERIORATING",
    "FORECAST_INSUFFICIENT_DATA",
    "CONFIDENCE_LOW",
    "CONFIDENCE_MODERATE",
    "CONFIDENCE_HIGH",
    "PredictiveForecastSnapshot",
    "PredictiveForecastEngine",
    "calculate_slope",
    "calculate_volatility",
    "project_value",
    "classify_forecast",
    "classify_confidence",
    "build_forecast_evidence",
]