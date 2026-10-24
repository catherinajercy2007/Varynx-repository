from datetime import datetime, timezone

import pytest

from app.audit_evidence import create_audit_evidence
from app.audit_evidence_store import AuditEvidenceStore
from app.event_schema import create_security_event


@pytest.fixture
def store(tmp_path):
    return AuditEvidenceStore(tmp_path / "day84-test.db")


def make_record(
    *,
    agent_id="agent-001",
    decision="ALLOW",
    event_id="event-001",
):
    event = create_security_event(
        timestamp=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
        agent_id=agent_id,
        action="read",
        resource="report.csv",
        context="analytics",
        risk_score=45,
        anomaly_score=20,
        capability="file_read",
        decision=decision,
        event_id=event_id,
    )
    return create_audit_evidence(
        event=event,
        decision=decision,
        reason="Day 84 storage test",
        source="test_day84",
    )


def test_save_and_retrieve_record(store):
    record = make_record()
    result = store.save(record)

    assert result["inserted"] is True
    loaded = store.get(record.audit_id)
    assert loaded is not None
    assert loaded.to_json() == record.to_json()


def test_identical_save_is_idempotent(store):
    record = make_record()
    assert store.save(record)["inserted"] is True
    assert store.save(record)["inserted"] is False


def test_conflicting_record_with_same_audit_id_is_rejected(store):
    record = make_record()
    store.save(record)

    conflicting = make_record(
        agent_id="agent-002",
        event_id="event-002",
    )
    conflicting = type(conflicting)(
        **{
            **conflicting.__dict__,
            "audit_id": record.audit_id,
        }
    )

    with pytest.raises(ValueError, match="Conflicting audit evidence"):
        store.save(conflicting)


def test_list_filters_and_pagination(store):
    store.save(make_record(agent_id="agent-001", event_id="event-001"))
    store.save(
        make_record(
            agent_id="agent-001",
            decision="DENY",
            event_id="event-002",
        )
    )
    store.save(make_record(agent_id="agent-002", event_id="event-003"))

    result = store.list_records(agent_id="agent-001", limit=1, offset=0)
    assert result["total"] == 2
    assert len(result["records"]) == 1
    assert result["records"][0]["agent_id"] == "agent-001"

    denied = store.list_records(decision="DENY")
    assert denied["total"] == 1
    assert denied["records"][0]["decision"] == "DENY"


def test_list_rejects_invalid_pagination(store):
    with pytest.raises(ValueError):
        store.list_records(limit=0)
    with pytest.raises(ValueError):
        store.list_records(limit=1001)
    with pytest.raises(ValueError):
        store.list_records(offset=-1)


def test_record_survives_store_recreation(tmp_path):
    database_path = tmp_path / "persistent-test.db"
    record = make_record()

    AuditEvidenceStore(database_path).save(record)
    reopened = AuditEvidenceStore(database_path)

    assert reopened.get(record.audit_id).to_json() == record.to_json()


def test_fingerprint_verification(store):
    record = make_record()
    store.save(record)

    result = store.verify(record.audit_id)
    assert result is not None
    assert result["valid"] is True
    assert result["stored_fingerprint"] == result["calculated_fingerprint"]


def test_missing_record_returns_none(store):
    assert store.get("audit_missing") is None
    assert store.verify("audit_missing") is None


def test_invalid_audit_id_is_rejected(store):
    with pytest.raises(ValueError):
        store.get("  ")
    with pytest.raises(ValueError):
        store.verify("")
