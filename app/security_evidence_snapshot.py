"""
Day 72 - Security Audit Evidence Snapshot & Historical Comparison.

Provides immutable historical snapshots of Day 71 integrity-monitoring
states and deterministic comparison between snapshots.

Security boundaries:
- Does not create security decisions.
- Does not modify security decisions.
- Does not execute enforcement.
- Does not modify audit events.
- Does not infer malicious intent.
- Does not calculate a universal security score.
- Does not replace Day 70 integrity verification.
- Does not replace Day 71 drift detection.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable

from app.security_integrity_monitor import (
    IntegrityDrift,
    IntegrityMonitoringSnapshot,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SNAPSHOT_STABLE = "SNAPSHOT_STABLE"
SNAPSHOT_CHANGED = "SNAPSHOT_CHANGED"

COMPARISON_IDENTICAL = "COMPARISON_IDENTICAL"
COMPARISON_CHANGED = "COMPARISON_CHANGED"


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _validate_text(
    value: str,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string"
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f"{field_name} must not be empty"
        )

    return value


def _validate_snapshot(
    snapshot: IntegrityMonitoringSnapshot,
) -> IntegrityMonitoringSnapshot:
    if not isinstance(
        snapshot,
        IntegrityMonitoringSnapshot,
    ):
        raise TypeError(
            "snapshot must be an IntegrityMonitoringSnapshot"
        )

    return snapshot


def _validate_snapshots(
    snapshots: Iterable[
        IntegrityMonitoringSnapshot
    ],
) -> tuple[
    IntegrityMonitoringSnapshot,
    ...,
]:
    if isinstance(
        snapshots,
        (str, bytes),
    ):
        raise TypeError(
            "snapshots must be an iterable of "
            "IntegrityMonitoringSnapshot"
        )

    materialized = tuple(snapshots)

    if not materialized:
        raise ValueError(
            "snapshots must not be empty"
        )

    for snapshot in materialized:
        _validate_snapshot(snapshot)

    return materialized


# ---------------------------------------------------------------------------
# Snapshot identity
# ---------------------------------------------------------------------------

def _snapshot_payload(
    snapshot: IntegrityMonitoringSnapshot,
) -> dict:
    return {
        "agent_id": snapshot.agent_id,
        "status": snapshot.status,
        "event_count": snapshot.event_count,
        "verified_events": snapshot.verified_events,
        "invalid_events": list(
            snapshot.invalid_events
        ),
        "sequence_valid": snapshot.sequence_valid,
        "chain_valid": snapshot.chain_valid,
        "execution_boundary_valid": (
            snapshot.execution_boundary_valid
        ),
        "fingerprints": list(
            snapshot.fingerprints
        ),
    }


def build_snapshot_id(
    snapshot: IntegrityMonitoringSnapshot,
) -> str:
    """
    Build a deterministic identifier for an integrity snapshot.
    """
    snapshot = _validate_snapshot(snapshot)

    canonical = json.dumps(
        _snapshot_payload(snapshot),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )

    digest = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()

    return (
        f"{snapshot.agent_id}-snapshot-"
        f"{digest[:16]}"
    )


# ---------------------------------------------------------------------------
# Historical snapshot model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SecurityEvidenceSnapshot:
    """
    Immutable historical representation of one integrity state.
    """

    snapshot_id: str
    agent_id: str
    observation_index: int
    status: str
    event_count: int
    verified_events: int
    invalid_events: tuple[int, ...]
    sequence_valid: bool
    chain_valid: bool
    execution_boundary_valid: bool
    fingerprints: tuple[str, ...]


@dataclass(frozen=True)
class SecurityEvidenceComparison:
    """
    Immutable comparison between two historical snapshots.
    """

    agent_id: str
    previous_snapshot_id: str
    current_snapshot_id: str
    comparison_status: str
    changed_fields: tuple[str, ...]
    event_count_delta: int
    verified_events_delta: int
    added_invalid_events: tuple[int, ...]
    removed_invalid_events: tuple[int, ...]
    fingerprint_changes: tuple[int, ...]


# ---------------------------------------------------------------------------
# Snapshot creation
# ---------------------------------------------------------------------------

def create_security_evidence_snapshot(
    integrity_snapshot: IntegrityMonitoringSnapshot,
    observation_index: int,
) -> SecurityEvidenceSnapshot:
    """
    Convert a Day 71 monitoring snapshot into a historical Day 72
    evidence snapshot.
    """
    integrity_snapshot = _validate_snapshot(
        integrity_snapshot
    )

    if not isinstance(
        observation_index,
        int,
    ):
        raise TypeError(
            "observation_index must be an integer"
        )

    if observation_index < 1:
        raise ValueError(
            "observation_index must be >= 1"
        )

    snapshot_id = build_snapshot_id(
        integrity_snapshot
    )

    return SecurityEvidenceSnapshot(
        snapshot_id=snapshot_id,
        agent_id=integrity_snapshot.agent_id,
        observation_index=observation_index,
        status=integrity_snapshot.status,
        event_count=integrity_snapshot.event_count,
        verified_events=(
            integrity_snapshot.verified_events
        ),
        invalid_events=tuple(
            integrity_snapshot.invalid_events
        ),
        sequence_valid=(
            integrity_snapshot.sequence_valid
        ),
        chain_valid=(
            integrity_snapshot.chain_valid
        ),
        execution_boundary_valid=(
            integrity_snapshot.execution_boundary_valid
        ),
        fingerprints=tuple(
            integrity_snapshot.fingerprints
        ),
    )


# ---------------------------------------------------------------------------
# Snapshot comparison
# ---------------------------------------------------------------------------

def compare_security_evidence(
    previous: SecurityEvidenceSnapshot,
    current: SecurityEvidenceSnapshot,
) -> SecurityEvidenceComparison:
    """
    Compare two historical evidence snapshots.

    This detects structural differences only. It does not determine
    whether a difference represents malicious behavior.
    """
    if not isinstance(
        previous,
        SecurityEvidenceSnapshot,
    ):
        raise TypeError(
            "previous must be a SecurityEvidenceSnapshot"
        )

    if not isinstance(
        current,
        SecurityEvidenceSnapshot,
    ):
        raise TypeError(
            "current must be a SecurityEvidenceSnapshot"
        )

    if previous.agent_id != current.agent_id:
        raise ValueError(
            "snapshots must belong to the same agent"
        )

    changed_fields: list[str] = []

    if previous.status != current.status:
        changed_fields.append("status")

    if previous.event_count != current.event_count:
        changed_fields.append("event_count")

    if (
        previous.verified_events
        != current.verified_events
    ):
        changed_fields.append(
            "verified_events"
        )

    if (
        previous.invalid_events
        != current.invalid_events
    ):
        changed_fields.append(
            "invalid_events"
        )

    if (
        previous.sequence_valid
        != current.sequence_valid
    ):
        changed_fields.append(
            "sequence_valid"
        )

    if (
        previous.chain_valid
        != current.chain_valid
    ):
        changed_fields.append(
            "chain_valid"
        )

    if (
        previous.execution_boundary_valid
        != current.execution_boundary_valid
    ):
        changed_fields.append(
            "execution_boundary_valid"
        )

    if (
        previous.fingerprints
        != current.fingerprints
    ):
        changed_fields.append(
            "fingerprints"
        )

    previous_invalid = set(
        previous.invalid_events
    )

    current_invalid = set(
        current.invalid_events
    )

    added_invalid_events = tuple(
        sorted(
            current_invalid - previous_invalid
        )
    )

    removed_invalid_events = tuple(
        sorted(
            previous_invalid - current_invalid
        )
    )

    fingerprint_changes: list[int] = []

    max_length = max(
        len(previous.fingerprints),
        len(current.fingerprints),
    )

    for index in range(max_length):
        previous_value = (
            previous.fingerprints[index]
            if index < len(
                previous.fingerprints
            )
            else None
        )

        current_value = (
            current.fingerprints[index]
            if index < len(
                current.fingerprints
            )
            else None
        )

        if previous_value != current_value:
            fingerprint_changes.append(
                index + 1
            )

    comparison_status = (
        COMPARISON_IDENTICAL
        if not changed_fields
        else COMPARISON_CHANGED
    )

    return SecurityEvidenceComparison(
        agent_id=current.agent_id,
        previous_snapshot_id=(
            previous.snapshot_id
        ),
        current_snapshot_id=(
            current.snapshot_id
        ),
        comparison_status=comparison_status,
        changed_fields=tuple(
            changed_fields
        ),
        event_count_delta=(
            current.event_count
            - previous.event_count
        ),
        verified_events_delta=(
            current.verified_events
            - previous.verified_events
        ),
        added_invalid_events=(
            added_invalid_events
        ),
        removed_invalid_events=(
            removed_invalid_events
        ),
        fingerprint_changes=tuple(
            fingerprint_changes
        ),
    )


# ---------------------------------------------------------------------------
# Historical snapshot manager
# ---------------------------------------------------------------------------

class SecurityEvidenceSnapshotManager:
    """
    Stores immutable historical security-evidence snapshots.

    The manager does not modify the original Day 71 snapshots.
    """

    def __init__(self) -> None:
        self._snapshots: dict[
            str,
            list[SecurityEvidenceSnapshot],
        ] = {}

        self._comparisons: dict[
            str,
            list[SecurityEvidenceComparison],
        ] = {}

    def capture(
        self,
        integrity_snapshot: IntegrityMonitoringSnapshot,
    ) -> SecurityEvidenceSnapshot:
        """
        Capture one historical observation.
        """
        integrity_snapshot = _validate_snapshot(
            integrity_snapshot
        )

        agent_id = integrity_snapshot.agent_id

        history = self._snapshots.setdefault(
            agent_id,
            [],
        )

        observation_index = len(history) + 1

        snapshot = create_security_evidence_snapshot(
            integrity_snapshot,
            observation_index,
        )

        if history:
            comparison = compare_security_evidence(
                history[-1],
                snapshot,
            )

            self._comparisons.setdefault(
                agent_id,
                [],
            ).append(comparison)

        history.append(snapshot)

        return snapshot

    def latest(
        self,
        agent_id: str,
    ) -> SecurityEvidenceSnapshot | None:
        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        history = self._snapshots.get(
            agent_id,
            [],
        )

        if not history:
            return None

        return history[-1]

    def history(
        self,
        agent_id: str,
    ) -> tuple[SecurityEvidenceSnapshot, ...]:
        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        return tuple(
            self._snapshots.get(
                agent_id,
                [],
            )
        )

    def compare(
        self,
        agent_id: str,
        previous_index: int,
        current_index: int,
    ) -> SecurityEvidenceComparison:
        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        if not isinstance(
            previous_index,
            int,
        ):
            raise TypeError(
                "previous_index must be an integer"
            )

        if not isinstance(
            current_index,
            int,
        ):
            raise TypeError(
                "current_index must be an integer"
            )

        if previous_index < 1:
            raise ValueError(
                "previous_index must be >= 1"
            )

        if current_index < 1:
            raise ValueError(
                "current_index must be >= 1"
            )

        history = self._snapshots.get(
            agent_id,
            [],
        )

        if previous_index > len(history):
            raise IndexError(
                "previous_index is outside snapshot history"
            )

        if current_index > len(history):
            raise IndexError(
                "current_index is outside snapshot history"
            )

        previous = history[
            previous_index - 1
        ]

        current = history[
            current_index - 1
        ]

        return compare_security_evidence(
            previous,
            current,
        )

    def comparisons(
        self,
        agent_id: str,
    ) -> tuple[
        SecurityEvidenceComparison,
        ...,
    ]:
        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        return tuple(
            self._comparisons.get(
                agent_id,
                [],
            )
        )

    def snapshot_all(
        self,
    ) -> dict[
        str,
        tuple[SecurityEvidenceSnapshot, ...],
    ]:
        return {
            agent_id: tuple(history)
            for agent_id, history
            in self._snapshots.items()
        }

    def reset(self) -> None:
        self._snapshots.clear()
        self._comparisons.clear()


# ---------------------------------------------------------------------------
# Standalone helpers
# ---------------------------------------------------------------------------

def snapshot_is_stable(
    previous: SecurityEvidenceSnapshot,
    current: SecurityEvidenceSnapshot,
) -> bool:
    return (
        compare_security_evidence(
            previous,
            current,
        ).comparison_status
        == COMPARISON_IDENTICAL
    )


def snapshot_is_changed(
    previous: SecurityEvidenceSnapshot,
    current: SecurityEvidenceSnapshot,
) -> bool:
    return (
        compare_security_evidence(
            previous,
            current,
        ).comparison_status
        == COMPARISON_CHANGED
    )


def snapshots_are_deterministic() -> bool:
    return True


def decisions_are_modified_here() -> bool:
    return False


def enforcement_is_executed_here() -> bool:
    return False


def malicious_intent_is_inferred_here() -> bool:
    return False


__all__ = [
    "SNAPSHOT_STABLE",
    "SNAPSHOT_CHANGED",
    "COMPARISON_IDENTICAL",
    "COMPARISON_CHANGED",
    "SecurityEvidenceSnapshot",
    "SecurityEvidenceComparison",
    "SecurityEvidenceSnapshotManager",
    "build_snapshot_id",
    "create_security_evidence_snapshot",
    "compare_security_evidence",
    "snapshot_is_stable",
    "snapshot_is_changed",
    "snapshots_are_deterministic",
    "decisions_are_modified_here",
    "enforcement_is_executed_here",
    "malicious_intent_is_inferred_here",
]