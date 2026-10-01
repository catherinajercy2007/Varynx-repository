"""
Tests for Day 48 evaluation scenarios.
"""

import pytest

from evaluation.scenarios import (
    SCENARIOS,
    EvaluationScenario,
    get_scenario,
    get_scenarios,
    get_scenarios_by_decision,
    get_scenarios_by_risk,
    scenario_summary,
)


def test_scenario_count():
    """Verify that the expected number of scenarios exists."""
    scenarios = get_scenarios()

    assert len(scenarios) == 8


def test_scenarios_have_unique_ids():
    """Every scenario must have a unique identifier."""
    scenario_ids = [scenario.scenario_id for scenario in get_scenarios()]

    assert len(scenario_ids) == len(set(scenario_ids))


def test_scenario_structure():
    """Every scenario must contain the required fields."""
    for scenario in get_scenarios():
        assert isinstance(scenario, EvaluationScenario)
        assert scenario.scenario_id
        assert scenario.name
        assert scenario.description
        assert scenario.agent_id
        assert scenario.action
        assert scenario.resource
        assert scenario.expected_decision
        assert scenario.expected_risk_level


def test_scenario_ids_are_complete():
    """Verify the S01-S08 scenario set."""
    scenario_ids = {
        scenario.scenario_id
        for scenario in get_scenarios()
    }

    expected_ids = {
        "S01",
        "S02",
        "S03",
        "S04",
        "S05",
        "S06",
        "S07",
        "S08",
    }

    assert scenario_ids == expected_ids


def test_authorized_scenarios_are_allowed():
    """Authorized scenarios should have ALLOW as expected decision."""
    allowed = get_scenarios_by_decision("ALLOW")

    assert len(allowed) == 2

    for scenario in allowed:
        assert scenario.expected_decision == "ALLOW"


def test_unauthorized_scenarios_are_denied():
    """Security-sensitive scenarios should be denied."""
    denied = get_scenarios_by_decision("DENY")

    assert len(denied) == 6

    for scenario in denied:
        assert scenario.expected_decision == "DENY"


def test_high_and_critical_risk_scenarios():
    """Verify high and critical risk scenarios."""
    high_risk = get_scenarios_by_risk("HIGH")
    critical_risk = get_scenarios_by_risk("CRITICAL")

    assert len(high_risk) == 4
    assert len(critical_risk) == 2


def test_get_scenario():
    """Verify individual scenario lookup."""
    scenario = get_scenario("S05")

    assert scenario.scenario_id == "S05"
    assert scenario.expected_decision == "DENY"
    assert scenario.expected_risk_level == "CRITICAL"


def test_unknown_scenario_raises_error():
    """Unknown scenario IDs should raise ValueError."""
    with pytest.raises(ValueError):
        get_scenario("S99")


def test_scenario_summary():
    """Verify scenario summary metrics."""
    summary = scenario_summary()

    assert summary["total_scenarios"] == 8
    assert summary["allow_cases"] == 2
    assert summary["deny_cases"] == 6
    assert summary["low_risk_cases"] == 2
    assert summary["high_risk_cases"] == 4
    assert summary["critical_risk_cases"] == 2


def test_case_insensitive_filters():
    """Scenario filters should accept lowercase input."""
    assert len(get_scenarios_by_decision("allow")) == 2
    assert len(get_scenarios_by_decision("deny")) == 6
    assert len(get_scenarios_by_risk("critical")) == 2