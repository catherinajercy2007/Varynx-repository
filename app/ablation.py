"""
Varynx Day 36
Ablation Study Framework

Purpose
-------
Evaluate the contribution of individual Varynx components by
comparing a complete configuration against controlled variants.

Research principle
------------------
Every ablation variant must be evaluated using the same:
- dataset
- labels
- seeds
- metric definitions
- evaluation procedure

Only the selected architectural component is disabled.

This module does not assume that the full system performs best.
The experiment is intended to measure the contribution of each
component objectively.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import sqrt
from statistics import mean
from typing import Any, Callable, Iterable, Mapping, Sequence


# ============================================================
# ABLATION VARIANTS
# ============================================================


class AblationVariant(str, Enum):
    """Controlled Varynx configurations."""

    FULL_VARYNX = "full_varynx"

    WITHOUT_BEHAVIOR = (
        "without_behavior"
    )

    WITHOUT_MULTIRESOLUTION = (
        "without_multiresolution"
    )

    WITHOUT_CROSS_CONTEXT = (
        "without_cross_context"
    )

    WITHOUT_ADAPTIVE_RESPONSE = (
        "without_adaptive_response"
    )


@dataclass(frozen=True)
class AblationConfiguration:
    """
    Explicit feature configuration for one experiment variant.
    """

    variant: AblationVariant

    behavioral: bool
    multiresolution: bool
    cross_context: bool
    adaptive_response: bool

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable configuration."""

        return {
            "variant": self.variant.value,
            "behavioral": self.behavioral,
            "multiresolution": self.multiresolution,
            "cross_context": self.cross_context,
            "adaptive_response": self.adaptive_response,
        }


@dataclass(frozen=True)
class AblationResult:
    """
    Result from one ablation experiment.

    Metrics are deliberately generic so the framework can work
    with the project's existing evaluation implementation.
    """

    variant: AblationVariant
    seed: int
    metrics: Mapping[str, float]
    sample_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable result."""

        return {
            "variant": self.variant.value,
            "seed": self.seed,
            "metrics": {
                key: float(value)
                for key, value in self.metrics.items()
            },
            "sample_count": self.sample_count,
        }


@dataclass(frozen=True)
class AblationSummary:
    """
    Aggregated result for one ablation variant.
    """

    variant: AblationVariant
    runs: int
    metrics_mean: Mapping[str, float]
    metrics_std: Mapping[str, float]
    sample_count: int

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable summary."""

        return {
            "variant": self.variant.value,
            "runs": self.runs,
            "metrics_mean": dict(
                self.metrics_mean
            ),
            "metrics_std": dict(
                self.metrics_std
            ),
            "sample_count": self.sample_count,
        }


# ============================================================
# CONFIGURATION
# ============================================================


ABLATION_CONFIGURATIONS = {
    AblationVariant.FULL_VARYNX: AblationConfiguration(
        variant=AblationVariant.FULL_VARYNX,
        behavioral=True,
        multiresolution=True,
        cross_context=True,
        adaptive_response=True,
    ),
    AblationVariant.WITHOUT_BEHAVIOR: AblationConfiguration(
        variant=AblationVariant.WITHOUT_BEHAVIOR,
        behavioral=False,
        multiresolution=True,
        cross_context=True,
        adaptive_response=True,
    ),
    AblationVariant.WITHOUT_MULTIRESOLUTION: AblationConfiguration(
        variant=AblationVariant.WITHOUT_MULTIRESOLUTION,
        behavioral=True,
        multiresolution=False,
        cross_context=True,
        adaptive_response=True,
    ),
    AblationVariant.WITHOUT_CROSS_CONTEXT: AblationConfiguration(
        variant=AblationVariant.WITHOUT_CROSS_CONTEXT,
        behavioral=True,
        multiresolution=True,
        cross_context=False,
        adaptive_response=True,
    ),
    AblationVariant.WITHOUT_ADAPTIVE_RESPONSE: AblationConfiguration(
        variant=AblationVariant.WITHOUT_ADAPTIVE_RESPONSE,
        behavioral=True,
        multiresolution=True,
        cross_context=True,
        adaptive_response=False,
    ),
}


