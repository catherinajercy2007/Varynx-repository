"""Tests for the Day60 predictive runtime platform adapter."""

import pytest

from app.platform.predictive_runtime import (
    PredictiveRuntimePlatformAdapter,
)
from app.predictive_runtime import (
    CONTROL_MAINTAIN,
    CONTROL_PREEMPTIVE_BLOCK,
    CONTROL_REDUCE_SCOPE,
    DIRECTION_DETERIORATING,
    DIRECTION_STABLE,
    CONFIDENCE_HIGH,
    RUNTIME_ESCALATED,
    RUNTIME_READY,
    PredictiveRuntimeIntegration,
)


def make_adapter() -> PredictiveRuntimePlatformAdapter:
    return PredictiveRuntimePlatformAdapter()


def test_prepare_decision_returns_runtime_decision():
    adapter = make_adapter()

    decision = adapter.prepare_decision(
        "agent-1",
        60.0,
        DIRECTION_DETERIORATING,
        10.0,
        CONFIDENCE_HIGH,
        CONTROL_REDUCE_SCOPE,
    )

    assert decision.agent_id == "agent-1"
    assert decision.projected_score == 60.0
    assert decision.direction == DIRECTION_DETERIORATING
    assert decision.slope == 10.0
    assert decision.confidence == CONFIDENCE_HIGH
    assert decision.recommendation == CONTROL_REDUCE_SCOPE
    assert decision.runtime_state == RUNTIME_READY
    assert decision.execution_required is True
    assert decision.evidence


def test_prepare_decision_serialized_returns_mapping():
    adapter = make_adapter()

    result = adapter.prepare_decision_serialized(
        "agent-1",
        60.0,
        DIRECTION_DETERIORATING,
        10.0,
        CONFIDENCE_HIGH,
        CONTROL_REDUCE_SCOPE,
    )

    assert isinstance(result, dict)
    assert result["agent_id"] == "agent-1"
    assert result["projected_score"] == 60.0
    assert result["direction"] == DIRECTION_DETERIORATING
    assert result["recommendation"] == CONTROL_REDUCE_SCOPE
    assert result["runtime_state"] == RUNTIME_READY
    assert result["execution_required"] is True
    assert isinstance(result["evidence"], list)


def test_escalated_recommendation_is_preserved():
    adapter = make_adapter()

    decision = adapter.prepare_decision(
        "agent-1",
        90.0,
        DIRECTION_DETERIORATING,
        20.0,
        CONFIDENCE_HIGH,
        CONTROL_PREEMPTIVE_BLOCK,
    )

    assert decision.runtime_state == RUNTIME_ESCALATED
    assert decision.recommendation == CONTROL_PREEMPTIVE_BLOCK
    assert decision.execution_required is True


def test_latest_returns_latest_decision():
    adapter = make_adapter()

    decision = adapter.prepare_decision(
        "agent-1",
        50.0,
        DIRECTION_STABLE,
        0.0,
        CONFIDENCE_HIGH,
        CONTROL_MAINTAIN,
    )

    assert adapter.latest("agent-1") == decision


def test_latest_serialized_returns_mapping():
    adapter = make_adapter()

    adapter.prepare_decision(
        "agent-1",
        50.0,
        DIRECTION_STABLE,
        0.0,
        CONFIDENCE_HIGH,
        CONTROL_MAINTAIN,
    )

    result = adapter.latest_serialized("agent-1")

    assert isinstance(result, dict)
    assert result["agent_id"] == "agent-1"
    assert result["recommendation"] == CONTROL_MAINTAIN
    assert isinstance(result["evidence"], list)


def test_latest_returns_none_for_unknown_agent():
    adapter = make_adapter()

    assert adapter.latest("missing-agent") is None
    assert adapter.latest_serialized("missing-agent") is None


def test_new_decision_replaces_latest_for_same_agent():
    adapter = make_adapter()

    adapter.prepare_decision(
        "agent-1",
        40.0,
        DIRECTION_STABLE,
        0.0,
        CONFIDENCE_HIGH,
        CONTROL_MAINTAIN,
    )

    second = adapter.prepare_decision(
        "agent-1",
        80.0,
        DIRECTION_DETERIORATING,
        10.0,
        CONFIDENCE_HIGH,
        CONTROL_REDUCE_SCOPE,
    )

    assert adapter.latest("agent-1") == second
    assert adapter.latest("agent-1").projected_score == 80.0


def test_snapshot_all_returns_tuple():
    adapter = make_adapter()

    adapter.prepare_decision(
        "agent-1",
        20.0,
        DIRECTION_STABLE,
        0.0,
        CONFIDENCE_HIGH,
        CONTROL_MAINTAIN,
    )
    adapter.prepare_decision(
        "agent-2",
        90.0,
        DIRECTION_DETERIORATING,
        20.0,
        CONFIDENCE_HIGH,
        CONTROL_PREEMPTIVE_BLOCK,
    )

    snapshots = adapter.snapshot_all()

    assert isinstance(snapshots, tuple)
    assert len(snapshots) == 2
    assert {
        item.agent_id
        for item in snapshots
    } == {"agent-1", "agent-2"}


