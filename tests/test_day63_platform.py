from dataclasses import fields

import pytest

from app.platform.security_decision_reconciliation import (
    SecurityDecisionReconciliationPlatformAdapter,
)
from app.security_decision_reconciliation import (
    SecurityDecisionReconciliation,
)


def make_snapshot(
    agent_id: str = "agent-1",
) -> SecurityDecisionReconciliation:
    field_names = {field.name for field in fields(SecurityDecisionReconciliation)}

    values = {
        "agent_id": agent_id,
        "proposed_decision": "STEP_UP_VERIFICATION",
        "reconciled_decision": "STEP_UP_VERIFICATION",
        "reconciliation_status": "SUPPORTED",
        "projected_score": 55.0,
        "direction": "DETERIORATING",
        "slope": 4.0,
        "confidence": "HIGH",
        "consequence_score": 50.0,
        "deviation_score": 0.0,
        "evidence": ("platform test evidence",),
    }

    return SecurityDecisionReconciliation(
        **{
            name: value
            for name, value in values.items()
            if name in field_names
        }
    )


def test_adapter_creation():
    adapter = SecurityDecisionReconciliationPlatformAdapter()

    assert adapter.latest("agent-1") is None
    assert adapter.history("agent-1") == ()


def test_reconcile_stores_snapshot():
    adapter = SecurityDecisionReconciliationPlatformAdapter()
    snapshot = make_snapshot()

    result = adapter.reconcile(snapshot=snapshot)

    assert result is snapshot
    assert adapter.latest("agent-1") is snapshot
    assert adapter.history("agent-1") == (snapshot,)


def test_serialized_returns_dictionary():
    adapter = SecurityDecisionReconciliationPlatformAdapter()
    snapshot = make_snapshot()

    result = adapter.serialized(snapshot=snapshot)

    assert isinstance(result, dict)
    assert result["agent_id"] == "agent-1"
    assert result["projected_score"] == 55.0
    assert result["evidence"] == ["platform test evidence"]


def test_latest_serialized():
    adapter = SecurityDecisionReconciliationPlatformAdapter()
    adapter.reconcile(snapshot=make_snapshot())

    result = adapter.latest_serialized("agent-1")

    assert result is not None
    assert result["agent_id"] == "agent-1"


def test_history_tracks_multiple_snapshots():
    adapter = SecurityDecisionReconciliationPlatformAdapter()

    first = make_snapshot("agent-1")
    second = make_snapshot("agent-1")

    adapter.reconcile(snapshot=first)
    adapter.reconcile(snapshot=second)

    assert adapter.history("agent-1") == (first, second)


def test_history_serialized():
    adapter = SecurityDecisionReconciliationPlatformAdapter()

    adapter.reconcile(snapshot=make_snapshot("agent-1"))
    adapter.reconcile(snapshot=make_snapshot("agent-1"))

    result = adapter.history_serialized("agent-1")

    assert len(result) == 2
    assert all(isinstance(item, dict) for item in result)


def test_snapshot_all():
    adapter = SecurityDecisionReconciliationPlatformAdapter()

    first = make_snapshot("agent-1")
    second = make_snapshot("agent-2")

    adapter.reconcile(snapshot=first)
    adapter.reconcile(snapshot=second)

    result = adapter.snapshot_all()

    assert result == (first, second)


def test_snapshot_all_serialized():
    adapter = SecurityDecisionReconciliationPlatformAdapter()

    adapter.reconcile(snapshot=make_snapshot("agent-1"))
    adapter.reconcile(snapshot=make_snapshot("agent-2"))

    result = adapter.snapshot_all_serialized()

    assert len(result) == 2
    assert all(isinstance(item, dict) for item in result)


def test_reset():
    adapter = SecurityDecisionReconciliationPlatformAdapter()

    adapter.reconcile(snapshot=make_snapshot())

    adapter.reset()

    assert adapter.latest("agent-1") is None
    assert adapter.history("agent-1") == ()
    assert adapter.snapshot_all() == ()


def test_invalid_snapshot_rejected():
    adapter = SecurityDecisionReconciliationPlatformAdapter()

    with pytest.raises(TypeError):
        adapter.reconcile(snapshot=object())