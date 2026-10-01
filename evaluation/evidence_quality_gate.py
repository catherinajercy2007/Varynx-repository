from dataclasses import dataclass
from typing import Any, Dict, List

from evaluation.evidence_index import verify_evidence_index
from evaluation.evidence_validation import validate_evidence_index


@dataclass
class EvidenceQualityGateResult:
    valid: bool
    status: str
    validation_errors: List[str]
    integrity_verified: bool
    artifact_count: int
    accepted: bool


def evaluate_evidence_quality_gate(
    index: Dict[str, Any],
    base_directory: str = ".",
) -> EvidenceQualityGateResult:
    validation = validate_evidence_index(index)

    validation_errors = list(
        validation.get("errors", [])
    )

    artifact_count = validation.get(
        "artifact_count",
        0,
    )

    if artifact_count == 0:
        validation_errors.append(
            "Evidence index must contain at least one artifact."
        )

    integrity_verified = False

    if not validation_errors:
        try:
            integrity_verified = verify_evidence_index(
                index,
                base_directory=base_directory,
            )
        except (FileNotFoundError, OSError):
            integrity_verified = False

        if not integrity_verified:
            validation_errors.append(
                "Evidence artifact integrity verification failed."
            )

    accepted = (
        len(validation_errors) == 0
        and integrity_verified
    )

    return EvidenceQualityGateResult(
        valid=len(validation_errors) == 0,
        status="PASS" if accepted else "FAIL",
        validation_errors=validation_errors,
        integrity_verified=integrity_verified,
        artifact_count=artifact_count,
        accepted=accepted,
    )


def generate_evidence_quality_gate(
    index: Dict[str, Any],
    base_directory: str = ".",
) -> EvidenceQualityGateResult:
    return evaluate_evidence_quality_gate(
        index,
        base_directory=base_directory,
    )


def evidence_quality_gate_to_dict(
    result: EvidenceQualityGateResult,
) -> Dict[str, Any]:
    return {
        "valid": result.valid,
        "status": result.status,
        "validation_errors": result.validation_errors,
        "integrity_verified": result.integrity_verified,
        "artifact_count": result.artifact_count,
        "accepted": result.accepted,
    }


def evidence_quality_gate_status(
    result: EvidenceQualityGateResult,
) -> str:
    return result.status