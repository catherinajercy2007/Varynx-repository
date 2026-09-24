"""Tests for the Day62 security decision bridge platform adapter."""

import pytest

from app.platform.security_decision_bridge import (
    SecurityDecisionBridgePlatformAdapter,
)
from app.security_decision_bridge import (
    BehavioralSecurityDecisionBridge,
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    DECISION_ALLOW,
    DECISION_BLOCK,
    DECISION_REDUCE_SCOPE,
    DECISION_STEP_UP,
    DIRECTION_DETERIORATING,
    DIRECTION_IMPROVING,
    DIRECTION_STABLE,
)


def make_adapter() -> SecurityDecisionBridgePlatformAdapter:
    return SecurityDecisionBridgePlatformAdapter()


def test_evaluate_returns_security_decision_snapshot():
    adapter = make_adapter()

    snapshot = adapter.evaluate(
        agent_id="agent-1",
        projected_score=60.0,
        direction=DIRECTION_DETERIORATING,
        slope=8.0,
        confidence=CONFIDENCE_HIGH,
    )

    assert snapshot.agent_id == "agent-1"
    assert snapshot.projected_score == 60.0
    assert snapshot.direction == DIRECTION_DETERIORATING
    assert snapshot.slope == 8.0
    assert snapshot.confidence == CONFIDENCE_HIGH
    assert snapshot.decision == DECISION_REDUCE_SCOPE
    assert snapshot.priority == 76.0
    assert snapshot.evidence


def test_evaluate_serialized_returns_mapping():
    adapter = make_adapter()

    result = adapter.evaluate_serialized(
        agent_id="agent-1",
        projected_score=60.0,
        direction=DIRECTION_DETERIORATING,
        slope=8.0,
        confidence=CONFIDENCE_HIGH,
    )

    assert isinstance(result, dict)
    assert result["agent_id"] == "agent-1"
    assert result["projected_score"] == 60.0
    assert result["decision"] == DECISION_REDUCE_SCOPE
    assert result["priority"] == 76.0
    assert isinstance(result["evidence"], list)


def test_critical_behavior_produces_block_recommendation():
    adapter = make_adapter()

    snapshot = adapter.evaluate(
        agent_id="agent-1",
        projected_score=90.0,
        direction=DIRECTION_DETERIORATING,
        slope=20.0,
        confidence=CONFIDENCE_HIGH,
    )

    assert snapshot.decision == DECISION_BLOCK
    assert snapshot.priority == 100.0


def test_improving_behavior_produces_step_up_for_high_score():
    adapter = make_adapter()

    snapshot = adapter.evaluate(
        agent_id="agent-1",
        projected_score=60.0,
        direction=DIRECTION_IMPROVING,
        slope=-8.0,
        confidence=CONFIDENCE_HIGH,
    )

    assert snapshot.decision == DECISION_STEP_UP
    assert snapshot.priority == 60.0


def test_latest_returns_latest_snapshot():
    adapter = make_adapter()

    created = adapter.evaluate(
        agent_id="agent-1",
        projected_score=20.0,
        direction=DIRECTION_STABLE,
        slope=0.0,
        confidence=CONFIDENCE_HIGH,
    )

    assert adapter.latest("agent-1") == created


def test_latest_serialized_returns_mapping():
    adapter = make_adapter()

    adapter.evaluate(
        agent_id="agent-1",
        projected_score=20.0,
        direction=DIRECTION_STABLE,
        slope=0.0,
        confidence=CONFIDENCE_HIGH,
    )

    result = adapter.latest_serialized("agent-1")

    assert isinstance(result, dict)
    assert result["agent_id"] == "agent-1"
    assert result["decision"] == DECISION_ALLOW
    assert isinstance(result["evidence"], list)


def test_latest_unknown_agent_returns_none():
    adapter = make_adapter()

    assert adapter.latest("missing-agent") is None
    assert adapter.latest_serialized("missing-agent") is None


def test_history_returns_all_agent_decisions():
    adapter = make_adapter()

    adapter.evaluate(
        agent_id="agent-1",
        projected_score=20.0,
        direction=DIRECTION_STABLE,
        slope=0.0,
        confidence=CONFIDENCE_HIGH,
    )

    adapter.evaluate(
        agent_id="agent-1",
        projected_score=60.0,
        direction=DIRECTION_DETERIORATING,
        slope=10.0,
        confidence=CONFIDENCE_HIGH,
    )

    history = adapter.history("agent-1")

    assert len(history) == 2
    assert history[0].projected_score == 20.0
    assert history[1].projected_score == 60.0


def test_history_serialized_returns_list():
    adapter = make_adapter()

    adapter.evaluate(
        agent_id="agent-1",
        projected_score=20.0,
        direction=DIRECTION_STABLE,
        slope=0.0,
        confidence=CONFIDENCE_HIGH,
    )

    history = adapter.history_serialized("agent-1")

    assert isinstance(history, list)
    assert len(history) == 1
    assert history[0]["agent_id"] == "agent-1"
    assert isinstance(history[0]["evidence"], list)


def test_snapshot_all_returns_dictionary():
    adapter = make_adapter()

    adapter.evaluate(
        agent_id="agent-1",
        projected_score=20.0,
        direction=DIRECTION_STABLE,
        slope=0.0,
        confidence=CONFIDENCE_HIGH,
    )

    adapter.evaluate(
        agent_id="agent-2",
        projected_score=85.0,
        direction=DIRECTION_DETERIORATING,
        slope=10.0,
        confidence=CONFIDENCE_HIGH,
    )

    snapshots = adapter.snapshot_all()

    assert isinstance(snapshots, dict)
    assert set(snapshots) == {"agent-1", "agent-2"}
    assert snapshots["agent-1"].decision == DECISION_ALLOW
    assert snapshots["agent-2"].decision == DECISION_BLOCK


