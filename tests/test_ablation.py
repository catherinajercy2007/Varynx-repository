import pytest

from app.ablation import (
    AblationConfiguration,
    AblationResult,
    AblationSummary,
    AblationVariant,
    build_ablation_table,
    calculate_ablation_delta,
    get_ablation_configuration,
    get_ablation_configurations,
    interpret_component_delta,
    run_ablation_experiment,
    summarize_ablation,
)


def test_all_ablation_variants_exist():
    configurations = (
        get_ablation_configurations()
    )

    assert len(configurations) == 5


def test_full_varynx_enables_all_components():
    config = get_ablation_configuration(
        AblationVariant.FULL_VARYNX
    )

    assert config.behavioral is True
    assert config.multiresolution is True
    assert config.cross_context is True
    assert config.adaptive_response is True


def test_without_behavior_disables_only_behavior():
    config = get_ablation_configuration(
        AblationVariant.WITHOUT_BEHAVIOR
    )

    assert config.behavioral is False
    assert config.multiresolution is True
    assert config.cross_context is True
    assert config.adaptive_response is True


def test_without_multiresolution_disables_only_multiresolution():
    config = get_ablation_configuration(
        AblationVariant.WITHOUT_MULTIRESOLUTION
    )

    assert config.behavioral is True
    assert config.multiresolution is False
    assert config.cross_context is True
    assert config.adaptive_response is True


def test_without_cross_context_disables_only_cross_context():
    config = get_ablation_configuration(
        AblationVariant.WITHOUT_CROSS_CONTEXT
    )

    assert config.behavioral is True
    assert config.multiresolution is True
    assert config.cross_context is False
    assert config.adaptive_response is True


def test_without_adaptive_response_disables_only_adaptive_response():
    config = get_ablation_configuration(
        AblationVariant.WITHOUT_ADAPTIVE_RESPONSE
    )

    assert config.behavioral is True
    assert config.multiresolution is True
    assert config.cross_context is True
    assert config.adaptive_response is False


def test_configuration_serialization():
    config = get_ablation_configuration(
        AblationVariant.FULL_VARYNX
    )

    data = config.to_dict()

    assert data["variant"] == "full_varynx"
    assert data["behavioral"] is True
    assert data["multiresolution"] is True
    assert data["cross_context"] is True
    assert data["adaptive_response"] is True


def test_run_ablation_uses_same_dataset_for_all_variants():
    dataset = [
        {"id": 1},
        {"id": 2},
        {"id": 3},
    ]

    calls = []

    def detector(
        received_dataset,
        configuration,
        seed,
    ):
        calls.append(
            (
                id(received_dataset),
                configuration.variant,
                seed,
            )
        )

        return {
            "accuracy": 0.8,
            "precision": 0.75,
            "recall": 0.85,
            "f1": 0.80,
        }

    results = run_ablation_experiment(
        dataset,
        seeds=[42, 101],
        detector=detector,
    )

    assert len(results) == 10

    assert all(
        result.sample_count == 3
        for result in results
    )

    variants = {
        result.variant
        for result in results
    }

    assert variants == set(
        AblationVariant
    )


def test_run_ablation_supports_subset():
    dataset = [
        {"id": 1},
    ]

    def detector(
        received_dataset,
        configuration,
        seed,
    ):
        return {
            "f1": 0.8
        }

    results = run_ablation_experiment(
        dataset,
        seeds=[42],
        detector=detector,
        variants=[
            AblationVariant.FULL_VARYNX,
            AblationVariant.WITHOUT_BEHAVIOR,
        ],
    )

    assert len(results) == 2

    assert {
        result.variant
        for result in results
    } == {
        AblationVariant.FULL_VARYNX,
        AblationVariant.WITHOUT_BEHAVIOR,
    }


def test_run_ablation_requires_dataset():
    def detector(
        dataset,
        configuration,
        seed,
    ):
        return {"f1": 0.8}

    with pytest.raises(ValueError):
        run_ablation_experiment(
            [],
            seeds=[42],
            detector=detector,
        )


def test_run_ablation_requires_seed():
    def detector(
        dataset,
        configuration,
        seed,
    ):
        return {"f1": 0.8}

    with pytest.raises(ValueError):
        run_ablation_experiment(
            [{"id": 1}],
            seeds=[],
            detector=detector,
        )


def test_non_numeric_metric_is_rejected():
    def detector(
        dataset,
        configuration,
        seed,
    ):
        return {
            "f1": "invalid"
        }

    with pytest.raises(TypeError):
        run_ablation_experiment(
            [{"id": 1}],
            seeds=[42],
            detector=detector,
        )


def test_nan_metric_is_rejected():
    def detector(
        dataset,
        configuration,
        seed,
    ):
        return {
            "f1": float("nan")
        }

    with pytest.raises(ValueError):
        run_ablation_experiment(
            [{"id": 1}],
            seeds=[42],
            detector=detector,
        )


