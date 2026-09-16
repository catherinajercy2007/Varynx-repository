"""
Tests for Varynx Day 49 platform behavioral integration.
"""

from __future__ import annotations

import pytest

from app.behavioral_baseline import AdaptiveBehavioralBaseline
from app.platform.behavioral import BehavioralPlatformAdapter


def make_adapter() -> BehavioralPlatformAdapter:
    """Create an adapter with deterministic test configuration."""
    manager = AdaptiveBehavioralBaseline(
        learning_rate=0.10,
        max_learning_deviation=30.0,
    )

    return BehavioralPlatformAdapter(manager)


def test_adapter_can_be_created():
    adapter = make_adapter()

    assert isinstance(
        adapter.manager,
        AdaptiveBehavioralBaseline,
    )


def test_set_baseline_returns_platform_response():
    adapter = make_adapter()

    result = adapter.set_baseline(
        "agent-1",
        {
            "tool_usage": 40.0,
            "resource_access": 50.0,
        },
    )

    assert result["status"] == "baseline_set"
    assert result["agent_id"] == "agent-1"
    assert result["baseline"] == {
        "tool_usage": 40.0,
        "resource_access": 50.0,
    }


def test_get_baseline_returns_existing_baseline():
    adapter = make_adapter()

    adapter.set_baseline(
        "agent-1",
        {
            "tool_usage": 40.0,
            "resource_access": 50.0,
        },
    )

    result = adapter.get_baseline("agent-1")

    assert result["status"] == "baseline_available"
    assert result["baseline"] == {
        "tool_usage": 40.0,
        "resource_access": 50.0,
    }


def test_get_missing_baseline_is_safe():
    adapter = make_adapter()

    result = adapter.get_baseline("unknown-agent")

    assert result["status"] == "baseline_not_found"
    assert result["baseline"] is None


def test_normal_observation_is_processed():
    adapter = make_adapter()

    adapter.set_baseline(
        "agent-1",
        {
            "tool_usage": 40.0,
            "resource_access": 50.0,
        },
    )

    result = adapter.observe(
        "agent-1",
        {
            "tool_usage": 45.0,
            "resource_access": 52.0,
        },
    )

    assert result["status"] == "observation_processed"
    assert result["result"]["accepted"] is True
    assert result["result"]["agent_id"] == "agent-1"


def test_observation_result_is_serialization_safe():
    adapter = make_adapter()

    adapter.set_baseline(
        "agent-1",
        {
            "tool_usage": 40.0,
        },
    )

    result = adapter.observe(
        "agent-1",
        {
            "tool_usage": 45.0,
        },
    )

    payload = result["result"]

    assert isinstance(payload, dict)
    assert isinstance(payload["previous_baseline"], dict)
    assert isinstance(payload["observation"], dict)
    assert isinstance(payload["updated_baseline"], dict)
    assert isinstance(payload["reason"], str)


def test_high_deviation_is_rejected_by_existing_engine():
    adapter = make_adapter()

    adapter.set_baseline(
        "agent-1",
        {
            "tool_usage": 20.0,
            "resource_access": 20.0,
        },
    )

    result = adapter.observe(
        "agent-1",
        {
            "tool_usage": 100.0,
            "resource_access": 100.0,
        },
    )

    assert result["result"]["accepted"] is False


def test_platform_adapter_does_not_override_baseline_decision():
    adapter = make_adapter()

    adapter.set_baseline(
        "agent-1",
        {
            "tool_usage": 20.0,
        },
    )

    result = adapter.observe(
        "agent-1",
        {
            "tool_usage": 100.0,
        },
    )

    baseline = adapter.get_baseline("agent-1")

    assert result["result"]["accepted"] is False
    assert baseline["baseline"] == {
        "tool_usage": 20.0,
    }


def test_history_is_exposed_through_platform():
    adapter = make_adapter()

    adapter.set_baseline(
        "agent-1",
        {
            "tool_usage": 40.0,
        },
    )

    adapter.observe(
        "agent-1",
        {
            "tool_usage": 45.0,
        },
    )

    adapter.observe(
        "agent-1",
        {
            "tool_usage": 50.0,
        },
    )

    result = adapter.history("agent-1")

    assert result["status"] == "history_available"
    assert result["count"] == 2
    assert len(result["history"]) == 2


