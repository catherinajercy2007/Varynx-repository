"""
Day 70 tests - Security Audit Integrity & Chain Verification.
"""

from dataclasses import FrozenInstanceError

import pytest

from app.security_audit_integrity import (
    GENESIS_FINGERPRINT,
    INTEGRITY_INVALID,
    INTEGRITY_PARTIAL,
    INTEGRITY_VALID,
    AuditIntegrityRecord,
    AuditIntegrityResult,
    SecurityAuditIntegrity,
    calculate_chain_fingerprint,
    calculate_event_fingerprint,
    canonicalize_evidence,
    canonicalize_event,
    decision_is_modified_here,
    enforcement_is_executed_here,
    integrity_is_deterministic,
    verify_execution_boundary,
    verify_sequence,
)


class FakeAuditEvent:
    def __init__(
        self,
        agent_id,
        request_id,
        sequence_number,
        event_type,
        decision=None,
        status="AUDIT_RECORDED",
        evidence=None,
        execution_performed_here=False,
    ):
        self.agent_id = agent_id
        self.request_id = request_id
        self.sequence_number = sequence_number
        self.event_type = event_type
        self.decision = decision
        self.status = status
        self.evidence = dict(evidence or {})
        self.execution_performed_here = execution_performed_here


def make_events():
    return [
        FakeAuditEvent(
            "agent-1",
            "request-1",
            1,
            "AUDIT_BEHAVIORAL",
            evidence={"reason": "behavior observed"},
        ),
        FakeAuditEvent(
            "agent-1",
            "request-1",
            2,
            "AUDIT_PREDICTIVE",
            evidence={"direction": "DETERIORATING"},
        ),
        FakeAuditEvent(
            "agent-1",
            "request-1",
            3,
            "AUDIT_DECISION",
            decision="MONITOR",
            evidence={"decision_reason": "moderate signal"},
        ),
        FakeAuditEvent(
            "agent-1",
            "request-2",
            4,
            "AUDIT_RUNTIME",
            decision="STEP_UP_VERIFICATION",
            evidence={"runtime_state": "RUNTIME_ESCALATED"},
        ),
    ]


def test_canonicalize_evidence_is_deterministic():
    first = canonicalize_evidence(
        {"b": 2, "a": 1}
    )

    second = canonicalize_evidence(
        {"a": 1, "b": 2}
    )

    assert first == second


def test_canonicalize_event_is_deterministic():
    events = make_events()

    assert canonicalize_event(events[0]) == canonicalize_event(
        events[0]
    )


def test_event_fingerprint_is_deterministic():
    events = make_events()

    assert calculate_event_fingerprint(
        events[0]
    ) == calculate_event_fingerprint(
        events[0]
    )


def test_different_events_have_different_fingerprints():
    events = make_events()

    assert calculate_event_fingerprint(
        events[0]
    ) != calculate_event_fingerprint(
        events[1]
    )


def test_chain_starts_from_genesis():
    events = make_events()

    event_fingerprint = calculate_event_fingerprint(
        events[0]
    )

    chain = calculate_chain_fingerprint(
        event_fingerprint
    )

    expected = calculate_chain_fingerprint(
        event_fingerprint,
        GENESIS_FINGERPRINT,
    )

    assert chain == expected


def test_chain_changes_when_previous_fingerprint_changes():
    events = make_events()

    fingerprint = calculate_event_fingerprint(
        events[1]
    )

    first = calculate_chain_fingerprint(
        fingerprint,
        "previous-a",
    )

    second = calculate_chain_fingerprint(
        fingerprint,
        "previous-b",
    )

    assert first != second


def test_build_records():
    integrity = SecurityAuditIntegrity()

    records = integrity.build_records(
        make_events()
    )

    assert len(records) == 4
    assert records[0].sequence_number == 1
    assert records[1].previous_fingerprint == (
        records[0].chain_fingerprint
    )


def test_build_records_use_genesis_for_first_event():
    integrity = SecurityAuditIntegrity()

    records = integrity.build_records(
        make_events()
    )

    assert records[0].previous_fingerprint == GENESIS_FINGERPRINT


def test_build_records_are_immutable():
    integrity = SecurityAuditIntegrity()

    records = integrity.build_records(
        make_events()
    )

    with pytest.raises(FrozenInstanceError):
        records[0].sequence_number = 99


def test_valid_chain():
    integrity = SecurityAuditIntegrity()

    events = make_events()

    records = integrity.build_records(events)

    result = integrity.verify(
        "agent-1",
        events,
        expected_records=records,
    )

    assert result.status == INTEGRITY_VALID
    assert result.event_count == 4
    assert result.verified_events == 4
    assert result.invalid_events == ()
    assert result.sequence_valid is True
    assert result.chain_valid is True
    assert result.execution_boundary_valid is True


def test_latest_result():
    integrity = SecurityAuditIntegrity()

    events = make_events()

    result = integrity.verify(
        "agent-1",
        events,
    )

    assert integrity.latest("agent-1") == result


def test_missing_latest_result():
    integrity = SecurityAuditIntegrity()

    assert integrity.latest("missing") is None


def test_snapshot_all():
    integrity = SecurityAuditIntegrity()

    integrity.verify(
        "agent-1",
        make_events(),
    )

    snapshot = integrity.snapshot_all()

    assert "agent-1" in snapshot


def test_reset():
    integrity = SecurityAuditIntegrity()

    integrity.verify(
        "agent-1",
        make_events(),
    )

    integrity.reset()

    assert integrity.latest("agent-1") is None
    assert integrity.snapshot_all() == {}


