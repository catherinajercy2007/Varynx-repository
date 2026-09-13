from __future__ import annotations

from typing import Iterable, Dict, Any, List

import pandas as pd

from app.experimental_dataset import (
    generate_experimental_dataset,
)

from app.comparison import (
    compare_detectors,
)


DEFAULT_SEEDS = [
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


EVALUATION_METRICS = [
    "accuracy",
    "precision",
    "recall",
    "f1_score",
    "specificity",
    "false_positive_rate",
    "false_negative_rate",
]


def run_single_experiment(
    scenarios: Iterable[Dict[str, Any]],
    events_per_scenario: int,
    seed: int,
    threshold: float,
) -> Dict[str, Any]:

    dataset = generate_experimental_dataset(
        scenarios=list(scenarios),
        events_per_scenario=events_per_scenario,
        seed=seed,
    )

    comparison = compare_detectors(
        dataset,
        threshold=threshold,
    )

    return {
        "seed": seed,
        "dataset_size": len(dataset),
        "baseline": comparison["baseline"],
        "aegisguard": comparison["aegisguard"],
    }


def run_repeated_experiments(
    scenarios: Iterable[Dict[str, Any]],
    seeds: Iterable[int] | None = None,
    events_per_scenario: int = 5,
    threshold: float = 70.0,
) -> List[Dict[str, Any]]:

    if seeds is None:
        seeds = DEFAULT_SEEDS

    scenarios = list(scenarios)

    results = []

    for seed in seeds:

        result = run_single_experiment(
            scenarios=scenarios,
            events_per_scenario=events_per_scenario,
            seed=int(seed),
            threshold=threshold,
        )

        results.append(result)

    return results


def build_experiment_table(
    results: Iterable[Dict[str, Any]],
) -> pd.DataFrame:

    rows = []

    for result in results:

        baseline = result["baseline"]
        aegisguard = result["aegisguard"]

        for metric in EVALUATION_METRICS:

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

            rows.append(
                {
                    "seed": result["seed"],
                    "dataset_size": result[
                        "dataset_size"
                    ],
                    "metric": metric,
                    "baseline": baseline_value,
                    "aegisguard": aegisguard_value,
                    "difference": (
                        aegisguard_value
                        - baseline_value
                    ),
                }
            )

    return pd.DataFrame(rows)


def build_summary_table(
    results: Iterable[Dict[str, Any]],
) -> pd.DataFrame:

    rows = []

    for metric in EVALUATION_METRICS:

        baseline_values = []
        aegisguard_values = []

        for result in results:

            baseline_values.append(
                float(
                    result[
                        "baseline"
                    ].get(
                        metric,
                        0.0,
                    )
                )
            )

            aegisguard_values.append(
                float(
                    result[
                        "aegisguard"
                    ].get(
                        metric,
                        0.0,
                    )
                )
            )

        baseline_series = pd.Series(
            baseline_values,
            dtype=float,
        )

        aegisguard_series = pd.Series(
            aegisguard_values,
            dtype=float,
        )

        difference_series = (
            aegisguard_series
            - baseline_series
        )

        rows.append(
            {
                "metric": metric,

                "baseline_mean":
                    baseline_series.mean(),

                "baseline_std":
                    baseline_series.std(
                        ddof=1
                    )
                    if len(
                        baseline_series
                    ) > 1
                    else 0.0,

                "baseline_min":
                    baseline_series.min(),

                "baseline_max":
                    baseline_series.max(),

                "aegisguard_mean":
                    aegisguard_series.mean(),

                "aegisguard_std":
                    aegisguard_series.std(
                        ddof=1
                    )
                    if len(
                        aegisguard_series
                    ) > 1
                    else 0.0,

                "aegisguard_min":
                    aegisguard_series.min(),

                "aegisguard_max":
                    aegisguard_series.max(),

                "mean_difference":
                    difference_series.mean(),

                "difference_std":
                    difference_series.std(
                        ddof=1
                    )
                    if len(
                        difference_series
                    ) > 1
                    else 0.0,
            }
        )

    return pd.DataFrame(rows)


def build_seed_summary(
    results: Iterable[Dict[str, Any]],
) -> pd.DataFrame:

    rows = []

    for result in results:

        baseline = result["baseline"]
        aegisguard = result["aegisguard"]

        rows.append(
            {
                "seed": result["seed"],

                "dataset_size":
                    result[
                        "dataset_size"
                    ],

                "baseline_accuracy":
                    baseline.get(
                        "accuracy",
                        0.0,
                    ),

                "aegisguard_accuracy":
                    aegisguard.get(
                        "accuracy",
                        0.0,
                    ),

                "baseline_f1":
                    baseline.get(
                        "f1_score",
                        0.0,
                    ),

                "aegisguard_f1":
                    aegisguard.get(
                        "f1_score",
                        0.0,
                    ),

                "baseline_recall":
                    baseline.get(
                        "recall",
                        0.0,
                    ),

                "aegisguard_recall":
                    aegisguard.get(
                        "recall",
                        0.0,
                    ),

                "f1_difference":
                    (
                        aegisguard.get(
                            "f1_score",
                            0.0,
                        )
                        - baseline.get(
                            "f1_score",
                            0.0,
                        )
                    ),
            }
        )

    return pd.DataFrame(rows)


def calculate_consistency(
    results: Iterable[Dict[str, Any]],
    metric: str = "f1_score",
) -> Dict[str, float]:

    differences = []

    for result in results:

        baseline_value = float(
            result["baseline"].get(
                metric,
                0.0,
            )
        )

        aegisguard_value = float(
            result["aegisguard"].get(
                metric,
                0.0,
            )
        )

        differences.append(
            aegisguard_value
            - baseline_value
        )

    if not differences:

        return {
            "experiments": 0,
            "positive_runs": 0,
            "positive_rate": 0.0,
            "mean_difference": 0.0,
            "std_difference": 0.0,
        }

    series = pd.Series(
        differences,
        dtype=float,
    )

    positive_runs = int(
        (series > 0).sum()
    )

    return {
        "experiments": len(
            differences
        ),

        "positive_runs":
            positive_runs,

        "positive_rate":
            positive_runs
            / len(differences),

        "mean_difference":
            float(
                series.mean()
            ),

        "std_difference":
            float(
                series.std(
                    ddof=1
                )
            )
            if len(
                series
            ) > 1
            else 0.0,
    }


def build_research_report(
    results: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:

    results = list(results)

    summary = build_summary_table(
        results
    )

    consistency = (
        calculate_consistency(
            results,
            metric="f1_score",
        )
    )

    return {
        "experiment_count": len(
            results
        ),
        "summary": summary,
        "consistency": consistency,
    }