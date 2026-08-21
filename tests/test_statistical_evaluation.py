import pytest
from app.statistical_evaluation import (
    calculate_paired_differences,
    calculate_descriptive_statistics,
    calculate_confidence_interval,
    paired_t_test,
    wilcoxon_test,
    calculate_cohens_d,
    interpret_effect_size,
    build_statistical_report,
)


def sample_results():
    return [
        {
            "baseline": {
                "f1_score": 0.50,
            },
            "aegisguard": {
                "f1_score": 0.60,
            },
        },
        {
            "baseline": {
                "f1_score": 0.55,
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
                "f1_score": 0.75,
            },
        },
        {
            "baseline": {
                "f1_score": 0.65,
            },
            "aegisguard": {
                "f1_score": 0.72,
            },
        },
        {
            "baseline": {
                "f1_score": 0.58,
            },
            "aegisguard": {
                "f1_score": 0.68,
            },
        },
    ]


def test_paired_differences():

    differences = (
        calculate_paired_differences(
            sample_results()
        )
    )

    assert len(differences) == 5

    assert differences[0] == pytest.approx(0.10)
    assert differences[1] == pytest.approx(0.15)


def test_descriptive_statistics():

    result = (
        calculate_descriptive_statistics(
            sample_results()
        )
    )

    assert result["n"] == 5

    assert result[
        "mean_difference"
    ] > 0

    assert result[
        "max_difference"
    ] > 0


def test_confidence_interval():

    result = (
        calculate_confidence_interval(
            sample_results()
        )
    )

    assert (
        result["lower"]
        <= result["upper"]
    )


def test_paired_t_test():

    result = paired_t_test(
        sample_results()
    )

    assert result["test"] == (
        "paired_t_test"
    )

    assert result["p_value"] is not None


def test_wilcoxon():

    result = wilcoxon_test(
        sample_results()
    )

    assert result["test"] == (
        "wilcoxon_signed_rank"
    )

    assert result["p_value"] is not None


def test_cohens_d():

    result = calculate_cohens_d(
        sample_results()
    )

    assert result > 0


def test_effect_interpretation():

    assert (
        interpret_effect_size(
            0.1
        )
        == "negligible"
    )

    assert (
        interpret_effect_size(
            0.3
        )
        == "small"
    )

    assert (
        interpret_effect_size(
            0.6
        )
        == "medium"
    )

    assert (
        interpret_effect_size(
            1.0
        )
        == "large"
    )


def test_complete_report():

    report = build_statistical_report(
        sample_results()
    )

    assert (
        report["metric"]
        == "f1_score"
    )

    assert (
        "descriptive"
        in report
    )

    assert (
        "confidence_interval"
        in report
    )

    assert (
        "paired_t_test"
        in report
    )

    assert (
        "wilcoxon"
        in report
    )

    assert (
        "cohens_d"
        in report
    )

    assert (
        "effect_size"
        in report
    )