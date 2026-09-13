import pytest

from app.threshold_sensitivity import (
    SensitivityResult,
    SensitivitySummary,
    build_research_interpretation,
    build_sensitivity_table,
    build_threshold_profiles,
    calculate_sensitivity_delta,
    classify_threshold_direction,
    get_threshold_profile,
    run_threshold_sensitivity,
    summarize_threshold_sensitivity,
    validate_threshold_profiles,
)


def test_default_profile_exists():
    profiles = build_threshold_profiles()

    names = {
        profile.name
        for profile in profiles
    }

    assert "default" in names


def test_expected_profiles_exist():
    profiles = build_threshold_profiles()

    names = {
        profile.name
        for profile in profiles
    }

    assert names == {
        "default",
        "lower",
        "slightly_lower",
        "slightly_higher",
        "higher",
    }


def test_profile_names_are_unique():
    profiles = build_threshold_profiles()

    names = [
        profile.name
        for profile in profiles
    ]

    assert len(names) == len(set(names))


def test_all_profiles_are_valid():
    profiles = build_threshold_profiles()

    validate_threshold_profiles(
        profiles
    )


def test_default_profile_matches_default_config():
    profile = get_threshold_profile(
        "default"
    )

    thresholds = profile.config.thresholds

    assert thresholds.monitoring == 30.0
    assert thresholds.step_up == 55.0
    assert thresholds.reduce_scope == 70.0
    assert thresholds.human_review == 80.0
    assert thresholds.block == 90.0


def test_lower_profile_reduces_thresholds():
    default = get_threshold_profile(
        "default"
    )

    lower = get_threshold_profile(
        "lower"
    )

    assert (
        lower.config.thresholds.monitoring
        < default.config.thresholds.monitoring
    )

    assert (
        lower.config.thresholds.block
        < default.config.thresholds.block
    )


def test_higher_profile_increases_thresholds():
    default = get_threshold_profile(
        "default"
    )

    higher = get_threshold_profile(
        "higher"
    )

    assert (
        higher.config.thresholds.monitoring
        > default.config.thresholds.monitoring
    )

    assert (
        higher.config.thresholds.block
        > default.config.thresholds.block
    )


def test_slight_profiles_are_between_extremes():
    lower = get_threshold_profile(
        "lower"
    )

    slightly_lower = get_threshold_profile(
        "slightly_lower"
    )

    default = get_threshold_profile(
        "default"
    )

    slightly_higher = get_threshold_profile(
        "slightly_higher"
    )

    higher = get_threshold_profile(
        "higher"
    )

    assert (
        lower.config.thresholds.block
        < slightly_lower.config.thresholds.block
        < default.config.thresholds.block
        < slightly_higher.config.thresholds.block
        < higher.config.thresholds.block
    )


def test_unknown_profile_raises_key_error():
    with pytest.raises(KeyError):
        get_threshold_profile(
            "unknown"
        )


def test_same_dataset_and_seed_are_used_for_each_profile():
    dataset = [
        {"id": 1},
        {"id": 2},
        {"id": 3},
    ]

    calls = []

    def detector(
        received_dataset,
        config,
        seed,
    ):
        calls.append(
            (
                len(received_dataset),
                seed,
                config.name,
            )
        )

        return {
            "f1": 0.8,
        }

    results = run_threshold_sensitivity(
        dataset,
        seeds=[42, 101],
        detector=detector,
    )

    assert len(results) == 10

    assert all(
        call[0] == 3
        for call in calls
    )

    assert {
        call[1]
        for call in calls
    } == {
        42,
        101,
    }


def test_sensitivity_subset_is_supported():
    dataset = [
        {"id": 1},
    ]

    profiles = [
        get_threshold_profile("default"),
        get_threshold_profile("higher"),
    ]

    def detector(
        received_dataset,
        config,
        seed,
    ):
        return {
            "f1": 0.8,
        }

    results = run_threshold_sensitivity(
        dataset,
        seeds=[42],
        detector=detector,
        profiles=profiles,
    )

    assert len(results) == 2

    assert {
        result.profile
        for result in results
    } == {
        "default",
        "higher",
    }


def test_empty_dataset_is_rejected():
    def detector(
        dataset,
        config,
        seed,
    ):
        return {"f1": 0.8}

    with pytest.raises(ValueError):
        run_threshold_sensitivity(
            [],
            seeds=[42],
            detector=detector,
        )


def test_empty_seed_list_is_rejected():
    def detector(
        dataset,
        config,
        seed,
    ):
        return {"f1": 0.8}

    with pytest.raises(ValueError):
        run_threshold_sensitivity(
            [{"id": 1}],
            seeds=[],
            detector=detector,
        )


def test_non_numeric_metric_is_rejected():
    def detector(
        dataset,
        config,
        seed,
    ):
        return {
            "f1": "invalid",
        }

    with pytest.raises(TypeError):
        run_threshold_sensitivity(
            [{"id": 1}],
            seeds=[42],
            detector=detector,
        )


def test_nan_metric_is_rejected():
    def detector(
        dataset,
        config,
        seed,
    ):
        return {
            "f1": float("nan"),
        }

    with pytest.raises(ValueError):
        run_threshold_sensitivity(
            [{"id": 1}],
            seeds=[42],
            detector=detector,
        )


