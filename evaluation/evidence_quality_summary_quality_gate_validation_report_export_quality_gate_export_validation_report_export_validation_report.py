from dataclasses import dataclass
from typing import Any, Dict, List

from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation_report_export_validation import (
    validate_exported_validation_report,
)


@dataclass
class ExportedValidationReportExportValidationReport:
    report: Dict[str, Any]
    valid: bool
    status: str
    errors: List[str]


def determine_exported_validation_report_export_validation_report_status(
    valid: bool,
) -> str:
    if valid:
        return "PASS"

    return "FAIL"


def generate_exported_validation_report_export_validation_report(
    report: Dict[str, Any],
) -> ExportedValidationReportExportValidationReport:
    validation = validate_exported_validation_report(
        report
    )

    valid = validation.get("valid") is True

    errors = list(
        validation.get("errors", [])
    )

    return ExportedValidationReportExportValidationReport(
        report=report,
        valid=valid,
        status=(
            determine_exported_validation_report_export_validation_report_status(
                valid
            )
        ),
        errors=errors,
    )


def exported_validation_report_export_validation_report_to_dict(
    report: ExportedValidationReportExportValidationReport,
) -> Dict[str, Any]:
    return {
        "report": report.report,
        "valid": report.valid,
        "status": report.status,
        "errors": report.errors,
    }


def exported_validation_report_export_validation_report_status(
    report: ExportedValidationReportExportValidationReport,
) -> str:
    return report.status


def generate_default_exported_validation_report_export_validation_report(
    report: Dict[str, Any],
) -> ExportedValidationReportExportValidationReport:
    return (
        generate_exported_validation_report_export_validation_report(
            report
        )
    )