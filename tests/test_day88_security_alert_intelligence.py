
from datetime import datetime, timedelta, timezone

import pytest

from app.security_alert_intelligence import (
    ESCALATION_EMERGENCY,
    ESCALATION_NONE,
    ESCALATION_PRIORITY,
    ESCALATION_REVIEW,
    REASON_EMERGENCY_CONTROL,
    REASON_EVIDENCE_INCOMPLETE,
    REASON_RISK_CRITICAL,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_INFO,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    AlertPolicy,
    build_security_alert,
    classify_alert_severity,
)


NOW = datetime(2026, 10, 20, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def policy():
    return AlertPolicy(
        policy_id="alert-policy-v1",
        medium_threshold=40,
        high_threshold=60,
        critical_threshold=80,
    )


def build(policy, **overrides):
    values = {
        "agent_id": "agent-1",
        "alert_type": "behavioral_anomaly",
        "risk_score": 25,
        "observed_at": NOW,
        "policy": policy,
        "reason_codes": (),
        "evidence_references": ("evidence-1",),
        "correlation_id": "request-1",
        "emergency_control_active": False,
        "evidence_complete": True,
    }
    values.update(overrides)
    return build_security_alert(**values)


@pytest.mark.parametrize(
    "score,expected",
    [
        (0, SEVERITY_INFO),
        (1, SEVERITY_LOW),
        (39.99, SEVERITY_LOW),
        (40, SEVERITY_MEDIUM),
        (59.99, SEVERITY_MEDIUM),
        (60, SEVERITY_HIGH),
        (79.99, SEVERITY_HIGH),
        (80, SEVERITY_CRITICAL),
        (100, SEVERITY_CRITICAL),
    ],
)
def test_severity_thresholds(policy, score, expected):
    assert classify_alert_severity(
        risk_score=score, policy=policy
    ) == expected


def test_low_risk_has_no_escalation(policy):
    alert = build(policy, risk_score=20)
    assert alert.severity == SEVERITY_LOW
    assert alert.escalation_recommendation == ESCALATION_NONE


def test_medium_risk_recommends_security_review(policy):
    alert = build(policy, risk_score=45)
    assert alert.severity == SEVERITY_MEDIUM
    assert alert.escalation_recommendation == ESCALATION_REVIEW


def test_high_risk_recommends_priority_review(policy):
    alert = build(policy, risk_score=70)
    assert alert.severity == SEVERITY_HIGH
    assert alert.escalation_recommendation == ESCALATION_PRIORITY


def test_critical_risk_recommends_emergency_review(policy):
    alert = build(policy, risk_score=90)
    assert alert.severity == SEVERITY_CRITICAL
    assert alert.escalation_recommendation == ESCALATION_EMERGENCY
    assert REASON_RISK_CRITICAL in alert.reason_codes


def test_active_emergency_control_raises_severity(policy):
    alert = build(
        policy,
        risk_score=10,
        emergency_control_active=True,
    )
    assert alert.severity == SEVERITY_HIGH
    assert REASON_EMERGENCY_CONTROL in alert.reason_codes


def test_incomplete_evidence_is_explicitly_recorded(policy):
    alert = build(policy, evidence_complete=False)
    assert alert.evidence_complete is False
    assert REASON_EVIDENCE_INCOMPLETE in alert.reason_codes
    assert "incomplete" in alert.summary.lower()


def test_incomplete_evidence_requires_review_for_noncritical_alert(policy):
    alert = build(
        policy,
        risk_score=70,
        evidence_complete=False,
    )
    assert alert.escalation_recommendation == ESCALATION_REVIEW


def test_critical_alert_remains_escalated_with_incomplete_evidence(policy):
    alert = build(
        policy,
        risk_score=90,
        evidence_complete=False,
    )
    assert alert.escalation_recommendation == ESCALATION_EMERGENCY


def test_reason_codes_are_deduplicated_and_sorted(policy):
    alert = build(
        policy,
        risk_score=90,
        reason_codes=("CUSTOM_REASON", "CUSTOM_REASON"),
    )
    assert alert.reason_codes == tuple(sorted(set(alert.reason_codes)))
    assert "CUSTOM_REASON" in alert.reason_codes


def test_evidence_references_are_deduplicated_and_sorted(policy):
    alert = build(
        policy,
        evidence_references=("ev-2", "ev-1", "ev-2"),
    )
    assert alert.evidence_references == ("ev-1", "ev-2")


def test_same_identity_produces_same_alert_id(policy):
    first = build(policy, observed_at=NOW, risk_score=50)
    second = build(
        policy,
        observed_at=NOW + timedelta(minutes=5),
        risk_score=75,
    )
    assert first.alert_id == second.alert_id
    assert first.deduplication_key == second.deduplication_key


def test_different_correlation_ids_produce_different_alert_ids(policy):
    first = build(policy, correlation_id="request-1")
    second = build(policy, correlation_id="request-2")
    assert first.alert_id != second.alert_id


def test_different_agents_produce_different_alert_ids(policy):
    first = build(policy, agent_id="agent-1")
    second = build(policy, agent_id="agent-2")
    assert first.alert_id != second.alert_id


def test_different_alert_types_produce_different_alert_ids(policy):
    first = build(policy, alert_type="ANOMALY")
    second = build(policy, alert_type="CAPABILITY_REVOCATION")
    assert first.alert_id != second.alert_id


def test_invalid_risk_score_is_rejected(policy):
    for score in (-1, 101, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            build(policy, risk_score=score)


def test_naive_timestamp_is_rejected(policy):
    with pytest.raises(ValueError, match="timezone-aware"):
        build(policy, observed_at=datetime(2026, 10, 20, 10, 0))


def test_invalid_threshold_order_is_rejected():
    with pytest.raises(ValueError, match="medium < high < critical"):
        AlertPolicy(
            policy_id="invalid",
            medium_threshold=60,
            high_threshold=50,
            critical_threshold=80,
        )


def test_empty_policy_id_is_rejected():
    with pytest.raises(ValueError):
        AlertPolicy(policy_id=" ")


def test_empty_reason_code_is_rejected(policy):
    with pytest.raises(ValueError):
        build(policy, reason_codes=(" ",))


def test_empty_evidence_reference_is_rejected(policy):
    with pytest.raises(ValueError):
        build(policy, evidence_references=(" ",))


def test_correlation_id_can_be_missing(policy):
    alert = build(policy, correlation_id=None)
    assert alert.correlation_id is None
    assert alert.alert_id.startswith("alert-")


def test_alert_serialization_declares_boundaries(policy):
    data = build(policy, risk_score=85).to_dict()
    assert data["is_authorization_decision"] is False
    assert data["executes_enforcement"] is False
    assert data["sends_notification"] is False
    assert data["version"] == "DAY88-V1"


def test_summary_contains_severity_agent_and_score(policy):
    alert = build(policy, risk_score=65)
    assert "HIGH" in alert.summary
    assert "agent-1" in alert.summary
    assert "65.00/100" in alert.summary


def test_input_collections_are_not_mutated(policy):
    reasons = ["CUSTOM_REASON"]
    references = ["evidence-2", "evidence-1"]
    build(
        policy,
        reason_codes=reasons,
        evidence_references=references,
    )
    assert reasons == ["CUSTOM_REASON"]
    assert references == ["evidence-2", "evidence-1"]


def test_emergency_control_at_critical_risk_is_critical(policy):
    assert classify_alert_severity(
        risk_score=95,
        policy=policy,
        emergency_control_active=True,
    ) == SEVERITY_CRITICAL
