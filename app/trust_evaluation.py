"""
Varynx Day 47
Dynamic Behavioral Trust Evaluation Adapter

Purpose
-------
Connect the DynamicBehavioralTrust engine to the existing research
evaluation pipeline without duplicating trust calculations.

The adapter:
    1. receives experimental events
    2. obtains trust evidence through an explicit evidence provider
    3. updates DynamicBehavioralTrust
    4. records the resulting TrustSnapshot
    5. converts trust into an explicitly configured binary
       low-trust prediction
    6. evaluates the predictions using the existing metric engine

Important
---------
This module does NOT define how behavioral evidence is generated.

The caller must provide an evidence_provider. This keeps the research
adapter from inventing or changing Varynx behavioral semantics.

It also does NOT replace:
    - authorization
    - risk assessment
    - behavioral analysis
    - adaptive response
    - the DynamicBehavioralTrust engine
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from app.behavioral_trust import (
    DynamicBehavioralTrust,
    TrustSnapshot,
)
from app.evaluation import calculate_metrics


MALICIOUS = "MALICIOUS"


EvidenceProvider = Callable[
    [Mapping[str, Any]],
    Mapping[str, Any] | None,
]


@dataclass(frozen=True)
class TrustEvaluationRecord:
    """
    One experimentally evaluated trust observation.

    The record preserves both the trust-engine output and the
    ground-truth/prediction information required for evaluation.
    """

    agent_id: str
    trust_score: float
    trust_band: str
    evidence_score: float
    update_index: int
    timestamp: str
    ground_truth: str
    predicted_low_trust: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "trust_score": self.trust_score,
            "trust_band": self.trust_band,
            "evidence_score": self.evidence_score,
            "update_index": self.update_index,
            "timestamp": self.timestamp,
            "ground_truth": self.ground_truth,
            "predicted_low_trust": self.predicted_low_trust,
        }


@dataclass(frozen=True)
class TrustEvaluationResult:
    """
    Complete result of one trust-evaluation sequence.
    """

    records: tuple[TrustEvaluationRecord, ...]
    metrics: dict[str, float | int]
    trust_threshold: float

    @property
    def snapshots(self) -> tuple[TrustEvaluationRecord, ...]:
        """Backward-compatible semantic alias for evaluated records."""

        return self.records

    def to_dict(self) -> dict[str, Any]:
        return {
            "records": [
                record.to_dict()
                for record in self.records
            ],
            "metrics": dict(self.metrics),
            "trust_threshold": self.trust_threshold,
        }


def _validate_threshold(
    threshold: float,
) -> float:
    """
    Validate the binary low-trust threshold.

    A trust score below the threshold is classified as low trust.

    Trust scores are bounded by the DynamicBehavioralTrust engine
    to [0, 100].
    """

    if isinstance(threshold, bool):
        raise TypeError(
            "trust_threshold must be numeric"
        )

    try:
        value = float(threshold)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "trust_threshold must be numeric"
        ) from exc

    if not 0.0 <= value <= 100.0:
        raise ValueError(
            "trust_threshold must be between 0 and 100"
        )

    return value


def _validate_event(
    event: Mapping[str, Any],
) -> None:
    if not isinstance(event, Mapping):
        raise TypeError(
            "each event must be a mapping"
        )

    agent_id = event.get("agent_id")

    if not isinstance(agent_id, str) or not agent_id.strip():
        raise ValueError(
            "event must contain a non-empty agent_id"
        )


def _ground_truth_is_malicious(
    event: Mapping[str, Any],
) -> bool:
    """
    Convert the existing Varynx ground_truth field into the positive
    class used by app.evaluation.calculate_metrics().
    """

    ground_truth = str(
        event.get(
            "ground_truth",
            "",
        )
    ).upper()

    return ground_truth == MALICIOUS


def _snapshot_to_record(
    snapshot: TrustSnapshot,
    event: Mapping[str, Any],
    trust_threshold: float,
) -> TrustEvaluationRecord:
    """
    Convert an immutable trust snapshot into an evaluation record.
    """

    return TrustEvaluationRecord(
        agent_id=snapshot.agent_id,
        trust_score=float(snapshot.trust_score),
        trust_band=snapshot.trust_band,
        evidence_score=float(snapshot.evidence_score),
        update_index=int(snapshot.update_index),
        timestamp=snapshot.timestamp,
        ground_truth=str(
            event.get(
                "ground_truth",
                "",
            )
        ).upper(),
        predicted_low_trust=(
            snapshot.trust_score
            < trust_threshold
        ),
    )


def evaluate_trust_sequence(
    events: Iterable[Mapping[str, Any]],
    trust_engine: DynamicBehavioralTrust,
    evidence_provider: EvidenceProvider,
    trust_threshold: float = 40.0,
) -> TrustEvaluationResult:
    """
    Evaluate Dynamic Behavioral Trust over an ordered event sequence.

    Parameters
    ----------
    events:
        Ordered experimental events. Each event must contain at least
        `agent_id`. `ground_truth` is used for classification metrics.

    trust_engine:
        An initialized DynamicBehavioralTrust instance.

    evidence_provider:
        Callable responsible for translating an experimental event into
        trust evidence accepted by DynamicBehavioralTrust.

    trust_threshold:
        Scores below this value are classified as low trust.

    Returns
    -------
    TrustEvaluationResult
        Immutable evaluation records plus the existing Varynx binary
        classification metrics.

    Notes
    -----
    Event ordering is significant because DynamicBehavioralTrust is
    stateful. The caller is responsible for providing deterministic
    ordering and timestamps.
    """

    if not isinstance(
        trust_engine,
        DynamicBehavioralTrust,
    ):
        raise TypeError(
            "trust_engine must be a DynamicBehavioralTrust instance"
        )

    if not callable(evidence_provider):
        raise TypeError(
            "evidence_provider must be callable"
        )

    threshold = _validate_threshold(
        trust_threshold
    )

    records: list[TrustEvaluationRecord] = []
    actual: list[bool] = []
    predicted: list[bool] = []

    for event in events:
        _validate_event(event)

        evidence = evidence_provider(event)

        if evidence is not None and not isinstance(
            evidence,
            Mapping,
        ):
            raise TypeError(
                "evidence_provider must return a mapping or None"
            )

        timestamp = event.get("timestamp")

        if timestamp is not None and not isinstance(
            timestamp,
            datetime,
        ):
            raise TypeError(
                "event timestamp must be a datetime when provided"
            )

        snapshot = trust_engine.update(
            str(event["agent_id"]).strip(),
            evidence,
            timestamp=timestamp,
        )

        record = _snapshot_to_record(
            snapshot,
            event,
            threshold,
        )

        records.append(record)

        actual.append(
            _ground_truth_is_malicious(event)
        )

        predicted.append(
            record.predicted_low_trust
        )

    metrics = calculate_metrics(
        actual,
        predicted,
    )

    return TrustEvaluationResult(
        records=tuple(records),
        metrics=metrics,
        trust_threshold=threshold,
    )


def records_to_dicts(
    records: Iterable[TrustEvaluationRecord],
) -> list[dict[str, Any]]:
    """
    Convert evaluation records to serializable dictionaries.
    """

    return [
        record.to_dict()
        for record in records
    ]


def snapshots_from_result(
    result: TrustEvaluationResult,
) -> tuple[TrustEvaluationRecord, ...]:
    """
    Return the evaluated trust observations.

    This intentionally returns adapter records rather than reaching
    into private state of DynamicBehavioralTrust.
    """

    if not isinstance(
        result,
        TrustEvaluationResult,
    ):
        raise TypeError(
            "result must be a TrustEvaluationResult"
        )

    return result.records


__all__ = [
    "EvidenceProvider",
    "TrustEvaluationRecord",
    "TrustEvaluationResult",
    "evaluate_trust_sequence",
    "records_to_dicts",
    "snapshots_from_result",
]