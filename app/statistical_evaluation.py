import pytest

from typing import Any, Dict, Iterable, List

import math
import statistics

from scipy import stats


DEFAULT_ALPHA = 0.05


def _extract_metric_values(
    results: Iterable[Dict[str, Any]],
    metric: str,
):
    baseline_values = []
    aegisguard_values = []

    for result in results:

        baseline = result.get(
            "baseline",
            {},
        )

        aegisguard = result.get(
            "aegisguard",
            {},
        )

        baseline_value = float(
            baseline.get(
                metric,
                0.0,
            )
        )

        aegisguard_value = float(
            aegisguard.get(
                metric,
                0.0,
            )
        )

        baseline_values.append(
            baseline_value
        )

        aegisguard_values.append(
            aegisguard_value
        )

    return (
        baseline_values,
        aegisguard_values,
    )


def calculate_paired_differences(
    results: Iterable[Dict[str, Any]],
    metric: str = "f1_score",
) -> List[float]:

    (
        baseline_values,
        aegisguard_values,
    ) = _extract_metric_values(
        results,
        metric,
    )

    return [
        aegisguard - baseline
        for baseline, aegisguard
        in zip(
            baseline_values,
            aegisguard_values,
        )
    ]


def calculate_descriptive_statistics(
    results: Iterable[Dict[str, Any]],
    metric: str = "f1_score",
) -> Dict[str, float]:

    differences = calculate_paired_differences(
        results,
        metric,
    )

    if not differences:

        return {
            "n": 0,
            "mean_difference": 0.0,
            "median_difference": 0.0,
            "std_difference": 0.0,
            "min_difference": 0.0,
            "max_difference": 0.0,
        }

    mean_difference = statistics.mean(
        differences
    )

    median_difference = statistics.median(
        differences
    )

    std_difference = (
        statistics.stdev(
            differences
        )
        if len(differences) > 1
        else 0.0
    )

    return {
        "n": len(differences),

        "mean_difference":
            mean_difference,

        "median_difference":
            median_difference,

        "std_difference":
            std_difference,

        "min_difference":
            min(differences),

        "max_difference":
            max(differences),
    }


def calculate_confidence_interval(
    results: Iterable[Dict[str, Any]],
    metric: str = "f1_score",
    confidence: float = 0.95,
) -> Dict[str, float]:

    differences = calculate_paired_differences(
        results,
        metric,
    )

    n = len(differences)

    if n == 0:

        return {
            "confidence_level": confidence,
            "lower": 0.0,
            "upper": 0.0,
            "margin": 0.0,
        }

    mean_difference = statistics.mean(
        differences
    )

    if n == 1:

        return {
            "confidence_level": confidence,
            "lower": mean_difference,
            "upper": mean_difference,
            "margin": 0.0,
        }

    std_difference = statistics.stdev(
        differences
    )

    standard_error = (
        std_difference
        / math.sqrt(n)
    )

    alpha = 1.0 - confidence

    critical_value = stats.t.ppf(
        1.0 - alpha / 2.0,
        df=n - 1,
    )

    margin = (
        critical_value
        * standard_error
    )

    return {
        "confidence_level": confidence,

        "lower":
            mean_difference - margin,

        "upper":
            mean_difference + margin,

        "margin":
            margin,
    }


def paired_t_test(
    results: Iterable[Dict[str, Any]],
    metric: str = "f1_score",
) -> Dict[str, Any]:

    (
        baseline_values,
        aegisguard_values,
    ) = _extract_metric_values(
        results,
        metric,
    )

    if len(baseline_values) < 2:

        return {
            "test": "paired_t_test",
            "statistic": None,
            "p_value": None,
            "significant": False,
            "reason":
                "At least two paired experiments are required.",
        }

    statistic, p_value = (
        stats.ttest_rel(
            aegisguard_values,
            baseline_values,
        )
    )

    return {
        "test":
            "paired_t_test",

        "statistic":
            float(statistic),

        "p_value":
            float(p_value),

        "significant":
            bool(
                p_value
                < DEFAULT_ALPHA
            ),
    }


def wilcoxon_test(
    results: Iterable[Dict[str, Any]],
    metric: str = "f1_score",
) -> Dict[str, Any]:

    differences = calculate_paired_differences(
        results,
        metric,
    )

    non_zero = [
        value
        for value in differences
        if value != 0
    ]

    if len(non_zero) < 2:

        return {
            "test":
                "wilcoxon_signed_rank",

            "statistic":
                None,

            "p_value":
                None,

            "significant":
                False,

            "reason":
                "At least two non-zero paired differences are required.",
        }

    try:

        statistic, p_value = (
            stats.wilcoxon(
                differences
            )
        )

    except ValueError as error:

        return {
            "test":
                "wilcoxon_signed_rank",

            "statistic":
                None,

            "p_value":
                None,

            "significant":
                False,

            "reason":
                str(error),
        }

    return {
        "test":
            "wilcoxon_signed_rank",

        "statistic":
            float(statistic),

        "p_value":
            float(p_value),

        "significant":
            bool(
                p_value
                < DEFAULT_ALPHA
            ),
    }


def calculate_cohens_d(
    results: Iterable[Dict[str, Any]],
    metric: str = "f1_score",
) -> float:

    differences = calculate_paired_differences(
        results,
        metric,
    )

    if len(differences) < 2:

        return 0.0

    std_difference = statistics.stdev(
        differences
    )

    if std_difference == 0:

        return 0.0

    return (
        statistics.mean(
            differences
        )
        / std_difference
    )


def interpret_effect_size(
    cohens_d: float,
) -> str:

    absolute_value = abs(
        cohens_d
    )

    if absolute_value < 0.2:
        return "negligible"

    if absolute_value < 0.5:
        return "small"

    if absolute_value < 0.8:
        return "medium"

    return "large"


def build_statistical_report(
    results: Iterable[Dict[str, Any]],
    metric: str = "f1_score",
    confidence: float = 0.95,
) -> Dict[str, Any]:

    results = list(results)

    descriptive = (
        calculate_descriptive_statistics(
            results,
            metric,
        )
    )

    confidence_interval = (
        calculate_confidence_interval(
            results,
            metric,
            confidence,
        )
    )

    t_test = paired_t_test(
        results,
        metric,
    )

    wilcoxon = wilcoxon_test(
        results,
        metric,
    )

    cohens_d = calculate_cohens_d(
        results,
        metric,
    )

    return {
        "metric":
            metric,

        "descriptive":
            descriptive,

        "confidence_interval":
            confidence_interval,

        "paired_t_test":
            t_test,

        "wilcoxon":
            wilcoxon,

        "cohens_d":
            cohens_d,

        "effect_size":
            interpret_effect_size(
                cohens_d
            ),
    }