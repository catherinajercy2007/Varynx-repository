from evaluation.scenario_runner import (
    evaluate_scenario,
    evaluation_summary,
    run_scenarios,
)
from evaluation.scenarios import get_scenario, get_scenarios


def test_run_all_scenarios():
    results = run_scenarios()

    assert len(results) == 8


def test_all_scenarios_pass():
    results = run_scenarios()

    assert all(result.passed for result in results)


def test_result_contains_expected_fields():
    result = evaluate_scenario(get_scenario("S01"))

    assert result.scenario_id == "S01"
    assert result.decision == "ALLOW"
    assert result.risk_level == "LOW"
    assert result.passed is True


def test_scenario_ids_are_preserved():
    scenarios = get_scenarios()
    results = run_scenarios(scenarios)

    assert [result.scenario_id for result in results] == [
        scenario.scenario_id for scenario in scenarios
    ]


def test_allow_and_deny_counts():
    results = run_scenarios()
    summary = evaluation_summary(results)

    assert summary["allow_count"] == 2
    assert summary["deny_count"] == 6


def test_summary_total():
    results = run_scenarios()
    summary = evaluation_summary(results)

    assert summary["total"] == 8
    assert summary["passed"] == 8
    assert summary["failed"] == 0


def test_summary_pass_rate():
    results = run_scenarios()
    summary = evaluation_summary(results)

    assert summary["pass_rate"] == 100.0