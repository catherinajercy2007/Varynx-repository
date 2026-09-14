"""
Day 55 tests:
BCSE Integration with Varynx.

These tests validate only the integration/orchestration layer.
They do not redefine Day 51, Day 52, or Day 53 behavior.
"""

import pytest

from app.bcse_scenario import (
    BehavioralContext,
    CounterfactualChange,
)

from app.bcse_integration import (
    BASELINE_NAME,
    VarynxBCSEIntegration,
)


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------

def build_context():
    return BehavioralContext(
        trust_score=75,
        state_score=80,
        deviation_score=20,
        attributes={
            "agent_type": "data-analysis-agent",
            "environment": "production",
        },
    )


def build_hypothetical_context():
    return BehavioralContext(
        trust_score=55,
        state_score=60,
        deviation_score=55,
        attributes={
            "agent_type": "data-analysis-agent",
            "environment": "production",
            "hypothetical": True,
        },
    )


def build_changes():
    return [
        CounterfactualChange(
            dimension="deviation_score",
            current_value=20,
            hypothetical_value=55,
            reason="Behavioral deviation increases",
        )
    ]


def build_consequence_dimensions():
    return {
        "confidentiality": 60,
        "integrity": 50,
        "availability": 40,
        "scope": 45,
        "privilege": 50,
        "persistence": 30,
    }


def build_security_context():
    return {
        "resource_sensitivity": 70,
        "privilege_context": 60,
        "scope_context": 50,
        "environment_context": 80,
        "persistence_context": 40,
    }


# ----------------------------------------------------------------------
# Scenario creation
# ----------------------------------------------------------------------

def test_create_scenario():
    integration = VarynxBCSEIntegration()

    scenario = integration.create_scenario(
        agent_id="agent-1",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        evidence=["Observed behavioral change"],
        assumptions=["Hypothetical continuation"],
    )

    assert scenario.agent_id == "agent-1"
    assert scenario.current_context == build_context()
    assert scenario.hypothetical_context == build_hypothetical_context()
    assert len(scenario.changes) == 1


def test_pipeline_preserves_hypothetical_context():
    integration = VarynxBCSEIntegration()

    result = integration.evaluate(
        agent_id="agent-1",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        consequence_dimensions=build_consequence_dimensions(),
        security_context=build_security_context(),
    )

    assert result.scenario.current_context == build_context()
    assert (
        result.scenario.hypothetical_context
        == build_hypothetical_context()
    )


def test_hypothetical_context_required():
    integration = VarynxBCSEIntegration()

    with pytest.raises(TypeError):
        integration.create_scenario(
            agent_id="agent-1",
            current_context=build_context(),
            hypothetical_context=None,
            changes=build_changes(),
        )


def test_current_context_required():
    integration = VarynxBCSEIntegration()

    with pytest.raises(TypeError):
        integration.create_scenario(
            agent_id="agent-1",
            current_context=None,
            hypothetical_context=build_hypothetical_context(),
            changes=build_changes(),
        )


# ----------------------------------------------------------------------
# Complete pipeline
# ----------------------------------------------------------------------

def test_complete_pipeline():
    integration = VarynxBCSEIntegration()

    result = integration.evaluate(
        agent_id="agent-1",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        consequence_dimensions=build_consequence_dimensions(),
        security_context=build_security_context(),
        evidence=["Behavioral observation"],
        assumptions=["Hypothetical continuation"],
    )

    assert result.agent_id == "agent-1"
    assert result.scenario is not None
    assert result.consequence is not None
    assert result.context_aware is not None


def test_baseline_name():
    integration = VarynxBCSEIntegration()

    result = integration.evaluate(
        agent_id="agent-1",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        consequence_dimensions=build_consequence_dimensions(),
        security_context=build_security_context(),
    )

    assert result.baseline == BASELINE_NAME
    assert result.baseline == "FULL_VARYNX_BCSE"


