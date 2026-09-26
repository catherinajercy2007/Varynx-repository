"""
Day 71 tests - Security Audit Integrity Monitoring & Drift Detection.
"""

from dataclasses import FrozenInstanceError

import pytest

from app.security_audit_integrity import (
    AuditIntegrityRecord,
    AuditIntegrityResult,
    INTEGRITY_INVALID,
    INTEGRITY_PARTIAL,
    INTEGRITY_VALID,
)

from app.security_integrity_monitor import (
    DRIFT_DETECTED,
    DRIFT_NONE,
    MONITORING_CHANGED,
    MONITORING_STABLE,
    IntegrityDrift,
    IntegrityMonitoringResult,
    IntegrityMonitoringSnapshot,
    SecurityIntegrityMonitor,
    create_integrity_snapshot,
    detect_integrity_drift,
    decisions_are_modified_here,
    enforcement_is_executed_here,
    integrity_is_monitored,
    integrity_status_changed,
    malicious_intent_is_inferred_here,
)


def make_records(
    agent_id="agent-1",
    count=3,
):
    records = []

    previous = "GENESIS"

    for index in range(1, count + 1):
        event_fingerprint = (
            f"event-fingerprint-{index}"
        )

        chain_fingerprint = (
            f"chain-fingerprint-{index}"
        )

        records.append(
            AuditIntegrityRecord(
                agent_id=agent_id,
                request_id=f"request-{index}",
                sequence_number=index,
                event_fingerprint=event_fingerprint,
                previous_fingerprint=previous,
                chain_fingerprint=chain_fingerprint,
            )
        )

        previous = chain_fingerprint

    return tuple(records)


def make_result(
    status=INTEGRITY_VALID,
    event_count=3,
    verified_events=3,
    invalid_events=(),
    sequence_valid=True,
    chain_valid=True,
    execution_boundary_valid=True,
    agent_id="agent-1",
):
    records = make_records(
        agent_id=agent_id,
        count=event_count,
    )

    return AuditIntegrityResult(
        agent_id=agent_id,
        status=status,
        event_count=event_count,
        verified_events=verified_events,
        invalid_events=tuple(invalid_events),
        sequence_valid=sequence_valid,
        chain_valid=chain_valid,
        execution_boundary_valid=(
            execution_boundary_valid
        ),
        records=records,
    )


def test_create_snapshot():
    result = make_result()

    snapshot = create_integrity_snapshot(
        result
    )

    assert snapshot.agent_id == "agent-1"
    assert snapshot.status == INTEGRITY_VALID
    assert snapshot.event_count == 3
    assert snapshot.verified_events == 3


def test_snapshot_preserves_invalid_events():
    result = make_result(
        status=INTEGRITY_INVALID,
        verified_events=2,
        invalid_events=(3,),
        chain_valid=False,
    )

    snapshot = create_integrity_snapshot(
        result
    )

    assert snapshot.invalid_events == (3,)
    assert snapshot.chain_valid is False


def test_snapshot_preserves_fingerprints():
    result = make_result()

    snapshot = create_integrity_snapshot(
        result
    )

    assert snapshot.fingerprints == (
        "chain-fingerprint-1",
        "chain-fingerprint-2",
        "chain-fingerprint-3",
    )


def test_snapshot_is_immutable():
    snapshot = create_integrity_snapshot(
        make_result()
    )

    with pytest.raises(FrozenInstanceError):
        snapshot.event_count = 99


def test_no_drift_for_identical_snapshots():
    snapshot = create_integrity_snapshot(
        make_result()
    )

    result = detect_integrity_drift(
        snapshot,
        snapshot,
    )

    assert result.drift_status == DRIFT_NONE
    assert result.changed_fields == ()


def test_status_drift_detected():
    previous = create_integrity_snapshot(
        make_result()
    )

    current = create_integrity_snapshot(
        make_result(
            status=INTEGRITY_INVALID,
            chain_valid=False,
        )
    )

    result = detect_integrity_drift(
        previous,
        current,
    )

    assert result.drift_status == DRIFT_DETECTED
    assert "status" in result.changed_fields
    assert "chain_valid" in result.changed_fields


def test_event_count_drift_detected():
    previous = create_integrity_snapshot(
        make_result(
            event_count=3,
        )
    )

    current = create_integrity_snapshot(
        make_result(
            event_count=4,
        )
    )

    result = detect_integrity_drift(
        previous,
        current,
    )

    assert result.drift_status == DRIFT_DETECTED
    assert "event_count" in result.changed_fields
    assert result.previous_event_count == 3
    assert result.current_event_count == 4


