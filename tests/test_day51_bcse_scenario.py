from app.bcse_scenario import (
    BehavioralContext,
    CounterfactualChange,
    CounterfactualScenarioBuilder,
)


def test_behavioral_context():
    context = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    assert context.trust_score == 80
    assert context.state_score == 75
    assert context.deviation_score == 10


def test_behavioral_context_attributes():
    context = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
        attributes={
            "resource": "public-data",
        },
    )

    assert context.attributes == {
        "resource": "public-data",
    }


def test_behavioral_context_rejects_invalid_score():
    try:
        BehavioralContext(
            trust_score=101,
            state_score=75,
            deviation_score=10,
        )
        assert False
    except ValueError:
        pass


def test_behavioral_context_rejects_negative_score():
    try:
        BehavioralContext(
            trust_score=-1,
            state_score=75,
            deviation_score=10,
        )
        assert False
    except ValueError:
        pass


def test_context_attributes_are_copied():
    attributes = {
        "resource": "public-data",
    }

    context = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
        attributes=attributes,
    )

    attributes["resource"] = "private-data"

    assert context.attributes["resource"] == "public-data"


def test_counterfactual_change():
    change = CounterfactualChange(
        dimension="resource",
        current_value="public-data",
        hypothetical_value="customer-data",
        reason="Evaluate impact of expanded resource access",
    )

    assert change.dimension == "resource"
    assert change.current_value == "public-data"
    assert change.hypothetical_value == "customer-data"


def test_counterfactual_change_requires_dimension():
    try:
        CounterfactualChange(
            dimension="",
            current_value="a",
            hypothetical_value="b",
            reason="test",
        )
        assert False
    except ValueError:
        pass


def test_counterfactual_change_requires_reason():
    try:
        CounterfactualChange(
            dimension="resource",
            current_value="a",
            hypothetical_value="b",
            reason="",
        )
        assert False
    except ValueError:
        pass


def test_scenario_creation():
    builder = CounterfactualScenarioBuilder()

    current = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    hypothetical = BehavioralContext(
        trust_score=65,
        state_score=55,
        deviation_score=70,
    )

    change = CounterfactualChange(
        dimension="resource",
        current_value="public-data",
        hypothetical_value="customer-data",
        reason="Evaluate expanded resource access",
    )

    scenario = builder.create_scenario(
        "agent-1",
        current_context=current,
        hypothetical_context=hypothetical,
        changes=[change],
    )

    assert scenario.agent_id == "agent-1"
    assert scenario.scenario_id == "agent-1-cf-1"
    assert len(scenario.changes) == 1


def test_scenario_ids_increment():
    builder = CounterfactualScenarioBuilder()

    context = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    first = builder.create_scenario(
        "agent-1",
        current_context=context,
        hypothetical_context=context,
        changes=[],
    )

    second = builder.create_scenario(
        "agent-1",
        current_context=context,
        hypothetical_context=context,
        changes=[],
    )

    assert first.scenario_id == "agent-1-cf-1"
    assert second.scenario_id == "agent-1-cf-2"


def test_scenario_ids_are_agent_specific():
    builder = CounterfactualScenarioBuilder()

    context = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    first = builder.create_scenario(
        "agent-a",
        current_context=context,
        hypothetical_context=context,
        changes=[],
    )

    second = builder.create_scenario(
        "agent-b",
        current_context=context,
        hypothetical_context=context,
        changes=[],
    )

    assert first.scenario_id == "agent-a-cf-1"
    assert second.scenario_id == "agent-b-cf-1"


def test_explicit_scenario_id():
    builder = CounterfactualScenarioBuilder()

    context = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    scenario = builder.create_scenario(
        "agent-1",
        current_context=context,
        hypothetical_context=context,
        changes=[],
        scenario_id="experiment-001",
    )

    assert scenario.scenario_id == "experiment-001"


def test_compare_contexts():
    builder = CounterfactualScenarioBuilder()

    current = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    hypothetical = BehavioralContext(
        trust_score=65,
        state_score=55,
        deviation_score=70,
    )

    result = builder.compare_contexts(
        current,
        hypothetical,
    )

    assert result == {
        "trust_delta": -15,
        "state_delta": -20,
        "deviation_delta": 60,
    }


def test_zero_context_difference():
    builder = CounterfactualScenarioBuilder()

    context = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    result = builder.compare_contexts(
        context,
        context,
    )

    assert result == {
        "trust_delta": 0,
        "state_delta": 0,
        "deviation_delta": 0,
    }


def test_changed_dimensions():
    builder = CounterfactualScenarioBuilder()

    current = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    hypothetical = BehavioralContext(
        trust_score=65,
        state_score=75,
        deviation_score=70,
    )

    result = builder.changed_dimensions(
        current,
        hypothetical,
    )

    assert result == [
        "trust_delta",
        "deviation_delta",
    ]


def test_no_changed_dimensions():
    builder = CounterfactualScenarioBuilder()

    context = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    assert builder.changed_dimensions(
        context,
        context,
    ) == []