def get_ablation_configurations() -> list[AblationConfiguration]:
    """
    Return all predefined ablation configurations.
    """

    return list(
        ABLATION_CONFIGURATIONS.values()
    )


def get_ablation_configuration(
    variant: AblationVariant | str,
) -> AblationConfiguration:
    """
    Retrieve one ablation configuration.
    """

    if not isinstance(
        variant,
        AblationVariant,
    ):
        variant = AblationVariant(
            variant
        )

    return ABLATION_CONFIGURATIONS[
        variant
    ]


# ============================================================
# RESULT VALIDATION
# ============================================================


def _validate_metric_mapping(
    metrics: Mapping[str, float],
) -> dict[str, float]:
    """
    Validate and normalize metric values.

    Metrics must be finite numeric values.
    """

    normalized: dict[str, float] = {}

    for name, value in metrics.items():
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                f"Metric '{name}' must be numeric"
            ) from exc

        if not (
            numeric == numeric
        ):
            raise ValueError(
                f"Metric '{name}' cannot be NaN"
            )

        if numeric in (
            float("inf"),
            float("-inf"),
        ):
            raise ValueError(
                f"Metric '{name}' must be finite"
            )

        normalized[name] = numeric

    return normalized


# ============================================================
# ABLATION EXECUTION
# ============================================================


DetectorFunction = Callable[
    [
        Sequence[Mapping[str, Any]],
        AblationConfiguration,
        int,
    ],
    Mapping[str, float],
]


def run_ablation_experiment(
    dataset: Sequence[Mapping[str, Any]],
    *,
    seeds: Iterable[int],
    detector: DetectorFunction,
    variants: Iterable[
        AblationVariant | str
    ] | None = None,
) -> list[AblationResult]:
    """
    Run the same dataset through multiple controlled variants.

    Parameters
    ----------
    dataset:
        The exact same evaluation dataset supplied to every
        variant.

    seeds:
        Reproducibility seeds.

    detector:
        Adapter around the existing Varynx evaluation pipeline.

        Signature:
            detector(dataset, configuration, seed) -> metrics

    variants:
        Optional subset of variants. By default all predefined
        variants are evaluated.

    Returns
    -------
    list[AblationResult]
    """

    if dataset is None:
        raise ValueError(
            "dataset cannot be None"
        )

    dataset = list(dataset)

    if not dataset:
        raise ValueError(
            "dataset cannot be empty"
        )

    seed_list = [
        int(seed)
        for seed in seeds
    ]

    if not seed_list:
        raise ValueError(
            "At least one seed is required"
        )

    if variants is None:
        variant_list = list(
            AblationVariant
        )
    else:
        variant_list = [
            item
            if isinstance(
                item,
                AblationVariant,
            )
            else AblationVariant(item)
            for item in variants
        ]

    results: list[AblationResult] = []

    for variant in variant_list:
        configuration = (
            get_ablation_configuration(
                variant
            )
        )

        for seed in seed_list:
            metrics = detector(
                dataset,
                configuration,
                seed,
            )

            validated = _validate_metric_mapping(
                metrics
            )

            results.append(
                AblationResult(
                    variant=variant,
                    seed=seed,
                    metrics=validated,
                    sample_count=len(
                        dataset
                    ),
                )
            )

    return results


# ============================================================
# AGGREGATION
# ============================================================


def _sample_std(
    values: Sequence[float],
) -> float:
    """
    Calculate sample standard deviation.

    Returns 0 for one observation.
    """

    if len(values) <= 1:
        return 0.0

    average = mean(values)

    variance = sum(
        (value - average) ** 2
        for value in values
    ) / (len(values) - 1)

    return sqrt(variance)


