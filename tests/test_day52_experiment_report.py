from evaluation.experiment_report import (
    generate_default_report,
    generate_report,
    report_to_dict,
)
from evaluation.reproducibility import run_repeated_experiments


def test_generate_report():
    runs = run_repeated_experiments(5)

    report = generate_report(runs)

    assert report.total_runs == 5
    assert report.scenarios_per_run == 8
    assert report.stable is True


def test_average_pass_rate():
    runs = run_repeated_experiments(5)

    report = generate_report(runs)

    assert report.average_pass_rate == 100.0
    assert report.minimum_pass_rate == 100.0
    assert report.maximum_pass_rate == 100.0


def test_average_allow_count():
    runs = run_repeated_experiments(5)

    report = generate_report(runs)

    assert report.average_allow_count == 2.0


def test_average_deny_count():
    runs = run_repeated_experiments(5)

    report = generate_report(runs)

    assert report.average_deny_count == 6.0


def test_default_report():
    report = generate_default_report(5)

    assert report.total_runs == 5
    assert report.scenarios_per_run == 8
    assert report.average_pass_rate == 100.0
    assert report.stable is True


def test_report_to_dict():
    report = generate_default_report(5)

    data = report_to_dict(report)

    assert data["total_runs"] == 5
    assert data["scenarios_per_run"] == 8
    assert data["stable"] is True
    assert data["average_pass_rate"] == 100.0
    assert data["average_allow_count"] == 2.0
    assert data["average_deny_count"] == 6.0


def test_empty_report():
    report = generate_report([])

    assert report.total_runs == 0
    assert report.scenarios_per_run == 0
    assert report.stable is True
    assert report.average_pass_rate == 0.0


def test_empty_report_to_dict():
    report = generate_report([])

    data = report_to_dict(report)

    assert data["total_runs"] == 0
    assert data["scenarios_per_run"] == 0
    assert data["stable"] is True