def test_scenario_id_preserved():
    integration = VarynxBCSEIntegration()

    result = integration.evaluate(
        agent_id="agent-1",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        consequence_dimensions=build_consequence_dimensions(),
        security_context=build_security_context(),
    )

    assert result.scenario.scenario_id
    assert result.consequence.scenario_id == result.scenario.scenario_id
    assert (
        result.context_aware.scenario_id
        == result.scenario.scenario_id
    )


def test_consequence_score_exists():
    integration = VarynxBCSEIntegration()

    result = integration.evaluate(
        agent_id="agent-1",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        consequence_dimensions=build_consequence_dimensions(),
        security_context=build_security_context(),
    )

    assert 0 <= result.consequence.consequence_score <= 100


def test_context_aware_score_exists():
    integration = VarynxBCSEIntegration()

    result = integration.evaluate(
        agent_id="agent-1",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        consequence_dimensions=build_consequence_dimensions(),
        security_context=build_security_context(),
    )

    assert 0 <= result.context_aware.adjusted_consequence_score <= 100


# ----------------------------------------------------------------------
# Evidence and assumptions
# ----------------------------------------------------------------------

def test_evidence_preserved():
    integration = VarynxBCSEIntegration()

    result = integration.evaluate(
        agent_id="agent-1",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        consequence_dimensions=build_consequence_dimensions(),
        security_context=build_security_context(),
        evidence=["Observed denial pattern"],
    )

    assert "Observed denial pattern" in result.evidence


def test_assumptions_preserved():
    integration = VarynxBCSEIntegration()

    result = integration.evaluate(
        agent_id="agent-1",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        consequence_dimensions=build_consequence_dimensions(),
        security_context=build_security_context(),
        assumptions=["Scenario is hypothetical"],
    )

    assert "Scenario is hypothetical" in result.assumptions


# ----------------------------------------------------------------------
# Multiple agents
# ----------------------------------------------------------------------

def test_multiple_agents():
    integration = VarynxBCSEIntegration()

    result_1 = integration.evaluate(
        agent_id="agent-1",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        consequence_dimensions=build_consequence_dimensions(),
        security_context=build_security_context(),
    )

    result_2 = integration.evaluate(
        agent_id="agent-2",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        consequence_dimensions=build_consequence_dimensions(),
        security_context=build_security_context(),
    )

    assert result_1.agent_id == "agent-1"
    assert result_2.agent_id == "agent-2"
    assert result_1.scenario.scenario_id != result_2.scenario.scenario_id


# ----------------------------------------------------------------------
# History
# ----------------------------------------------------------------------

def test_history():
    integration = VarynxBCSEIntegration()

    integration.evaluate(
        agent_id="agent-1",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        consequence_dimensions=build_consequence_dimensions(),
        security_context=build_security_context(),
    )

    integration.evaluate(
        agent_id="agent-2",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        consequence_dimensions=build_consequence_dimensions(),
        security_context=build_security_context(),
    )

    history = integration.history()

    assert len(history) == 2


def test_latest():
    integration = VarynxBCSEIntegration()

    result = integration.evaluate(
        agent_id="agent-1",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        consequence_dimensions=build_consequence_dimensions(),
        security_context=build_security_context(),
    )

    assert integration.latest() == result


def test_history_count():
    integration = VarynxBCSEIntegration()

    assert integration.history_count() == 0

    integration.evaluate(
        agent_id="agent-1",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        consequence_dimensions=build_consequence_dimensions(),
        security_context=build_security_context(),
    )

    assert integration.history_count() == 1


def test_reset():
    integration = VarynxBCSEIntegration()

    integration.evaluate(
        agent_id="agent-1",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        consequence_dimensions=build_consequence_dimensions(),
        security_context=build_security_context(),
    )

    assert integration.history_count() == 1

    integration.reset()

    assert integration.history_count() == 0
    assert integration.latest() is None


# ----------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------

def test_invalid_agent_id():
    integration = VarynxBCSEIntegration()

    with pytest.raises(ValueError):
        integration.evaluate(
            agent_id="",
            current_context=build_context(),
            hypothetical_context=build_hypothetical_context(),
            changes=build_changes(),
            consequence_dimensions=build_consequence_dimensions(),
            security_context=build_security_context(),
        )


