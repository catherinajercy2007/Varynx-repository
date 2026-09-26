"""
Day 72 tests - Security Audit Evidence Snapshot & Historical Comparison.
"""

from dataclasses import FrozenInstanceError

import pytest

from app.security_integrity_monitor import (
    IntegrityMonitoringSnapshot,
)

from app.security_evidence_snapshot import (
    COMPARISON_CHANGED,
    COMPARISON_IDENTICAL,
    SNAPSHOT_CHANGED,
    SNAPSHOT_STABLE,
    SecurityEvidenceComparison,
    SecurityEvidenceSnapshot,
    SecurityEvidenceSnapshotManager,
    build_snapshot_id,
    compare_security_evidence,
    create_security_evidence_snapshot,
    decisions_are_modified_here,
    enforcement_is_executed_here,
    malicious_intent_is_inferred_here,
    snapshot_is_changed,
    snapshot_is_stable,
    snapshots_are_deterministic,
)


def make_monitoring_snapshot(
    agent_id="agent-1",
    status="INTEGRITY_VALID",
    event_count=3,
    verified_events=3,
    invalid_events=(),
    sequence_valid=True,
    chain_valid=True,
    execution_boundary_valid=True,
    fingerprints=None,
):
    if fingerprints is None:
        fingerprints = (
            "chain-1",
            "chain-2",
            "chain-3",
        )

    return IntegrityMonitoringSnapshot(
        agent_id=agent_id,
        status=status,
        event_count=event_count,
        verified_events=verified_events,
        invalid_events=tuple(
            invalid_events
        ),
        sequence_valid=sequence_valid,
        chain_valid=chain_valid,
        execution_boundary_valid=(
            execution_boundary_valid
        ),
        fingerprints=tuple(
            fingerprints
        ),
    )


def test_build_snapshot_id_is_deterministic():
    snapshot = make_monitoring_snapshot()

    first = build_snapshot_id(snapshot)
    second = build_snapshot_id(snapshot)

    assert first == second


def test_different_snapshots_have_different_ids():
    first = make_monitoring_snapshot()

    second = make_monitoring_snapshot(
        event_count=4,
        verified_events=4,
        fingerprints=(
            "chain-1",
            "chain-2",
            "chain-3",
            "chain-4",
        ),
    )

    assert build_snapshot_id(first) != build_snapshot_id(
        second
    )


def test_create_snapshot():
    monitoring = make_monitoring_snapshot()

    snapshot = create_security_evidence_snapshot(
        monitoring,
        1,
    )

    assert snapshot.agent_id == "agent-1"
    assert snapshot.observation_index == 1
    assert snapshot.event_count == 3
    assert snapshot.status == "INTEGRITY_VALID"


def test_snapshot_preserves_invalid_events():
    monitoring = make_monitoring_snapshot(
        status="INTEGRITY_INVALID",
        verified_events=2,
        invalid_events=(2,),
        chain_valid=False,
    )

    snapshot = create_security_evidence_snapshot(
        monitoring,
        1,
    )

    assert snapshot.invalid_events == (2,)
    assert snapshot.chain_valid is False


def test_snapshot_preserves_fingerprints():
    monitoring = make_monitoring_snapshot()

    snapshot = create_security_evidence_snapshot(
        monitoring,
        1,
    )

    assert snapshot.fingerprints == (
        "chain-1",
        "chain-2",
        "chain-3",
    )


def test_snapshot_is_immutable():
    snapshot = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        1,
    )

    with pytest.raises(FrozenInstanceError):
        snapshot.event_count = 99


def test_invalid_observation_index_type():
    with pytest.raises(TypeError):
        create_security_evidence_snapshot(
            make_monitoring_snapshot(),
            "1",
        )


def test_invalid_observation_index_value():
    with pytest.raises(ValueError):
        create_security_evidence_snapshot(
            make_monitoring_snapshot(),
            0,
        )


def test_identical_snapshots():
    first = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        1,
    )

    second = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        2,
    )

    result = compare_security_evidence(
        first,
        second,
    )

    assert result.comparison_status == (
        COMPARISON_IDENTICAL
    )

    assert result.changed_fields == ()
    assert result.event_count_delta == 0
    assert result.verified_events_delta == 0


def test_status_change():
    previous = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        1,
    )

    current = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            status="INTEGRITY_INVALID",
            chain_valid=False,
        ),
        2,
    )

    result = compare_security_evidence(
        previous,
        current,
    )

    assert result.comparison_status == (
        COMPARISON_CHANGED
    )

    assert "status" in result.changed_fields
    assert "chain_valid" in result.changed_fields