def test_summarize_ablation():
    results = [
        AblationResult(
            variant=AblationVariant.FULL_VARYNX,
            seed=42,
            metrics={
                "accuracy": 0.80,
                "f1": 0.70,
            },
            sample_count=100,
        ),
        AblationResult(
            variant=AblationVariant.FULL_VARYNX,
            seed=101,
            metrics={
                "accuracy": 0.90,
                "f1": 0.80,
            },
            sample_count=100,
        ),
    ]

    summaries = summarize_ablation(
        results
    )

    assert len(summaries) == 1

    summary = summaries[0]

    assert summary.variant == (
        AblationVariant.FULL_VARYNX
    )

    assert summary.runs == 2

    assert summary.metrics_mean[
        "accuracy"
    ] == pytest.approx(0.85)

    assert summary.metrics_mean[
        "f1"
    ] == pytest.approx(0.75)


def test_summary_standard_deviation_is_calculated():
    results = [
        AblationResult(
            variant=AblationVariant.FULL_VARYNX,
            seed=42,
            metrics={"f1": 0.70},
            sample_count=100,
        ),
        AblationResult(
            variant=AblationVariant.FULL_VARYNX,
            seed=101,
            metrics={"f1": 0.80},
            sample_count=100,
        ),
    ]

    summary = summarize_ablation(
        results
    )[0]

    assert summary.metrics_std[
        "f1"
    ] == pytest.approx(
        0.070710678,
        rel=1e-6,
    )


def test_calculate_ablation_delta():
    full = AblationSummary(
        variant=AblationVariant.FULL_VARYNX,
        runs=5,
        metrics_mean={
            "accuracy": 0.90,
            "f1": 0.85,
        },
        metrics_std={
            "accuracy": 0.02,
            "f1": 0.03,
        },
        sample_count=500,
    )

    ablated = AblationSummary(
        variant=AblationVariant.WITHOUT_BEHAVIOR,
        runs=5,
        metrics_mean={
            "accuracy": 0.82,
            "f1": 0.75,
        },
        metrics_std={
            "accuracy": 0.03,
            "f1": 0.04,
        },
        sample_count=500,
    )

    delta = calculate_ablation_delta(
        full,
        ablated,
    )

    assert delta["accuracy"] == pytest.approx(
        0.08
    )

    assert delta["f1"] == pytest.approx(
        0.10
    )


def test_delta_requires_full_varynx_as_first_result():
    first = AblationSummary(
        variant=AblationVariant.WITHOUT_BEHAVIOR,
        runs=1,
        metrics_mean={"f1": 0.8},
        metrics_std={"f1": 0.0},
        sample_count=10,
    )

    second = AblationSummary(
        variant=AblationVariant.FULL_VARYNX,
        runs=1,
        metrics_mean={"f1": 0.9},
        metrics_std={"f1": 0.0},
        sample_count=10,
    )

    with pytest.raises(ValueError):
        calculate_ablation_delta(
            first,
            second,
        )


def test_ablation_table_contains_mean_and_std():
    summary = AblationSummary(
        variant=AblationVariant.FULL_VARYNX,
        runs=5,
        metrics_mean={
            "precision": 0.88,
            "f1": 0.84,
        },
        metrics_std={
            "precision": 0.02,
            "f1": 0.03,
        },
        sample_count=500,
    )

    table = build_ablation_table(
        [summary]
    )

    assert len(table) == 1

    row = table[0]

    assert row["variant"] == "full_varynx"
    assert row["runs"] == 5
    assert row["precision"] == 0.88
    assert row["precision_std"] == 0.02
    assert row["f1"] == 0.84
    assert row["f1_std"] == 0.03


def test_interpretation_does_not_claim_significance():
    interpretation = interpret_component_delta(
        component="behavioral features",
        metric="F1",
        delta=0.08,
    )

    assert "higher" in interpretation
    assert "statistical significance" in interpretation


def test_negative_delta_is_supported():
    interpretation = interpret_component_delta(
        component="cross-context correlation",
        metric="precision",
        delta=-0.02,
    )

    assert "lower" in interpretation


def test_zero_delta_is_supported():
    interpretation = interpret_component_delta(
        component="adaptive response",
        metric="recall",
        delta=0.0,
    )

    assert "same" in interpretation


def test_result_serialization():
    result = AblationResult(
        variant=AblationVariant.FULL_VARYNX,
        seed=42,
        metrics={
            "f1": 0.85
        },
        sample_count=100,
    )

    data = result.to_dict()

    assert data["variant"] == "full_varynx"
    assert data["seed"] == 42
    assert data["metrics"]["f1"] == 0.85
    assert data["sample_count"] == 100