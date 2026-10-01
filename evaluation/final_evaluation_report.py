from dataclasses import dataclass
from typing import Any, Dict

from evaluation.comparison_summary import (
    ComparisonSummary,
    comparison_summary_to_dict,
    generate_default_comparison_summary,
)
from evaluation.experiment_quality_gate import (
    QualityGateResult,
    generate_default_quality_gate,
    quality_gate_to_dict,
)
from evaluation.experiment_report import (
    ExperimentReport,
    generate_default_report,
)
from evaluation.experiment_export import report_to_json_dict


@dataclass
class FinalEvaluationReport:
    experiment: Dict[str, Any]
    quality_gate: Dict[str, Any]
    comparison: Dict[str, Any]
    overall_status: str


def determine_overall_status(
    quality_gate: QualityGateResult,
    comparison: ComparisonSummary,
) -> str:
    """
    Determine the final status of the experimental evaluation.
    """

    if not quality_gate.valid:
        return "INVALID"

    if not comparison.valid:
        return "INVALID"

    if not comparison.baseline_aligned:
        return "DIFFERS"

    return "PASS"


def generate_final_report(
    report: ExperimentReport,
    quality_gate: QualityGateResult,
    comparison: ComparisonSummary,
) -> FinalEvaluationReport:
    """
    Combine experiment, validation, and comparison results.
    """

    experiment_data = report_to_json_dict(report)
    quality_gate_data = quality_gate_to_dict(quality_gate)
    comparison_data = comparison_summary_to_dict(comparison)

    overall_status = determine_overall_status(
        quality_gate,
        comparison,
    )

    return FinalEvaluationReport(
        experiment=experiment_data,
        quality_gate=quality_gate_data,
        comparison=comparison_data,
        overall_status=overall_status,
    )


def generate_default_final_report(
    repetitions: int = 5,
) -> FinalEvaluationReport:
    """
    Generate the complete default experimental evaluation report.
    """

    report = generate_default_report(repetitions)
    quality_gate = generate_default_quality_gate(repetitions)
    comparison = generate_default_comparison_summary(repetitions)

    return generate_final_report(
        report,
        quality_gate,
        comparison,
    )


def final_report_to_dict(
    report: FinalEvaluationReport,
) -> Dict[str, Any]:
    """
    Convert the final evaluation report into a serializable dictionary.
    """

    return {
        "experiment": report.experiment,
        "quality_gate": report.quality_gate,
        "comparison": report.comparison,
        "overall_status": report.overall_status,
    }