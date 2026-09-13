"""
Varynx Day 37
Threshold Sensitivity Analysis

Purpose
-------
Evaluate how changes in adaptive-response thresholds affect
security outcomes.

Research principles
-------------------
1. The default configuration is preserved.
2. Alternative configurations are explicit.
3. Threshold changes are systematic rather than arbitrary.
4. The same dataset and seeds should be used across profiles.
5. Results are observations, not automatic evidence of
   statistical significance.
6. The framework does not select an "optimal" threshold.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, stdev
from typing import Any, Callable, Iterable, Mapping, Sequence

from app.adaptive_config import (
    AdaptiveConfig,
    build_adaptive_config,
    get_default_adaptive_config,
)


# ============================================================
# TYPES
# ============================================================

ThresholdDetector = Callable[
    [
        Sequence[Mapping[str, Any]],
        AdaptiveConfig,
        int,
    ],
    Mapping[str, float],
]


@dataclass(frozen=True)
class ThresholdProfile:
    """
    Named threshold configuration used in sensitivity analysis.
    """

    name: str
    description: str
    config: AdaptiveConfig

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "config": self.config.to_dict(),
        }


@dataclass(frozen=True)
class SensitivityResult:
    """
    Result from one threshold profile and one seed.
    """

    profile: str
    seed: int
    metrics: Mapping[str, float]
    sample_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "seed": self.seed,
            "metrics": dict(self.metrics),
            "sample_count": self.sample_count,
        }


@dataclass(frozen=True)
class SensitivitySummary:
    """
    Aggregated results for one threshold profile.
    """

    profile: str
    runs: int
    sample_count: int
    metrics_mean: Mapping[str, float]
    metrics_std: Mapping[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "runs": self.runs,
            "sample_count": self.sample_count,
            "metrics_mean": dict(self.metrics_mean),
            "metrics_std": dict(self.metrics_std),
        }


# ============================================================
# PROFILE CONSTRUCTION
# ============================================================

def _profile_values(
    *,
    monitoring: float,
    step_up: float,
    reduce_scope: float,
    human_review: float,
    block: float,
) -> dict[str, float]:
    return {
        "monitoring": monitoring,
        "step_up": step_up,
        "reduce_scope": reduce_scope,
        "human_review": human_review,
        "block": block,
    }


def build_threshold_profiles() -> list[ThresholdProfile]:
    """
    Build the controlled sensitivity profiles.

    The default configuration is copied first so escalation
    thresholds remain unchanged during this experiment.

    Only the adaptive response ladder is varied here.
    """

    default = get_default_adaptive_config()

    base = default.thresholds

    profiles = [
        (
            "default",
            "Current/default adaptive thresholds.",
            _profile_values(
                monitoring=base.monitoring,
                step_up=base.step_up,
                reduce_scope=base.reduce_scope,
                human_review=base.human_review,
                block=base.block,
            ),
        ),
        (
            "lower",
            "Earlier escalation across the response ladder.",
            _profile_values(
                monitoring=max(
                    0.0,
                    base.monitoring - 5.0,
                ),
                step_up=max(
                    0.0,
                    base.step_up - 5.0,
                ),
                reduce_scope=max(
                    0.0,
                    base.reduce_scope - 5.0,
                ),
                human_review=max(
                    0.0,
                    base.human_review - 5.0,
                ),
                block=max(
                    0.0,
                    base.block - 5.0,
                ),
            ),
        ),
        (
            "slightly_lower",
            "Small downward threshold shift.",
            _profile_values(
                monitoring=max(
                    0.0,
                    base.monitoring - 2.0,
                ),
                step_up=max(
                    0.0,
                    base.step_up - 2.0,
                ),
                reduce_scope=max(
                    0.0,
                    base.reduce_scope - 2.0,
                ),
                human_review=max(
                    0.0,
                    base.human_review - 2.0,
                ),
                block=max(
                    0.0,
                    base.block - 2.0,
                ),
            ),
        ),
        (
            "slightly_higher",
            "Small upward threshold shift.",
            _profile_values(
                monitoring=min(
                    100.0,
                    base.monitoring + 2.0,
                ),
                step_up=min(
                    100.0,
                    base.step_up + 2.0,
                ),
                reduce_scope=min(
                    100.0,
                    base.reduce_scope + 2.0,
                ),
                human_review=min(
                    100.0,
                    base.human_review + 2.0,
                ),
                block=min(
                    100.0,
                    base.block + 2.0,
                ),
            ),
        ),
        (
            "higher",
            "Later escalation across the response ladder.",
            _profile_values(
                monitoring=min(
                    100.0,
                    base.monitoring + 5.0,
                ),
                step_up=min(
                    100.0,
                    base.step_up + 5.0,
                ),
                reduce_scope=min(
                    100.0,
                    base.reduce_scope + 5.0,
                ),
                human_review=min(
                    100.0,
                    base.human_review + 5.0,
                ),
                block=min(
                    100.0,
                    base.block + 5.0,
                ),
            ),
        ),
    ]

    result: list[ThresholdProfile] = []

    for name, description, thresholds in profiles:
        config = build_adaptive_config(
            name=f"sensitivity-{name}",
            version="1.0",
            thresholds=thresholds,
        )

        result.append(
            ThresholdProfile(
                name=name,
                description=description,
                config=config,
            )
        )

    return result


def get_threshold_profile(
    name: str,
) -> ThresholdProfile:
    """
    Retrieve one named threshold profile.
    """

    for profile in build_threshold_profiles():
        if profile.name == name:
            return profile

    raise KeyError(
        f"Unknown threshold profile: {name}"
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_threshold_profiles(
    profiles: Sequence[ThresholdProfile],
) -> None:
    """
    Validate that every profile has a valid configuration.
    """

    if not profiles:
        raise ValueError(
            "At least one threshold profile is required"
        )

    names = [
        profile.name
        for profile in profiles
    ]

    if len(names) != len(set(names)):
        raise ValueError(
            "Threshold profile names must be unique"
        )

    for profile in profiles:
        profile.config.validate()


# ============================================================
# EXECUTION
# ============================================================

def run_threshold_sensitivity(
    dataset: Sequence[Mapping[str, Any]],
    *,
    seeds: Iterable[int],
    detector: ThresholdDetector,
    profiles: Sequence[ThresholdProfile] | None = None,
) -> list[SensitivityResult]:
    """
    Run the same dataset against each threshold profile.

    The detector receives:

        dataset
        threshold configuration
        seed

    This allows the existing Varynx evaluation pipeline to be
    connected without duplicating its logic.
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

    if profiles is None:
        profiles = build_threshold_profiles()

    profiles = list(profiles)

    validate_threshold_profiles(
        profiles
    )

    results: list[SensitivityResult] = []

    for profile in profiles:
        for seed in seed_list:
            metrics = detector(
                dataset,
                profile.config,
                seed,
            )

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

            results.append(
                SensitivityResult(
                    profile=profile.name,
                    seed=seed,
                    metrics=normalized,
                    sample_count=len(dataset),
                )
            )

    return results


