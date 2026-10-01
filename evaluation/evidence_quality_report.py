from dataclasses import dataclass
from typing import Any, Dict

from evaluation.evidence_quality_gate import (
    EvidenceQualityGateResult,
    evaluate_evidence_quality_gate,
    evidence_quality_gate_to_dict,
)


@dataclass
class EvidenceQualityReport:
    evidence_index: Dict[str, Any]
    quality_gate: Dict[str, Any]
    overall_status: str
    accepted: bool


def determine_evidence_report_status(
    quality_gate: EvidenceQualityGateResult,
) -> str:
    if quality_gate.accepted:
        return "ACCEPTED"

    return "REJECTED"


def generate_evidence_quality_report(
    index: Dict[str, Any],
    base_directory: str = ".",
) -> EvidenceQualityReport:
    quality_gate = evaluate_evidence_quality_gate(
        index,
        base_directory=base_directory,
    )

    return EvidenceQualityReport(
        evidence_index=index,
        quality_gate=evidence_quality_gate_to_dict(
            quality_gate
        ),
        overall_status=determine_evidence_report_status(
            quality_gate
        ),
        accepted=quality_gate.accepted,
    )


def evidence_quality_report_to_dict(
    report: EvidenceQualityReport,
) -> Dict[str, Any]:
    return {
        "evidence_index": report.evidence_index,
        "quality_gate": report.quality_gate,
        "overall_status": report.overall_status,
        "accepted": report.accepted,
    }


def evidence_quality_report_status(
    report: EvidenceQualityReport,
) -> str:
    return report.overall_status