from evaluation.comparative_metrics import (
    calculate_metrics,
    compare_with_baseline,
    security_distribution,
)
from evaluation.scenario_runner import run_scenarios


def test_calculate_metrics():
    results = run_scenarios()

    metrics = calculate_metrics(results)

    assert metrics.total == 8
    assert metrics.passed == 8
    assert metrics.failed == 0


def test_pass_rate():
    results = run_scenarios()

    metrics = calculate_metrics(results)

    assert metrics.pass_rate == 100.0


def test_allow_and_deny_distribution():
    results = run_scenarios()

    metrics = calculate_metrics(results)

    assert metrics.allow_count == 2
    assert metrics.deny_count == 6


def test_risk_distribution():
    results = run_scenarios()

    metrics = calculate_metrics(results)

    assert metrics.high_risk_count == 4
    assert metrics.critical_risk_count == 2


def test_baseline_comparison():
    results = run_scenarios()

    metrics = calculate_metrics(results)

    comparison = compare_with_baseline(
        metrics,
        baseline_pass_rate=100.0,
    )

    assert comparison["measured_pass_rate"] == 100.0
    assert comparison["baseline_pass_rate"] == 100.0
    assert comparison["difference"] == 0.0
    assert comparison["meets_baseline"] is True


def test_security_distribution():
    results = run_scenarios()

    metrics = calculate_metrics(results)

    distribution = security_distribution(metrics)

    assert distribution["allow_percentage"] == 25.0
    assert distribution["deny_percentage"] == 75.0


def test_empty_metrics():
    metrics = calculate_metrics([])

    assert metrics.total == 0
    assert metrics.passed == 0
    assert metrics.failed == 0
    assert metrics.pass_rate == 0.0


def test_empty_security_distribution():
    metrics = calculate_metrics([])

    distribution = security_distribution(metrics)

    assert distribution["allow_percentage"] == 0.0
    assert distribution["deny_percentage"] == 0.0