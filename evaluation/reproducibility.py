from dataclasses import dataclass
from typing import List

from evaluation.comparative_metrics import (
    ComparativeMetrics,
    calculate_metrics,
)
from evaluation.scenario_runner import run_scenarios


@dataclass
class ExperimentRun:
    run_id: int
    metrics: ComparativeMetrics


@dataclass
class StabilityReport:
    runs: int
    stable: bool
    pass_rates: List[float]
    allow_counts: List[int]
    deny_counts: List[int]


def run_experiment(run_id: int) -> ExperimentRun:
    """
    Execute one complete evaluation run and calculate its metrics.
    """

    results = run_scenarios()
    metrics = calculate_metrics(results)

    return ExperimentRun(
        run_id=run_id,
        metrics=metrics,
    )


def run_repeated_experiments(
    repetitions: int = 5,
) -> List[ExperimentRun]:
    """
    Execute the evaluation repeatedly for reproducibility analysis.
    """

    if repetitions < 1:
        raise ValueError("repetitions must be at least 1")

    return [
        run_experiment(run_id)
        for run_id in range(1, repetitions + 1)
    ]


def analyze_stability(
    runs: List[ExperimentRun],
) -> StabilityReport:
    """
    Determine whether repeated evaluation runs produce stable metrics.
    """

    if not runs:
        return StabilityReport(
            runs=0,
            stable=True,
            pass_rates=[],
            allow_counts=[],
            deny_counts=[],
        )

    pass_rates = [
        run.metrics.pass_rate
        for run in runs
    ]

    allow_counts = [
        run.metrics.allow_count
        for run in runs
    ]

    deny_counts = [
        run.metrics.deny_count
        for run in runs
    ]

    stable = (
        len(set(pass_rates)) == 1
        and len(set(allow_counts)) == 1
        and len(set(deny_counts)) == 1
    )

    return StabilityReport(
        runs=len(runs),
        stable=stable,
        pass_rates=pass_rates,
        allow_counts=allow_counts,
        deny_counts=deny_counts,
    )