# ============================================================
# AGGREGATION
# ============================================================

def summarize_threshold_sensitivity(
    results: Sequence[SensitivityResult],
) -> list[SensitivitySummary]:
    """
    Aggregate repeated runs by threshold profile.
    """

    if not results:
        return []

    grouped: dict[
        str,
        list[SensitivityResult],
    ] = {}

    for result in results:
        grouped.setdefault(
            result.profile,
            [],
        ).append(result)

    summaries: list[SensitivitySummary] = []

    for profile, profile_results in grouped.items():
        metric_names: set[str] = set()

        for result in profile_results:
            metric_names.update(
                result.metrics.keys()
            )

        means: dict[str, float] = {}
        stds: dict[str, float] = {}

        for metric in sorted(metric_names):
            values = [
                float(
                    result.metrics[metric]
                )
                for result in profile_results
                if metric in result.metrics
            ]

            if not values:
                continue

            means[metric] = mean(values)

            stds[metric] = (
                stdev(values)
                if len(values) > 1
                else 0.0
            )

        summaries.append(
            SensitivitySummary(
                profile=profile,
                runs=len(profile_results),
                sample_count=sum(
                    result.sample_count
                    for result in profile_results
                ),
                metrics_mean=means,
                metrics_std=stds,
            )
        )

    return summaries


# ============================================================
# COMPARISON
# ============================================================

def calculate_sensitivity_delta(
    default_summary: SensitivitySummary,
    comparison_summary: SensitivitySummary,
) -> dict[str, float]:
    """
    Calculate:

        comparison profile - default profile

    Positive values mean the comparison profile achieved a
    higher metric.

    This is an observed difference only.
    """

    if default_summary.profile != "default":
        raise ValueError(
            "default_summary must represent the default profile"
        )

    delta: dict[str, float] = {}

    common_metrics = (
        set(default_summary.metrics_mean)
        & set(comparison_summary.metrics_mean)
    )

    for metric in sorted(common_metrics):
        delta[metric] = (
            comparison_summary.metrics_mean[metric]
            - default_summary.metrics_mean[metric]
        )

    return delta


def build_sensitivity_table(
    summaries: Sequence[SensitivitySummary],
) -> list[dict[str, Any]]:
    """
    Build a flat table suitable for dashboard/report output.
    """

    table: list[dict[str, Any]] = []

    for summary in summaries:
        row: dict[str, Any] = {
            "profile": summary.profile,
            "runs": summary.runs,
            "sample_count": summary.sample_count,
        }

        for metric, value in (
            summary.metrics_mean.items()
        ):
            row[metric] = round(
                float(value),
                6,
            )

            row[f"{metric}_std"] = round(
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
# TRADE-OFF ANALYSIS
# ============================================================

def classify_threshold_direction(
    default_summary: SensitivitySummary,
    comparison_summary: SensitivitySummary,
    *,
    metric: str,
) -> str:
    """
    Describe the observed direction of a metric relative to
    the default profile.

    No statistical significance is inferred.
    """

    delta = calculate_sensitivity_delta(
        default_summary,
        comparison_summary,
    ).get(metric)

    if delta is None:
        raise KeyError(
            f"Metric '{metric}' not available"
        )

    if delta > 0:
        return "higher_than_default"

    if delta < 0:
        return "lower_than_default"

    return "unchanged_from_default"


def build_research_interpretation(
    *,
    profile: ThresholdProfile,
    metric: str,
    delta: float,
) -> str:
    """
    Produce cautious research language for an observed
    threshold effect.
    """

    if delta > 0:
        direction = "increased"
    elif delta < 0:
        direction = "decreased"
    else:
        direction = "did not change"

    return (
        f"The '{profile.name}' threshold profile "
        f"{direction} {metric} relative to the default "
        "configuration in the observed experiment. "
        "This observed difference does not by itself establish "
        "statistical significance or generalization."
    )


__all__ = [
    "ThresholdProfile",
    "SensitivityResult",
    "SensitivitySummary",
    "build_threshold_profiles",
    "get_threshold_profile",
    "validate_threshold_profiles",
    "run_threshold_sensitivity",
    "summarize_threshold_sensitivity",
    "calculate_sensitivity_delta",
    "build_sensitivity_table",
    "classify_threshold_direction",
    "build_research_interpretation",
]