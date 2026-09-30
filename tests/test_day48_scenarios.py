"""
Day 48 - Experimental Scenario Matrix Tests
"""

import sys
from pathlib import Path


EVALUATION_DIR = (
    Path(__file__).resolve().parents[1] / "evaluation"
)

sys.path.insert(0, str(EVALUATION_DIR))


from scenarios import (
    SCENARIO_CATEGORIES,
    get_scenario,
    get_scenarios,
    get_scenarios_by_category,
)


def test_scenario_matrix_is_not_empty():
    scenarios = get_scenarios()

    assert len(scenarios) > 0


def test_scenario_ids_are_unique():
    scenarios = get_scenarios()

    ids = [scenario.scenario_id for scenario in scenarios]

    assert len(ids) == len(set(ids))


def test_all_categories_are_represented():
    scenarios = get_scenarios()

    categories = {
        scenario.category
        for scenario in scenarios
    }

    assert categories == set(SCENARIO_CATEGORIES)


def test_normal_scenarios_are_non_malicious():
    scenarios = get_scenarios_by_category("normal")

    assert len(scenarios) > 0

    for scenario in scenarios:
        assert scenario.expected_label == 0
        assert scenario.expected_risk == "low"


def test_suspicious_scenarios_are_present():
    scenarios = get_scenarios_by_category("suspicious")

    assert len(scenarios) > 0

    for scenario in scenarios:
        assert scenario.expected_label == 1


def test_malicious_scenarios_are_present():
    scenarios = get_scenarios_by_category("malicious")

    assert len(scenarios) > 0

    for scenario in scenarios:
        assert scenario.expected_label == 1
        assert scenario.expected_risk == "high"


def test_scenario_lookup():
    scenario = get_scenario("S05")

    assert scenario.name == "Behavioral Drift"
    assert scenario.category == "suspicious"


def test_invalid_scenario_id_is_rejected():
    try:
        get_scenario("INVALID")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_invalid_category_is_rejected():
    try:
        get_scenarios_by_category("unknown")
        assert False, "Expected ValueError"
    except ValueError:
        pass