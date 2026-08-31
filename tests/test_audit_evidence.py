from datetime import datetime, timezone

import pytest

from app.audit_evidence import (
    AUDIT_SCHEMA_NAME,
    AUDIT_SCHEMA_VERSION,
    AuditEvidenceRecord,
    audit_evidence_from_dict,
    audit_evidence_from_json,
    build_evidence_summary,
    calculate_evidence_fingerprint,
    create_audit_evidence,
    create_audit_from_event,
    generate_audit_id,
    validate_audit_evidence,
)
from app.event_schema import (
    SCHEMA_VERSION,
    create_security_event,
)

TIMESTAMP = datetime(
    2026,
    8,
    29,
    10,
    0,
    0,
    tzinfo=timezone.utc,
)


def build_event():
    return create_security_event(
        timestamp=TIMESTAMP,
        agent_id="agent-001",
        action="read",
        resource="sales.csv",
        context="analytics",
        risk_score=45,
        anomaly_score=20,
        capability="file_read",
        decision="ALLOW_WITH_MONITORING",
    )


def build_record():
    return create_audit_evidence(
        event=build_event(),
        decision="ALLOW_WITH_MONITORING",
        reason="Moderate risk requires monitoring",
        behavioral_evidence={
            "denial_count": 2,
            "action_diversity": 3,
        },
        cross_context_evidence={
            "context_count": 2,
            "correlation_score": 0.65,
        },
        policy_evidence={
            "policy": "data-analysis-policy",
            "authorized": True,
        },
        triggered_rules=[
            "MODERATE_RISK",
            "BEHAVIOR_MONITORING",
        ],
        source="adaptive_response",
    )


def test_audit_schema_metadata():
    record = build_record()

    assert record.schema_name == AUDIT_SCHEMA_NAME
    assert record.schema_version == AUDIT_SCHEMA_VERSION


def test_event_schema_version_is_preserved():
    record = build_record()

    assert record.event_schema_version == SCHEMA_VERSION


def test_create_audit_evidence():
    record = build_record()

    assert isinstance(
        record,
        AuditEvidenceRecord,
    )

    assert record.agent_id == "agent-001"
    assert record.decision == (
        "ALLOW_WITH_MONITORING"
    )
    assert record.risk_score == pytest.approx(
        45.0
    )
    assert record.anomaly_score == pytest.approx(
        20.0
    )


def test_audit_id_is_generated():
    record = build_record()

    assert record.audit_id.startswith(
        "audit_"
    )

    assert len(record.audit_id) == 38


def test_audit_id_is_deterministic():
    first = generate_audit_id(
        event_id="evt_test",
        decision="ALLOW",
        timestamp=TIMESTAMP,
    )

    second = generate_audit_id(
        event_id="evt_test",
        decision="ALLOW",
        timestamp=TIMESTAMP,
    )

    assert first == second


def test_different_decision_changes_audit_id():
    first = generate_audit_id(
        event_id="evt_test",
        decision="ALLOW",
        timestamp=TIMESTAMP,
    )

    second = generate_audit_id(
        event_id="evt_test",
        decision="DENY",
        timestamp=TIMESTAMP,
    )

    assert first != second


def test_event_identity_is_preserved():
    event = build_event()
    record = build_record()

    assert record.event_id == event.event_id
    assert record.agent_id == event.agent_id
    assert record.timestamp == event.timestamp


def test_scores_are_copied_from_event():
    event = build_event()

    record = create_audit_evidence(
        event=event,
        decision="ALLOW",
        reason="Authorized",
    )

    assert record.risk_score == event.risk_score
    assert (
        record.anomaly_score
        == event.anomaly_score
    )


def test_evidence_is_preserved():
    record = build_record()

    assert record.behavioral_evidence[
        "denial_count"
    ] == 2

    assert record.cross_context_evidence[
        "context_count"
    ] == 2

    assert record.policy_evidence[
        "authorized"
    ] is True

    assert len(
        record.triggered_rules
    ) == 2


def test_to_dict():
    record = build_record()

    data = record.to_dict()

    assert data["schema_name"] == (
        AUDIT_SCHEMA_NAME
    )

    assert data["audit_id"] == (
        record.audit_id
    )

    assert data["event_id"] == (
        record.event_id
    )

    assert data["decision"] == (
        "ALLOW_WITH_MONITORING"
    )


def test_to_json_is_deterministic():
    record = build_record()

    first = record.to_json()
    second = record.to_json()

    assert first == second


def test_dict_round_trip():
    record = build_record()

    restored = audit_evidence_from_dict(
        record.to_dict()
    )

    assert restored == record


def test_json_round_trip():
    record = build_record()

    restored = audit_evidence_from_json(
        record.to_json()
    )

    assert restored == record


def test_missing_required_field_rejected():
    data = build_record().to_dict()

    del data["event_id"]

    with pytest.raises(ValueError):
        audit_evidence_from_dict(data)


def test_invalid_decision_rejected():
    with pytest.raises(ValueError):
        create_audit_evidence(
            event=build_event(),
            decision="",
            reason="Invalid",
        )


def test_invalid_reason_rejected():
    with pytest.raises(ValueError):
        create_audit_evidence(
            event=build_event(),
            decision="ALLOW",
            reason="",
        )