def test_scenario_evidence():
    builder = CounterfactualScenarioBuilder()

    context = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    scenario = builder.create_scenario(
        "agent-1",
        current_context=context,
        hypothetical_context=context,
        changes=[],
        evidence=[
            "Observed resource expansion",
        ],
    )

    assert scenario.evidence == [
        "Observed resource expansion",
    ]


def test_scenario_assumptions():
    builder = CounterfactualScenarioBuilder()

    context = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    scenario = builder.create_scenario(
        "agent-1",
        current_context=context,
        hypothetical_context=context,
        changes=[],
        assumptions=[
            "Hypothetical action is permitted",
        ],
    )

    assert scenario.assumptions == [
        "Hypothetical action is permitted",
    ]


def test_evidence_is_copied():
    builder = CounterfactualScenarioBuilder()

    context = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    evidence = ["Evidence A"]

    scenario = builder.create_scenario(
        "agent-1",
        current_context=context,
        hypothetical_context=context,
        changes=[],
        evidence=evidence,
    )

    evidence.append("Evidence B")

    assert scenario.evidence == ["Evidence A"]


def test_assumptions_are_copied():
    builder = CounterfactualScenarioBuilder()

    context = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    assumptions = ["Assumption A"]

    scenario = builder.create_scenario(
        "agent-1",
        current_context=context,
        hypothetical_context=context,
        changes=[],
        assumptions=assumptions,
    )

    assumptions.append("Assumption B")

    assert scenario.assumptions == ["Assumption A"]


def test_scenario_is_immutable():
    builder = CounterfactualScenarioBuilder()

    context = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    scenario = builder.create_scenario(
        "agent-1",
        current_context=context,
        hypothetical_context=context,
        changes=[],
    )

    try:
        scenario.agent_id = "other-agent"
        assert False
    except AttributeError:
        pass


def test_invalid_agent_id():
    builder = CounterfactualScenarioBuilder()

    context = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    try:
        builder.create_scenario(
            "",
            current_context=context,
            hypothetical_context=context,
            changes=[],
        )
        assert False
    except ValueError:
        pass


def test_invalid_current_context():
    builder = CounterfactualScenarioBuilder()

    context = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    try:
        builder.create_scenario(
            "agent-1",
            current_context="invalid",
            hypothetical_context=context,
            changes=[],
        )
        assert False
    except TypeError:
        pass


def test_invalid_hypothetical_context():
    builder = CounterfactualScenarioBuilder()

    context = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    try:
        builder.create_scenario(
            "agent-1",
            current_context=context,
            hypothetical_context="invalid",
            changes=[],
        )
        assert False
    except TypeError:
        pass


def test_changes_must_be_list():
    builder = CounterfactualScenarioBuilder()

    context = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    try:
        builder.create_scenario(
            "agent-1",
            current_context=context,
            hypothetical_context=context,
            changes=None,
        )
        assert False
    except TypeError:
        pass


def test_changes_must_contain_valid_objects():
    builder = CounterfactualScenarioBuilder()

    context = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    try:
        builder.create_scenario(
            "agent-1",
            current_context=context,
            hypothetical_context=context,
            changes=["invalid"],
        )
        assert False
    except TypeError:
        pass


def test_history_count():
    builder = CounterfactualScenarioBuilder()

    context = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    assert builder.history_count("agent-1") == 0

    builder.create_scenario(
        "agent-1",
        current_context=context,
        hypothetical_context=context,
        changes=[],
    )

    builder.create_scenario(
        "agent-1",
        current_context=context,
        hypothetical_context=context,
        changes=[],
    )

    assert builder.history_count("agent-1") == 2


def test_different_agents_have_independent_counts():
    builder = CounterfactualScenarioBuilder()

    context = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    builder.create_scenario(
        "agent-a",
        current_context=context,
        hypothetical_context=context,
        changes=[],
    )

    builder.create_scenario(
        "agent-a",
        current_context=context,
        hypothetical_context=context,
        changes=[],
    )

    builder.create_scenario(
        "agent-b",
        current_context=context,
        hypothetical_context=context,
        changes=[],
    )

    assert builder.history_count("agent-a") == 2
    assert builder.history_count("agent-b") == 1


def test_counterfactual_does_not_execute_anything():
    builder = CounterfactualScenarioBuilder()

    current = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    hypothetical = BehavioralContext(
        trust_score=50,
        state_score=40,
        deviation_score=80,
    )

    scenario = builder.create_scenario(
        "agent-1",
        current_context=current,
        hypothetical_context=hypothetical,
        changes=[],
    )

    assert scenario.hypothetical_context == hypothetical

    assert not hasattr(
        scenario,
        "execution_result",
    )

    assert not hasattr(
        scenario,
        "security_decision",
    )


def test_counterfactual_is_deterministic():
    builder = CounterfactualScenarioBuilder()

    current = BehavioralContext(
        trust_score=80,
        state_score=75,
        deviation_score=10,
    )

    hypothetical = BehavioralContext(
        trust_score=60,
        state_score=50,
        deviation_score=70,
    )

    first = builder.compare_contexts(
        current,
        hypothetical,
    )

    second = builder.compare_contexts(
        current,
        hypothetical,
    )

    assert first == second