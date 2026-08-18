from app.attack_scenarios import (
    get_attack_scenarios,
)

from app.repeated_evaluation import (
    build_experiment_table,
    build_seed_summary,
    build_summary_table,
    calculate_consistency,
    run_repeated_experiments,
)


def test_repeated_experiment_count():

    scenarios = get_attack_scenarios()

    results = run_repeated_experiments(
        scenarios=scenarios,
        seeds=[1, 2, 3],
        events_per_scenario=2,
        threshold=70,
    )

    assert len(results) == 3


def test_repeated_experiment_contains_dataset():

    scenarios = get_attack_scenarios()

    results = run_repeated_experiments(
        scenarios=scenarios,
        seeds=[42],
        events_per_scenario=2,
        threshold=70,
    )

    assert len(results) == 1

    result = results[0]

    assert result["seed"] == 42

    assert result["dataset_size"] > 0

    assert "baseline" in result

    assert "aegisguard" in result


def test_seed_summary_contains_expected_columns():

    results = [
        {
            "seed": 42,
            "dataset_size": 10,
            "baseline": {
                "accuracy": 0.5,
                "f1_score": 0.4,
                "recall": 0.3,
            },
            "aegisguard": {
                "accuracy": 0.7,
                "f1_score": 0.6,
                "recall": 0.5,
            },
        }
    ]

    table = build_seed_summary(results)

    assert "seed" in table.columns
    assert "baseline_f1" in table.columns
    assert "aegisguard_f1" in table.columns
    assert "f1_difference" in table.columns


def test_summary_calculates_mean_difference():

    results = [
        {
            "seed": 1,
            "dataset_size": 10,
            "baseline": {
                "accuracy": 0.50,
                "f1_score": 0.40,
                "recall": 0.30,
                "precision": 0.50,
                "specificity": 0.70,
                "false_positive_rate": 0.30,
                "false_negative_rate": 0.70,
            },
            "aegisguard": {
                "accuracy": 0.70,
                "f1_score": 0.60,
                "recall": 0.50,
                "precision": 0.70,
                "specificity": 0.80,
                "false_positive_rate": 0.20,
                "false_negative_rate": 0.50,
            },
        }
    ]

    table = build_summary_table(results)

    f1_row = table[
        table["metric"] == "f1_score"
    ].iloc[0]

    assert round(
        f1_row["mean_difference"],
        2,
    ) == 0.20


def test_consistency():

    results = [
        {
            "baseline": {
                "f1_score": 0.50,
            },
            "aegisguard": {
                "f1_score": 0.70,
            },
        },
        {
            "baseline": {
                "f1_score": 0.60,
            },
            "aegisguard": {
                "f1_score": 0.65,
            },
        },
        {
            "baseline": {
                "f1_score": 0.70,
            },
            "aegisguard": {
                "f1_score": 0.60,
            },
        },
    ]

    consistency = calculate_consistency(
        results
    )

    assert consistency["experiments"] == 3

    assert consistency["positive_runs"] == 2

    assert round(
        consistency["positive_rate"],
        2,
    ) == 0.67


def test_experiment_table():

    results = [
        {
            "seed": 42,
            "dataset_size": 20,
            "baseline": {
                "f1_score": 0.50,
            },
            "aegisguard": {
                "f1_score": 0.70,
            },
        }
    ]

    table = build_experiment_table(
        results
    )

    assert len(table) == 7

    assert "baseline" in table.columns
    assert "aegisguard" in table.columns
    assert "difference" in table.columns