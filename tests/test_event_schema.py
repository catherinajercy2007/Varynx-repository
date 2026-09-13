from datetime import datetime, timezone

import pytest

from app.event_schema import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SecurityEvent,
    canonicalize_event,
    create_security_event,
    generate_event_id,
    get_schema_metadata,
    validate_event,
)


TIMESTAMP = datetime(
    2026,
    8,
    23,
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
        risk_score=35,
        anomaly_score=10,
        capability="file_read",
        decision="ALLOW",
        reason="Authorized resource access",
        source="runtime",
        behavioral_evidence={
            "action_diversity": 2,
            "denial_count": 0,
        },
        cross_context_evidence={
            "context_count": 1,
        },
        metadata={
            "environment": "test",
        },
    )


def test_schema_metadata():
    metadata = get_schema_metadata()

    assert metadata["schema_name"] == SCHEMA_NAME
    assert metadata["schema_version"] == SCHEMA_VERSION


def test_create_security_event():
    event = build_event()

    assert isinstance(event, SecurityEvent)
    assert event.agent_id == "agent-001"
    assert event.action == "read"
    assert event.resource == "sales.csv"
    assert event.context == "analytics"
    assert event.risk_score == pytest.approx(35.0)
    assert event.anomaly_score == pytest.approx(10.0)


def test_event_id_is_generated():
    event = build_event()

    assert event.event_id.startswith(
        "evt_"
    )

    assert len(event.event_id) == 36


def test_event_id_is_deterministic():
    first = generate_event_id(
        timestamp=TIMESTAMP,
        agent_id="agent-001",
        action="read",
        resource="sales.csv",
        context="analytics",
    )

    second = generate_event_id(
        timestamp=TIMESTAMP,
        agent_id="agent-001",
        action="read",
        resource="sales.csv",
        context="analytics",
    )

    assert first == second


def test_different_event_attributes_produce_different_ids():
    first = generate_event_id(
        timestamp=TIMESTAMP,
        agent_id="agent-001",
        action="read",
        resource="sales.csv",
        context="analytics",
    )

    second = generate_event_id(
        timestamp=TIMESTAMP,
        agent_id="agent-001",
        action="delete",
        resource="sales.csv",
        context="analytics",
    )

    assert first != second


def test_event_to_dict():
    event = build_event()

    data = event.to_dict()

    assert data["schema_name"] == SCHEMA_NAME
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["agent_id"] == "agent-001"
    assert data["action"] == "read"
    assert data["risk_score"] == 35.0


def test_event_to_json_is_valid_and_deterministic():
    event = build_event()

    first = event.to_json()
    second = event.to_json()

    assert first == second
    assert '"agent_id":"agent-001"' in first


def test_round_trip_dict():
    original = build_event()

    restored = SecurityEvent.from_dict(
        original.to_dict()
    )

    assert restored == original


def test_round_trip_json():
    original = build_event()

    restored = SecurityEvent.from_json(
        original.to_json()
    )

    assert restored == original


def test_missing_required_field_is_rejected():
    data = build_event().to_dict()

    del data["agent_id"]

    with pytest.raises(ValueError):
        SecurityEvent.from_dict(data)


def test_invalid_risk_score_is_rejected():
    with pytest.raises(ValueError):
        create_security_event(
            timestamp=TIMESTAMP,
            agent_id="agent-001",
            action="read",
            resource="sales.csv",
            context="analytics",
            risk_score=101,
            anomaly_score=10,
        )


def test_negative_risk_score_is_rejected():
    with pytest.raises(ValueError):
        create_security_event(
            timestamp=TIMESTAMP,
            agent_id="agent-001",
            action="read",
            resource="sales.csv",
            context="analytics",
            risk_score=-1,
            anomaly_score=10,
        )


def test_invalid_anomaly_score_is_rejected():
    with pytest.raises(ValueError):
        create_security_event(
            timestamp=TIMESTAMP,
            agent_id="agent-001",
            action="read",
            resource="sales.csv",
            context="analytics",
            risk_score=20,
            anomaly_score=101,
        )


def test_boolean_score_is_rejected():
    with pytest.raises(TypeError):
        create_security_event(
            timestamp=TIMESTAMP,
            agent_id="agent-001",
            action="read",
            resource="sales.csv",
            context="analytics",
            risk_score=True,
            anomaly_score=10,
        )


def test_empty_agent_id_is_rejected():
    with pytest.raises(ValueError):
        create_security_event(
            timestamp=TIMESTAMP,
            agent_id="",
            action="read",
            resource="sales.csv",
            context="analytics",
            risk_score=20,
            anomaly_score=10,
        )


