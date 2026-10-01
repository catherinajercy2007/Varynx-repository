from dataclasses import dataclass
from typing import Any, Dict

from evaluation.experiment_export import report_to_json_dict
from evaluation.experiment_report import (
    ExperimentReport,
    generate_default_report,
)
from evaluation.experiment_validation import validate_report


@dataclass
class QualityGateResult:
    valid: bool
    status: str
    missing_fields: list
    value_errors: list
    consistency_errors: list


def evaluate_quality_gate(
    report: Dict[str, Any],
) -> QualityGateResult:
    """
    Evaluate whether an experiment report satisfies the quality gate.
    """

    validation = validate_report(report)

    valid = validation["valid"]

    return QualityGateResult(
        valid=valid,
        status="PASS" if valid else "FAIL",
        missing_fields=validation["missing_fields"],
        value_errors=validation["value_errors"],
        consistency_errors=validation["consistency_errors"],
    )


def evaluate_experiment_quality(
    report: ExperimentReport,
) -> QualityGateResult:
    """
    Validate an ExperimentReport using the quality gate.
    """

    data = report_to_json_dict(report)

    return evaluate_quality_gate(data)


def generate_default_quality_gate(
    repetitions: int = 5,
) -> QualityGateResult:
    """
    Generate the default experiment and evaluate its quality.
    """

    report = generate_default_report(repetitions)

    return evaluate_experiment_quality(report)


def quality_gate_to_dict(
    result: QualityGateResult,
) -> Dict[str, Any]:
    """
    Convert a quality-gate result into a serializable dictionary.
    """

    return {
        "valid": result.valid,
        "status": result.status,
        "missing_fields": result.missing_fields,
        "value_errors": result.value_errors,
        "consistency_errors": result.consistency_errors,
    }