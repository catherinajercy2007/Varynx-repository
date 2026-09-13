import pytest

from app.bcse_context import (
    DEFAULT_CONTEXT_WEIGHTS,
    ContextAwareConsequenceModel,
    apply_context_to_consequence,
    calculate_context_index,
    calculate_context_modifier,
    classify_context,
    identify_context_evidence,
)


def test_default_weights_sum_to_one():
    assert sum(DEFAULT_CONTEXT_WEIGHTS.values()) == pytest.approx(1.0)


def test_context_index_with_single_dimension():
    context = {
        "resource_sensitivity": 80,
    }

    assert calculate_context_index(context) == 80.0


def test_context_index_weighted_average():
    context = {
        "resource_sensitivity": 80,
        "privilege_context": 40,
    }

    expected = (80 * 0.25 + 40 * 0.20) / (0.25 + 0.20)

    assert calculate_context_index(context) == pytest.approx(
        expected
    )


def test_missing_dimensions_are_renormalized():
    context = {
        "resource_sensitivity": 100,
    }

    assert calculate_context_index(context) == 100.0


def test_empty_context_returns_zero():
    assert calculate_context_index({}) == 0.0


def test_context_index_is_bounded():
    context = {
        "resource_sensitivity": 100,
        "privilege_context": 100,
        "scope_context": 100,
        "environment_context": 100,
        "persistence_context": 100,
    }

    assert calculate_context_index(context) == 100.0


def test_context_index_rejects_negative_values():
    with pytest.raises(ValueError):
        calculate_context_index(
            {"resource_sensitivity": -1}
        )


def test_context_index_rejects_values_above_100():
    with pytest.raises(ValueError):
        calculate_context_index(
            {"resource_sensitivity": 101}
        )


def test_context_modifier_at_zero():
    assert calculate_context_modifier(0) == 0.5


def test_context_modifier_at_fifty():
    assert calculate_context_modifier(50) == 1.0


def test_context_modifier_at_hundred():
    assert calculate_context_modifier(100) == 1.5


def test_context_modifier_is_bounded():
    assert 0.5 <= calculate_context_modifier(25) <= 1.5
    assert 0.5 <= calculate_context_modifier(75) <= 1.5


def test_low_context_classification():
    assert classify_context(10) == "LOW"


def test_moderate_context_classification():
    assert classify_context(30) == "MODERATE"


def test_high_context_classification():
    assert classify_context(60) == "HIGH"


def test_critical_context_classification():
    assert classify_context(80) == "CRITICAL"


def test_context_classification_boundary():
    assert classify_context(20) == "MODERATE"
    assert classify_context(40) == "HIGH"
    assert classify_context(70) == "CRITICAL"


def test_consequence_with_neutral_context():
    assert apply_context_to_consequence(
        60,
        50,
    ) == 60.0


def test_low_context_reduces_consequence():
    result = apply_context_to_consequence(
        60,
        0,
    )

    assert result == 30.0


def test_high_context_increases_consequence():
    result = apply_context_to_consequence(
        60,
        80,
    )

    assert result == 78.0


def test_consequence_result_is_bounded():
    result = apply_context_to_consequence(
        100,
        100,
    )

    assert result == 100.0


def test_context_evidence_for_high_dimension():
    evidence = identify_context_evidence(
        {
            "resource_sensitivity": 90,
        }
    )

    assert len(evidence) == 1
    assert "Resource sensitivity is high" in evidence[0]


def test_context_evidence_for_moderate_dimension():
    evidence = identify_context_evidence(
        {
            "scope_context": 50,
        }
    )

    assert "Scope context is moderate" in evidence[0]


def test_context_evidence_for_low_dimension():
    evidence = identify_context_evidence(
        {
            "environment_context": 10,
        }
    )

    assert "Environment context is low" in evidence[0]


def test_model_creates_estimate():
    model = ContextAwareConsequenceModel()

    result = model.estimate(
        scenario_id="agent-1-cf-1",
        consequence_score=60,
        context={
            "resource_sensitivity": 80,
            "privilege_context": 60,
        },
    )

    assert result.scenario_id == "agent-1-cf-1"
    assert result.base_consequence_score == 60.0
    assert 0 <= result.context_index <= 100
    assert 0 <= result.adjusted_consequence_score <= 100
    assert result.context_level in {
        "LOW",
        "MODERATE",
        "HIGH",
        "CRITICAL",
    }


