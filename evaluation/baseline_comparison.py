from dataclasses import dataclass
from typing import Dict, Any

from evaluation.experiment_export import report_to_json_dict
from evaluation.experiment_report import (
    ExperimentReport,
    generate_default_report,
)
from evaluation.experiment_quality_gate import (
    evaluate_experiment_quality,
)


@dataclass
class BaselineMetrics:
    pass_rate: float
    allow_count: float
    deny_count: float


@dataclass
class BaselineComparison:
    valid: bool
    pass_rate_difference: float
    allow_count_difference: float
    deny_count_difference: float
    pass_rate_meets_baseline: bool
    allow_count_matches_baseline: bool
    deny_count_matches_baseline: bool


DEFAULT_BASELINE = BaselineMetrics(
    pass_rate=100.0,
    allow_count=2.0,
    deny_count=6.0,
)


def compare_with_baseline(
    report: Dict[str, Any],
    baseline: BaselineMetrics = DEFAULT_BASELINE,
) -> BaselineComparison:
    """
    Compare a validated experiment report with baseline metrics.
    """

    quality_result = evaluate_experiment_quality_from_dict(report)

    if not quality_result.valid:
        return BaselineComparison(
            valid=False,
            pass_rate_difference=0.0,
            allow_count_difference=0.0,
            deny_count_difference=0.0,
            pass_rate_meets_baseline=False,
            allow_count_matches_baseline=False,
            deny_count_matches_baseline=False,
        )

    pass_rate = report["average_pass_rate"]
    allow_count = report["average_allow_count"]
    deny_count = report["average_deny_count"]

    pass_rate_difference = pass_rate - baseline.pass_rate
    allow_count_difference = allow_count - baseline.allow_count
    deny_count_difference = deny_count - baseline.deny_count

    return BaselineComparison(
        valid=True,
        pass_rate_difference=pass_rate_difference,
        allow_count_difference=allow_count_difference,
        deny_count_difference=deny_count_difference,
        pass_rate_meets_baseline=pass_rate >= baseline.pass_rate,
        allow_count_matches_baseline=allow_count == baseline.allow_count,
        deny_count_matches_baseline=deny_count == baseline.deny_count,
    )


def evaluate_experiment_quality_from_dict(
    report: Dict[str, Any],
):
    """
    Validate a serialized experiment report.
    """

    from evaluation.experiment_validation import validate_report

    validation = validate_report(report)

    class ValidationResult:
        def __init__(self, result):
            self.valid = result["valid"]

    return ValidationResult(validation)


def compare_experiment_report(
    report: ExperimentReport,
    baseline: BaselineMetrics = DEFAULT_BASELINE,
) -> BaselineComparison:
    """
    Compare an ExperimentReport with baseline metrics.
    """

    report_data = report_to_json_dict(report)

    return compare_with_baseline(
        report_data,
        baseline,
    )


def generate_default_baseline_comparison(
    repetitions: int = 5,
) -> BaselineComparison:
    """
    Generate the default experiment and compare it with the baseline.
    """

    report = generate_default_report(repetitions)

    return compare_experiment_report(report)


def baseline_comparison_to_dict(
    comparison: BaselineComparison,
) -> Dict[str, Any]:
    """
    Convert a baseline comparison into a serializable dictionary.
    """

    return {
        "valid": comparison.valid,
        "pass_rate_difference": comparison.pass_rate_difference,
        "allow_count_difference": comparison.allow_count_difference,
        "deny_count_difference": comparison.deny_count_difference,
        "pass_rate_meets_baseline": comparison.pass_rate_meets_baseline,
        "allow_count_matches_baseline": (
            comparison.allow_count_matches_baseline
        ),
        "deny_count_matches_baseline": (
            comparison.deny_count_matches_baseline
        ),
    }