def test_verified_event_drift_detected():
    previous = create_integrity_snapshot(
        make_result(
            verified_events=3,
        )
    )

    current = create_integrity_snapshot(
        make_result(
            verified_events=2,
        )
    )

    result = detect_integrity_drift(
        previous,
        current,
    )

    assert "verified_events" in result.changed_fields


def test_invalid_event_added():
    previous = create_integrity_snapshot(
        make_result()
    )

    current = create_integrity_snapshot(
        make_result(
            status=INTEGRITY_INVALID,
            invalid_events=(2,),
            verified_events=2,
            chain_valid=False,
        )
    )

    result = detect_integrity_drift(
        previous,
        current,
    )

    assert result.added_invalid_events == (2,)


def test_invalid_event_removed():
    previous = create_integrity_snapshot(
        make_result(
            status=INTEGRITY_INVALID,
            invalid_events=(2,),
            verified_events=2,
            chain_valid=False,
        )
    )

    current = create_integrity_snapshot(
        make_result()
    )

    result = detect_integrity_drift(
        previous,
        current,
    )

    assert result.removed_invalid_events == (2,)


def test_sequence_validity_drift():
    previous = create_integrity_snapshot(
        make_result()
    )

    current = create_integrity_snapshot(
        make_result(
            status=INTEGRITY_INVALID,
            sequence_valid=False,
        )
    )

    result = detect_integrity_drift(
        previous,
        current,
    )

    assert "sequence_valid" in result.changed_fields


def test_chain_validity_drift():
    previous = create_integrity_snapshot(
        make_result()
    )

    current = create_integrity_snapshot(
        make_result(
            status=INTEGRITY_INVALID,
            chain_valid=False,
        )
    )

    result = detect_integrity_drift(
        previous,
        current,
    )

    assert "chain_valid" in result.changed_fields


def test_execution_boundary_drift():
    previous = create_integrity_snapshot(
        make_result()
    )

    current = create_integrity_snapshot(
        make_result(
            status=INTEGRITY_PARTIAL,
            execution_boundary_valid=False,
        )
    )

    result = detect_integrity_drift(
        previous,
        current,
    )

    assert (
        "execution_boundary_valid"
        in result.changed_fields
    )


def test_fingerprint_drift_detected():
    previous = IntegrityMonitoringSnapshot(
        agent_id="agent-1",
        status=INTEGRITY_VALID,
        event_count=3,
        verified_events=3,
        invalid_events=(),
        sequence_valid=True,
        chain_valid=True,
        execution_boundary_valid=True,
        fingerprints=(
            "a",
            "b",
            "c",
        ),
    )

    current = IntegrityMonitoringSnapshot(
        agent_id="agent-1",
        status=INTEGRITY_VALID,
        event_count=3,
        verified_events=3,
        invalid_events=(),
        sequence_valid=True,
        chain_valid=True,
        execution_boundary_valid=True,
        fingerprints=(
            "a",
            "CHANGED",
            "c",
        ),
    )

    result = detect_integrity_drift(
        previous,
        current,
    )

    assert result.drift_status == DRIFT_DETECTED
    assert "fingerprints" in result.changed_fields
    assert result.fingerprint_changes == (2,)


def test_added_fingerprint_detected():
    previous = IntegrityMonitoringSnapshot(
        agent_id="agent-1",
        status=INTEGRITY_VALID,
        event_count=2,
        verified_events=2,
        invalid_events=(),
        sequence_valid=True,
        chain_valid=True,
        execution_boundary_valid=True,
        fingerprints=("a", "b"),
    )

    current = IntegrityMonitoringSnapshot(
        agent_id="agent-1",
        status=INTEGRITY_VALID,
        event_count=3,
        verified_events=3,
        invalid_events=(),
        sequence_valid=True,
        chain_valid=True,
        execution_boundary_valid=True,
        fingerprints=("a", "b", "c"),
    )

    result = detect_integrity_drift(
        previous,
        current,
    )

    assert result.fingerprint_changes == (3,)


def test_removed_fingerprint_detected():
    previous = IntegrityMonitoringSnapshot(
        agent_id="agent-1",
        status=INTEGRITY_VALID,
        event_count=3,
        verified_events=3,
        invalid_events=(),
        sequence_valid=True,
        chain_valid=True,
        execution_boundary_valid=True,
        fingerprints=("a", "b", "c"),
    )

    current = IntegrityMonitoringSnapshot(
        agent_id="agent-1",
        status=INTEGRITY_VALID,
        event_count=2,
        verified_events=2,
        invalid_events=(),
        sequence_valid=True,
        chain_valid=True,
        execution_boundary_valid=True,
        fingerprints=("a", "b"),
    )

    result = detect_integrity_drift(
        previous,
        current,
    )

    assert result.fingerprint_changes == (3,)