def test_invalid_consequence_dimensions():
    integration = VarynxBCSEIntegration()

    with pytest.raises(TypeError):
        integration.evaluate(
            agent_id="agent-1",
            current_context=build_context(),
            hypothetical_context=build_hypothetical_context(),
            changes=build_changes(),
            consequence_dimensions=None,
            security_context=build_security_context(),
        )


def test_invalid_security_context():
    integration = VarynxBCSEIntegration()

    with pytest.raises(TypeError):
        integration.evaluate(
            agent_id="agent-1",
            current_context=build_context(),
            hypothetical_context=build_hypothetical_context(),
            changes=build_changes(),
            consequence_dimensions=build_consequence_dimensions(),
            security_context=None,
        )


def test_invalid_changes():
    integration = VarynxBCSEIntegration()

    with pytest.raises(TypeError):
        integration.evaluate(
            agent_id="agent-1",
            current_context=build_context(),
            hypothetical_context=build_hypothetical_context(),
            changes=None,
            consequence_dimensions=build_consequence_dimensions(),
            security_context=build_security_context(),
        )


# ----------------------------------------------------------------------
# Boundary checks
# ----------------------------------------------------------------------

def test_scores_are_bounded():
    integration = VarynxBCSEIntegration()

    result = integration.evaluate(
        agent_id="agent-boundary",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        consequence_dimensions={
            "confidentiality": 100,
            "integrity": 100,
            "availability": 100,
            "scope": 100,
            "privilege": 100,
            "persistence": 100,
        },
        security_context={
            "resource_sensitivity": 100,
            "privilege_context": 100,
            "scope_context": 100,
            "environment_context": 100,
            "persistence_context": 100,
        },
    )

    assert 0 <= result.consequence.consequence_score <= 100
    assert (
        0
        <= result.context_aware.adjusted_consequence_score
        <= 100
    )


# ----------------------------------------------------------------------
# Immutability
# ----------------------------------------------------------------------

def test_result_is_immutable():
    integration = VarynxBCSEIntegration()

    result = integration.evaluate(
        agent_id="agent-immutable",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        consequence_dimensions=build_consequence_dimensions(),
        security_context=build_security_context(),
    )

    with pytest.raises((AttributeError, TypeError)):
        result.agent_id = "changed"


# ----------------------------------------------------------------------
# Determinism
# ----------------------------------------------------------------------

def test_repeated_evaluation_is_deterministic():
    integration = VarynxBCSEIntegration()

    result_1 = integration.evaluate(
        agent_id="agent-deterministic",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        consequence_dimensions=build_consequence_dimensions(),
        security_context=build_security_context(),
    )

    result_2 = integration.evaluate(
        agent_id="agent-deterministic",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        consequence_dimensions=build_consequence_dimensions(),
        security_context=build_security_context(),
    )

    assert (
        result_1.consequence.consequence_score
        == result_2.consequence.consequence_score
    )

    assert (
        result_1.context_aware.adjusted_consequence_score
        == result_2.context_aware.adjusted_consequence_score
    )


def test_context_adjustment_changes_with_security_context():
    integration = VarynxBCSEIntegration()

    low_context = {
        "resource_sensitivity": 10,
        "privilege_context": 10,
        "scope_context": 10,
        "environment_context": 10,
        "persistence_context": 10,
    }

    high_context = {
        "resource_sensitivity": 90,
        "privilege_context": 90,
        "scope_context": 90,
        "environment_context": 90,
        "persistence_context": 90,
    }

    low_result = integration.evaluate(
        agent_id="agent-context",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        consequence_dimensions=build_consequence_dimensions(),
        security_context=low_context,
    )

    high_result = integration.evaluate(
        agent_id="agent-context",
        current_context=build_context(),
        hypothetical_context=build_hypothetical_context(),
        changes=build_changes(),
        consequence_dimensions=build_consequence_dimensions(),
        security_context=high_context,
    )

    assert (
        high_result.context_aware.adjusted_consequence_score
        >= low_result.context_aware.adjusted_consequence_score
    )