def test_event_count_delta():
    previous = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            event_count=3,
        ),
        1,
    )

    current = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            event_count=5,
            verified_events=5,
            fingerprints=(
                "chain-1",
                "chain-2",
                "chain-3",
                "chain-4",
                "chain-5",
            ),
        ),
        2,
    )

    result = compare_security_evidence(
        previous,
        current,
    )

    assert result.event_count_delta == 2
    assert result.verified_events_delta == 2


def test_negative_event_count_delta():
    previous = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            event_count=5,
            verified_events=5,
            fingerprints=(
                "chain-1",
                "chain-2",
                "chain-3",
                "chain-4",
                "chain-5",
            ),
        ),
        1,
    )

    current = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            event_count=3,
        ),
        2,
    )

    result = compare_security_evidence(
        previous,
        current,
    )

    assert result.event_count_delta == -2
    assert result.verified_events_delta == -2


def test_verified_event_change():
    previous = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            verified_events=3,
        ),
        1,
    )

    current = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            verified_events=2,
        ),
        2,
    )

    result = compare_security_evidence(
        previous,
        current,
    )

    assert "verified_events" in (
        result.changed_fields
    )

    assert result.verified_events_delta == -1


def test_invalid_event_added():
    previous = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        1,
    )

    current = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            status="INTEGRITY_INVALID",
            invalid_events=(2,),
            verified_events=2,
            chain_valid=False,
        ),
        2,
    )

    result = compare_security_evidence(
        previous,
        current,
    )

    assert result.added_invalid_events == (2,)
    assert "invalid_events" in (
        result.changed_fields
    )


def test_invalid_event_removed():
    previous = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            status="INTEGRITY_INVALID",
            invalid_events=(2,),
            verified_events=2,
            chain_valid=False,
        ),
        1,
    )

    current = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        2,
    )

    result = compare_security_evidence(
        previous,
        current,
    )

    assert result.removed_invalid_events == (2,)


def test_sequence_validity_change():
    previous = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        1,
    )

    current = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            status="INTEGRITY_INVALID",
            sequence_valid=False,
        ),
        2,
    )

    result = compare_security_evidence(
        previous,
        current,
    )

    assert "sequence_valid" in (
        result.changed_fields
    )


def test_chain_validity_change():
    previous = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        1,
    )

    current = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            status="INTEGRITY_INVALID",
            chain_valid=False,
        ),
        2,
    )

    result = compare_security_evidence(
        previous,
        current,
    )

    assert "chain_valid" in (
        result.changed_fields
    )


def test_execution_boundary_change():
    previous = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        1,
    )

    current = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            status="INTEGRITY_PARTIAL",
            execution_boundary_valid=False,
        ),
        2,
    )

    result = compare_security_evidence(
        previous,
        current,
    )

    assert (
        "execution_boundary_valid"
        in result.changed_fields
    )


def test_fingerprint_change():
    previous = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        1,
    )

    current = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            fingerprints=(
                "chain-1",
                "changed",
                "chain-3",
            ),
        ),
        2,
    )

    result = compare_security_evidence(
        previous,
        current,
    )

    assert "fingerprints" in (
        result.changed_fields
    )

    assert result.fingerprint_changes == (2,)


def test_added_fingerprint():
    previous = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        1,
    )

    current = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            event_count=4,
            verified_events=4,
            fingerprints=(
                "chain-1",
                "chain-2",
                "chain-3",
                "chain-4",
            ),
        ),
        2,
    )

    result = compare_security_evidence(
        previous,
        current,
    )

    assert result.fingerprint_changes == (4,)


def test_removed_fingerprint():
    previous = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            event_count=4,
            verified_events=4,
            fingerprints=(
                "chain-1",
                "chain-2",
                "chain-3",
                "chain-4",
            ),
        ),
        1,
    )

    current = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        2,
    )

    result = compare_security_evidence(
        previous,
        current,
    )

    assert result.fingerprint_changes == (4,)


def test_cross_agent_comparison_rejected():
    first = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            agent_id="agent-1",
        ),
        1,
    )

    second = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            agent_id="agent-2",
        ),
        1,
    )

    with pytest.raises(ValueError):
        compare_security_evidence(
            first,
            second,
        )


def test_invalid_previous_snapshot_type():
    current = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        1,
    )

    with pytest.raises(TypeError):
        compare_security_evidence(
            "invalid",
            current,
        )


