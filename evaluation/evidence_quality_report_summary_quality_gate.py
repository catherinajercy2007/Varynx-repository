from dataclasses import dataclass
from typing import Any, Dict, List

from evaluation.evidence_quality_report_summary_validation import (
    validate_evidence_quality_summary,
)


@dataclass
class EvidenceQualitySummaryQualityGateResult:
    valid: bool
    status: str
    validation_errors: List[str]
    accepted: bool
    artifact_count: int
    verified_artifact_count: int


def evaluate_evidence_quality_summary_quality_gate(
    summary: Dict[str, Any],
) -> EvidenceQualitySummaryQualityGateResult:
    validation = validate_evidence_quality_summary(summary)

    validation_errors = list(
        validation.get("errors", [])
    )

    valid = validation.get("valid") is True

    accepted = (
        valid
        and summary.get("accepted") is True
    ) if isinstance(summary, dict) else False

    artifact_count = (
        summary.get("artifact_count", 0)
        if isinstance(summary, dict)
        else 0
    )

    verified_artifact_count = (
        summary.get("verified_artifact_count", 0)
        if isinstance(summary, dict)
        else 0
    )

    status = "PASS" if accepted else "FAIL"

    return EvidenceQualitySummaryQualityGateResult(
        valid=valid,
        status=status,
        validation_errors=validation_errors,
        accepted=accepted,
        artifact_count=artifact_count,
        verified_artifact_count=verified_artifact_count,
    )


def generate_evidence_quality_summary_quality_gate(
    summary: Dict[str, Any],
) -> EvidenceQualitySummaryQualityGateResult:
    return evaluate_evidence_quality_summary_quality_gate(
        summary
    )


def evidence_quality_summary_quality_gate_to_dict(
    result: EvidenceQualitySummaryQualityGateResult,
) -> Dict[str, Any]:
    return {
        "valid": result.valid,
        "status": result.status,
        "validation_errors": result.validation_errors,
        "accepted": result.accepted,
        "artifact_count": result.artifact_count,
        "verified_artifact_count": result.verified_artifact_count,
    }


def evidence_quality_summary_quality_gate_status(
    result: EvidenceQualitySummaryQualityGateResult,
) -> str:
    return result.status