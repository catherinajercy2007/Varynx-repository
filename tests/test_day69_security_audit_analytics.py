"""
Day 69 tests - Security Audit Analytics & Evidence Correlation.
"""

from dataclasses import FrozenInstanceError

import pytest

from app.security_audit_analytics import (
    ANALYTICS_COMPLETE,
    ANALYTICS_PARTIAL,
    AuditAnalyticsSummary,
    AuditEvidenceCorrelation,
    AuditRequestAnalysis,
    SecurityAuditAnalytics,
    analytics_is_read_only,
    count_decisions,
    count_event_types,
    decision_is_modified_here,
    enforcement_is_executed_here,
    verify_non_execution_boundary,
)


class FakeAuditEvent:
    def __init__(
        self,
        agent_id,
        request_id,
        sequence_number,
        event_type,
        decision=None,
        evidence=None,
        execution_performed_here=False,
    ):
        self.agent_id = agent_id
        self.request_id = request_id
        self.sequence_number = sequence_number
        self.event_type = event_type
        self.decision = decision
        self.status = "AUDIT_RECORDED"
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


def test_summary_counts_events():
    analytics = SecurityAuditAnalytics()

    result = analytics.summarize(
        "agent-1",
        make_events(),
    )

    assert result.total_events == 4
    assert result.unique_requests == 2


def test_summary_counts_event_types():
    analytics = SecurityAuditAnalytics()

    result = analytics.summarize(
        "agent-1",
        make_events(),
    )

    assert result.event_type_counts["AUDIT_BEHAVIORAL"] == 1
    assert result.event_type_counts["AUDIT_PREDICTIVE"] == 1
    assert result.event_type_counts["AUDIT_DECISION"] == 1
    assert result.event_type_counts["AUDIT_RUNTIME"] == 1


def test_summary_counts_decisions():
    analytics = SecurityAuditAnalytics()

    result = analytics.summarize(
        "agent-1",
        make_events(),
    )

    assert result.decision_counts == {
        "MONITOR": 1,
        "STEP_UP_VERIFICATION": 1,
    }


def test_summary_counts_requests():
    analytics = SecurityAuditAnalytics()

    result = analytics.summarize(
        "agent-1",
        make_events(),
    )

    assert result.request_event_counts["request-1"] == 3
    assert result.request_event_counts["request-2"] == 1


def test_summary_reports_non_execution_boundary():
    analytics = SecurityAuditAnalytics()

    result = analytics.summarize(
        "agent-1",
        make_events(),
    )

    assert result.execution_events == 0
    assert result.non_execution_events == 4
    assert result.status == ANALYTICS_COMPLETE


def test_summary_reports_evidence_events():
    analytics = SecurityAuditAnalytics()

    result = analytics.summarize(
        "agent-1",
        make_events(),
    )

    assert result.evidence_event_count == 4


def test_summary_preserves_first_seen_event_types():
    analytics = SecurityAuditAnalytics()

    result = analytics.summarize(
        "agent-1",
        make_events(),
    )

    assert result.event_types == (
        "AUDIT_BEHAVIORAL",
        "AUDIT_PREDICTIVE",
        "AUDIT_DECISION",
        "AUDIT_RUNTIME",
    )


def test_request_analysis_filters_request():
    analytics = SecurityAuditAnalytics()

    result = analytics.analyze_request(
        "agent-1",
        "request-1",
        make_events(),
    )

    assert result.event_count == 3
    assert result.request_id == "request-1"


def test_request_analysis_preserves_sequence_numbers():
    analytics = SecurityAuditAnalytics()

    result = analytics.analyze_request(
        "agent-1",
        "request-1",
        make_events(),
    )

    assert result.sequence_numbers == (1, 2, 3)


def test_request_analysis_collects_decisions():
    analytics = SecurityAuditAnalytics()

    result = analytics.analyze_request(
        "agent-1",
        "request-1",
        make_events(),
    )

    assert result.decisions == ("MONITOR",)