def test_invalid_current_snapshot_type():
    previous = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        1,
    )

    with pytest.raises(TypeError):
        compare_security_evidence(
            previous,
            "invalid",
        )


def test_manager_capture():
    manager = SecurityEvidenceSnapshotManager()

    snapshot = manager.capture(
        make_monitoring_snapshot()
    )

    assert snapshot.agent_id == "agent-1"
    assert snapshot.observation_index == 1


def test_manager_observation_index_increments():
    manager = SecurityEvidenceSnapshotManager()

    first = manager.capture(
        make_monitoring_snapshot()
    )

    second = manager.capture(
        make_monitoring_snapshot()
    )

    assert first.observation_index == 1
    assert second.observation_index == 2


def test_manager_latest():
    manager = SecurityEvidenceSnapshotManager()

    manager.capture(
        make_monitoring_snapshot()
    )

    latest = manager.capture(
        make_monitoring_snapshot(
            event_count=4,
            verified_events=4,
            fingerprints=(
                "chain-1",
                "chain-2",
                "chain-3",
                "chain-4",
            ),
        )
    )

    assert manager.latest(
        "agent-1"
    ) == latest


def test_manager_history():
    manager = SecurityEvidenceSnapshotManager()

    manager.capture(
        make_monitoring_snapshot()
    )

    manager.capture(
        make_monitoring_snapshot()
    )

    history = manager.history(
        "agent-1"
    )

    assert len(history) == 2
    assert history[0].observation_index == 1
    assert history[1].observation_index == 2


def test_manager_history_is_tuple():
    manager = SecurityEvidenceSnapshotManager()

    manager.capture(
        make_monitoring_snapshot()
    )

    assert isinstance(
        manager.history("agent-1"),
        tuple,
    )


def test_manager_creates_comparison_history():
    manager = SecurityEvidenceSnapshotManager()

    manager.capture(
        make_monitoring_snapshot()
    )

    manager.capture(
        make_monitoring_snapshot(
            status="INTEGRITY_INVALID",
            chain_valid=False,
        )
    )

    comparisons = manager.comparisons(
        "agent-1"
    )

    assert len(comparisons) == 1
    assert comparisons[0].comparison_status == (
        COMPARISON_CHANGED
    )


def test_manager_compare_arbitrary_snapshots():
    manager = SecurityEvidenceSnapshotManager()

    manager.capture(
        make_monitoring_snapshot()
    )

    manager.capture(
        make_monitoring_snapshot(
            event_count=4,
            verified_events=4,
            fingerprints=(
                "chain-1",
                "chain-2",
                "chain-3",
                "chain-4",
            ),
        )
    )

    manager.capture(
        make_monitoring_snapshot(
            status="INTEGRITY_INVALID",
            chain_valid=False,
        )
    )

    result = manager.compare(
        "agent-1",
        1,
        3,
    )

    assert result.comparison_status == (
        COMPARISON_CHANGED
    )


def test_manager_invalid_previous_index():
    manager = SecurityEvidenceSnapshotManager()

    manager.capture(
        make_monitoring_snapshot()
    )

    with pytest.raises(ValueError):
        manager.compare(
            "agent-1",
            0,
            1,
        )


def test_manager_invalid_current_index():
    manager = SecurityEvidenceSnapshotManager()

    manager.capture(
        make_monitoring_snapshot()
    )

    with pytest.raises(ValueError):
        manager.compare(
            "agent-1",
            1,
            0,
        )


def test_manager_out_of_range_previous_index():
    manager = SecurityEvidenceSnapshotManager()

    manager.capture(
        make_monitoring_snapshot()
    )

    with pytest.raises(IndexError):
        manager.compare(
            "agent-1",
            2,
            1,
        )


def test_manager_out_of_range_current_index():
    manager = SecurityEvidenceSnapshotManager()

    manager.capture(
        make_monitoring_snapshot()
    )

    with pytest.raises(IndexError):
        manager.compare(
            "agent-1",
            1,
            2,
        )


def test_manager_snapshot_all():
    manager = SecurityEvidenceSnapshotManager()

    manager.capture(
        make_monitoring_snapshot()
    )

    result = manager.snapshot_all()

    assert "agent-1" in result
    assert len(result["agent-1"]) == 1


def test_manager_reset():
    manager = SecurityEvidenceSnapshotManager()

    manager.capture(
        make_monitoring_snapshot()
    )

    manager.capture(
        make_monitoring_snapshot()
    )

    manager.reset()

    assert manager.snapshot_all() == {}
    assert manager.latest("agent-1") is None
    assert manager.history("agent-1") == ()
    assert manager.comparisons("agent-1") == ()


