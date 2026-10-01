from evaluation.baseline_comparison import (
    BaselineMetrics,
    DEFAULT_BASELINE,
    baseline_comparison_to_dict,
    compare_experiment_report,
    compare_with_baseline,
    generate_default_baseline_comparison,
)
from evaluation.experiment_export import report_to_json_dict
from evaluation.experiment_report import generate_default_report


def test_default_baseline_values():
    assert DEFAULT_BASELINE.pass_rate == 100.0
    assert DEFAULT_BASELINE.allow_count == 2.0
    assert DEFAULT_BASELINE.deny_count == 6.0


def test_default_baseline_comparison():
    comparison = generate_default_baseline_comparison(5)

    assert comparison.valid is True
    assert comparison.pass_rate_difference == 0.0
    assert comparison.allow_count_difference == 0.0
    assert comparison.deny_count_difference == 0.0


def test_baseline_requirements():
    comparison = generate_default_baseline_comparison(5)

    assert comparison.pass_rate_meets_baseline is True
    assert comparison.allow_count_matches_baseline is True
    assert comparison.deny_count_matches_baseline is True


def test_compare_experiment_report():
    report = generate_default_report(5)

    comparison = compare_experiment_report(report)

    assert comparison.valid is True
    assert comparison.pass_rate_difference == 0.0


def test_custom_baseline():
    report = generate_default_report(5)

    baseline = BaselineMetrics(
        pass_rate=90.0,
        allow_count=2.0,
        deny_count=6.0,
    )

    comparison = compare_experiment_report(
        report,
        baseline,
    )

    assert comparison.valid is True
    assert comparison.pass_rate_difference == 10.0
    assert comparison.pass_rate_meets_baseline is True


def test_custom_baseline_decision_difference():
    report = generate_default_report(5)
    data = report_to_json_dict(report)

    baseline = BaselineMetrics(
        pass_rate=100.0,
        allow_count=1.0,
        deny_count=7.0,
    )

    comparison = compare_with_baseline(
        data,
        baseline,
    )

    assert comparison.valid is True
    assert comparison.allow_count_difference == 1.0
    assert comparison.deny_count_difference == -1.0
    assert comparison.allow_count_matches_baseline is False
    assert comparison.deny_count_matches_baseline is False


def test_invalid_report_fails_baseline_comparison():
    report = generate_default_report(5)
    data = report_to_json_dict(report)

    data["average_pass_rate"] = 150.0

    comparison = compare_with_baseline(data)

    assert comparison.valid is False
    assert comparison.pass_rate_meets_baseline is False


def test_baseline_comparison_to_dict():
    comparison = generate_default_baseline_comparison(5)

    data = baseline_comparison_to_dict(comparison)

    assert data["valid"] is True
    assert data["pass_rate_difference"] == 0.0
    assert data["allow_count_difference"] == 0.0
    assert data["deny_count_difference"] == 0.0
    assert data["pass_rate_meets_baseline"] is True
    assert data["allow_count_matches_baseline"] is True
    assert data["deny_count_matches_baseline"] is True