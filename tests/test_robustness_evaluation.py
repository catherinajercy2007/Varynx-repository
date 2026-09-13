import pytest

from app.robustness_evaluation import (
    BehavioralDistribution,
    RobustnessCondition,
    RobustnessDimension,
    RobustnessResult,
    RobustnessSummary,
    build_all_robustness_conditions,
    build_attack_ratio_conditions,
    build_behavior_distribution_conditions,
    build_event_volume_conditions,
    build_noise_conditions,
    build_robustness_table,
    build_seed_conditions,
    calculate_condition_stability,
    calculate_metric_range,
    calculate_reference_delta,
    calculate_relative_change,
    interpret_robustness,
    run_robustness_experiment,
    summarize_robustness,
    validate_condition,
    validate_conditions,
)


def test_seed_conditions_exist():
    conditions = build_seed_conditions()

    assert len(conditions) == 10

    assert conditions[0].value == 42
    assert conditions[-1].value == 909


def test_event_volume_conditions_exist():
    conditions = build_event_volume_conditions()

    assert len(conditions) == 5

    assert {
        condition.value
        for condition in conditions
    } == {
        100,
        500,
        1000,
        5000,
        10000,
    }


def test_attack_ratio_conditions_exist():
    conditions = build_attack_ratio_conditions()

    assert len(conditions) == 6

    assert {
        condition.value
        for condition in conditions
    } == {
        0.01,
        0.05,
        0.10,
        0.20,
        0.30,
        0.50,
    }


def test_behavior_distribution_conditions_exist():
    conditions = (
        build_behavior_distribution_conditions()
    )

    assert len(conditions) == 4

    assert {
        condition.value
        for condition in conditions
    } == {
        BehavioralDistribution.NORMAL.value,
        BehavioralDistribution.DIVERSE.value,
        BehavioralDistribution.CONCENTRATED.value,
        BehavioralDistribution.DRIFTING.value,
    }


def test_noise_conditions_exist():
    conditions = build_noise_conditions()

    assert len(conditions) == 5

    assert {
        condition.value
        for condition in conditions
    } == {
        0.00,
        0.05,
        0.10,
        0.20,
        0.30,
    }


def test_all_dimensions_exist():
    conditions = (
        build_all_robustness_conditions()
    )

    assert set(conditions.keys()) == {
        RobustnessDimension.SEED,
        RobustnessDimension.EVENT_VOLUME,
        RobustnessDimension.ATTACK_RATIO,
        RobustnessDimension.BEHAVIOR_DISTRIBUTION,
        RobustnessDimension.NOISE,
    }


def test_attack_ratio_must_be_between_zero_and_one():
    condition = RobustnessCondition(
        dimension=RobustnessDimension.ATTACK_RATIO,
        name="invalid",
        value=1.5,
        description="invalid",
    )

    with pytest.raises(ValueError):
        validate_condition(condition)


def test_noise_must_be_between_zero_and_one():
    condition = RobustnessCondition(
        dimension=RobustnessDimension.NOISE,
        name="invalid",
        value=-0.1,
        description="invalid",
    )

    with pytest.raises(ValueError):
        validate_condition(condition)


def test_event_volume_must_be_positive():
    condition = RobustnessCondition(
        dimension=RobustnessDimension.EVENT_VOLUME,
        name="invalid",
        value=0,
        description="invalid",
    )

    with pytest.raises(ValueError):
        validate_condition(condition)


def test_condition_name_cannot_be_empty():
    condition = RobustnessCondition(
        dimension=RobustnessDimension.SEED,
        name="",
        value=42,
        description="invalid",
    )

    with pytest.raises(ValueError):
        validate_condition(condition)


def test_duplicate_condition_names_are_rejected():
    condition_a = RobustnessCondition(
        dimension=RobustnessDimension.SEED,
        name="same",
        value=42,
        description="one",
    )

    condition_b = RobustnessCondition(
        dimension=RobustnessDimension.SEED,
        name="same",
        value=101,
        description="two",
    )

    with pytest.raises(ValueError):
        validate_conditions(
            [
                condition_a,
                condition_b,
            ]
        )


