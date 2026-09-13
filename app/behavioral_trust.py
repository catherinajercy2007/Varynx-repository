"""
Varynx Day 46
Dynamic Behavioral Trust Engine

Purpose
-------
Maintain a deterministic, bounded behavioral trust state for an
autonomous AI agent based on accumulated behavioral evidence.

Design principles
-----------------
- Trust is distinct from risk.
- Missing evidence is neutral.
- Trust is bounded to 0-100.
- State evolution is deterministic.
- Older trust evidence gradually decays toward neutral trust.
- New evidence is incorporated using a configurable learning rate.
- Trust history is retained as immutable snapshots.
- The engine does not make authorization or adaptive-response decisions.

Research position
-----------------
This component provides the stateful behavioral-trust foundation
for later behavioral drift analysis and the Behavioral Counterfactual
Security Engine (BCSE).

It does NOT claim to prove malicious intent.
It does NOT replace authorization.
It does NOT replace the existing Varynx risk engine.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import exp, isfinite, log
from typing import Any, Mapping


TRUST_MIN = 0.0
TRUST_MAX = 100.0
NEUTRAL_TRUST = 50.0


DEFAULT_WEIGHTS: dict[str, float] = {
    "behavioral_consistency": 0.30,
    "anomaly_resistance": 0.20,
    "authorization_consistency": 0.15,
    "context_consistency": 0.15,
    "risk_stability": 0.10,
    "activity_stability": 0.10,
}


TRUST_BANDS = (
    (80.0, "HIGH"),
    (60.0, "MODERATE"),
    (40.0, "LOW"),
    (0.0, "CRITICAL"),
)


@dataclass(frozen=True)
class TrustSnapshot:
    """
    Immutable representation of one behavioral trust state.
    """

    agent_id: str
    trust_score: float
    trust_band: str
    evidence_score: float
    evidence: dict[str, float]
    timestamp: str
    update_index: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class _AgentState:
    """
    Internal mutable state for one agent.

    This class is intentionally private. External callers interact
    through DynamicBehavioralTrust.
    """

    agent_id: str
    trust_score: float = NEUTRAL_TRUST
    update_index: int = 0
    last_timestamp: datetime | None = None


def _clamp(
    value: float,
    minimum: float = TRUST_MIN,
    maximum: float = TRUST_MAX,
) -> float:
    return max(minimum, min(maximum, value))


def _number(
    value: Any,
    *,
    name: str,
) -> float:
    """
    Convert and validate a trust-related numeric value.
    """

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


def _validate_agent_id(agent_id: str) -> str:
    if not isinstance(agent_id, str):
        raise TypeError("agent_id must be a string")

    normalized = agent_id.strip()

    if not normalized:
        raise ValueError("agent_id must not be empty")

    return normalized


def _validate_learning_rate(
    learning_rate: float,
) -> float:
    value = _number(
        learning_rate,
        name="learning_rate",
    )

    if not 0.0 <= value <= 1.0:
        raise ValueError(
            "learning_rate must be between 0 and 1"
        )

    return value


def _validate_half_life(
    half_life_hours: float,
) -> float:
    value = _number(
        half_life_hours,
        name="half_life_hours",
    )

    if value <= 0.0:
        raise ValueError(
            "half_life_hours must be greater than zero"
        )

    return value


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


def _validate_evidence(
    evidence: Mapping[str, Any] | None,
) -> dict[str, float]:
    """
    Validate supplied trust evidence.

    Values represent trust-supporting evidence:

        0   = strongly unfavorable
        50  = neutral
        100 = strongly favorable

    Missing dimensions are not treated as zero.
    """

    if evidence is None:
        return {}

    if not isinstance(evidence, Mapping):
        raise TypeError(
            "evidence must be a mapping"
        )

    validated: dict[str, float] = {}

    for key, raw_value in evidence.items():
        if not isinstance(key, str):
            raise TypeError(
                "evidence keys must be strings"
            )

        name = key.strip()

        if not name:
            raise ValueError(
                "evidence keys must not be empty"
            )

        value = _number(
            raw_value,
            name=f"evidence[{name!r}]",
        )

        if not TRUST_MIN <= value <= TRUST_MAX:
            raise ValueError(
                f"evidence[{name!r}] must be between "
                f"{TRUST_MIN} and {TRUST_MAX}"
            )

        validated[name] = value

    return validated


def _validate_weights(
    weights: Mapping[str, Any],
) -> dict[str, float]:
    if not isinstance(weights, Mapping):
        raise TypeError(
            "weights must be a mapping"
        )

    validated: dict[str, float] = {}

    for key, raw_value in weights.items():
        if not isinstance(key, str):
            raise TypeError(
                "weight keys must be strings"
            )

        value = _number(
            raw_value,
            name=f"weights[{key!r}]",
        )

        if value < 0.0:
            raise ValueError(
                f"weights[{key!r}] cannot be negative"
            )

        validated[key] = value

    if not validated:
        raise ValueError(
            "weights must contain at least one dimension"
        )

    if sum(validated.values()) <= 0.0:
        raise ValueError(
            "weights must contain a positive total weight"
        )

    return validated


def aggregate_trust_evidence(
    evidence: Mapping[str, Any] | None,
    weights: Mapping[str, Any] | None = None,
) -> float:
    """
    Aggregate available trust evidence into a bounded 0-100 score.

    Missing dimensions are excluded from the denominator.

    Therefore:

        missing evidence != negative evidence

    If no evidence is supplied, the neutral trust score of 50 is
    returned.
    """

    validated_evidence = _validate_evidence(evidence)

    if not validated_evidence:
        return NEUTRAL_TRUST

    selected_weights = _validate_weights(
        weights or DEFAULT_WEIGHTS
    )

    numerator = 0.0
    denominator = 0.0

    for dimension, value in validated_evidence.items():
        weight = selected_weights.get(
            dimension
        )

        if weight is None or weight <= 0.0:
            continue

        numerator += value * weight
        denominator += weight

    if denominator <= 0.0:
        return NEUTRAL_TRUST

    return round(
        _clamp(
            numerator / denominator
        ),
        4,
    )


def calculate_time_decay(
    age_hours: float,
    half_life_hours: float,
) -> float:
    """
    Calculate exponential time decay.

    At one half-life, the remaining influence is 0.5.

    The result is bounded to [0, 1].
    """

    age = _number(
        age_hours,
        name="age_hours",
    )

    if age < 0.0:
        raise ValueError(
            "age_hours cannot be negative"
        )

    half_life = _validate_half_life(
        half_life_hours
    )

    decay = exp(
        -log(2.0)
        * age
        / half_life
    )

    return _clamp(
        decay,
        minimum=0.0,
        maximum=1.0,
    )


def apply_time_decay(
    trust_score: float,
    age_hours: float,
    half_life_hours: float,
) -> float:
    """
    Move historical trust toward neutral as evidence ages.
    """

    score = _number(
        trust_score,
        name="trust_score",
    )

    if not TRUST_MIN <= score <= TRUST_MAX:
        raise ValueError(
            "trust_score must be between 0 and 100"
        )

    decay = calculate_time_decay(
        age_hours=age_hours,
        half_life_hours=half_life_hours,
    )

    decayed = (
        NEUTRAL_TRUST
        + (
            score - NEUTRAL_TRUST
        )
        * decay
    )

    return round(
        _clamp(decayed),
        4,
    )


def classify_trust(
    trust_score: float,
) -> str:
    """
    Convert a bounded trust score into an interpretable band.
    """

    score = _number(
        trust_score,
        name="trust_score",
    )

    if not TRUST_MIN <= score <= TRUST_MAX:
        raise ValueError(
            "trust_score must be between 0 and 100"
        )

    for threshold, band in TRUST_BANDS:
        if score >= threshold:
            return band

    return "CRITICAL"


class DynamicBehavioralTrust:
    """
    Stateful deterministic behavioral trust engine.

    The engine maintains independent trust state for each agent.
    """

    def __init__(
        self,
        *,
        learning_rate: float = 0.25,
        half_life_hours: float = 72.0,
        weights: Mapping[str, Any] | None = None,
        neutral_trust: float = NEUTRAL_TRUST,
    ) -> None:

        self.learning_rate = _validate_learning_rate(
            learning_rate
        )

        self.half_life_hours = _validate_half_life(
            half_life_hours
        )

        self.weights = _validate_weights(
            weights or DEFAULT_WEIGHTS
        )

        self.neutral_trust = _number(
            neutral_trust,
            name="neutral_trust",
        )

        if not TRUST_MIN <= self.neutral_trust <= TRUST_MAX:
            raise ValueError(
                "neutral_trust must be between 0 and 100"
            )

        self._states: dict[str, _AgentState] = {}

        self._history: dict[
            str,
            list[TrustSnapshot],
        ] = {}

    def _get_or_create_state(
        self,
        agent_id: str,
    ) -> _AgentState:

        if agent_id not in self._states:
            self._states[agent_id] = _AgentState(
                agent_id=agent_id,
                trust_score=self.neutral_trust,
            )

        return self._states[agent_id]

    def update(
        self,
        agent_id: str,
        evidence: Mapping[str, Any] | None,
        *,
        timestamp: datetime | None = None,
    ) -> TrustSnapshot:
        """
        Incorporate new behavioral evidence.

        Process:

            evidence
                ↓
            aggregate evidence
                ↓
            decay historical trust
                ↓
            apply learning rate
                ↓
            bounded trust state
                ↓
            immutable snapshot
        """

        normalized_agent_id = _validate_agent_id(
            agent_id
        )

        validated_evidence = _validate_evidence(
            evidence
        )

        current_time = _validate_timestamp(
            timestamp
        )

        state = self._get_or_create_state(
            normalized_agent_id
        )

        if (
            state.last_timestamp is not None
            and current_time < state.last_timestamp
        ):
            raise ValueError(
                "timestamp cannot move backwards"
            )

        evidence_score = aggregate_trust_evidence(
            validated_evidence,
            self.weights,
        )

        if state.last_timestamp is None:
            decayed_previous = state.trust_score

        else:
            age_hours = (
                current_time
                - state.last_timestamp
            ).total_seconds() / 3600.0

            decayed_previous = apply_time_decay(
                state.trust_score,
                age_hours,
                self.half_life_hours,
            )

        updated_score = (
            (
                1.0
                - self.learning_rate
            )
            * decayed_previous
            + self.learning_rate
            * evidence_score
        )

        state.trust_score = round(
            _clamp(updated_score),
            4,
        )

        state.update_index += 1
        state.last_timestamp = current_time

        snapshot = TrustSnapshot(
            agent_id=normalized_agent_id,
            trust_score=state.trust_score,
            trust_band=classify_trust(
                state.trust_score
            ),
            evidence_score=evidence_score,
            evidence=dict(validated_evidence),
            timestamp=current_time.isoformat(),
            update_index=state.update_index,
        )

        self._history.setdefault(
            normalized_agent_id,
            [],
        ).append(snapshot)

        return snapshot

    def get_trust(
        self,
        agent_id: str,
    ) -> float:
        """
        Return the current trust score.

        Unknown agents receive neutral trust.
        """

        normalized_agent_id = _validate_agent_id(
            agent_id
        )

        state = self._states.get(
            normalized_agent_id
        )

        if state is None:
            return self.neutral_trust

        return state.trust_score

    def get_band(
        self,
        agent_id: str,
    ) -> str:
        """
        Return the current trust band.
        """

        return classify_trust(
            self.get_trust(agent_id)
        )

    def get_snapshot(
        self,
        agent_id: str,
    ) -> TrustSnapshot | None:
        """
        Return the latest immutable snapshot.
        """

        normalized_agent_id = _validate_agent_id(
            agent_id
        )

        history = self._history.get(
            normalized_agent_id,
            [],
        )

        if not history:
            return None

        return history[-1]

    def get_history(
        self,
        agent_id: str,
    ) -> tuple[TrustSnapshot, ...]:
        """
        Return immutable trust history.
        """

        normalized_agent_id = _validate_agent_id(
            agent_id
        )

        return tuple(
            self._history.get(
                normalized_agent_id,
                [],
            )
        )

    def reset(
        self,
        agent_id: str,
    ) -> None:
        """
        Remove state and history for one agent.
        """

        normalized_agent_id = _validate_agent_id(
            agent_id
        )

        self._states.pop(
            normalized_agent_id,
            None,
        )

        self._history.pop(
            normalized_agent_id,
            None,
        )

    def snapshot_all(self) -> dict[str, dict[str, Any]]:
        """
        Return the latest snapshot for every tracked agent.
        """

        result: dict[str, dict[str, Any]] = {}

        for agent_id in self._states:
            snapshot = self.get_snapshot(
                agent_id
            )

            if snapshot is not None:
                result[agent_id] = snapshot.to_dict()

        return result


__all__ = [
    "TRUST_MIN",
    "TRUST_MAX",
    "NEUTRAL_TRUST",
    "DEFAULT_WEIGHTS",
    "TrustSnapshot",
    "aggregate_trust_evidence",
    "calculate_time_decay",
    "apply_time_decay",
    "classify_trust",
    "DynamicBehavioralTrust",
]