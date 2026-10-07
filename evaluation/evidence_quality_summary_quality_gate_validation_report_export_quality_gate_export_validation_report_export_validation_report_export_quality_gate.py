from dataclasses import dataclass
from typing import Any, Dict, List

from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation_report_export_validation import (
    validate_exported_validation_report,
)


@dataclass
class ExportedValidationReportExportQualityGateResult:
    valid: bool
    status: str
    validation_errors: List[str]
    accepted: bool


def evaluate_exported_validation_report_export_quality_gate(
    report: Dict[str, Any],
) -> ExportedValidationReportExportQualityGateResult:
    validation = validate_exported_validation_report(
        report
    )

    validation_errors = list(
        validation.get("errors", [])
    )

    valid = validation.get("valid") is True

    accepted = valid

    status = "PASS" if accepted else "FAIL"

    return ExportedValidationReportExportQualityGateResult(
        valid=valid,
        status=status,
        validation_errors=validation_errors,
        accepted=accepted,
    )


def generate_exported_validation_report_export_quality_gate(
    report: Dict[str, Any],
) -> ExportedValidationReportExportQualityGateResult:
    return (
        evaluate_exported_validation_report_export_quality_gate(
            report
        )
    )


def exported_validation_report_export_quality_gate_to_dict(
    result: ExportedValidationReportExportQualityGateResult,
) -> Dict[str, Any]:
    return {
        "valid": result.valid,
        "status": result.status,
        "validation_errors": result.validation_errors,
        "accepted": result.accepted,
    }


def exported_validation_report_export_quality_gate_status(
    result: ExportedValidationReportExportQualityGateResult,
) -> str:
    return result.status