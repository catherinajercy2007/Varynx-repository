from dataclasses import dataclass
from typing import List

from evaluation.reproducibility import (
    ExperimentRun,
    analyze_stability,
    run_repeated_experiments,
)


@dataclass
class ExperimentReport:
    total_runs: int
    scenarios_per_run: int
    stable: bool
    average_pass_rate: float
    minimum_pass_rate: float
    maximum_pass_rate: float
    average_allow_count: float
    average_deny_count: float


def generate_report(
    runs: List[ExperimentRun],
) -> ExperimentReport:
    """
    Aggregate repeated experiment runs into a reproducible report.
    """

    if not runs:
        return ExperimentReport(
            total_runs=0,
            scenarios_per_run=0,
            stable=True,
            average_pass_rate=0.0,
            minimum_pass_rate=0.0,
            maximum_pass_rate=0.0,
            average_allow_count=0.0,
            average_deny_count=0.0,
        )

    stability = analyze_stability(runs)

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

    scenarios_per_run = runs[0].metrics.total

    return ExperimentReport(
        total_runs=len(runs),
        scenarios_per_run=scenarios_per_run,
        stable=stability.stable,
        average_pass_rate=sum(pass_rates) / len(pass_rates),
        minimum_pass_rate=min(pass_rates),
        maximum_pass_rate=max(pass_rates),
        average_allow_count=sum(allow_counts) / len(allow_counts),
        average_deny_count=sum(deny_counts) / len(deny_counts),
    )


def generate_default_report(
    repetitions: int = 5,
) -> ExperimentReport:
    """
    Execute repeated experiments and generate an aggregate report.
    """

    runs = run_repeated_experiments(repetitions)

    return generate_report(runs)


def report_to_dict(report: ExperimentReport) -> dict:
    """
    Convert an experiment report into a serializable dictionary.
    """

    return {
        "total_runs": report.total_runs,
        "scenarios_per_run": report.scenarios_per_run,
        "stable": report.stable,
        "average_pass_rate": report.average_pass_rate,
        "minimum_pass_rate": report.minimum_pass_rate,
        "maximum_pass_rate": report.maximum_pass_rate,
        "average_allow_count": report.average_allow_count,
        "average_deny_count": report.average_deny_count,
    }