def test_snapshot_all_serialized_returns_list():
    adapter = make_adapter()

    adapter.prepare_decision(
        "agent-1",
        20.0,
        DIRECTION_STABLE,
        0.0,
        CONFIDENCE_HIGH,
        CONTROL_MAINTAIN,
    )
    adapter.prepare_decision(
        "agent-2",
        90.0,
        DIRECTION_DETERIORATING,
        20.0,
        CONFIDENCE_HIGH,
        CONTROL_PREEMPTIVE_BLOCK,
    )

    snapshots = adapter.snapshot_all_serialized()

    assert isinstance(snapshots, list)
    assert len(snapshots) == 2

    by_agent = {
        item["agent_id"]: item
        for item in snapshots
    }

    assert by_agent["agent-1"]["recommendation"] == CONTROL_MAINTAIN
    assert (
        by_agent["agent-2"]["recommendation"]
        == CONTROL_PREEMPTIVE_BLOCK
    )
    assert isinstance(by_agent["agent-2"]["evidence"], list)


def test_reset_single_agent():
    adapter = make_adapter()

    adapter.prepare_decision(
        "agent-1",
        20.0,
        DIRECTION_STABLE,
        0.0,
        CONFIDENCE_HIGH,
        CONTROL_MAINTAIN,
    )
    adapter.prepare_decision(
        "agent-2",
        80.0,
        DIRECTION_DETERIORATING,
        10.0,
        CONFIDENCE_HIGH,
        CONTROL_REDUCE_SCOPE,
    )

    adapter.reset("agent-1")

    assert adapter.latest("agent-1") is None
    assert adapter.latest("agent-2") is not None


def test_reset_all_agents():
    adapter = make_adapter()

    adapter.prepare_decision(
        "agent-1",
        20.0,
        DIRECTION_STABLE,
        0.0,
        CONFIDENCE_HIGH,
        CONTROL_MAINTAIN,
    )
    adapter.prepare_decision(
        "agent-2",
        80.0,
        DIRECTION_DETERIORATING,
        10.0,
        CONFIDENCE_HIGH,
        CONTROL_REDUCE_SCOPE,
    )

    adapter.reset()

    assert adapter.snapshot_all() == ()


def test_custom_integration_can_be_injected():
    integration = PredictiveRuntimeIntegration()
    adapter = PredictiveRuntimePlatformAdapter(
        integration=integration,
    )

    decision = adapter.prepare_decision(
        "agent-1",
        60.0,
        DIRECTION_DETERIORATING,
        10.0,
        CONFIDENCE_HIGH,
        CONTROL_REDUCE_SCOPE,
    )

    assert adapter.integration is integration
    assert adapter.latest("agent-1") == decision


def test_custom_evidence_is_preserved():
    adapter = make_adapter()

    decision = adapter.prepare_decision(
        "agent-1",
        60.0,
        DIRECTION_DETERIORATING,
        10.0,
        CONFIDENCE_HIGH,
        CONTROL_REDUCE_SCOPE,
        evidence=[
            "External behavioral evidence",
            "Context evidence",
        ],
    )

    assert "External behavioral evidence" in decision.evidence
    assert "Context evidence" in decision.evidence


def test_serialized_evidence_is_independent_list():
    adapter = make_adapter()

    result = adapter.prepare_decision_serialized(
        "agent-1",
        60.0,
        DIRECTION_DETERIORATING,
        10.0,
        CONFIDENCE_HIGH,
        CONTROL_REDUCE_SCOPE,
    )

    result["evidence"].append("local mutation")

    latest = adapter.latest("agent-1")

    assert latest is not None
    assert "local mutation" not in latest.evidence


def test_invalid_agent_id_is_rejected():
    adapter = make_adapter()

    with pytest.raises(ValueError):
        adapter.prepare_decision(
            "",
            50.0,
            DIRECTION_STABLE,
            0.0,
            CONFIDENCE_HIGH,
            CONTROL_MAINTAIN,
        )


def test_invalid_score_is_rejected():
    adapter = make_adapter()

    with pytest.raises(ValueError):
        adapter.prepare_decision(
            "agent-1",
            101.0,
            DIRECTION_STABLE,
            0.0,
            CONFIDENCE_HIGH,
            CONTROL_MAINTAIN,
        )


def test_invalid_direction_is_rejected():
    adapter = make_adapter()

    with pytest.raises(ValueError):
        adapter.prepare_decision(
            "agent-1",
            50.0,
            "INVALID",
            0.0,
            CONFIDENCE_HIGH,
            CONTROL_MAINTAIN,
        )


def test_invalid_confidence_is_rejected():
    adapter = make_adapter()

    with pytest.raises(ValueError):
        adapter.prepare_decision(
            "agent-1",
            50.0,
            DIRECTION_STABLE,
            0.0,
            "INVALID",
            CONTROL_MAINTAIN,
        )


def test_invalid_recommendation_is_rejected():
    adapter = make_adapter()

    with pytest.raises(ValueError):
        adapter.prepare_decision(
            "agent-1",
            50.0,
            DIRECTION_STABLE,
            0.0,
            CONFIDENCE_HIGH,
            "INVALID",
        )


def test_runtime_adapter_does_not_expose_execution_api():
    adapter = make_adapter()

    assert not hasattr(adapter, "execute")
    assert not hasattr(adapter, "enforce")
    assert not hasattr(adapter, "authorize")
    assert not hasattr(adapter, "block")