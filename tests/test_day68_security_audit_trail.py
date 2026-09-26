from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.security_audit_trail import (
    AUDIT_BEHAVIORAL,
    AUDIT_DECISION,
    AUDIT_ENFORCEMENT,
    AUDIT_PREDICTIVE,
    AUDIT_PROVENANCE,
    AUDIT_RECONCILIATION,
    AUDIT_RECORDED,
    AUDIT_RUNTIME,
    AUDIT_VALIDATION,
    SecurityAuditEvent,
    SecurityDecisionAuditTrail,
    AuditTrailSummary,
    decision_is_modified_here,
    enforcement_is_executed_here,
    summarize_audit_history,
)


# ---------------------------------------------------------------------------
# Basic recording
# ---------------------------------------------------------------------------


def test_record_creates_audit_event():
    trail = SecurityDecisionAuditTrail()

    event = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
        decision="MONITOR",
    )

    assert isinstance(
        event,
        SecurityAuditEvent,
    )

    assert event.agent_id == "agent-1"
    assert event.request_id == "request-1"
    assert event.event_type == AUDIT_DECISION
    assert event.decision == "MONITOR"
    assert event.status == AUDIT_RECORDED
    assert event.execution_performed_here is False


def test_first_event_has_sequence_one():
    trail = SecurityDecisionAuditTrail()

    event = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
    )

    assert event.sequence_number == 1
    assert event.audit_id == "agent-1-audit-1"


def test_sequence_numbers_increment():
    trail = SecurityDecisionAuditTrail()

    first = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_BEHAVIORAL,
    )

    second = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_PREDICTIVE,
    )

    third = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
        decision="MONITOR",
    )

    assert first.sequence_number == 1
    assert second.sequence_number == 2
    assert third.sequence_number == 3


# ---------------------------------------------------------------------------
# Agent isolation
# ---------------------------------------------------------------------------


def test_sequence_numbers_are_isolated_by_agent():
    trail = SecurityDecisionAuditTrail()

    first = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
    )

    second = trail.record(
        agent_id="agent-2",
        request_id="request-1",
        event_type=AUDIT_DECISION,
    )

    assert first.sequence_number == 1
    assert second.sequence_number == 1


def test_agent_histories_are_isolated():
    trail = SecurityDecisionAuditTrail()

    trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
    )

    trail.record(
        agent_id="agent-2",
        request_id="request-2",
        event_type=AUDIT_ENFORCEMENT,
    )

    assert trail.count("agent-1") == 1
    assert trail.count("agent-2") == 1


# ---------------------------------------------------------------------------
# Event coverage
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "event_type",
    [
        AUDIT_BEHAVIORAL,
        AUDIT_PREDICTIVE,
        AUDIT_DECISION,
        AUDIT_RECONCILIATION,
        AUDIT_RUNTIME,
        AUDIT_ENFORCEMENT,
        AUDIT_VALIDATION,
        AUDIT_PROVENANCE,
    ],
)
def test_supported_event_type_can_be_recorded(event_type):
    trail = SecurityDecisionAuditTrail()

    event = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=event_type,
    )

    assert event.event_type == event_type


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


def test_evidence_is_preserved():
    trail = SecurityDecisionAuditTrail()

    event = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
        decision="REDUCE_SCOPE",
        evidence={
            "projected_score": 72,
            "confidence": "HIGH",
        },
    )

    assert event.evidence == {
        "projected_score": 72,
        "confidence": "HIGH",
    }


def test_evidence_is_defensively_copied():
    source = {
        "signals": [
            "deviation",
            "trajectory",
        ]
    }

    trail = SecurityDecisionAuditTrail()

    event = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_PREDICTIVE,
        evidence=source,
    )

    source["signals"].append("modified")

    assert event.evidence["signals"] == [
        "deviation",
        "trajectory",
    ]


def test_nested_evidence_is_defensively_copied():
    source = {
        "context": {
            "resource": "sensitive",
        }
    }

    trail = SecurityDecisionAuditTrail()

    event = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_BEHAVIORAL,
        evidence=source,
    )

    source["context"]["resource"] = "modified"

    assert (
        event.evidence["context"]["resource"]
        == "sensitive"
    )


# ---------------------------------------------------------------------------
# Latest and history
# ---------------------------------------------------------------------------


def test_latest_returns_last_event():
    trail = SecurityDecisionAuditTrail()

    trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_BEHAVIORAL,
    )

    latest = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
        decision="BLOCK",
    )

    assert trail.latest("agent-1") == latest