def test_monitor_first_observation_has_no_drift():
    monitor = SecurityIntegrityMonitor()

    snapshot = monitor.observe(
        make_result()
    )

    assert snapshot.agent_id == "agent-1"
    assert monitor.compare_latest(
        "agent-1"
    ) is None


def test_monitor_second_identical_observation_is_stable():
    monitor = SecurityIntegrityMonitor()

    result = make_result()

    monitor.observe(result)
    monitor.observe(result)

    monitoring = monitor.monitor(
        "agent-1"
    )

    assert monitoring.monitoring_status == (
        MONITORING_STABLE
    )
    assert monitoring.snapshot_count == 2
    assert monitoring.drift_count == 0
    assert monitoring.latest_drift_status == (
        DRIFT_NONE
    )


def test_monitor_detects_status_change():
    monitor = SecurityIntegrityMonitor()

    monitor.observe(
        make_result()
    )

    monitor.observe(
        make_result(
            status=INTEGRITY_INVALID,
            chain_valid=False,
        )
    )

    monitoring = monitor.monitor(
        "agent-1"
    )

    assert monitoring.monitoring_status == (
        MONITORING_CHANGED
    )
    assert monitoring.drift_count == 1
    assert monitoring.latest_drift_status == (
        DRIFT_DETECTED
    )


def test_monitor_keeps_drift_history():
    monitor = SecurityIntegrityMonitor()

    monitor.observe(
        make_result()
    )

    monitor.observe(
        make_result(
            status=INTEGRITY_INVALID,
            chain_valid=False,
        )
    )

    monitor.observe(
        make_result()
    )

    monitoring = monitor.monitor(
        "agent-1"
    )

    assert monitoring.snapshot_count == 3
    assert monitoring.drift_count == 2


def test_compare_latest_returns_latest_drift():
    monitor = SecurityIntegrityMonitor()

    monitor.observe(
        make_result()
    )

    monitor.observe(
        make_result(
            status=INTEGRITY_INVALID,
            chain_valid=False,
        )
    )

    drift = monitor.compare_latest(
        "agent-1"
    )

    assert drift is not None
    assert drift.drift_status == (
        DRIFT_DETECTED
    )


def test_latest_snapshot():
    monitor = SecurityIntegrityMonitor()

    first = monitor.observe(
        make_result()
    )

    second = monitor.observe(
        make_result(
            status=INTEGRITY_PARTIAL,
            execution_boundary_valid=False,
        )
    )

    assert monitor.latest_snapshot(
        "agent-1"
    ) == second

    assert first != second


def test_snapshot_history():
    monitor = SecurityIntegrityMonitor()

    monitor.observe(
        make_result()
    )

    monitor.observe(
        make_result(
            status=INTEGRITY_INVALID,
            chain_valid=False,
        )
    )

    history = monitor.snapshot_history(
        "agent-1"
    )

    assert len(history) == 2
    assert history[0].status == INTEGRITY_VALID
    assert history[1].status == INTEGRITY_INVALID


def test_snapshot_history_is_tuple():
    monitor = SecurityIntegrityMonitor()

    monitor.observe(
        make_result()
    )

    history = monitor.snapshot_history(
        "agent-1"
    )

    assert isinstance(history, tuple)


def test_snapshot_all():
    monitor = SecurityIntegrityMonitor()

    monitor.observe(
        make_result()
    )

    snapshot = monitor.snapshot_all()

    assert "agent-1" in snapshot
    assert len(snapshot["agent-1"]) == 1


def test_agent_isolation():
    monitor = SecurityIntegrityMonitor()

    monitor.observe(
        make_result(
            agent_id="agent-1"
        )
    )

    monitor.observe(
        make_result(
            agent_id="agent-2"
        )
    )

    assert len(
        monitor.snapshot_history("agent-1")
    ) == 1

    assert len(
        monitor.snapshot_history("agent-2")
    ) == 1


def test_cross_agent_comparison_rejected():
    first = create_integrity_snapshot(
        make_result(
            agent_id="agent-1"
        )
    )

    second = create_integrity_snapshot(
        make_result(
            agent_id="agent-2"
        )
    )

    with pytest.raises(ValueError):
        detect_integrity_drift(
            first,
            second,
        )


def test_invalid_result_type_rejected():
    with pytest.raises(TypeError):
        create_integrity_snapshot(
            "not-a-result"
        )


