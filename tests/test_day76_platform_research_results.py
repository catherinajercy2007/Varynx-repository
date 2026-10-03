"""Day 76 - Platform Research Results Integration Tests."""

from app.attack_scenarios import get_attack_scenarios
from app.repeated_evaluation import (
    run_repeated_experiments,
    build_seed_summary,
    build_summary_table,
    calculate_consistency,
)


def _run_day76_experiments():
    return run_repeated_experiments(
        scenarios=get_attack_scenarios(),
        seeds=[42, 101],
        events_per_scenario=5,
        threshold=70.0,
    )


def test_day76_repeated_experiments_run():
    results = _run_day76_experiments()

    assert len(results) == 2

    for result in results:
        assert "seed" in result
        assert "dataset_size" in result
        assert "baseline" in result
        assert "aegisguard" in result


def test_day76_seed_summary_contains_expected_metrics():
    results = _run_day76_experiments()
    summary = build_seed_summary(results)

    assert len(summary) == 2
    assert "seed" in summary.columns
    assert "baseline_accuracy" in summary.columns
    assert "aegisguard_accuracy" in summary.columns
    assert "baseline_f1" in summary.columns
    assert "aegisguard_f1" in summary.columns


def test_day76_summary_table_is_generated():
    results = _run_day76_experiments()
    summary = build_summary_table(results)

    assert not summary.empty


def test_day76_consistency_is_calculated():
    results = _run_day76_experiments()
    consistency = calculate_consistency(
        results,
        metric="f1_score",
    )

    assert consistency["experiments"] == 2
    assert "positive_runs" in consistency
    assert "positive_rate" in consistency
    assert "mean_difference" in consistency
    assert "std_difference" in consistency