def test_latest_unknown_agent_returns_none():
    trail = SecurityDecisionAuditTrail()

    assert trail.latest("unknown") is None


def test_history_preserves_insertion_order():
    trail = SecurityDecisionAuditTrail()

    first = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_BEHAVIORAL,
    )

    second = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_PREDICTIVE,
    )

    third = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
        decision="MONITOR",
    )

    assert trail.history("agent-1") == (
        first,
        second,
        third,
    )


# ---------------------------------------------------------------------------
# Request filtering
# ---------------------------------------------------------------------------


def test_by_request_returns_matching_events():
    trail = SecurityDecisionAuditTrail()

    first = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_BEHAVIORAL,
    )

    second = trail.record(
        agent_id="agent-1",
        request_id="request-2",
        event_type=AUDIT_BEHAVIORAL,
    )

    third = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
    )

    assert trail.by_request("request-1") == (
        first,
        third,
    )

    assert second not in trail.by_request(
        "request-1"
    )


def test_by_request_can_span_agents():
    trail = SecurityDecisionAuditTrail()

    first = trail.record(
        agent_id="agent-1",
        request_id="shared-request",
        event_type=AUDIT_DECISION,
    )

    second = trail.record(
        agent_id="agent-2",
        request_id="shared-request",
        event_type=AUDIT_VALIDATION,
    )

    assert trail.by_request(
        "shared-request"
    ) == (
        first,
        second,
    )


# ---------------------------------------------------------------------------
# Event-type filtering
# ---------------------------------------------------------------------------


def test_by_event_type_filters_agent_history():
    trail = SecurityDecisionAuditTrail()

    behavioral = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_BEHAVIORAL,
    )

    decision = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
        decision="MONITOR",
    )

    trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_VALIDATION,
    )

    assert trail.by_event_type(
        "agent-1",
        AUDIT_DECISION,
    ) == (
        decision,
    )

    assert trail.by_event_type(
        "agent-1",
        AUDIT_BEHAVIORAL,
    ) == (
        behavioral,
    )


# ---------------------------------------------------------------------------
# Snapshot
# ---------------------------------------------------------------------------


def test_snapshot_all_contains_all_agents():
    trail = SecurityDecisionAuditTrail()

    trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
    )

    trail.record(
        agent_id="agent-2",
        request_id="request-2",
        event_type=AUDIT_ENFORCEMENT,
    )

    snapshot = trail.snapshot_all()

    assert set(snapshot.keys()) == {
        "agent-1",
        "agent-2",
    }

    assert len(snapshot["agent-1"]) == 1
    assert len(snapshot["agent-2"]) == 1


# ---------------------------------------------------------------------------
# Count
# ---------------------------------------------------------------------------


def test_count_returns_event_count():
    trail = SecurityDecisionAuditTrail()

    assert trail.count("agent-1") == 0

    trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_BEHAVIORAL,
    )

    trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
    )

    assert trail.count("agent-1") == 2


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


def test_reset_one_agent():
    trail = SecurityDecisionAuditTrail()

    trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
    )

    trail.record(
        agent_id="agent-2",
        request_id="request-2",
        event_type=AUDIT_DECISION,
    )

    trail.reset("agent-1")

    assert trail.latest("agent-1") is None
    assert trail.latest("agent-2") is not None


def test_reset_all_agents():
    trail = SecurityDecisionAuditTrail()

    trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
    )

    trail.record(
        agent_id="agent-2",
        request_id="request-2",
        event_type=AUDIT_DECISION,
    )

    trail.reset()

    assert trail.snapshot_all() == {}


def test_reset_restarts_sequence():
    trail = SecurityDecisionAuditTrail()

    first = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
    )

    trail.reset("agent-1")

    second = trail.record(
        agent_id="agent-1",
        request_id="request-2",
        event_type=AUDIT_DECISION,
    )

    assert first.sequence_number == 1
    assert second.sequence_number == 1


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_empty_agent_id_is_rejected():
    trail = SecurityDecisionAuditTrail()

    with pytest.raises(ValueError):
        trail.record(
            agent_id="",
            request_id="request-1",
            event_type=AUDIT_DECISION,
        )


def test_empty_request_id_is_rejected():
    trail = SecurityDecisionAuditTrail()

    with pytest.raises(ValueError):
        trail.record(
            agent_id="agent-1",
            request_id="",
            event_type=AUDIT_DECISION,
        )