def test_latest_is_exposed_through_platform():
    adapter = make_adapter()

    adapter.set_baseline(
        "agent-1",
        {
            "tool_usage": 40.0,
        },
    )

    adapter.observe(
        "agent-1",
        {
            "tool_usage": 45.0,
        },
    )

    result = adapter.latest("agent-1")

    assert result["status"] == "latest_available"
    assert result["latest"] is not None
    assert result["latest"]["update_index"] == 1


def test_latest_for_agent_without_history_is_safe():
    adapter = make_adapter()

    result = adapter.latest("agent-1")

    assert result["status"] == "latest_not_found"
    assert result["latest"] is None


def test_multiple_agents_are_isolated():
    adapter = make_adapter()

    adapter.set_baseline(
        "agent-1",
        {
            "tool_usage": 20.0,
        },
    )

    adapter.set_baseline(
        "agent-2",
        {
            "tool_usage": 80.0,
        },
    )

    agent1 = adapter.get_baseline("agent-1")
    agent2 = adapter.get_baseline("agent-2")

    assert agent1["baseline"] == {
        "tool_usage": 20.0,
    }

    assert agent2["baseline"] == {
        "tool_usage": 80.0,
    }


def test_reset_single_agent():
    adapter = make_adapter()

    adapter.set_baseline(
        "agent-1",
        {
            "tool_usage": 20.0,
        },
    )

    adapter.set_baseline(
        "agent-2",
        {
            "tool_usage": 80.0,
        },
    )

    result = adapter.reset("agent-1")

    assert result["status"] == "baseline_reset"
    assert result["agent_id"] == "agent-1"

    assert adapter.get_baseline(
        "agent-1"
    )["baseline"] is None

    assert adapter.get_baseline(
        "agent-2"
    )["baseline"] == {
        "tool_usage": 80.0,
    }


def test_reset_all_agents():
    adapter = make_adapter()

    adapter.set_baseline(
        "agent-1",
        {
            "tool_usage": 20.0,
        },
    )

    adapter.set_baseline(
        "agent-2",
        {
            "tool_usage": 80.0,
        },
    )

    result = adapter.reset()

    assert result["status"] == "all_baselines_reset"

    assert adapter.get_baseline(
        "agent-1"
    )["baseline"] is None

    assert adapter.get_baseline(
        "agent-2"
    )["baseline"] is None


def test_adapter_preserves_validation_errors():
    adapter = make_adapter()

    with pytest.raises(ValueError):
        adapter.set_baseline(
            "agent-1",
            {},
        )


def test_observation_requires_existing_baseline():
    adapter = make_adapter()

    with pytest.raises(ValueError):
        adapter.observe(
            "agent-1",
            {
                "tool_usage": 50.0,
            },
        )


def test_adapter_does_not_make_security_decisions():
    adapter = make_adapter()

    adapter.set_baseline(
        "agent-1",
        {
            "tool_usage": 40.0,
        },
    )

    result = adapter.observe(
        "agent-1",
        {
            "tool_usage": 45.0,
        },
    )

    assert "allow" not in result
    assert "block" not in result
    assert "decision" not in result
    assert "response" not in result


def test_baseline_observation_changes_are_reflected():
    adapter = make_adapter()

    adapter.set_baseline(
        "agent-1",
        {
            "tool_usage": 40.0,
        },
    )

    adapter.observe(
        "agent-1",
        {
            "tool_usage": 60.0,
        },
    )

    result = adapter.get_baseline("agent-1")

    assert result["baseline"]["tool_usage"] == 42.0


def test_platform_history_contains_explanation():
    adapter = make_adapter()

    adapter.set_baseline(
        "agent-1",
        {
            "tool_usage": 40.0,
        },
    )

    adapter.observe(
        "agent-1",
        {
            "tool_usage": 45.0,
        },
    )

    result = adapter.history("agent-1")

    record = result["history"][0]

    assert record["reason"]
    assert isinstance(record["reason"], str)