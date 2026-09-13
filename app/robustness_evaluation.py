"""
Varynx Day 38
Robustness Evaluation Framework

Purpose
-------
Evaluate whether Varynx remains stable when experimental
conditions change.

Robustness dimensions
---------------------
1. Random seeds
2. Event volume
3. Attack ratio
4. Behavioral distribution
5. Noise level

Research principles
-------------------
- Use controlled condition changes.
- Keep evaluation methodology consistent.
- Never silently retune the system for each condition.
- Compare conditions against an explicit reference.
- Report observed degradation rather than claiming robustness
  without evidence.
- Statistical significance must be established separately.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from statistics import mean, stdev
from typing import Any, Callable, Iterable, Mapping, Sequence


# ============================================================
# ENUMERATIONS
# ============================================================


class RobustnessDimension(str, Enum):
    """Dimensions along which robustness is evaluated."""

    SEED = "seed"
    EVENT_VOLUME = "event_volume"
    ATTACK_RATIO = "attack_ratio"
    BEHAVIOR_DISTRIBUTION = (
        "behavior_distribution"
    )
    NOISE = "noise"


class BehavioralDistribution(str, Enum):
    """Controlled behavioral-distribution profiles."""

    NORMAL = "normal"
    DIVERSE = "diverse"
    CONCENTRATED = "concentrated"
    DRIFTING = "drifting"


# ============================================================
# CONFIGURATION
# ============================================================


@dataclass(frozen=True)
class RobustnessCondition:
    """
    One controlled experimental condition.
    """

    dimension: RobustnessDimension
    name: str

    value: Any
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "name": self.name,
            "value": self.value,
            "description": self.description,
        }


@dataclass(frozen=True)
class RobustnessResult:
    """
    Result from one robustness experiment.
    """

    dimension: RobustnessDimension
    condition: str
    seed: int
    metrics: Mapping[str, float]
    sample_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "condition": self.condition,
            "seed": self.seed,
            "metrics": dict(self.metrics),
            "sample_count": self.sample_count,
        }


@dataclass(frozen=True)
class RobustnessSummary:
    """
    Aggregated results for one robustness condition.
    """

    dimension: RobustnessDimension
    condition: str
    runs: int
    sample_count: int

    metrics_mean: Mapping[str, float]
    metrics_std: Mapping[str, float]
    metrics_min: Mapping[str, float]
    metrics_max: Mapping[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "condition": self.condition,
            "runs": self.runs,
            "sample_count": self.sample_count,
            "metrics_mean": dict(
                self.metrics_mean
            ),
            "metrics_std": dict(
                self.metrics_std
            ),
            "metrics_min": dict(
                self.metrics_min
            ),
            "metrics_max": dict(
                self.metrics_max
            ),
        }


# ============================================================
# DEFAULT CONDITIONS
# ============================================================


def build_seed_conditions() -> list[RobustnessCondition]:
    """
    Build deterministic seed conditions.

    Seeds are intentionally explicit so experiments can be
    reproduced.
    """

    seeds = [
        42,
        101,
        202,
        303,
        404,
        505,
        606,
        707,
        808,
        909,
    ]

    return [
        RobustnessCondition(
            dimension=RobustnessDimension.SEED,
            name=f"seed_{seed}",
            value=seed,
            description=(
                f"Experiment using random seed {seed}."
            ),
        )
        for seed in seeds
    ]


def build_event_volume_conditions() -> list[
    RobustnessCondition
]:
    """
    Build controlled event-volume conditions.

    Values represent the number of events in an experimental
    dataset.
    """

    volumes = [
        100,
        500,
        1000,
        5000,
        10000,
    ]

    return [
        RobustnessCondition(
            dimension=RobustnessDimension.EVENT_VOLUME,
            name=f"events_{volume}",
            value=volume,
            description=(
                f"Experimental dataset containing "
                f"{volume} events."
            ),
        )
        for volume in volumes
    ]


def build_attack_ratio_conditions() -> list[
    RobustnessCondition
]:
    """
    Build controlled attack-ratio conditions.

    Values are represented as fractions.
    """

    ratios = [
        0.01,
        0.05,
        0.10,
        0.20,
        0.30,
        0.50,
    ]

    return [
        RobustnessCondition(
            dimension=RobustnessDimension.ATTACK_RATIO,
            name=f"attack_ratio_{int(ratio * 100)}pct",
            value=ratio,
            description=(
                f"Dataset containing approximately "
                f"{ratio:.0%} attack events."
            ),
        )
        for ratio in ratios
    ]


def build_behavior_distribution_conditions() -> list[
    RobustnessCondition
]:
    """
    Build behavioral-distribution conditions.
    """

    distributions = [
        BehavioralDistribution.NORMAL,
        BehavioralDistribution.DIVERSE,
        BehavioralDistribution.CONCENTRATED,
        BehavioralDistribution.DRIFTING,
    ]

    descriptions = {
        BehavioralDistribution.NORMAL: (
            "Representative baseline behavioral distribution."
        ),
        BehavioralDistribution.DIVERSE: (
            "Higher behavioral diversity across actions and resources."
        ),
        BehavioralDistribution.CONCENTRATED: (
            "Behavior concentrated around a smaller set of actions "
            "and resources."
        ),
        BehavioralDistribution.DRIFTING: (
            "Behavior gradually shifts from the baseline distribution."
        ),
    }

    return [
        RobustnessCondition(
            dimension=(
                RobustnessDimension
                .BEHAVIOR_DISTRIBUTION
            ),
            name=distribution.value,
            value=distribution.value,
            description=descriptions[
                distribution
            ],
        )
        for distribution in distributions
    ]


def build_noise_conditions() -> list[
    RobustnessCondition
]:
    """
    Build controlled noise conditions.

    Values represent the approximate fraction of events whose
    behavioral/evidence attributes are perturbed.
    """

    levels = [
        0.00,
        0.05,
        0.10,
        0.20,
        0.30,
    ]

    return [
        RobustnessCondition(
            dimension=RobustnessDimension.NOISE,
            name=f"noise_{int(level * 100)}pct",
            value=level,
            description=(
                f"Approximately {level:.0%} "
                "controlled evidence noise."
            ),
        )
        for level in levels
    ]


def build_all_robustness_conditions() -> dict[
    RobustnessDimension,
    list[RobustnessCondition],
]:
    """
    Return all default robustness conditions.
    """

    return {
        RobustnessDimension.SEED:
            build_seed_conditions(),

        RobustnessDimension.EVENT_VOLUME:
            build_event_volume_conditions(),

        RobustnessDimension.ATTACK_RATIO:
            build_attack_ratio_conditions(),

        RobustnessDimension.BEHAVIOR_DISTRIBUTION:
            build_behavior_distribution_conditions(),

        RobustnessDimension.NOISE:
            build_noise_conditions(),
    }


# ============================================================
# CONDITION VALIDATION
# ============================================================


def validate_condition(
    condition: RobustnessCondition,
) -> None:
    """
    Validate an individual robustness condition.
    """

    if not condition.name.strip():
        raise ValueError(
            "Condition name cannot be empty"
        )

    if condition.dimension == (
        RobustnessDimension.ATTACK_RATIO
    ):
        ratio = float(condition.value)

        if not 0.0 <= ratio <= 1.0:
            raise ValueError(
                "Attack ratio must be between 0 and 1"
            )

    if condition.dimension == (
        RobustnessDimension.NOISE
    ):
        noise = float(condition.value)

        if not 0.0 <= noise <= 1.0:
            raise ValueError(
                "Noise level must be between 0 and 1"
            )

    if condition.dimension == (
        RobustnessDimension.EVENT_VOLUME
    ):
        volume = int(condition.value)

        if volume <= 0:
            raise ValueError(
                "Event volume must be positive"
            )


def validate_conditions(
    conditions: Sequence[RobustnessCondition],
) -> None:
    """
    Validate a collection of robustness conditions.
    """

    if not conditions:
        raise ValueError(
            "At least one robustness condition is required"
        )

    names = [
        condition.name
        for condition in conditions
    ]

    if len(names) != len(set(names)):
        raise ValueError(
            "Robustness condition names must be unique"
        )

    for condition in conditions:
        validate_condition(
            condition
        )


# ============================================================
# METRIC VALIDATION
# ============================================================


def _normalize_metrics(
    metrics: Mapping[str, float],
) -> dict[str, float]:
    """
    Validate metric values.
    """

    normalized: dict[str, float] = {}

    for name, value in metrics.items():
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                f"Metric '{name}' must be numeric"
            ) from exc

        if numeric != numeric:
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
# EXECUTION
# ============================================================


RobustnessDetector = Callable[
    [
        Sequence[Mapping[str, Any]],
        RobustnessCondition,
        int,
    ],
    Mapping[str, float],
]


def run_robustness_experiment(
    dataset_factory: Callable[
        [RobustnessCondition, int],
        Sequence[Mapping[str, Any]],
    ],
    *,
    conditions: Sequence[RobustnessCondition],
    seeds: Iterable[int],
    detector: RobustnessDetector,
) -> list[RobustnessResult]:
    """
    Execute a robustness experiment.

    dataset_factory:
        Creates a controlled dataset for a given condition
        and seed.

    detector:
        Existing Varynx evaluation adapter.

    The framework intentionally does not implement the actual
    Varynx detector. That belongs to the project's existing
    security/evaluation pipeline.
    """

    validate_conditions(
        conditions
    )

    seed_list = [
        int(seed)
        for seed in seeds
    ]

    if not seed_list:
        raise ValueError(
            "At least one evaluation seed is required"
        )

    results: list[RobustnessResult] = []

    for condition in conditions:
        for seed in seed_list:

            dataset = list(
                dataset_factory(
                    condition,
                    seed,
                )
            )

            if not dataset:
                raise ValueError(
                    "dataset_factory returned an empty dataset "
                    f"for condition '{condition.name}'"
                )

            metrics = detector(
                dataset,
                condition,
                seed,
            )

            normalized = _normalize_metrics(
                metrics
            )

            results.append(
                RobustnessResult(
                    dimension=condition.dimension,
                    condition=condition.name,
                    seed=seed,
                    metrics=normalized,
                    sample_count=len(dataset),
                )
            )

    return results


# ============================================================
# AGGREGATION
# ============================================================


def summarize_robustness(
    results: Sequence[RobustnessResult],
) -> list[RobustnessSummary]:
    """
    Aggregate repeated runs for every condition.
    """

    if not results:
        return []

    grouped: dict[
        tuple[RobustnessDimension, str],
        list[RobustnessResult],
    ] = {}

    for result in results:
        key = (
            result.dimension,
            result.condition,
        )

        grouped.setdefault(
            key,
            [],
        ).append(result)

    summaries: list[RobustnessSummary] = []

    for (
        dimension,
        condition,
    ), condition_results in grouped.items():

        metric_names: set[str] = set()

        for result in condition_results:
            metric_names.update(
                result.metrics.keys()
            )

        means: dict[str, float] = {}
        stds: dict[str, float] = {}
        minimums: dict[str, float] = {}
        maximums: dict[str, float] = {}

        for metric in sorted(metric_names):

            values = [
                float(
                    result.metrics[metric]
                )
                for result in condition_results
                if metric in result.metrics
            ]

            if not values:
                continue

            means[metric] = mean(
                values
            )

            stds[metric] = (
                stdev(values)
                if len(values) > 1
                else 0.0
            )

            minimums[metric] = min(
                values
            )

            maximums[metric] = max(
                values
            )

        summaries.append(
            RobustnessSummary(
                dimension=dimension,
                condition=condition,
                runs=len(
                    condition_results
                ),
                sample_count=sum(
                    result.sample_count
                    for result in condition_results
                ),
                metrics_mean=means,
                metrics_std=stds,
                metrics_min=minimums,
                metrics_max=maximums,
            )
        )

    return summaries


# ============================================================
# REFERENCE COMPARISON
# ============================================================


def calculate_reference_delta(
    reference: RobustnessSummary,
    comparison: RobustnessSummary,
) -> dict[str, float]:
    """
    Calculate:

        comparison - reference

    Positive values indicate that the comparison condition
    achieved a higher metric.
    """

    delta: dict[str, float] = {}

    common_metrics = (
        set(reference.metrics_mean)
        & set(comparison.metrics_mean)
    )

    for metric in sorted(common_metrics):
        delta[metric] = (
            comparison.metrics_mean[metric]
            - reference.metrics_mean[metric]
        )

    return delta


def calculate_relative_change(
    reference: RobustnessSummary,
    comparison: RobustnessSummary,
) -> dict[str, float]:
    """
    Calculate relative percentage change from the reference.

    Formula:

        ((comparison - reference) / abs(reference)) * 100

    When the reference value is zero, the relative change is
    reported as 0 to avoid division by zero.
    """

    changes: dict[str, float] = {}

    delta = calculate_reference_delta(
        reference,
        comparison,
    )

    for metric, difference in delta.items():
        baseline = float(
            reference.metrics_mean[metric]
        )

        if baseline == 0:
            changes[metric] = 0.0
        else:
            changes[metric] = (
                difference
                / abs(baseline)
                * 100.0
            )

    return changes


# ============================================================
# ROBUSTNESS INDICATORS
# ============================================================


def calculate_metric_range(
    summary: RobustnessSummary,
    metric: str,
) -> float:
    """
    Return max-min for one metric.
    """

    if metric not in summary.metrics_min:
        raise KeyError(
            f"Metric '{metric}' not found"
        )

    return (
        summary.metrics_max[metric]
        - summary.metrics_min[metric]
    )


def calculate_condition_stability(
    summaries: Sequence[RobustnessSummary],
    *,
    metric: str,
) -> dict[str, float]:
    """
    Calculate observed stability across conditions.

    Returns:

        mean
        standard deviation
        minimum
        maximum
        range

    This is descriptive analysis, not a statistical
    significance test.
    """

    values = [
        float(
            summary.metrics_mean[metric]
        )
        for summary in summaries
        if metric in summary.metrics_mean
    ]

    if not values:
        raise KeyError(
            f"Metric '{metric}' not found"
        )

    return {
        "mean": mean(values),
        "std": (
            stdev(values)
            if len(values) > 1
            else 0.0
        ),
        "min": min(values),
        "max": max(values),
        "range": max(values) - min(values),
    }


# ============================================================
# TABLE GENERATION
# ============================================================


def build_robustness_table(
    summaries: Sequence[RobustnessSummary],
) -> list[dict[str, Any]]:
    """
    Convert summaries to flat dashboard/report rows.
    """

    table: list[dict[str, Any]] = []

    for summary in summaries:

        row: dict[str, Any] = {
            "dimension": (
                summary.dimension.value
            ),
            "condition": summary.condition,
            "runs": summary.runs,
            "sample_count": (
                summary.sample_count
            ),
        }

        for metric, value in (
            summary.metrics_mean.items()
        ):
            row[metric] = round(
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

            row[
                f"{metric}_min"
            ] = round(
                float(
                    summary.metrics_min.get(
                        metric,
                        value,
                    )
                ),
                6,
            )

            row[
                f"{metric}_max"
            ] = round(
                float(
                    summary.metrics_max.get(
                        metric,
                        value,
                    )
                ),
                6,
            )

        table.append(row)

    return table


# ============================================================
# RESEARCH INTERPRETATION
# ============================================================


def interpret_robustness(
    *,
    dimension: RobustnessDimension,
    condition: str,
    metric: str,
    relative_change_percent: float,
) -> str:
    """
    Generate cautious descriptive interpretation.

    This function deliberately avoids terms such as
    "statistically significant", "proven robust", or
    "generalizable".
    """

    if relative_change_percent > 0:
        direction = "increased"
    elif relative_change_percent < 0:
        direction = "decreased"
    else:
        direction = "did not change"

    return (
        f"Under the {dimension.value} condition "
        f"'{condition}', {metric} {direction} relative "
        "to the selected reference condition. "
        "This is an observed experimental change and does "
        "not by itself establish statistical significance "
        "or real-world generalization."
    )


__all__ = [
    "RobustnessDimension",
    "BehavioralDistribution",
    "RobustnessCondition",
    "RobustnessResult",
    "RobustnessSummary",
    "build_seed_conditions",
    "build_event_volume_conditions",
    "build_attack_ratio_conditions",
    "build_behavior_distribution_conditions",
    "build_noise_conditions",
    "build_all_robustness_conditions",
    "validate_condition",
    "validate_conditions",
    "run_robustness_experiment",
    "summarize_robustness",
    "calculate_reference_delta",
    "calculate_relative_change",
    "calculate_metric_range",
    "calculate_condition_stability",
    "build_robustness_table",
    "interpret_robustness",
]