def test_results_are_aggregated():
    results = [
        SensitivityResult(
            profile="default",
            seed=42,
            metrics={
                "precision": 0.80,
                "f1": 0.70,
            },
            sample_count=100,
        ),
        SensitivityResult(
            profile="default",
            seed=101,
            metrics={
                "precision": 0.90,
                "f1": 0.80,
            },
            sample_count=100,
        ),
    ]

    summaries = (
        summarize_threshold_sensitivity(
            results
        )
    )

    assert len(summaries) == 1

    summary = summaries[0]

    assert summary.profile == "default"
    assert summary.runs == 2
    assert summary.metrics_mean[
        "precision"
    ] == pytest.approx(0.85)
    assert summary.metrics_mean[
        "f1"
    ] == pytest.approx(0.75)


def test_standard_deviation_is_calculated():
    results = [
        SensitivityResult(
            profile="default",
            seed=42,
            metrics={
                "f1": 0.70,
            },
            sample_count=100,
        ),
        SensitivityResult(
            profile="default",
            seed=101,
            metrics={
                "f1": 0.80,
            },
            sample_count=100,
        ),
    ]

    summary = (
        summarize_threshold_sensitivity(
            results
        )[0]
    )

    assert summary.metrics_std[
        "f1"
    ] == pytest.approx(
        0.070710678,
        rel=1e-6,
    )


def test_sensitivity_delta():
    default = SensitivitySummary(
        profile="default",
        runs=5,
        sample_count=500,
        metrics_mean={
            "precision": 0.80,
            "recall": 0.75,
            "f1": 0.77,
        },
        metrics_std={
            "precision": 0.02,
            "recall": 0.03,
            "f1": 0.02,
        },
    )

    higher = SensitivitySummary(
        profile="higher",
        runs=5,
        sample_count=500,
        metrics_mean={
            "precision": 0.85,
            "recall": 0.70,
            "f1": 0.76,
        },
        metrics_std={
            "precision": 0.02,
            "recall": 0.04,
            "f1": 0.03,
        },
    )

    delta = calculate_sensitivity_delta(
        default,
        higher,
    )

    assert delta["precision"] == pytest.approx(
        0.05
    )

    assert delta["recall"] == pytest.approx(
        -0.05
    )

    assert delta["f1"] == pytest.approx(
        -0.01
    )


def test_delta_requires_default_profile():
    not_default = SensitivitySummary(
        profile="higher",
        runs=1,
        sample_count=100,
        metrics_mean={
            "f1": 0.80,
        },
        metrics_std={
            "f1": 0.0,
        },
    )

    comparison = SensitivitySummary(
        profile="lower",
        runs=1,
        sample_count=100,
        metrics_mean={
            "f1": 0.70,
        },
        metrics_std={
            "f1": 0.0,
        },
    )

    with pytest.raises(ValueError):
        calculate_sensitivity_delta(
            not_default,
            comparison,
        )


def test_direction_classification():
    default = SensitivitySummary(
        profile="default",
        runs=1,
        sample_count=100,
        metrics_mean={
            "f1": 0.80,
        },
        metrics_std={
            "f1": 0.0,
        },
    )

    higher = SensitivitySummary(
        profile="higher",
        runs=1,
        sample_count=100,
        metrics_mean={
            "f1": 0.85,
        },
        metrics_std={
            "f1": 0.0,
        },
    )

    assert (
        classify_threshold_direction(
            default,
            higher,
            metric="f1",
        )
        == "higher_than_default"
    )


def test_zero_direction_classification():
    default = SensitivitySummary(
        profile="default",
        runs=1,
        sample_count=100,
        metrics_mean={
            "f1": 0.80,
        },
        metrics_std={
            "f1": 0.0,
        },
    )

    comparison = SensitivitySummary(
        profile="higher",
        runs=1,
        sample_count=100,
        metrics_mean={
            "f1": 0.80,
        },
        metrics_std={
            "f1": 0.0,
        },
    )

    assert (
        classify_threshold_direction(
            default,
            comparison,
            metric="f1",
        )
        == "unchanged_from_default"
    )


def test_sensitivity_table_contains_mean_and_std():
    summary = SensitivitySummary(
        profile="default",
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
    )

    table = build_sensitivity_table(
        [summary]
    )

    assert len(table) == 1

    assert table[0]["profile"] == "default"
    assert table[0]["precision"] == 0.85
    assert table[0]["precision_std"] == 0.02
    assert table[0]["f1"] == 0.80
    assert table[0]["f1_std"] == 0.03


def test_research_interpretation_is_cautious():
    profile = get_threshold_profile(
        "higher"
    )

    interpretation = (
        build_research_interpretation(
            profile=profile,
            metric="F1",
            delta=0.04,
        )
    )

    assert "increased" in interpretation
    assert "statistical significance" in interpretation
    assert "generalization" in interpretation


def test_profile_serialization():
    profile = get_threshold_profile(
        "default"
    )

    data = profile.to_dict()

    assert data["name"] == "default"
    assert "config" in data
    assert (
        data["config"]["name"]
        == "sensitivity-default"
    )