def test_invalid_event_type_is_rejected():
    trail = SecurityDecisionAuditTrail()

    with pytest.raises(ValueError):
        trail.record(
            agent_id="agent-1",
            request_id="request-1",
            event_type="INVALID",
        )


def test_empty_status_is_rejected():
    trail = SecurityDecisionAuditTrail()

    with pytest.raises(ValueError):
        trail.record(
            agent_id="agent-1",
            request_id="request-1",
            event_type=AUDIT_DECISION,
            status="",
        )


def test_invalid_evidence_type_is_rejected():
    trail = SecurityDecisionAuditTrail()

    with pytest.raises(TypeError):
        trail.record(
            agent_id="agent-1",
            request_id="request-1",
            event_type=AUDIT_DECISION,
            evidence=["invalid"],
        )


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


def test_audit_event_is_immutable():
    trail = SecurityDecisionAuditTrail()

    event = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
        decision="BLOCK",
    )

    with pytest.raises(FrozenInstanceError):
        event.decision = "ALLOW"


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def test_summary_contains_event_count():
    trail = SecurityDecisionAuditTrail()

    first = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_BEHAVIORAL,
    )

    second = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
        decision="MONITOR",
    )

    summary = summarize_audit_history(
        trail.history("agent-1")
    )

    assert isinstance(
        summary,
        AuditTrailSummary,
    )

    assert summary.agent_id == "agent-1"
    assert summary.event_count == 2
    assert summary.event_types == (
        AUDIT_BEHAVIORAL,
        AUDIT_DECISION,
    )

    assert summary.request_ids == (
        "request-1",
    )

    assert summary.decisions == (
        "MONITOR",
    )


def test_summary_preserves_first_seen_order():
    trail = SecurityDecisionAuditTrail()

    trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
        decision="MONITOR",
    )

    trail.record(
        agent_id="agent-1",
        request_id="request-2",
        event_type=AUDIT_DECISION,
        decision="BLOCK",
    )

    trail.record(
        agent_id="agent-1",
        request_id="request-3",
        event_type=AUDIT_DECISION,
        decision="MONITOR",
    )

    summary = summarize_audit_history(
        trail.history("agent-1")
    )

    assert summary.decisions == (
        "MONITOR",
        "BLOCK",
    )


def test_empty_summary_is_rejected():
    with pytest.raises(ValueError):
        summarize_audit_history(())


# ---------------------------------------------------------------------------
# Security boundaries
# ---------------------------------------------------------------------------


def test_decision_is_not_modified_here():
    assert decision_is_modified_here() is False


def test_enforcement_is_not_executed_here():
    assert enforcement_is_executed_here() is False


def test_block_event_is_only_recorded():
    trail = SecurityDecisionAuditTrail()

    event = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
        decision="BLOCK",
    )

    assert event.decision == "BLOCK"
    assert event.execution_performed_here is False


def test_allow_event_is_only_recorded():
    trail = SecurityDecisionAuditTrail()

    event = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
        decision="ALLOW",
    )

    assert event.decision == "ALLOW"
    assert event.execution_performed_here is False


def test_no_universal_security_score():
    trail = SecurityDecisionAuditTrail()

    event = trail.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
        decision="BLOCK",
        evidence={
            "projected_score": 90,
            "consequence_score": 85,
            "deviation_score": 80,
        },
    )

    assert not hasattr(
        event,
        "overall_risk_score",
    )

    assert not hasattr(
        event,
        "security_score",
    )


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_same_event_inputs_preserve_same_security_fields():
    trail1 = SecurityDecisionAuditTrail()
    trail2 = SecurityDecisionAuditTrail()

    event1 = trail1.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
        decision="REDUCE_SCOPE",
        status=AUDIT_RECORDED,
        evidence={
            "projected_score": 72,
            "confidence": "HIGH",
        },
    )

    event2 = trail2.record(
        agent_id="agent-1",
        request_id="request-1",
        event_type=AUDIT_DECISION,
        decision="REDUCE_SCOPE",
        status=AUDIT_RECORDED,
        evidence={
            "projected_score": 72,
            "confidence": "HIGH",
        },
    )

    assert event1.agent_id == event2.agent_id
    assert event1.request_id == event2.request_id
    assert event1.sequence_number == event2.sequence_number
    assert event1.event_type == event2.event_type
    assert event1.decision == event2.decision
    assert event1.status == event2.status
    assert event1.evidence == event2.evidence
    assert (
        event1.execution_performed_here
        == event2.execution_performed_here
    )