def test_invalid_previous_snapshot_rejected():
    current = create_integrity_snapshot(
        make_result()
    )

    with pytest.raises(TypeError):
        detect_integrity_drift(
            "invalid",
            current,
        )


def test_invalid_current_snapshot_rejected():
    previous = create_integrity_snapshot(
        make_result()
    )

    with pytest.raises(TypeError):
        detect_integrity_drift(
            previous,
            "invalid",
        )


def test_empty_monitoring_history_rejected():
    monitor = SecurityIntegrityMonitor()

    with pytest.raises(ValueError):
        monitor.monitor(
            "agent-1"
        )


def test_latest_missing_agent():
    monitor = SecurityIntegrityMonitor()

    assert monitor.latest_snapshot(
        "missing"
    ) is None


def test_compare_latest_missing_agent():
    monitor = SecurityIntegrityMonitor()

    assert monitor.compare_latest(
        "missing"
    ) is None


def test_reset():
    monitor = SecurityIntegrityMonitor()

    monitor.observe(
        make_result()
    )

    monitor.observe(
        make_result(
            status=INTEGRITY_INVALID,
            chain_valid=False,
        )
    )

    monitor.reset()

    assert monitor.snapshot_all() == {}

    assert monitor.latest_snapshot(
        "agent-1"
    ) is None

    assert monitor.compare_latest(
        "agent-1"
    ) is None


def test_drift_result_is_immutable():
    previous = create_integrity_snapshot(
        make_result()
    )

    current = create_integrity_snapshot(
        make_result(
            status=INTEGRITY_INVALID,
            chain_valid=False,
        )
    )

    drift = detect_integrity_drift(
        previous,
        current,
    )

    with pytest.raises(FrozenInstanceError):
        drift.drift_status = DRIFT_NONE


def test_monitoring_result_is_immutable():
    monitor = SecurityIntegrityMonitor()

    monitor.observe(
        make_result()
    )

    result = monitor.monitor(
        "agent-1"
    )

    with pytest.raises(FrozenInstanceError):
        result.snapshot_count = 999


def test_status_change_helper():
    previous = create_integrity_snapshot(
        make_result()
    )

    current = create_integrity_snapshot(
        make_result(
            status=INTEGRITY_INVALID,
            chain_valid=False,
        )
    )

    assert integrity_status_changed(
        previous,
        current,
    ) is True


def test_no_status_change_helper():
    previous = create_integrity_snapshot(
        make_result()
    )

    current = create_integrity_snapshot(
        make_result()
    )

    assert integrity_status_changed(
        previous,
        current,
    ) is False


def test_monitoring_boundary():
    assert integrity_is_monitored() is True


def test_decision_boundary():
    assert decisions_are_modified_here() is False


def test_enforcement_boundary():
    assert enforcement_is_executed_here() is False


def test_intent_boundary():
    assert malicious_intent_is_inferred_here() is False


def test_no_risk_score():
    monitor = SecurityIntegrityMonitor()

    monitor.observe(
        make_result()
    )

    result = monitor.monitor(
        "agent-1"
    )

    assert not hasattr(result, "risk_score")
    assert not hasattr(result, "security_score")
    assert not hasattr(result, "trust_score")


def test_observation_does_not_modify_original_result():
    result = make_result()

    original_invalid_events = result.invalid_events

    monitor = SecurityIntegrityMonitor()

    monitor.observe(result)

    assert result.invalid_events == (
        original_invalid_events
    )


def test_identical_results_are_deterministic():
    monitor_one = SecurityIntegrityMonitor()
    monitor_two = SecurityIntegrityMonitor()

    result_one = make_result()
    result_two = make_result()

    monitor_one.observe(result_one)
    monitor_two.observe(result_two)

    assert monitor_one.monitor(
        "agent-1"
    ) == monitor_two.monitor(
        "agent-1"
    )


def test_multiple_field_changes_are_reported():
    previous = create_integrity_snapshot(
        make_result()
    )

    current = create_integrity_snapshot(
        make_result(
            status=INTEGRITY_INVALID,
            verified_events=2,
            invalid_events=(2,),
            sequence_valid=False,
            chain_valid=False,
            execution_boundary_valid=False,
        )
    )

    result = detect_integrity_drift(
        previous,
        current,
    )

    assert result.drift_status == DRIFT_DETECTED

    assert "status" in result.changed_fields
    assert "verified_events" in result.changed_fields
    assert "invalid_events" in result.changed_fields
    assert "sequence_valid" in result.changed_fields
    assert "chain_valid" in result.changed_fields
    assert (
        "execution_boundary_valid"
        in result.changed_fields
    )