"""
Tests for the Day 51 BCSE platform integration.
"""

from app.bcse_scenario import (
    BehavioralContext,
    CounterfactualChange,
    CounterfactualScenarioBuilder,
)
from app.platform.bcse import BCSEPlatformAdapter


def _build_scenario(
    agent_id: str = "agent-1",
    scenario_id: str | None = None,
):
    builder = CounterfactualScenarioBuilder()

    current = BehavioralContext(
        trust_score=80.0,
        state_score=70.0,
        deviation_score=10.0,
        attributes={
            "mode": "normal",
        },
    )

    hypothetical = BehavioralContext(
        trust_score=60.0,
        state_score=50.0,
        deviation_score=30.0,
        attributes={
            "mode": "counterfactual",
        },
    )

    changes = [
        CounterfactualChange(
            dimension="trust_score",
            current_value=80.0,
            hypothetical_value=60.0,
            reason="Hypothetical trust reduction",
        ),
        CounterfactualChange(
            dimension="deviation_score",
            current_value=10.0,
            hypothetical_value=30.0,
            reason="Hypothetical deviation increase",
        ),
    ]

    return builder.create_scenario(
        agent_id,
        current_context=current,
        hypothetical_context=hypothetical,
        changes=changes,
        evidence=["behavioral observation"],
        assumptions=["hypothetical only"],
        scenario_id=scenario_id,
    )


def test_record_scenario():
    adapter = BCSEPlatformAdapter()

    scenario = _build_scenario()

    result = adapter.record_scenario(scenario)

    assert result["agent_id"] == "agent-1"
    assert result["scenario_id"] == scenario.scenario_id
    assert adapter.history_count("agent-1") == 1


def test_latest_scenario():
    adapter = BCSEPlatformAdapter()

    first = _build_scenario(
        scenario_id="agent-1-cf-1",
    )
    second = _build_scenario(
        scenario_id="agent-1-cf-2",
    )

    adapter.record_scenario(first)
    adapter.record_scenario(second)

    latest = adapter.latest_scenario("agent-1")

    assert latest is not None
    assert latest["scenario_id"] == "agent-1-cf-2"


def test_history_preserves_scenario_data():
    adapter = BCSEPlatformAdapter()

    scenario = _build_scenario()

    adapter.record_scenario(scenario)

    history = adapter.scenario_history("agent-1")

    assert len(history) == 1

    stored = history[0]

    assert stored["agent_id"] == "agent-1"
    assert stored["scenario_id"] == scenario.scenario_id

    assert stored["current_context"]["trust_score"] == 80.0
    assert stored["hypothetical_context"]["trust_score"] == 60.0

    assert len(stored["changes"]) == 2
    assert stored["changes"][0]["dimension"] == "trust_score"

    assert stored["evidence"] == [
        "behavioral observation",
    ]

    assert stored["assumptions"] == [
        "hypothetical only",
    ]


def test_context_attributes_are_serialized():
    adapter = BCSEPlatformAdapter()

    scenario = _build_scenario()

    result = adapter.record_scenario(scenario)

    assert result["current_context"]["attributes"] == {
        "mode": "normal",
    }

    assert result["hypothetical_context"]["attributes"] == {
        "mode": "counterfactual",
    }


def test_agent_histories_are_isolated():
    adapter = BCSEPlatformAdapter()

    scenario_a = _build_scenario(
        agent_id="agent-a",
        scenario_id="agent-a-cf-1",
    )

    scenario_b = _build_scenario(
        agent_id="agent-b",
        scenario_id="agent-b-cf-1",
    )

    adapter.record_scenario(scenario_a)
    adapter.record_scenario(scenario_b)

    assert adapter.history_count("agent-a") == 1
    assert adapter.history_count("agent-b") == 1

    assert (
        adapter.latest_scenario("agent-a")["agent_id"]
        == "agent-a"
    )

    assert (
        adapter.latest_scenario("agent-b")["agent_id"]
        == "agent-b"
    )


def test_missing_agent_has_no_history():
    adapter = BCSEPlatformAdapter()

    assert adapter.latest_scenario("unknown-agent") is None
    assert adapter.scenario_history("unknown-agent") == []
    assert adapter.history_count("unknown-agent") == 0


def test_reset_single_agent():
    adapter = BCSEPlatformAdapter()

    adapter.record_scenario(
        _build_scenario(
            agent_id="agent-a",
            scenario_id="agent-a-cf-1",
        )
    )

    adapter.record_scenario(
        _build_scenario(
            agent_id="agent-b",
            scenario_id="agent-b-cf-1",
        )
    )

    adapter.reset_scenarios("agent-a")

    assert adapter.history_count("agent-a") == 0
    assert adapter.history_count("agent-b") == 1


def test_reset_all_agents():
    adapter = BCSEPlatformAdapter()

    adapter.record_scenario(
        _build_scenario(
            agent_id="agent-a",
            scenario_id="agent-a-cf-1",
        )
    )

    adapter.record_scenario(
        _build_scenario(
            agent_id="agent-b",
            scenario_id="agent-b-cf-1",
        )
    )

    adapter.reset_scenarios()

    assert adapter.history_count("agent-a") == 0
    assert adapter.history_count("agent-b") == 0


def test_invalid_scenario_is_rejected():
    adapter = BCSEPlatformAdapter()

    try:
        adapter.record_scenario("not-a-scenario")
    except TypeError as exc:
        assert "CounterfactualScenario" in str(exc)
    else:
        raise AssertionError(
            "Expected TypeError for invalid scenario"
        )


def test_platform_does_not_create_security_decision():
    adapter = BCSEPlatformAdapter()

    scenario = _build_scenario()

    result = adapter.record_scenario(scenario)

    assert "risk_score" not in result
    assert "decision" not in result
    assert "action" not in result
    assert "response" not in result
    assert "authorized" not in result


def test_scenario_history_returns_serialized_copies():
    adapter = BCSEPlatformAdapter()

    scenario = _build_scenario()

    adapter.record_scenario(scenario)

    history = adapter.scenario_history("agent-1")

    history[0]["evidence"].append("local mutation")

    fresh_history = adapter.scenario_history("agent-1")

    assert fresh_history[0]["evidence"] == [
        "behavioral observation",
    ]