def test_invalid_risk_score_rejected():
    event_data = build_event().to_dict()

    event_data["risk_score"] = 150

    from app.event_schema import (
        SecurityEvent,
    )

    with pytest.raises(ValueError):
        SecurityEvent.from_dict(
            event_data
        )


def test_non_mapping_behavior_evidence_rejected():
    with pytest.raises(TypeError):
        create_audit_evidence(
            event=build_event(),
            decision="ALLOW",
            reason="Test",
            behavioral_evidence=[
                "invalid"
            ],
        )


def test_non_mapping_cross_context_evidence_rejected():
    with pytest.raises(TypeError):
        create_audit_evidence(
            event=build_event(),
            decision="ALLOW",
            reason="Test",
            cross_context_evidence=[
                "invalid"
            ],
        )


def test_non_mapping_policy_evidence_rejected():
    with pytest.raises(TypeError):
        create_audit_evidence(
            event=build_event(),
            decision="ALLOW",
            reason="Test",
            policy_evidence=[
                "invalid"
            ],
        )


def test_invalid_triggered_rules_rejected():
    with pytest.raises(TypeError):
        create_audit_evidence(
            event=build_event(),
            decision="ALLOW",
            reason="Test",
            triggered_rules="invalid",
        )


def test_wrong_event_type_rejected():
    with pytest.raises(TypeError):
        create_audit_evidence(
            event={
                "event_id": "fake",
            },
            decision="ALLOW",
            reason="Test",
        )


def test_create_audit_from_event():
    event = build_event()

    record = create_audit_from_event(
        event,
        decision="DENY",
        reason="High-risk behavior",
        triggered_rules=[
            "HIGH_RISK",
        ],
    )

    assert record.event_id == event.event_id
    assert record.decision == "DENY"
    assert record.triggered_rules == [
        "HIGH_RISK"
    ]


def test_empty_evidence_defaults_to_empty():
    record = create_audit_evidence(
        event=build_event(),
        decision="ALLOW",
        reason="Authorized",
    )

    assert record.behavioral_evidence == {}
    assert record.cross_context_evidence == {}
    assert record.policy_evidence == {}
    assert record.triggered_rules == []


def test_evidence_summary():
    record = build_record()

    summary = build_evidence_summary(
        record
    )

    assert summary["audit_id"] == (
        record.audit_id
    )

    assert summary["event_id"] == (
        record.event_id
    )

    assert summary["agent_id"] == (
        "agent-001"
    )

    assert summary[
        "behavioral_evidence_count"
    ] == 2

    assert summary[
        "cross_context_evidence_count"
    ] == 2

    assert summary[
        "policy_evidence_count"
    ] == 2

    assert summary[
        "triggered_rule_count"
    ] == 2


def test_evidence_fingerprint_is_deterministic():
    record = build_record()

    first = calculate_evidence_fingerprint(
        record
    )

    second = calculate_evidence_fingerprint(
        record
    )

    assert first == second
    assert len(first) == 64


def test_different_record_has_different_fingerprint():
    first = build_record()

    second = create_audit_evidence(
        event=build_event(),
        decision="DENY",
        reason="Different decision",
    )

    assert (
        calculate_evidence_fingerprint(first)
        != calculate_evidence_fingerprint(second)
    )


def test_validate_audit_evidence():
    record = build_record()

    assert (
        validate_audit_evidence(record)
        is True
    )


def test_validate_rejects_wrong_type():
    with pytest.raises(TypeError):
        validate_audit_evidence(
            {"audit_id": "invalid"}
        )


def test_invalid_audit_schema_name_rejected():
    data = build_record().to_dict()

    data["schema_name"] = (
        "invalid.schema"
    )

    with pytest.raises(ValueError):
        audit_evidence_from_dict(data)


def test_invalid_audit_schema_version_rejected():
    data = build_record().to_dict()

    data["schema_version"] = "999.0"

    with pytest.raises(ValueError):
        audit_evidence_from_dict(data)


def test_invalid_event_schema_version_rejected():
    data = build_record().to_dict()

    data[
        "event_schema_version"
    ] = "999.0"

    with pytest.raises(ValueError):
        audit_evidence_from_dict(data)


def test_invalid_json_rejected():
    with pytest.raises(ValueError):
        audit_evidence_from_json(
            "{invalid"
        )


def test_non_mapping_input_rejected():
    with pytest.raises(TypeError):
        audit_evidence_from_dict(
            ["invalid"]
        )


def test_naive_timestamp_rejected():
    from app.event_schema import (
        create_security_event,
    )

    with pytest.raises(ValueError):
        create_security_event(
            timestamp=datetime(
                2026,
                8,
                29,
                10,
                0,
            ),
            agent_id="agent-001",
            action="read",
            resource="sales.csv",
            context="analytics",
            risk_score=20,
            anomaly_score=10,
        )


def test_source_is_optional():
    record = create_audit_evidence(
        event=build_event(),
        decision="ALLOW",
        reason="Authorized",
    )

    assert record.source is None


def test_source_is_preserved():
    record = create_audit_evidence(
        event=build_event(),
        decision="ALLOW",
        reason="Authorized",
        source="runtime",
    )

    assert record.source == "runtime"