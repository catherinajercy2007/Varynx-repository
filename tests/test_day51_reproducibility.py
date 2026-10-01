import pytest

from evaluation.reproducibility import (
    analyze_stability,
    run_experiment,
    run_repeated_experiments,
)


def test_single_experiment():
    result = run_experiment(1)

    assert result.run_id == 1
    assert result.metrics.total == 8
    assert result.metrics.passed == 8
    assert result.metrics.failed == 0
    assert result.metrics.pass_rate == 100.0


def test_repeated_experiments_count():
    runs = run_repeated_experiments(5)

    assert len(runs) == 5
    assert [run.run_id for run in runs] == [1, 2, 3, 4, 5]


def test_repeated_experiments_are_stable():
    runs = run_repeated_experiments(5)

    report = analyze_stability(runs)

    assert report.runs == 5
    assert report.stable is True


def test_pass_rates_are_reproducible():
    runs = run_repeated_experiments(5)

    report = analyze_stability(runs)

    assert report.pass_rates == [
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
    ]


def test_allow_counts_are_reproducible():
    runs = run_repeated_experiments(5)

    report = analyze_stability(runs)

    assert report.allow_counts == [2, 2, 2, 2, 2]


def test_deny_counts_are_reproducible():
    runs = run_repeated_experiments(5)

    report = analyze_stability(runs)

    assert report.deny_counts == [6, 6, 6, 6, 6]


def test_empty_stability_report():
    report = analyze_stability([])

    assert report.runs == 0
    assert report.stable is True
    assert report.pass_rates == []
    assert report.allow_counts == []
    assert report.deny_counts == []


def test_invalid_repetition_count():
    with pytest.raises(ValueError):
        run_repeated_experiments(0)