def test_sequence_verification():
    assert verify_sequence(make_events()) is True


def test_invalid_sequence_detected():
    events = make_events()

    events[2].sequence_number = 5

    assert verify_sequence(events) is False


def test_tampered_event_detected():
    integrity = SecurityAuditIntegrity()

    events = make_events()

    original_records = integrity.build_records(events)

    events[1].evidence["tampered"] = True

    result = integrity.verify(
        "agent-1",
        events,
        expected_records=original_records,
    )

    assert result.status == INTEGRITY_INVALID
    assert result.chain_valid is False
    assert 2 in result.invalid_events


def test_tampered_decision_detected():
    integrity = SecurityAuditIntegrity()

    events = make_events()

    original_records = integrity.build_records(events)

    events[2].decision = "BLOCK"

    result = integrity.verify(
        "agent-1",
        events,
        expected_records=original_records,
    )

    assert result.status == INTEGRITY_INVALID
    assert result.chain_valid is False
    assert 3 in result.invalid_events


def test_tampered_event_type_detected():
    integrity = SecurityAuditIntegrity()

    events = make_events()

    original_records = integrity.build_records(events)

    events[0].event_type = "AUDIT_BLOCKED"

    result = integrity.verify(
        "agent-1",
        events,
        expected_records=original_records,
    )

    assert result.status == INTEGRITY_INVALID
    assert result.chain_valid is False


def test_tampered_agent_detected():
    integrity = SecurityAuditIntegrity()

    events = make_events()

    original_records = integrity.build_records(events)

    events[0].agent_id = "agent-2"

    with pytest.raises(ValueError):
        integrity.verify(
            "agent-1",
            events,
            expected_records=original_records,
        )


def test_execution_boundary():
    assert verify_execution_boundary(
        make_events()
    ) is True


def test_execution_boundary_violation():
    events = make_events()

    events[3].execution_performed_here = True

    assert verify_execution_boundary(events) is False


def test_execution_boundary_produces_partial_result():
    integrity = SecurityAuditIntegrity()

    events = make_events()

    events[3].execution_performed_here = True

    result = integrity.verify(
        "agent-1",
        events,
    )

    assert result.status == INTEGRITY_PARTIAL
    assert result.execution_boundary_valid is False


def test_wrong_agent_rejected():
    integrity = SecurityAuditIntegrity()

    with pytest.raises(ValueError):
        integrity.verify(
            "agent-2",
            make_events(),
        )


def test_empty_events_rejected():
    integrity = SecurityAuditIntegrity()

    with pytest.raises(ValueError):
        integrity.verify(
            "agent-1",
            [],
        )


def test_invalid_sequence_number_type():
    events = make_events()

    events[0].sequence_number = "1"

    with pytest.raises(TypeError):
        verify_sequence(events)


def test_invalid_sequence_number_value():
    events = make_events()

    events[0].sequence_number = 0

    with pytest.raises(ValueError):
        verify_sequence(events)


def test_invalid_event_missing_evidence():
    integrity = SecurityAuditIntegrity()

    class BrokenEvent:
        agent_id = "agent-1"
        request_id = "request-1"
        sequence_number = 1
        event_type = "AUDIT_BEHAVIORAL"
        decision = None
        status = "AUDIT_RECORDED"
        execution_performed_here = False

    with pytest.raises(AttributeError):
        integrity.build_records(
            [BrokenEvent()]
        )


def test_result_is_immutable():
    integrity = SecurityAuditIntegrity()

    result = integrity.verify(
        "agent-1",
        make_events(),
    )

    with pytest.raises(FrozenInstanceError):
        result.event_count = 100


def test_records_are_defensively_recreated():
    integrity = SecurityAuditIntegrity()

    events = make_events()

    first = integrity.build_records(events)

    events[0].evidence["changed"] = True

    second = integrity.build_records(events)

    assert first[0].event_fingerprint != second[0].event_fingerprint


def test_same_events_produce_same_records():
    integrity = SecurityAuditIntegrity()

    first = integrity.build_records(
        make_events()
    )

    second = integrity.build_records(
        make_events()
    )

    assert first == second


def test_same_events_produce_same_result():
    integrity = SecurityAuditIntegrity()

    first = integrity.verify(
        "agent-1",
        make_events(),
    )

    second = integrity.verify(
        "agent-1",
        make_events(),
    )

    assert first == second


def test_expected_record_length_mismatch_invalidates_chain():
    integrity = SecurityAuditIntegrity()

    events = make_events()

    records = integrity.build_records(events)

    result = integrity.verify(
        "agent-1",
        events,
        expected_records=records[:-1],
    )

    assert result.status == INTEGRITY_INVALID
    assert result.chain_valid is False


def test_execution_boundary_function():
    assert enforcement_is_executed_here() is False


def test_decision_boundary_function():
    assert decision_is_modified_here() is False


def test_determinism_function():
    assert integrity_is_deterministic() is True


def test_no_universal_score():
    integrity = SecurityAuditIntegrity()

    result = integrity.verify(
        "agent-1",
        make_events(),
    )

    assert not hasattr(result, "risk_score")
    assert not hasattr(result, "security_score")
    assert not hasattr(result, "trust_score")


def test_verification_does_not_modify_decision():
    events = make_events()

    original_decision = events[2].decision

    integrity = SecurityAuditIntegrity()

    integrity.verify(
        "agent-1",
        events,
    )

    assert events[2].decision == original_decision