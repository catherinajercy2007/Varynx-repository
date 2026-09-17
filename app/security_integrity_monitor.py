"""
Day 71 - Security Audit Integrity Monitoring & Drift Detection.

Provides deterministic comparison of audit-integrity verification results
across observation points.

Security boundaries:
- Does not create security decisions.
- Does not modify security decisions.
- Does not execute enforcement.
- Does not modify audit events.
- Does not infer malicious intent.
- Does not calculate a universal security score.
- Does not replace Day 70 integrity verification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from app.security_audit_integrity import (
    INTEGRITY_INVALID,
    INTEGRITY_PARTIAL,
    INTEGRITY_VALID,
    AuditIntegrityRecord,
    AuditIntegrityResult,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DRIFT_NONE = "DRIFT_NONE"
DRIFT_DETECTED = "DRIFT_DETECTED"

MONITORING_STABLE = "MONITORING_STABLE"
MONITORING_CHANGED = "MONITORING_CHANGED"


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _validate_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    value = value.strip()

    if not value:
        raise ValueError(f"{field_name} must not be empty")

    return value


def _validate_result(
    result: AuditIntegrityResult,
) -> AuditIntegrityResult:
    if not isinstance(
        result,
        AuditIntegrityResult,
    ):
        raise TypeError(
            "result must be an AuditIntegrityResult"
        )

    return result


def _validate_results(
    results: Iterable[AuditIntegrityResult],
) -> tuple[AuditIntegrityResult, ...]:
    if isinstance(results, (str, bytes)):
        raise TypeError(
            "results must be an iterable of AuditIntegrityResult"
        )

    materialized = tuple(results)

    if not materialized:
        raise ValueError(
            "results must not be empty"
        )

    for result in materialized:
        _validate_result(result)

    return materialized


# ---------------------------------------------------------------------------
# Snapshot model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IntegrityMonitoringSnapshot:
    """
    Immutable representation of one integrity observation point.
    """

    agent_id: str
    status: str
    event_count: int
    verified_events: int
    invalid_events: tuple[int, ...]
    sequence_valid: bool
    chain_valid: bool
    execution_boundary_valid: bool
    fingerprints: tuple[str, ...]


@dataclass(frozen=True)
class IntegrityDrift:
    """
    Immutable description of differences between two integrity states.
    """

    agent_id: str
    drift_status: str
    changed_fields: tuple[str, ...]
    previous_status: str
    current_status: str
    previous_event_count: int
    current_event_count: int
    added_invalid_events: tuple[int, ...]
    removed_invalid_events: tuple[int, ...]
    fingerprint_changes: tuple[int, ...]


@dataclass(frozen=True)
class IntegrityMonitoringResult:
    """
    Immutable monitoring result for an agent.
    """

    agent_id: str
    monitoring_status: str
    snapshot_count: int
    latest_status: str
    drift_count: int
    latest_drift_status: str
    drifts: tuple[IntegrityDrift, ...]


# ---------------------------------------------------------------------------
# Snapshot creation
# ---------------------------------------------------------------------------

def create_integrity_snapshot(
    result: AuditIntegrityResult,
) -> IntegrityMonitoringSnapshot:
    """
    Convert a Day 70 integrity result into an immutable monitoring
    snapshot.
    """
    result = _validate_result(result)

    fingerprints = tuple(
        record.chain_fingerprint
        for record in result.records
    )

    return IntegrityMonitoringSnapshot(
        agent_id=result.agent_id,
        status=result.status,
        event_count=result.event_count,
        verified_events=result.verified_events,
        invalid_events=tuple(
            result.invalid_events
        ),
        sequence_valid=result.sequence_valid,
        chain_valid=result.chain_valid,
        execution_boundary_valid=(
            result.execution_boundary_valid
        ),
        fingerprints=fingerprints,
    )


# ---------------------------------------------------------------------------
# Drift detection
# ---------------------------------------------------------------------------

def detect_integrity_drift(
    previous: IntegrityMonitoringSnapshot,
    current: IntegrityMonitoringSnapshot,
) -> IntegrityDrift:
    """
    Compare two integrity snapshots.

    This function detects structural changes only. It does not determine
    whether the change represents an attack or malicious behavior.
    """
    if not isinstance(
        previous,
        IntegrityMonitoringSnapshot,
    ):
        raise TypeError(
            "previous must be an IntegrityMonitoringSnapshot"
        )

    if not isinstance(
        current,
        IntegrityMonitoringSnapshot,
    ):
        raise TypeError(
            "current must be an IntegrityMonitoringSnapshot"
        )

    if previous.agent_id != current.agent_id:
        raise ValueError(
            "previous and current snapshots must belong "
            "to the same agent"
        )

    changed_fields: list[str] = []

    if previous.status != current.status:
        changed_fields.append("status")

    if previous.event_count != current.event_count:
        changed_fields.append("event_count")

    if previous.verified_events != current.verified_events:
        changed_fields.append("verified_events")

    if previous.invalid_events != current.invalid_events:
        changed_fields.append("invalid_events")

    if previous.sequence_valid != current.sequence_valid:
        changed_fields.append("sequence_valid")

    if previous.chain_valid != current.chain_valid:
        changed_fields.append("chain_valid")

    if (
        previous.execution_boundary_valid
        != current.execution_boundary_valid
    ):
        changed_fields.append(
            "execution_boundary_valid"
        )

    if previous.fingerprints != current.fingerprints:
        changed_fields.append("fingerprints")

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
            if index < len(previous.fingerprints)
            else None
        )

        current_value = (
            current.fingerprints[index]
            if index < len(current.fingerprints)
            else None
        )

        if previous_value != current_value:
            fingerprint_changes.append(index + 1)

    drift_status = (
        DRIFT_DETECTED
        if changed_fields
        else DRIFT_NONE
    )

    return IntegrityDrift(
        agent_id=current.agent_id,
        drift_status=drift_status,
        changed_fields=tuple(changed_fields),
        previous_status=previous.status,
        current_status=current.status,
        previous_event_count=previous.event_count,
        current_event_count=current.event_count,
        added_invalid_events=added_invalid_events,
        removed_invalid_events=removed_invalid_events,
        fingerprint_changes=tuple(
            fingerprint_changes
        ),
    )


# ---------------------------------------------------------------------------
# Monitoring engine
# ---------------------------------------------------------------------------

class SecurityIntegrityMonitor:
    """
    Maintains immutable integrity observations and detects structural
    changes between consecutive snapshots.
    """

    def __init__(self) -> None:
        self._snapshots: dict[
            str,
            list[IntegrityMonitoringSnapshot],
        ] = {}

        self._drifts: dict[
            str,
            list[IntegrityDrift],
        ] = {}

    def observe(
        self,
        result: AuditIntegrityResult,
    ) -> IntegrityMonitoringSnapshot:
        """
        Record one integrity observation.

        The supplied Day 70 result is not modified.
        """
        result = _validate_result(result)

        snapshot = create_integrity_snapshot(
            result
        )

        agent_id = snapshot.agent_id

        history = self._snapshots.setdefault(
            agent_id,
            [],
        )

        drift_history = self._drifts.setdefault(
            agent_id,
            [],
        )

        if history:
            drift = detect_integrity_drift(
                history[-1],
                snapshot,
            )

            drift_history.append(drift)

        history.append(snapshot)

        return snapshot

    def compare_latest(
        self,
        agent_id: str,
    ) -> IntegrityDrift | None:
        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        drift_history = self._drifts.get(
            agent_id,
            [],
        )

        if not drift_history:
            return None

        return drift_history[-1]

    def monitor(
        self,
        agent_id: str,
    ) -> IntegrityMonitoringResult:
        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        snapshots = self._snapshots.get(
            agent_id,
            [],
        )

        if not snapshots:
            raise ValueError(
                "no integrity observations found"
            )

        drifts = tuple(
            self._drifts.get(
                agent_id,
                [],
            )
        )

        drift_count = sum(
            1
            for drift in drifts
            if drift.drift_status == DRIFT_DETECTED
        )

        latest_drift_status = (
            drifts[-1].drift_status
            if drifts
            else DRIFT_NONE
        )

        monitoring_status = (
            MONITORING_CHANGED
            if drift_count > 0
            else MONITORING_STABLE
        )

        return IntegrityMonitoringResult(
            agent_id=agent_id,
            monitoring_status=monitoring_status,
            snapshot_count=len(snapshots),
            latest_status=snapshots[-1].status,
            drift_count=drift_count,
            latest_drift_status=latest_drift_status,
            drifts=drifts,
        )

    def latest_snapshot(
        self,
        agent_id: str,
    ) -> IntegrityMonitoringSnapshot | None:
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

    def snapshot_history(
        self,
        agent_id: str,
    ) -> tuple[IntegrityMonitoringSnapshot, ...]:
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

    def snapshot_all(
        self,
    ) -> dict[
        str,
        tuple[IntegrityMonitoringSnapshot, ...],
    ]:
        return {
            agent_id: tuple(history)
            for agent_id, history
            in self._snapshots.items()
        }

    def reset(self) -> None:
        self._snapshots.clear()
        self._drifts.clear()


# ---------------------------------------------------------------------------
# Standalone helpers
# ---------------------------------------------------------------------------

def integrity_status_changed(
    previous: IntegrityMonitoringSnapshot,
    current: IntegrityMonitoringSnapshot,
) -> bool:
    return (
        detect_integrity_drift(
            previous,
            current,
        ).drift_status
        == DRIFT_DETECTED
    )


def integrity_is_monitored() -> bool:
    return True


def decisions_are_modified_here() -> bool:
    return False


def enforcement_is_executed_here() -> bool:
    return False


def malicious_intent_is_inferred_here() -> bool:
    return False


__all__ = [
    "DRIFT_NONE",
    "DRIFT_DETECTED",
    "MONITORING_STABLE",
    "MONITORING_CHANGED",
    "IntegrityMonitoringSnapshot",
    "IntegrityDrift",
    "IntegrityMonitoringResult",
    "SecurityIntegrityMonitor",
    "create_integrity_snapshot",
    "detect_integrity_drift",
    "integrity_status_changed",
    "integrity_is_monitored",
    "decisions_are_modified_here",
    "enforcement_is_executed_here",
    "malicious_intent_is_inferred_here",
]