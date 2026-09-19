"""Tests for the Day59 predictive control platform adapter."""

import pytest

from app.platform.predictive_control import PredictiveControlPlatformAdapter
from app.predictive_control import PredictiveControlEngine


def make_adapter() -> PredictiveControlPlatformAdapter:
    return PredictiveControlPlatformAdapter(
        high_threshold=60.0,
        critical_threshold=80.0,
        deterioration_slope=5.0,
    )


def test_recommend_returns_snapshot():
    adapter = make_adapter()

    snapshot = adapter.recommend(
        "agent-1",
        85.0,
        "DETERIORATING",
        6.0,
        "HIGH",
    )

    assert snapshot.agent_id == "agent-1"
    assert snapshot.projected_score == 85.0
    assert snapshot.projected_level == "CRITICAL"
    assert snapshot.direction == "DETERIORATING"
    assert snapshot.slope == 6.0
    assert snapshot.confidence == "HIGH"
    assert snapshot.priority >= 0.0
    assert snapshot.recommendation == "PREEMPTIVE_BLOCK"
    assert isinstance(snapshot.evidence, tuple)
    assert snapshot.evidence


def test_recommend_serialized_returns_json_friendly_mapping():
    adapter = make_adapter()

    result = adapter.recommend_serialized(
        "agent-1",
        85.0,
        "DETERIORATING",
        6.0,
        "HIGH",
    )

    assert isinstance(result, dict)
    assert result["agent_id"] == "agent-1"
    assert result["projected_score"] == 85.0
    assert result["projected_level"] == "CRITICAL"
    assert result["direction"] == "DETERIORATING"
    assert result["slope"] == 6.0
    assert result["confidence"] == "HIGH"
    assert isinstance(result["evidence"], list)
    assert result["evidence"]


def test_latest_returns_latest_snapshot_for_agent():
    adapter = make_adapter()

    adapter.recommend(
        "agent-1",
        65.0,
        "DETERIORATING",
        4.0,
        "MODERATE",
    )

    latest = adapter.latest("agent-1")

    assert latest is not None
    assert latest.agent_id == "agent-1"
    assert latest.projected_score == 65.0


def test_latest_serialized_returns_mapping():
    adapter = make_adapter()

    adapter.recommend(
        "agent-1",
        65.0,
        "DETERIORATING",
        4.0,
        "MODERATE",
    )

    latest = adapter.latest_serialized("agent-1")

    assert latest is not None
    assert isinstance(latest, dict)
    assert latest["agent_id"] == "agent-1"
    assert latest["projected_score"] == 65.0
    assert isinstance(latest["evidence"], list)


def test_latest_returns_none_for_unknown_agent():
    adapter = make_adapter()

    assert adapter.latest("missing-agent") is None
    assert adapter.latest_serialized("missing-agent") is None


def test_new_recommendation_replaces_latest_for_same_agent():
    adapter = make_adapter()

    first = adapter.recommend(
        "agent-1",
        50.0,
        "STABLE",
        0.0,
        "MODERATE",
    )

    second = adapter.recommend(
        "agent-1",
        90.0,
        "DETERIORATING",
        8.0,
        "HIGH",
    )

    assert first.projected_score == 50.0
    assert second.projected_score == 90.0

    latest = adapter.latest("agent-1")

    assert latest is not None
    assert latest.projected_score == 90.0
    assert latest.recommendation == "PREEMPTIVE_BLOCK"


def test_snapshot_all_returns_all_latest_snapshots():
    adapter = make_adapter()

    adapter.recommend(
        "agent-1",
        30.0,
        "STABLE",
        0.0,
        "MODERATE",
    )
    adapter.recommend(
        "agent-2",
        85.0,
        "DETERIORATING",
        6.0,
        "HIGH",
    )

    snapshots = adapter.snapshot_all()

    assert isinstance(snapshots, tuple)
    assert len(snapshots) == 2

    by_agent = {snapshot.agent_id: snapshot for snapshot in snapshots}

    assert set(by_agent) == {"agent-1", "agent-2"}
    assert by_agent["agent-1"].projected_score == 30.0
    assert by_agent["agent-2"].projected_score == 85.0