def test_comparison_is_immutable():
    previous = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        1,
    )

    current = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            status="INTEGRITY_INVALID",
            chain_valid=False,
        ),
        2,
    )

    result = compare_security_evidence(
        previous,
        current,
    )

    with pytest.raises(FrozenInstanceError):
        result.event_count_delta = 999


def test_snapshot_stable_helper():
    first = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        1,
    )

    second = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        2,
    )

    assert snapshot_is_stable(
        first,
        second,
    ) is True


def test_snapshot_changed_helper():
    first = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        1,
    )

    second = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            status="INTEGRITY_INVALID",
            chain_valid=False,
        ),
        2,
    )

    assert snapshot_is_changed(
        first,
        second,
    ) is True


def test_snapshot_helpers_have_expected_labels():
    first = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        1,
    )

    second = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            status="INTEGRITY_INVALID",
            chain_valid=False,
        ),
        2,
    )

    comparison = compare_security_evidence(
        first,
        second,
    )

    assert comparison.comparison_status == (
        COMPARISON_CHANGED
    )


def test_snapshot_id_contains_agent_id():
    snapshot = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        1,
    )

    assert snapshot.snapshot_id.startswith(
        "agent-1-snapshot-"
    )


def test_snapshot_id_same_for_same_state():
    first = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        1,
    )

    second = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        2,
    )

    assert first.snapshot_id == second.snapshot_id


def test_snapshot_id_changes_when_state_changes():
    first = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        1,
    )

    second = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            event_count=4,
            verified_events=4,
            fingerprints=(
                "chain-1",
                "chain-2",
                "chain-3",
                "chain-4",
            ),
        ),
        2,
    )

    assert first.snapshot_id != second.snapshot_id


def test_multiple_field_changes_are_reported():
    previous = create_security_evidence_snapshot(
        make_monitoring_snapshot(),
        1,
    )

    current = create_security_evidence_snapshot(
        make_monitoring_snapshot(
            status="INTEGRITY_INVALID",
            event_count=4,
            verified_events=2,
            invalid_events=(2,),
            sequence_valid=False,
            chain_valid=False,
            execution_boundary_valid=False,
            fingerprints=(
                "changed-1",
                "changed-2",
                "changed-3",
                "changed-4",
            ),
        ),
        2,
    )

    result = compare_security_evidence(
        previous,
        current,
    )

    assert result.comparison_status == (
        COMPARISON_CHANGED
    )

    assert "status" in result.changed_fields
    assert "event_count" in result.changed_fields
    assert "verified_events" in result.changed_fields
    assert "invalid_events" in result.changed_fields
    assert "sequence_valid" in result.changed_fields
    assert "chain_valid" in result.changed_fields
    assert (
        "execution_boundary_valid"
        in result.changed_fields
    )
    assert "fingerprints" in result.changed_fields


def test_no_security_score():
    manager = SecurityEvidenceSnapshotManager()

    snapshot = manager.capture(
        make_monitoring_snapshot()
    )

    assert not hasattr(
        snapshot,
        "risk_score",
    )

    assert not hasattr(
        snapshot,
        "security_score",
    )

    assert not hasattr(
        snapshot,
        "trust_score",
    )


def test_decision_boundary():
    assert decisions_are_modified_here() is False


def test_enforcement_boundary():
    assert enforcement_is_executed_here() is False


def test_intent_boundary():
    assert malicious_intent_is_inferred_here() is False


def test_determinism_boundary():
    assert snapshots_are_deterministic() is True


def test_original_monitoring_snapshot_is_not_modified():
    monitoring = make_monitoring_snapshot()

    original = (
        monitoring.event_count,
        monitoring.invalid_events,
        monitoring.fingerprints,
    )

    create_security_evidence_snapshot(
        monitoring,
        1,
    )

    assert (
        monitoring.event_count,
        monitoring.invalid_events,
        monitoring.fingerprints,
    ) == original


def test_manager_agent_isolation():
    manager = SecurityEvidenceSnapshotManager()

    manager.capture(
        make_monitoring_snapshot(
            agent_id="agent-1"
        )
    )

    manager.capture(
        make_monitoring_snapshot(
            agent_id="agent-2"
        )
    )

    assert len(
        manager.history("agent-1")
    ) == 1

    assert len(
        manager.history("agent-2")
    ) == 1