def test_model_preserves_base_consequence():
    model = ContextAwareConsequenceModel()

    result = model.estimate(
        scenario_id="scenario-1",
        consequence_score=55,
        context={
            "resource_sensitivity": 90,
        },
    )

    assert result.base_consequence_score == 55.0


def test_model_generates_evidence():
    model = ContextAwareConsequenceModel()

    result = model.estimate(
        scenario_id="scenario-1",
        consequence_score=50,
        context={
            "resource_sensitivity": 90,
            "scope_context": 30,
        },
    )

    assert len(result.evidence) == 2


def test_model_history():
    model = ContextAwareConsequenceModel()

    model.estimate(
        scenario_id="scenario-1",
        consequence_score=50,
        context={"resource_sensitivity": 50},
    )

    model.estimate(
        scenario_id="scenario-1",
        consequence_score=60,
        context={"resource_sensitivity": 80},
    )

    history = model.history("scenario-1")

    assert len(history) == 2


def test_model_latest():
    model = ContextAwareConsequenceModel()

    model.estimate(
        scenario_id="scenario-1",
        consequence_score=40,
        context={"resource_sensitivity": 30},
    )

    latest = model.latest("scenario-1")

    assert latest is not None
    assert latest.base_consequence_score == 40


def test_latest_returns_none_for_unknown_scenario():
    model = ContextAwareConsequenceModel()

    assert model.latest("unknown") is None


def test_reset_single_scenario():
    model = ContextAwareConsequenceModel()

    model.estimate(
        scenario_id="scenario-1",
        consequence_score=40,
        context={"resource_sensitivity": 30},
    )

    model.reset("scenario-1")

    assert model.latest("scenario-1") is None


def test_reset_all():
    model = ContextAwareConsequenceModel()

    model.estimate(
        scenario_id="scenario-1",
        consequence_score=40,
        context={"resource_sensitivity": 30},
    )

    model.estimate(
        scenario_id="scenario-2",
        consequence_score=50,
        context={"resource_sensitivity": 50},
    )

    model.reset()

    assert model.latest("scenario-1") is None
    assert model.latest("scenario-2") is None


def test_custom_weights():
    context = {
        "resource_sensitivity": 100,
        "privilege_context": 0,
    }

    weights = {
        "resource_sensitivity": 0.75,
        "privilege_context": 0.25,
    }

    result = calculate_context_index(
        context,
        weights,
    )

    assert result == 75.0


def test_custom_weights_are_supported_by_model():
    model = ContextAwareConsequenceModel()

    result = model.estimate(
        scenario_id="scenario-custom",
        consequence_score=50,
        context={
            "resource_sensitivity": 100,
            "privilege_context": 0,
        },
        weights={
            "resource_sensitivity": 0.75,
            "privilege_context": 0.25,
        },
    )

    assert result.context_index == 75.0


def test_model_rejects_empty_scenario_id():
    model = ContextAwareConsequenceModel()

    with pytest.raises(ValueError):
        model.estimate(
            scenario_id="",
            consequence_score=50,
            context={"resource_sensitivity": 50},
        )


def test_model_rejects_invalid_consequence_score():
    model = ContextAwareConsequenceModel()

    with pytest.raises(ValueError):
        model.estimate(
            scenario_id="scenario-1",
            consequence_score=101,
            context={"resource_sensitivity": 50},
        )


def test_model_rejects_invalid_context_type():
    model = ContextAwareConsequenceModel()

    with pytest.raises(TypeError):
        model.estimate(
            scenario_id="scenario-1",
            consequence_score=50,
            context=None,
        )


def test_estimate_is_immutable():
    model = ContextAwareConsequenceModel()

    result = model.estimate(
        scenario_id="scenario-1",
        consequence_score=50,
        context={"resource_sensitivity": 50},
    )

    with pytest.raises(Exception):
        result.adjusted_consequence_score = 90