def test_same_dataset_factory_protocol_is_used():
    conditions = [
        RobustnessCondition(
            dimension=RobustnessDimension.SEED,
            name="seed_test",
            value=42,
            description="test",
        )
    ]

    calls = []

    def dataset_factory(
        condition,
        seed,
    ):
        calls.append(
            (
                condition.name,
                seed,
            )
        )

        return [
            {"id": 1},
            {"id": 2},
        ]

    def detector(
        dataset,
        condition,
        seed,
    ):
        assert len(dataset) == 2

        return {
            "precision": 0.8,
            "recall": 0.7,
            "f1": 0.75,
        }

    results = run_robustness_experiment(
        dataset_factory,
        conditions=conditions,
        seeds=[42, 101],
        detector=detector,
    )

    assert len(results) == 2

    assert calls == [
        ("seed_test", 42),
        ("seed_test", 101),
    ]


def test_empty_seed_list_is_rejected():
    conditions = build_seed_conditions()

    def dataset_factory(
        condition,
        seed,
    ):
        return [{"id": 1}]

    def detector(
        dataset,
        condition,
        seed,
    ):
        return {"f1": 0.8}

    with pytest.raises(ValueError):
        run_robustness_experiment(
            dataset_factory,
            conditions=conditions,
            seeds=[],
            detector=detector,
        )


def test_empty_dataset_is_rejected():
    conditions = [
        build_seed_conditions()[0]
    ]

    def dataset_factory(
        condition,
        seed,
    ):
        return []

    def detector(
        dataset,
        condition,
        seed,
    ):
        return {"f1": 0.8}

    with pytest.raises(ValueError):
        run_robustness_experiment(
            dataset_factory,
            conditions=conditions,
            seeds=[42],
            detector=detector,
        )


def test_invalid_metric_type_is_rejected():
    conditions = [
        build_seed_conditions()[0]
    ]

    def dataset_factory(
        condition,
        seed,
    ):
        return [{"id": 1}]

    def detector(
        dataset,
        condition,
        seed,
    ):
        return {
            "f1": "invalid"
        }

    with pytest.raises(TypeError):
        run_robustness_experiment(
            dataset_factory,
            conditions=conditions,
            seeds=[42],
            detector=detector,
        )


def test_nan_metric_is_rejected():
    conditions = [
        build_seed_conditions()[0]
    ]

    def dataset_factory(
        condition,
        seed,
    ):
        return [{"id": 1}]

    def detector(
        dataset,
        condition,
        seed,
    ):
        return {
            "f1": float("nan")
        }

    with pytest.raises(ValueError):
        run_robustness_experiment(
            dataset_factory,
            conditions=conditions,
            seeds=[42],
            detector=detector,
        )


def test_results_can_be_aggregated():
    results = [
        RobustnessResult(
            dimension=RobustnessDimension.NOISE,
            condition="noise_0pct",
            seed=42,
            metrics={
                "precision": 0.8,
                "f1": 0.7,
            },
            sample_count=100,
        ),
        RobustnessResult(
            dimension=RobustnessDimension.NOISE,
            condition="noise_0pct",
            seed=101,
            metrics={
                "precision": 0.9,
                "f1": 0.8,
            },
            sample_count=100,
        ),
    ]

    summaries = summarize_robustness(
        results
    )

    assert len(summaries) == 1

    summary = summaries[0]

    assert summary.runs == 2
    assert summary.metrics_mean[
        "precision"
    ] == pytest.approx(0.85)

    assert summary.metrics_mean[
        "f1"
    ] == pytest.approx(0.75)