def summarize_ablation(
    results: Sequence[AblationResult],
) -> list[AblationSummary]:
    """
    Aggregate repeated ablation runs by variant.
    """

    if not results:
        return []

    grouped: dict[
        AblationVariant,
        list[AblationResult],
    ] = {}

    for result in results:
        grouped.setdefault(
            result.variant,
            [],
        ).append(result)

    summaries: list[AblationSummary] = []

    for variant, variant_results in grouped.items():
        metric_names = set()

        for result in variant_results:
            metric_names.update(
                result.metrics.keys()
            )

        metric_means: dict[str, float] = {}
        metric_stds: dict[str, float] = {}

        for metric_name in sorted(
            metric_names
        ):
            values = [
                float(
                    result.metrics[
                        metric_name
                    ]
                )
                for result in variant_results
                if metric_name
                in result.metrics
            ]

            if not values:
                continue

            metric_means[
                metric_name
            ] = mean(values)

            metric_stds[
                metric_name
            ] = _sample_std(values)

        summaries.append(
            AblationSummary(
                variant=variant,
                runs=len(
                    variant_results
                ),
                metrics_mean=metric_means,
                metrics_std=metric_stds,
                sample_count=sum(
                    result.sample_count
                    for result in variant_results
                ),
            )
        )

    return summaries


# ============================================================
# COMPARISON
# ============================================================


def calculate_ablation_delta(
    full_result: AblationSummary,
    ablated_result: AblationSummary,
) -> dict[str, float]:
    """
    Calculate:

        Full Varynx - Ablated Variant

    Positive values mean the full system achieved the higher
    metric value.

    No claim about statistical significance is made here.
    """

    if (
        full_result.variant
        != AblationVariant.FULL_VARYNX
    ):
        raise ValueError(
            "full_result must be FULL_VARYNX"
        )

    delta: dict[str, float] = {}

    common_metrics = (
        set(
            full_result.metrics_mean.keys()
        )
        & set(
            ablated_result.metrics_mean.keys()
        )
    )

    for metric in sorted(
        common_metrics
    ):
        delta[metric] = (
            float(
                full_result.metrics_mean[
                    metric
                ]
            )
            - float(
                ablated_result.metrics_mean[
                    metric
                ]
            )
        )

    return delta


def build_ablation_table(
    summaries: Sequence[AblationSummary],
) -> list[dict[str, Any]]:
    """
    Build a dashboard/research-report friendly table.
    """

    table: list[dict[str, Any]] = []

    for summary in summaries:
        row: dict[str, Any] = {
            "variant": summary.variant.value,
            "runs": summary.runs,
            "sample_count": summary.sample_count,
        }

        for metric, value in (
            summary.metrics_mean.items()
        ):
            row[
                metric
            ] = round(
                float(value),
                6,
            )

            row[
                f"{metric}_std"
            ] = round(
                float(
                    summary.metrics_std.get(
                        metric,
                        0.0,
                    )
                ),
                6,
            )

        table.append(row)

    return table


# ============================================================
# RESEARCH INTERPRETATION
# ============================================================


def interpret_component_delta(
    *,
    component: str,
    metric: str,
    delta: float,
) -> str:
    """
    Produce a cautious interpretation.

    This intentionally avoids saying that a component is
    statistically significant because delta alone cannot
    establish statistical significance.
    """

    if delta > 0:
        direction = (
            f"Full Varynx produced a higher {metric} "
            f"than the configuration without {component}."
        )
    elif delta < 0:
        direction = (
            f"Full Varynx produced a lower {metric} "
            f"than the configuration without {component}."
        )
    else:
        direction = (
            f"Full Varynx and the configuration without "
            f"{component} produced the same {metric}."
        )

    return (
        f"{direction} "
        "This is an observed experimental difference, "
        "not evidence of statistical significance by itself."
    )


__all__ = [
    "AblationVariant",
    "AblationConfiguration",
    "AblationResult",
    "AblationSummary",
    "ABLATION_CONFIGURATIONS",
    "get_ablation_configurations",
    "get_ablation_configuration",
    "run_ablation_experiment",
    "summarize_ablation",
    "calculate_ablation_delta",
    "build_ablation_table",
    "interpret_component_delta",
]