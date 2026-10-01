from evaluation.baseline_comparison import (
    BaselineComparison,
    BaselineMetrics,
    compare_experiment_report,
)
from evaluation.comparison_summary import (
    comparison_summary_details,
    comparison_summary_status,
    comparison_summary_to_dict,
    create_comparison_summary,
    generate_default_comparison_summary,
)
from evaluation.experiment_report import generate_default_report


def test_default_comparison_summary():
    summary = generate_default_comparison_summary(5)

    assert summary.valid is True
    assert summary.pass_rate_difference == 0.0
    assert summary.allow_count_difference == 0.0
    assert summary.deny_count_difference == 0.0


def test_default_summary_is_aligned():
    summary = generate_default_comparison_summary(5)

    assert summary.baseline_aligned is True
    assert summary.pass_rate_meets_baseline is True
    assert summary.allow_count_matches_baseline is True
    assert summary.deny_count_matches_baseline is True


def test_default_summary_status():
    summary = generate_default_comparison_summary(5)

    assert comparison_summary_status(summary) == "ALIGNED"


def test_summary_dictionary():
    summary = generate_default_comparison_summary(5)

    data = comparison_summary_to_dict(summary)

    assert data["valid"] is True
    assert data["baseline_aligned"] is True
    assert data["pass_rate_difference"] == 0.0
    assert data["allow_count_difference"] == 0.0
    assert data["deny_count_difference"] == 0.0


def test_summary_details():
    summary = generate_default_comparison_summary(5)

    details = comparison_summary_details(summary)

    assert details["status"] == "ALIGNED"
    assert details["valid"] is True
    assert details["baseline_aligned"] is True


def test_custom_baseline_difference():
    report = generate_default_report(5)

    baseline = BaselineMetrics(
        pass_rate=90.0,
        allow_count=1.0,
        deny_count=7.0,
    )

    comparison = compare_experiment_report(
        report,
        baseline,
    )

    summary = create_comparison_summary(comparison)

    assert summary.valid is True
    assert summary.pass_rate_difference == 10.0
    assert summary.allow_count_difference == 1.0
    assert summary.deny_count_difference == -1.0
    assert summary.baseline_aligned is False


def test_custom_baseline_status():
    report = generate_default_report(5)

    baseline = BaselineMetrics(
        pass_rate=90.0,
        allow_count=1.0,
        deny_count=7.0,
    )

    comparison = compare_experiment_report(
        report,
        baseline,
    )

    summary = create_comparison_summary(comparison)

    assert comparison_summary_status(summary) == "DIFFERS"


def test_invalid_comparison_status():
    comparison = BaselineComparison(
        valid=False,
        pass_rate_difference=0.0,
        allow_count_difference=0.0,
        deny_count_difference=0.0,
        pass_rate_meets_baseline=False,
        allow_count_matches_baseline=False,
        deny_count_matches_baseline=False,
    )

    summary = create_comparison_summary(comparison)

    assert summary.valid is False
    assert summary.baseline_aligned is False
    assert comparison_summary_status(summary) == "INVALID"