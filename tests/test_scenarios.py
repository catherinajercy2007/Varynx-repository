import pytest

from app.scenarios import (
    BENIGN,
    SUSPICIOUS,
    MALICIOUS,
    SCENARIO_TYPES,
    get_scenario,
    get_scenario_catalog,
    get_scenario_summary,
    get_scenarios,
    sample_scenarios,
)


def test_scenario_types():

    assert BENIGN in SCENARIO_TYPES
    assert SUSPICIOUS in SCENARIO_TYPES
    assert MALICIOUS in SCENARIO_TYPES


def test_catalog_not_empty():

    scenarios = get_scenario_catalog()

    assert isinstance(
        scenarios,
        list,
    )

    assert len(scenarios) > 0


def test_catalog_structure():

    scenario = get_scenario_catalog()[0]

    required_fields = {
        "scenario_id",
        "scenario_type",
        "agent_id",
        "task_id",
        "action",
        "resource",
        "description",
        "expected_behavior",
    }

    assert required_fields.issubset(
        scenario.keys()
    )


def test_scenario_types_are_valid():

    scenarios = get_scenario_catalog()

    for scenario in scenarios:

        assert (
            scenario["scenario_type"]
            in SCENARIO_TYPES
        )


def test_get_scenario():

    scenario = get_scenario(
        "BENIGN-001"
    )

    assert scenario is not None

    assert (
        scenario["scenario_type"]
        == BENIGN
    )


def test_unknown_scenario():

    assert (
        get_scenario(
            "DOES-NOT-EXIST"
        )
        is None
    )


def test_filter_benign():

    scenarios = get_scenarios(
        BENIGN
    )

    assert scenarios

    assert all(
        scenario["scenario_type"]
        == BENIGN
        for scenario
        in scenarios
    )


def test_filter_suspicious():

    scenarios = get_scenarios(
        SUSPICIOUS
    )

    assert scenarios

    assert all(
        scenario["scenario_type"]
        == SUSPICIOUS
        for scenario
        in scenarios
    )


def test_filter_malicious():

    scenarios = get_scenarios(
        MALICIOUS
    )

    assert scenarios

    assert all(
        scenario["scenario_type"]
        == MALICIOUS
        for scenario
        in scenarios
    )


def test_summary():

    summary = (
        get_scenario_summary()
    )

    assert (
        summary["total"]
        ==
        (
            summary["benign"]
            + summary["suspicious"]
            + summary["malicious"]
        )
    )


def test_reproducible_sampling():

    first = sample_scenarios(
        count=5,
        seed=42,
    )

    second = sample_scenarios(
        count=5,
        seed=42,
    )

    assert first == second


def test_invalid_sample_count():

    with pytest.raises(
        ValueError
    ):

        sample_scenarios(
            count=0
        )