def test_empty_action_is_rejected():
    with pytest.raises(ValueError):
        create_security_event(
            timestamp=TIMESTAMP,
            agent_id="agent-001",
            action="",
            resource="sales.csv",
            context="analytics",
            risk_score=20,
            anomaly_score=10,
        )


def test_empty_resource_is_rejected():
    with pytest.raises(ValueError):
        create_security_event(
            timestamp=TIMESTAMP,
            agent_id="agent-001",
            action="read",
            resource="",
            context="analytics",
            risk_score=20,
            anomaly_score=10,
        )


def test_empty_context_is_rejected():
    with pytest.raises(ValueError):
        create_security_event(
            timestamp=TIMESTAMP,
            agent_id="agent-001",
            action="read",
            resource="sales.csv",
            context="",
            risk_score=20,
            anomaly_score=10,
        )


def test_naive_timestamp_is_rejected():
    with pytest.raises(ValueError):
        create_security_event(
            timestamp=datetime(
                2026,
                8,
                23,
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


def test_iso_timestamp_is_supported():
    event = create_security_event(
        timestamp="2026-08-23T10:00:00Z",
        agent_id="agent-001",
        action="read",
        resource="sales.csv",
        context="analytics",
        risk_score=20,
        anomaly_score=10,
    )

    assert event.timestamp.tzinfo is not None
    assert event.timestamp.utcoffset().total_seconds() == 0


def test_timestamp_is_normalized_to_utc():
    event = create_security_event(
        timestamp="2026-08-23T15:30:00+05:30",
        agent_id="agent-001",
        action="read",
        resource="sales.csv",
        context="analytics",
        risk_score=20,
        anomaly_score=10,
    )

    assert event.timestamp.hour == 10
    assert event.timestamp.minute == 0


def test_optional_fields_can_be_absent():
    event = create_security_event(
        timestamp=TIMESTAMP,
        agent_id="agent-001",
        action="read",
        resource="sales.csv",
        context="analytics",
        risk_score=20,
        anomaly_score=10,
    )

    assert event.capability is None
    assert event.decision is None
    assert event.reason is None
    assert event.source is None


def test_evidence_defaults_to_empty_mapping():
    event = create_security_event(
        timestamp=TIMESTAMP,
        agent_id="agent-001",
        action="read",
        resource="sales.csv",
        context="analytics",
        risk_score=20,
        anomaly_score=10,
    )

    assert event.behavioral_evidence == {}
    assert event.cross_context_evidence == {}
    assert event.metadata == {}


def test_validate_event():
    event = build_event()

    assert validate_event(event) is True


def test_validate_event_rejects_wrong_type():
    with pytest.raises(TypeError):
        validate_event({"agent_id": "agent-001"})


def test_canonicalize_event():
    event = build_event()

    canonical = canonicalize_event(
        event.to_dict()
    )

    assert canonical["schema_name"] == SCHEMA_NAME
    assert canonical["schema_version"] == SCHEMA_VERSION
    assert canonical["agent_id"] == "agent-001"


def test_invalid_schema_name_is_rejected():
    data = build_event().to_dict()

    data["schema_name"] = (
        "some.other.schema"
    )

    with pytest.raises(ValueError):
        SecurityEvent.from_dict(data)


def test_invalid_schema_version_is_rejected():
    data = build_event().to_dict()

    data["schema_version"] = "999.0"

    with pytest.raises(ValueError):
        SecurityEvent.from_dict(data)


def test_invalid_json_is_rejected():
    with pytest.raises(ValueError):
        SecurityEvent.from_json(
            "{invalid-json"
        )


def test_non_mapping_evidence_is_rejected():
    with pytest.raises(TypeError):
        create_security_event(
            timestamp=TIMESTAMP,
            agent_id="agent-001",
            action="read",
            resource="sales.csv",
            context="analytics",
            risk_score=20,
            anomaly_score=10,
            behavioral_evidence=[
                "invalid"
            ],
        )


def test_long_agent_id_is_rejected():
    with pytest.raises(ValueError):
        create_security_event(
            timestamp=TIMESTAMP,
            agent_id="a" * 129,
            action="read",
            resource="sales.csv",
            context="analytics",
            risk_score=20,
            anomaly_score=10,
        )


def test_long_action_is_rejected():
    with pytest.raises(ValueError):
        create_security_event(
            timestamp=TIMESTAMP,
            agent_id="agent-001",
            action="a" * 129,
            resource="sales.csv",
            context="analytics",
            risk_score=20,
            anomaly_score=10,
        )