def test_request_analysis_collects_event_types():
    analytics = SecurityAuditAnalytics()

    result = analytics.analyze_request(
        "agent-1",
        "request-1",
        make_events(),
    )

    assert result.event_types == (
        "AUDIT_BEHAVIORAL",
        "AUDIT_PREDICTIVE",
        "AUDIT_DECISION",
    )


def test_request_analysis_copies_evidence():
    analytics = SecurityAuditAnalytics()

    events = make_events()

    result = analytics.analyze_request(
        "agent-1",
        "request-1",
        events,
    )

    events[0].evidence["new"] = "mutation"

    assert "new" not in result.evidence[0]


def test_request_analysis_detects_execution_boundary():
    analytics = SecurityAuditAnalytics()

    events = make_events()
    events.append(
        FakeAuditEvent(
            "agent-1",
            "request-3",
            5,
            "AUDIT_ENFORCEMENT",
            decision="BLOCK",
            evidence={"external": True},
            execution_performed_here=False,
        )
    )

    result = analytics.analyze_request(
        "agent-1",
        "request-3",
        events,
    )

    assert result.execution_performed_here is False


def test_evidence_correlation_collects_keys():
    analytics = SecurityAuditAnalytics()

    result = analytics.correlate_evidence(
        "agent-1",
        make_events(),
    )

    assert result.event_count == 4
    assert "reason" in result.evidence_keys
    assert "direction" in result.evidence_keys
    assert "decision_reason" in result.evidence_keys


def test_evidence_correlation_can_filter_request():
    analytics = SecurityAuditAnalytics()

    result = analytics.correlate_evidence(
        "agent-1",
        make_events(),
        request_id="request-1",
    )

    assert result.event_count == 3
    assert result.request_id == "request-1"


def test_evidence_correlation_is_non_executing():
    analytics = SecurityAuditAnalytics()

    result = analytics.correlate_evidence(
        "agent-1",
        make_events(),
    )

    assert result.consistent_execution_boundary is True


def test_evidence_correlation_detects_execution_flag():
    analytics = SecurityAuditAnalytics()

    events = make_events()
    events.append(
        FakeAuditEvent(
            "agent-1",
            "request-9",
            9,
            "AUDIT_ENFORCEMENT",
            decision="BLOCK",
            evidence={"external": True},
            execution_performed_here=True,
        )
    )

    result = analytics.correlate_evidence(
        "agent-1",
        events,
    )

    assert result.consistent_execution_boundary is False


def test_event_type_helper():
    result = count_event_types(make_events())

    assert result["AUDIT_BEHAVIORAL"] == 1
    assert result["AUDIT_DECISION"] == 1


def test_decision_helper():
    result = count_decisions(make_events())

    assert result == {
        "MONITOR": 1,
        "STEP_UP_VERIFICATION": 1,
    }


def test_boundary_helper():
    assert verify_non_execution_boundary(make_events()) is True


def test_read_only_boundary():
    assert analytics_is_read_only() is True


def test_decision_is_not_modified():
    assert decision_is_modified_here() is False


def test_enforcement_is_not_executed():
    assert enforcement_is_executed_here() is False


def test_agent_isolation():
    analytics = SecurityAuditAnalytics()

    with pytest.raises(ValueError):
        analytics.summarize(
            "agent-2",
            make_events(),
        )


def test_empty_events_rejected():
    analytics = SecurityAuditAnalytics()

    with pytest.raises(ValueError):
        analytics.summarize(
            "agent-1",
            [],
        )


def test_empty_request_rejected():
    analytics = SecurityAuditAnalytics()

    with pytest.raises(ValueError):
        analytics.analyze_request(
            "agent-1",
            "missing-request",
            make_events(),
        )


def test_missing_evidence_rejected():
    analytics = SecurityAuditAnalytics()

    class BrokenEvent:
        agent_id = "agent-1"
        request_id = "request-1"
        sequence_number = 1
        event_type = "AUDIT_BEHAVIORAL"
        decision = None
        execution_performed_here = False

    with pytest.raises(AttributeError):
        analytics.summarize(
            "agent-1",
            [BrokenEvent()],
        )