def test_snapshot_all_serialized_returns_json_friendly_list():
    adapter = make_adapter()

    adapter.recommend(
        "agent-1",
        30.0,
        "STABLE",
        0.0,
        "MODERATE",
    )
    adapter.recommend(
        "agent-2",
        85.0,
        "DETERIORATING",
        6.0,
        "HIGH",
    )

    snapshots = adapter.snapshot_all_serialized()

    assert isinstance(snapshots, list)
    assert len(snapshots) == 2

    by_agent = {snapshot["agent_id"]: snapshot for snapshot in snapshots}

    assert set(by_agent) == {"agent-1", "agent-2"}
    assert by_agent["agent-1"]["projected_score"] == 30.0
    assert by_agent["agent-2"]["projected_score"] == 85.0
    assert isinstance(by_agent["agent-2"]["evidence"], list)

def test_reset_one_agent():
    adapter = make_adapter()

    adapter.recommend(
        "agent-1",
        85.0,
        "DETERIORATING",
        6.0,
        "HIGH",
    )
    adapter.recommend(
        "agent-2",
        30.0,
        "STABLE",
        0.0,
        "MODERATE",
    )

    adapter.reset("agent-1")

    assert adapter.latest("agent-1") is None
    assert adapter.latest("agent-2") is not None


def test_reset_all_agents():
    adapter = make_adapter()

    adapter.recommend(
        "agent-1",
        85.0,
        "DETERIORATING",
        6.0,
        "HIGH",
    )
    adapter.recommend(
        "agent-2",
        30.0,
        "STABLE",
        0.0,
        "MODERATE",
    )

    adapter.reset()

    assert adapter.snapshot_all() == ()


def test_custom_engine_can_be_injected():
    engine = PredictiveControlEngine(
        high_threshold=60.0,
        critical_threshold=85.0,
        deterioration_slope=4.0,
    )

    adapter = PredictiveControlPlatformAdapter(engine=engine)

    snapshot = adapter.recommend(
        "agent-1",
        85.0,
        "DETERIORATING",
        4.0,
        "HIGH",
    )

    assert snapshot.projected_level == "CRITICAL"
    assert snapshot.recommendation == "PREEMPTIVE_BLOCK"


def test_agents_are_isolated():
    adapter = make_adapter()

    agent_one = adapter.recommend(
        "agent-1",
        85.0,
        "DETERIORATING",
        6.0,
        "HIGH",
    )

    agent_two = adapter.recommend(
        "agent-2",
        25.0,
        "STABLE",
        0.0,
        "MODERATE",
    )

    assert agent_one.agent_id == "agent-1"
    assert agent_two.agent_id == "agent-2"
    assert adapter.latest("agent-1").projected_score == 85.0
    assert adapter.latest("agent-2").projected_score == 25.0


def test_serialization_does_not_mutate_snapshot():
    adapter = make_adapter()

    snapshot = adapter.recommend(
        "agent-1",
        85.0,
        "DETERIORATING",
        6.0,
        "HIGH",
    )

    serialized = adapter.recommend_serialized(
        "agent-2",
        85.0,
        "DETERIORATING",
        6.0,
        "HIGH",
    )

    serialized["evidence"].append("local-test-change")

    assert isinstance(snapshot.evidence, tuple)
    assert "local-test-change" not in snapshot.evidence


def test_engine_property_returns_underlying_engine():
    engine = PredictiveControlEngine(
        high_threshold=60.0,
        critical_threshold=80.0,
        deterioration_slope=5.0,
    )

    adapter = PredictiveControlPlatformAdapter(engine=engine)

    assert adapter.engine is engine


def test_invalid_agent_id_is_rejected():
    adapter = make_adapter()

    with pytest.raises(ValueError):
        adapter.recommend(
            "",
            85.0,
            "DETERIORATING",
            6.0,
            "HIGH",
        )


def test_invalid_projected_score_is_rejected():
    adapter = make_adapter()

    with pytest.raises(ValueError):
        adapter.recommend(
            "agent-1",
            101.0,
            "DETERIORATING",
            6.0,
            "HIGH",
        )


def test_adapter_does_not_expose_execution_or_authorization_api():
    adapter = make_adapter()

    assert not hasattr(adapter, "execute")
    assert not hasattr(adapter, "enforce")
    assert not hasattr(adapter, "authorize")