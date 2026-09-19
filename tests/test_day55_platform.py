import pytest

from app.bcse_integration import (
    BCSEIntegrationResult,
    VarynxBCSEIntegration,
)
from app.bcse_scenario import (
    BehavioralContext,
    CounterfactualChange,
)
from app.platform.bcse_integration import (
    BCSEIntegrationPlatformAdapter,
)


def build_result(agent_id: str = "agent-1") -> BCSEIntegrationResult:
    integration = VarynxBCSEIntegration()

    current_context = BehavioralContext(
        trust_score=70.0,
        state_score=60.0,
        deviation_score=20.0,
        attributes={"source": "test"},
    )

    hypothetical_context = BehavioralContext(
        trust_score=50.0,
        state_score=45.0,
        deviation_score=40.0,
        attributes={"source": "test"},
    )

    changes = (
        CounterfactualChange(
            dimension="trust_score",
            current_value=70.0,
            hypothetical_value=50.0,
            reason="test counterfactual change",
        ),
    )

    return integration.evaluate(
        agent_id=agent_id,
        current_context=current_context,
        hypothetical_context=hypothetical_context,
        changes=changes,
        consequence_dimensions={
            "availability": 50.0,
            "integrity": 40.0,
        },
        security_context={
            "trust": 30.0,
            "state": 40.0,
            "deviation": 30.0,
        },
        evidence=("test evidence",),
        assumptions=("test assumption",),
    )


def test_record_integration():
    adapter = BCSEIntegrationPlatformAdapter()
    result = build_result()

    stored = adapter.record_integration(result)

    assert stored["agent_id"] == "agent-1"
    assert stored["scenario"]["scenario_id"] == (
        result.scenario.scenario_id
    )
    assert stored["consequence"]["scenario_id"] == (
        result.consequence.scenario_id
    )
    assert stored["context_aware"]["scenario_id"] == (
        result.context_aware.scenario_id
    )


def test_latest_integration():
    adapter = BCSEIntegrationPlatformAdapter()

    first = build_result()
    second = build_result()

    adapter.record_integration(first)
    adapter.record_integration(second)

    latest = adapter.latest_integration("agent-1")

    assert latest is not None
    assert latest["scenario"]["scenario_id"] == (
        second.scenario.scenario_id
    )


def test_latest_missing_agent_returns_none():
    adapter = BCSEIntegrationPlatformAdapter()

    assert adapter.latest_integration("missing") is None


def test_history_preserves_order():
    adapter = BCSEIntegrationPlatformAdapter()

    first = build_result()
    second = build_result()

    adapter.record_integration(first)
    adapter.record_integration(second)

    history = adapter.integration_history("agent-1")

    assert len(history) == 2
    assert (
        history[0]["scenario"]["scenario_id"]
        == first.scenario.scenario_id
    )
    assert (
        history[1]["scenario"]["scenario_id"]
        == second.scenario.scenario_id
    )


def test_history_count():
    adapter = BCSEIntegrationPlatformAdapter()

    assert adapter.history_count("agent-1") == 0

    adapter.record_integration(build_result())

    assert adapter.history_count("agent-1") == 1


def test_agent_isolation():
    adapter = BCSEIntegrationPlatformAdapter()

    agent_a = build_result("agent-a")
    agent_b = build_result("agent-b")

    adapter.record_integration(agent_a)
    adapter.record_integration(agent_b)

    assert adapter.history_count("agent-a") == 1
    assert adapter.history_count("agent-b") == 1

    assert (
        adapter.latest_integration("agent-a")["agent_id"]
        == "agent-a"
    )
    assert (
        adapter.latest_integration("agent-b")["agent_id"]
        == "agent-b"
    )


def test_reset_single_agent():
    adapter = BCSEIntegrationPlatformAdapter()

    adapter.record_integration(build_result("agent-a"))
    adapter.record_integration(build_result("agent-b"))

    adapter.reset_integrations("agent-a")

    assert adapter.history_count("agent-a") == 0
    assert adapter.history_count("agent-b") == 1


def test_reset_all_agents():
    adapter = BCSEIntegrationPlatformAdapter()

    adapter.record_integration(build_result("agent-a"))
    adapter.record_integration(build_result("agent-b"))

    adapter.reset_integrations()

    assert adapter.history_count("agent-a") == 0
    assert adapter.history_count("agent-b") == 0


def test_serialization_is_fresh():
    adapter = BCSEIntegrationPlatformAdapter()
    result = build_result()

    stored = adapter.record_integration(result)

    stored["agent_id"] = "tampered"
    stored["evidence"].append("tampered")
    stored["scenario"]["evidence"].append("tampered")

    latest = adapter.latest_integration("agent-1")

    assert latest is not None
    assert latest["agent_id"] == "agent-1"
    assert "tampered" not in latest["evidence"]
    assert "tampered" not in latest["scenario"]["evidence"]


def test_scenario_changes_are_serialized():
    adapter = BCSEIntegrationPlatformAdapter()
    result = build_result()

    stored = adapter.record_integration(result)

    assert len(stored["scenario"]["changes"]) == 1
    assert (
        stored["scenario"]["changes"][0]["dimension"]
        == "trust_score"
    )


def test_consequence_fields_are_preserved():
    adapter = BCSEIntegrationPlatformAdapter()
    result = build_result()

    stored = adapter.record_integration(result)

    consequence = stored["consequence"]

    assert consequence["consequence_score"] == (
        result.consequence.consequence_score
    )
    assert consequence["consequence_level"] == (
        result.consequence.consequence_level
    )
    assert consequence["confidence"] == (
        result.consequence.confidence
    )


def test_context_aware_fields_are_preserved():
    adapter = BCSEIntegrationPlatformAdapter()
    result = build_result()

    stored = adapter.record_integration(result)

    context = stored["context_aware"]

    assert context["context_index"] == (
        result.context_aware.context_index
    )
    assert context["context_modifier"] == (
        result.context_aware.context_modifier
    )
    assert context["adjusted_consequence_score"] == (
        result.context_aware.adjusted_consequence_score
    )


def test_evidence_and_assumptions_are_preserved():
    adapter = BCSEIntegrationPlatformAdapter()
    result = build_result()

    stored = adapter.record_integration(result)

    assert "test evidence" in stored["evidence"]
    assert "test assumption" in stored["assumptions"]


def test_invalid_result_is_rejected():
    adapter = BCSEIntegrationPlatformAdapter()

    with pytest.raises(TypeError):
        adapter.record_integration(object())


def test_invalid_agent_id_is_rejected():
    adapter = BCSEIntegrationPlatformAdapter()

    with pytest.raises(ValueError):
        adapter.latest_integration("")


def test_reset_invalid_agent_id_is_rejected():
    adapter = BCSEIntegrationPlatformAdapter()

    with pytest.raises(TypeError):
        adapter.reset_integrations(123)