def test_execution_event_makes_summary_partial():
    analytics = SecurityAuditAnalytics()

    events = make_events()
    events.append(
        FakeAuditEvent(
            "agent-1",
            "request-5",
            5,
            "AUDIT_ENFORCEMENT",
            decision="BLOCK",
            evidence={"external": True},
            execution_performed_here=True,
        )
    )

    result = analytics.summarize(
        "agent-1",
        events,
    )

    assert result.status == ANALYTICS_PARTIAL
    assert result.execution_events == 1


def test_latest_summary():
    analytics = SecurityAuditAnalytics()

    result = analytics.summarize(
        "agent-1",
        make_events(),
    )

    assert analytics.latest_summary("agent-1") == result


def test_latest_missing_summary():
    analytics = SecurityAuditAnalytics()

    assert analytics.latest_summary("missing") is None


def test_snapshot_summaries():
    analytics = SecurityAuditAnalytics()

    analytics.summarize(
        "agent-1",
        make_events(),
    )

    snapshot = analytics.snapshot_summaries()

    assert "agent-1" in snapshot


def test_latest_request_analysis():
    analytics = SecurityAuditAnalytics()

    result = analytics.analyze_request(
        "agent-1",
        "request-1",
        make_events(),
    )

    assert (
        analytics.latest_request_analysis(
            "agent-1",
            "request-1",
        )
        == result
    )


def test_snapshot_request_analyses():
    analytics = SecurityAuditAnalytics()

    analytics.analyze_request(
        "agent-1",
        "request-1",
        make_events(),
    )

    snapshot = analytics.snapshot_request_analyses()

    assert ("agent-1", "request-1") in snapshot


def test_reset():
    analytics = SecurityAuditAnalytics()

    analytics.summarize(
        "agent-1",
        make_events(),
    )

    analytics.analyze_request(
        "agent-1",
        "request-1",
        make_events(),
    )

    analytics.reset()

    assert analytics.latest_summary("agent-1") is None
    assert (
        analytics.latest_request_analysis(
            "agent-1",
            "request-1",
        )
        is None
    )


def test_summary_is_immutable():
    analytics = SecurityAuditAnalytics()

    result = analytics.summarize(
        "agent-1",
        make_events(),
    )

    with pytest.raises(FrozenInstanceError):
        result.total_events = 999


def test_request_analysis_is_immutable():
    analytics = SecurityAuditAnalytics()

    result = analytics.analyze_request(
        "agent-1",
        "request-1",
        make_events(),
    )

    with pytest.raises(FrozenInstanceError):
        result.event_count = 999


def test_evidence_correlation_is_immutable():
    analytics = SecurityAuditAnalytics()

    result = analytics.correlate_evidence(
        "agent-1",
        make_events(),
    )

    with pytest.raises(FrozenInstanceError):
        result.event_count = 999


def test_summary_determinism():
    analytics = SecurityAuditAnalytics()

    first = analytics.summarize(
        "agent-1",
        make_events(),
    )

    second = analytics.summarize(
        "agent-1",
        make_events(),
    )

    assert first == second


def test_request_analysis_determinism():
    analytics = SecurityAuditAnalytics()

    first = analytics.analyze_request(
        "agent-1",
        "request-1",
        make_events(),
    )

    second = analytics.analyze_request(
        "agent-1",
        "request-1",
        make_events(),
    )

    assert first == second


def test_no_universal_security_score():
    analytics = SecurityAuditAnalytics()

    result = analytics.summarize(
        "agent-1",
        make_events(),
    )

    assert not hasattr(result, "risk_score")
    assert not hasattr(result, "security_score")
    assert not hasattr(result, "trust_score")


def test_analytics_does_not_modify_decision():
    events = make_events()

    original = events[2].decision

    analytics = SecurityAuditAnalytics()

    analytics.summarize(
        "agent-1",
        events,
    )

    assert events[2].decision == original