def test_minimum_and_maximum_are_calculated():
    results = [
        RobustnessResult(
            dimension=RobustnessDimension.NOISE,
            condition="noise",
            seed=42,
            metrics={"f1": 0.6},
            sample_count=100,
        ),
        RobustnessResult(
            dimension=RobustnessDimension.NOISE,
            condition="noise",
            seed=101,
            metrics={"f1": 0.8},
            sample_count=100,
        ),
        RobustnessResult(
            dimension=RobustnessDimension.NOISE,
            condition="noise",
            seed=202,
            metrics={"f1": 0.7},
            sample_count=100,
        ),
    ]

    summary = summarize_robustness(
        results
    )[0]

    assert summary.metrics_min[
        "f1"
    ] == pytest.approx(0.6)

    assert summary.metrics_max[
        "f1"
    ] == pytest.approx(0.8)


def test_reference_delta():
    reference = RobustnessSummary(
        dimension=RobustnessDimension.NOISE,
        condition="noise_0pct",
        runs=5,
        sample_count=500,
        metrics_mean={
            "precision": 0.90,
            "recall": 0.80,
            "f1": 0.85,
        },
        metrics_std={
            "precision": 0.02,
            "recall": 0.03,
            "f1": 0.02,
        },
        metrics_min={
            "precision": 0.86,
            "recall": 0.75,
            "f1": 0.81,
        },
        metrics_max={
            "precision": 0.93,
            "recall": 0.84,
            "f1": 0.88,
        },
    )

    comparison = RobustnessSummary(
        dimension=RobustnessDimension.NOISE,
        condition="noise_20pct",
        runs=5,
        sample_count=500,
        metrics_mean={
            "precision": 0.85,
            "recall": 0.70,
            "f1": 0.76,
        },
        metrics_std={
            "precision": 0.03,
            "recall": 0.04,
            "f1": 0.03,
        },
        metrics_min={
            "precision": 0.80,
            "recall": 0.65,
            "f1": 0.71,
        },
        metrics_max={
            "precision": 0.89,
            "recall": 0.75,
            "f1": 0.80,
        },
    )

    delta = calculate_reference_delta(
        reference,
        comparison,
    )

    assert delta["precision"] == pytest.approx(
        -0.05
    )

    assert delta["recall"] == pytest.approx(
        -0.10
    )

    assert delta["f1"] == pytest.approx(
        -0.09
    )


def test_relative_change():
    reference = RobustnessSummary(
        dimension=RobustnessDimension.NOISE,
        condition="reference",
        runs=1,
        sample_count=100,
        metrics_mean={
            "f1": 0.80,
        },
        metrics_std={
            "f1": 0.0,
        },
        metrics_min={
            "f1": 0.80,
        },
        metrics_max={
            "f1": 0.80,
        },
    )

    comparison = RobustnessSummary(
        dimension=RobustnessDimension.NOISE,
        condition="comparison",
        runs=1,
        sample_count=100,
        metrics_mean={
            "f1": 0.72,
        },
        metrics_std={
            "f1": 0.0,
        },
        metrics_min={
            "f1": 0.72,
        },
        metrics_max={
            "f1": 0.72,
        },
    )

    change = calculate_relative_change(
        reference,
        comparison,
    )

    assert change["f1"] == pytest.approx(
        -10.0
    )


def test_relative_change_handles_zero_reference():
    reference = RobustnessSummary(
        dimension=RobustnessDimension.NOISE,
        condition="reference",
        runs=1,
        sample_count=100,
        metrics_mean={
            "f1": 0.0,
        },
        metrics_std={
            "f1": 0.0,
        },
        metrics_min={
            "f1": 0.0,
        },
        metrics_max={
            "f1": 0.0,
        },
    )

    comparison = RobustnessSummary(
        dimension=RobustnessDimension.NOISE,
        condition="comparison",
        runs=1,
        sample_count=100,
        metrics_mean={
            "f1": 0.5,
        },
        metrics_std={
            "f1": 0.0,
        },
        metrics_min={
            "f1": 0.5,
        },
        metrics_max={
            "f1": 0.5,
        },
    )

    change = calculate_relative_change(
        reference,
        comparison,
    )

    assert change["f1"] == 0.0