def test_snapshot_all_serialized_returns_dictionary():
    adapter = make_adapter()

    adapter.evaluate(
        agent_id="agent-1",
        projected_score=20.0,
        direction=DIRECTION_STABLE,
        slope=0.0,
        confidence=CONFIDENCE_HIGH,
    )

    snapshots = adapter.snapshot_all_serialized()

    assert isinstance(snapshots, dict)
    assert "agent-1" in snapshots
    assert isinstance(snapshots["agent-1"], dict)
    assert isinstance(snapshots["agent-1"]["evidence"], list)


def test_reset_single_agent():
    adapter = make_adapter()

    adapter.evaluate(
        agent_id="agent-1",
        projected_score=20.0,
        direction=DIRECTION_STABLE,
        slope=0.0,
        confidence=CONFIDENCE_HIGH,
    )

    adapter.evaluate(
        agent_id="agent-2",
        projected_score=30.0,
        direction=DIRECTION_STABLE,
        slope=0.0,
        confidence=CONFIDENCE_HIGH,
    )

    adapter.reset("agent-1")

    assert adapter.latest("agent-1") is None
    assert adapter.latest("agent-2") is not None


def test_reset_all_agents():
    adapter = make_adapter()

    adapter.evaluate(
        agent_id="agent-1",
        projected_score=20.0,
        direction=DIRECTION_STABLE,
        slope=0.0,
        confidence=CONFIDENCE_HIGH,
    )

    adapter.evaluate(
        agent_id="agent-2",
        projected_score=30.0,
        direction=DIRECTION_STABLE,
        slope=0.0,
        confidence=CONFIDENCE_HIGH,
    )

    adapter.reset()

    assert adapter.snapshot_all() == {}


def test_custom_bridge_can_be_injected():
    bridge = BehavioralSecurityDecisionBridge()

    adapter = SecurityDecisionBridgePlatformAdapter(
        bridge=bridge,
    )

    assert adapter.bridge is bridge


def test_source_evidence_is_preserved():
    adapter = make_adapter()

    snapshot = adapter.evaluate(
        agent_id="agent-1",
        projected_score=75.0,
        direction=DIRECTION_DETERIORATING,
        slope=5.0,
        confidence=CONFIDENCE_HIGH,
        evidence=[
            "high behavioral deviation",
            "declining trust",
        ],
    )

    assert "high behavioral deviation" in snapshot.evidence
    assert "declining trust" in snapshot.evidence


def test_serialization_does_not_mutate_snapshot():
    adapter = make_adapter()

    result = adapter.evaluate_serialized(
        agent_id="agent-1",
        projected_score=60.0,
        direction=DIRECTION_DETERIORATING,
        slope=8.0,
        confidence=CONFIDENCE_HIGH,
    )

    result["evidence"].append("local mutation")

    latest = adapter.latest("agent-1")

    assert latest is not None
    assert "local mutation" not in latest.evidence


def test_agents_are_isolated():
    adapter = make_adapter()

    first = adapter.evaluate(
        agent_id="agent-1",
        projected_score=10.0,
        direction=DIRECTION_STABLE,
        slope=0.0,
        confidence=CONFIDENCE_HIGH,
    )

    second = adapter.evaluate(
        agent_id="agent-2",
        projected_score=85.0,
        direction=DIRECTION_DETERIORATING,
        slope=10.0,
        confidence=CONFIDENCE_HIGH,
    )

    assert adapter.latest("agent-1") == first
    assert adapter.latest("agent-2") == second
    assert len(adapter.history("agent-1")) == 1
    assert len(adapter.history("agent-2")) == 1


def test_invalid_agent_id_is_rejected():
    adapter = make_adapter()

    with pytest.raises(ValueError):
        adapter.evaluate(
            agent_id="",
            projected_score=50.0,
            direction=DIRECTION_STABLE,
            slope=0.0,
            confidence=CONFIDENCE_HIGH,
        )


def test_invalid_score_is_rejected():
    adapter = make_adapter()

    with pytest.raises(ValueError):
        adapter.evaluate(
            agent_id="agent-1",
            projected_score=101.0,
            direction=DIRECTION_STABLE,
            slope=0.0,
            confidence=CONFIDENCE_HIGH,
        )


def test_invalid_direction_is_rejected():
    adapter = make_adapter()

    with pytest.raises(ValueError):
        adapter.evaluate(
            agent_id="agent-1",
            projected_score=50.0,
            direction="INVALID",
            slope=0.0,
            confidence=CONFIDENCE_HIGH,
        )


def test_invalid_confidence_is_rejected():
    adapter = make_adapter()

    with pytest.raises(ValueError):
        adapter.evaluate(
            agent_id="agent-1",
            projected_score=50.0,
            direction=DIRECTION_STABLE,
            slope=0.0,
            confidence="INVALID",
        )


def test_invalid_evidence_is_rejected():
    adapter = make_adapter()

    with pytest.raises(ValueError):
        adapter.evaluate(
            agent_id="agent-1",
            projected_score=50.0,
            direction=DIRECTION_STABLE,
            slope=0.0,
            confidence=CONFIDENCE_HIGH,
            evidence="not-a-list",
        )


def test_adapter_does_not_expose_authorization_or_execution_api():
    adapter = make_adapter()

    assert not hasattr(adapter, "authorize")
    assert not hasattr(adapter, "execute")
    assert not hasattr(adapter, "enforce")
    assert not hasattr(adapter, "block")