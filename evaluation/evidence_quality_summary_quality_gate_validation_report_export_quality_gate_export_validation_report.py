from dataclasses import dataclass
from typing import Any, Dict, List

from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation import (
    validate_exported_quality_gate,
)


@dataclass
class ExportedQualityGateValidationReport:
    quality_gate: Dict[str, Any]
    valid: bool
    status: str
    errors: List[str]


def determine_exported_quality_gate_validation_report_status(
    valid: bool,
) -> str:
    if valid:
        return "PASS"

    return "FAIL"


def generate_exported_quality_gate_validation_report(
    quality_gate: Dict[str, Any],
) -> ExportedQualityGateValidationReport:
    validation = validate_exported_quality_gate(
        quality_gate
    )

    valid = validation.get("valid") is True
    errors = list(
        validation.get("errors", [])
    )

    return ExportedQualityGateValidationReport(
        quality_gate=quality_gate,
        valid=valid,
        status=(
            determine_exported_quality_gate_validation_report_status(
                valid
            )
        ),
        errors=errors,
    )


def exported_quality_gate_validation_report_to_dict(
    report: ExportedQualityGateValidationReport,
) -> Dict[str, Any]:
    return {
        "quality_gate": report.quality_gate,
        "valid": report.valid,
        "status": report.status,
        "errors": report.errors,
    }


def exported_quality_gate_validation_report_status(
    report: ExportedQualityGateValidationReport,
) -> str:
    return report.status


def generate_default_exported_quality_gate_validation_report(
    quality_gate: Dict[str, Any],
) -> ExportedQualityGateValidationReport:
    return generate_exported_quality_gate_validation_report(
        quality_gate
    )