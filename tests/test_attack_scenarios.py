import pytest

from app.attack_scenarios import (
    ATTACK_SCENARIO_TYPES,
    get_attack_scenario,
    get_attack_scenarios,
    get_attack_scenarios_by_severity,
    get_attack_scenarios_by_type,
    get_attack_scenario_summary,
    sample_attack_scenarios,
)


def test_attack_catalog_contains_eight_scenarios():

    scenarios = get_attack_scenarios()

    assert len(scenarios) == 8


def test_all_attack_types_are_represented():

    scenarios = get_attack_scenarios()

    scenario_types = {
        scenario["scenario_type"]
        for scenario in scenarios
    }

    assert scenario_types == set(
        ATTACK_SCENARIO_TYPES
    )


def test_required_fields_exist():

    scenario = get_attack_scenarios()[0]

    required_fields = {
        "scenario_id",
        "scenario_type",
        "name",
        "agent_id",
        "task_id",
        "actions",
        "resources",
        "severity",
        "ground_truth",
        "expected_signal",
        "description",
        "evaluation_purpose",
    }

    assert required_fields.issubset(
        scenario.keys()
    )


def test_scenario_ids_are_unique():

    scenarios = get_attack_scenarios()

    ids = [
        scenario["scenario_id"]
        for scenario in scenarios
    ]

    assert len(ids) == len(
        set(ids)
    )


def test_get_specific_scenario():

    scenario = get_attack_scenario(
        "ATTACK-001"
    )

    assert scenario is not None

    assert (
        scenario["name"]
        == "Unauthorized Resource Access"
    )


def test_unknown_scenario_returns_none():

    assert (
        get_attack_scenario(
            "INVALID-ID"
        )
        is None
    )


def test_severity_filter():

    critical = (
        get_attack_scenarios_by_severity(
            "CRITICAL"
        )
    )

    assert critical

    assert all(
        scenario["severity"]
        == "CRITICAL"
        for scenario in critical
    )


def test_type_filter():

    scenarios = (
        get_attack_scenarios_by_type(
            "PRIVILEGE_EXPANSION"
        )
    )

    assert len(scenarios) == 1

    assert (
        scenarios[0]["scenario_id"]
        == "ATTACK-003"
    )


def test_ground_truth_is_valid():

    scenarios = get_attack_scenarios()

    for scenario in scenarios:

        assert scenario[
            "ground_truth"
        ] in {
            "BENIGN",
            "MALICIOUS",
        }


def test_summary_is_consistent():

    summary = (
        get_attack_scenario_summary()
    )

    assert summary["total"] == 8

    assert (
        summary["malicious"]
        + summary["benign"]
        == summary["total"]
    )

    assert (
        summary["critical"]
        + summary["high"]
        + summary["medium"]
        + summary["low"]
        == summary["total"]
    )


def test_reproducible_sampling():

    first = sample_attack_scenarios(
        count=5,
        seed=42,
    )

    second = sample_attack_scenarios(
        count=5,
        seed=42,
    )

    assert first == second


def test_sampling_changes_with_seed():

    first = sample_attack_scenarios(
        count=5,
        seed=42,
    )

    second = sample_attack_scenarios(
        count=5,
        seed=99,
    )

    assert first != second


def test_invalid_sampling_count():

    with pytest.raises(
        ValueError
    ):

        sample_attack_scenarios(
            count=0
        )