def test_metric_range():
    summary = RobustnessSummary(
        dimension=RobustnessDimension.NOISE,
        condition="noise",
        runs=3,
        sample_count=300,
        metrics_mean={"f1": 0.7},
        metrics_std={"f1": 0.1},
        metrics_min={"f1": 0.6},
        metrics_max={"f1": 0.8},
    )

    assert calculate_metric_range(
        summary,
        "f1",
    ) == pytest.approx(0.2)


def test_condition_stability():
    summaries = [
        RobustnessSummary(
            dimension=RobustnessDimension.NOISE,
            condition="a",
            runs=1,
            sample_count=100,
            metrics_mean={"f1": 0.7},
            metrics_std={"f1": 0.0},
            metrics_min={"f1": 0.7},
            metrics_max={"f1": 0.7},
        ),
        RobustnessSummary(
            dimension=RobustnessDimension.NOISE,
            condition="b",
            runs=1,
            sample_count=100,
            metrics_mean={"f1": 0.8},
            metrics_std={"f1": 0.0},
            metrics_min={"f1": 0.8},
            metrics_max={"f1": 0.8},
        ),
        RobustnessSummary(
            dimension=RobustnessDimension.NOISE,
            condition="c",
            runs=1,
            sample_count=100,
            metrics_mean={"f1": 0.6},
            metrics_std={"f1": 0.0},
            metrics_min={"f1": 0.6},
            metrics_max={"f1": 0.6},
        ),
    ]

    stability = calculate_condition_stability(
        summaries,
        metric="f1",
    )

    assert stability["min"] == pytest.approx(0.6)
    assert stability["max"] == pytest.approx(0.8)
    assert stability["range"] == pytest.approx(0.2)


def test_condition_stability_missing_metric():
    summaries = [
        RobustnessSummary(
            dimension=RobustnessDimension.NOISE,
            condition="a",
            runs=1,
            sample_count=100,
            metrics_mean={"precision": 0.8},
            metrics_std={"precision": 0.0},
            metrics_min={"precision": 0.8},
            metrics_max={"precision": 0.8},
        )
    ]

    with pytest.raises(KeyError):
        calculate_condition_stability(
            summaries,
            metric="f1",
        )


def test_robustness_table_contains_metrics():
    summary = RobustnessSummary(
        dimension=RobustnessDimension.NOISE,
        condition="noise_10pct",
        runs=5,
        sample_count=500,
        metrics_mean={
            "precision": 0.85,
            "f1": 0.80,
        },
        metrics_std={
            "precision": 0.02,
            "f1": 0.03,
        },
        metrics_min={
            "precision": 0.80,
            "f1": 0.75,
        },
        metrics_max={
            "precision": 0.90,
            "f1": 0.85,
        },
    )

    table = build_robustness_table(
        [summary]
    )

    assert len(table) == 1

    row = table[0]

    assert row["dimension"] == "noise"
    assert row["condition"] == "noise_10pct"
    assert row["precision"] == 0.85
    assert row["precision_std"] == 0.02
    assert row["precision_min"] == 0.80
    assert row["precision_max"] == 0.90


def test_interpretation_is_cautious():
    text = interpret_robustness(
        dimension=RobustnessDimension.NOISE,
        condition="noise_20pct",
        metric="F1",
        relative_change_percent=-8.5,
    )

    assert "decreased" in text
    assert "statistical significance" in text
    assert "generalization" in text


def test_result_serialization():
    result = RobustnessResult(
        dimension=RobustnessDimension.SEED,
        condition="seed_42",
        seed=42,
        metrics={
            "f1": 0.8
        },
        sample_count=100,
    )

    data = result.to_dict()

    assert data["dimension"] == "seed"
    assert data["condition"] == "seed_42"
    assert data["seed"] == 42
    assert data["metrics"]["f1"] == 0.8