"""Tests for the Day 64 security decision runtime handoff."""

from app.platform.security_decision_runtime_handoff import (
    SecurityDecisionRuntimeHandoffPlatformAdapter,
)
from app.security_decision_reconciliation import (
    SecurityDecisionReconciliation,
)


def make_reconciliation(
    agent_id: str = "agent-1",
) -> SecurityDecisionReconciliation:
    return SecurityDecisionReconciliation(
        agent_id=agent_id,
        proposed_decision="STEP_UP_VERIFICATION",
        reconciled_decision="STEP_UP_VERIFICATION",
        reconciliation_status="SUPPORTED",
        projected_score=60.0,
        direction="DETERIORATING",
        slope=4.0,
        confidence="HIGH",
        consequence_score=50.0,
        deviation_score=20.0,
        evidence=("runtime handoff evidence",),
    )


def test_adapter_can_prepare_handoff():
    adapter = SecurityDecisionRuntimeHandoffPlatformAdapter()

    result = adapter.handoff(make_reconciliation())

    assert result["agent_id"] == "agent-1"
    assert result["reconciled_decision"] == (
        "STEP_UP_VERIFICATION"
    )
    assert result["runtime_handoff"] is True
    assert result["execution_required"] is True


def test_handoff_preserves_evidence():
    adapter = SecurityDecisionRuntimeHandoffPlatformAdapter()

    result = adapter.handoff(make_reconciliation())

    assert result["evidence"] == [
        "runtime handoff evidence",
    ]


def test_handoff_contains_reconciliation_snapshot():
    adapter = SecurityDecisionRuntimeHandoffPlatformAdapter()

    result = adapter.handoff(make_reconciliation())

    assert result["reconciliation"]["agent_id"] == "agent-1"
    assert result["reconciliation"]["projected_score"] == 60.0


def test_latest_returns_latest_agent_handoff():
    adapter = SecurityDecisionRuntimeHandoffPlatformAdapter()

    adapter.handoff(make_reconciliation())

    result = adapter.latest("agent-1")

    assert result is not None
    assert result["agent_id"] == "agent-1"


def test_latest_unknown_agent_returns_none():
    adapter = SecurityDecisionRuntimeHandoffPlatformAdapter()

    assert adapter.latest("unknown") is None


def test_snapshot_all_returns_mapping():
    adapter = SecurityDecisionRuntimeHandoffPlatformAdapter()

    adapter.handoff(make_reconciliation("agent-1"))
    adapter.handoff(make_reconciliation("agent-2"))

    snapshots = adapter.snapshot_all()

    assert isinstance(snapshots, dict)
    assert set(snapshots) == {
        "agent-1",
        "agent-2",
    }


def test_snapshot_all_serialized_is_json_friendly():
    adapter = SecurityDecisionRuntimeHandoffPlatformAdapter()

    adapter.handoff(make_reconciliation())

    snapshots = adapter.snapshot_all_serialized()

    assert isinstance(snapshots, dict)
    assert snapshots["agent-1"]["evidence"] == [
        "runtime handoff evidence",
    ]


def test_handoff_rejects_invalid_input():
    adapter = SecurityDecisionRuntimeHandoffPlatformAdapter()

    try:
        adapter.handoff(object())
    except TypeError as exc:
        assert "SecurityDecisionReconciliation" in str(exc)
    else:
        raise AssertionError("Expected TypeError")


def test_latest_rejects_invalid_agent_id():
    adapter = SecurityDecisionRuntimeHandoffPlatformAdapter()

    try:
        adapter.latest("")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


def test_reset_one_agent():
    adapter = SecurityDecisionRuntimeHandoffPlatformAdapter()

    adapter.handoff(make_reconciliation("agent-1"))
    adapter.handoff(make_reconciliation("agent-2"))

    adapter.reset("agent-1")

    assert adapter.latest("agent-1") is None
    assert adapter.latest("agent-2") is not None


def test_reset_all_agents():
    adapter = SecurityDecisionRuntimeHandoffPlatformAdapter()

    adapter.handoff(make_reconciliation("agent-1"))
    adapter.handoff(make_reconciliation("agent-2"))

    adapter.reset()

    assert adapter.snapshot_all() == {}