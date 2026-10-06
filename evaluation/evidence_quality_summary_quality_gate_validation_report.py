from dataclasses import dataclass
from typing import Any, Dict, List

from evaluation.evidence_quality_summary_quality_gate_validation import (
    validate_evidence_quality_summary_quality_gate,
)


@dataclass
class EvidenceQualitySummaryQualityGateValidationReport:
    quality_gate: Dict[str, Any]
    valid: bool
    status: str
    errors: List[str]


def determine_quality_gate_validation_report_status(
    valid: bool,
) -> str:
    if valid:
        return "PASS"

    return "FAIL"


def generate_evidence_quality_summary_quality_gate_validation_report(
    quality_gate: Dict[str, Any],
) -> EvidenceQualitySummaryQualityGateValidationReport:
    validation = (
        validate_evidence_quality_summary_quality_gate(
            quality_gate
        )
    )

    valid = validation.get("valid") is True
    errors = list(validation.get("errors", []))

    return EvidenceQualitySummaryQualityGateValidationReport(
        quality_gate=quality_gate,
        valid=valid,
        status=(
            determine_quality_gate_validation_report_status(
                valid
            )
        ),
        errors=errors,
    )


def evidence_quality_summary_quality_gate_validation_report_to_dict(
    report: EvidenceQualitySummaryQualityGateValidationReport,
) -> Dict[str, Any]:
    return {
        "quality_gate": report.quality_gate,
        "valid": report.valid,
        "status": report.status,
        "errors": report.errors,
    }


def evidence_quality_summary_quality_gate_validation_report_status(
    report: EvidenceQualitySummaryQualityGateValidationReport,
) -> str:
    return report.status


def generate_default_quality_gate_validation_report(
    quality_gate: Dict[str, Any],
) -> EvidenceQualitySummaryQualityGateValidationReport:
    return (
        generate_evidence_quality_summary_quality_gate_validation_report(
            quality_gate
        )
    )