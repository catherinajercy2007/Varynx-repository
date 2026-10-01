from typing import Any, Dict, List


EXPECTED_STATUSES = {
    "ACCEPTED",
    "REJECTED",
}

EXPECTED_GATE_STATUSES = {
    "PASS",
    "FAIL",
}


REQUIRED_FIELDS = {
    "overall_status",
    "accepted",
    "quality_gate_status",
    "integrity_verified",
    "artifact_count",
    "verified_artifact_count",
    "validation_error_count",
}


def validate_summary_structure(
    summary: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []

    if not isinstance(summary, dict):
        return [
            "Evidence quality summary must be a dictionary."
        ]

    for field in REQUIRED_FIELDS:
        if field not in summary:
            errors.append(
                f"Missing summary field: {field}"
            )

    return errors


def validate_summary_values(
    summary: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []

    overall_status = summary.get("overall_status")

    if "overall_status" in summary:
        if overall_status not in EXPECTED_STATUSES:
            errors.append(
                "Invalid overall_status value."
            )

    accepted = summary.get("accepted")

    if "accepted" in summary:
        if not isinstance(accepted, bool):
            errors.append(
                "Accepted field must be a boolean."
            )

    quality_gate_status = summary.get(
        "quality_gate_status"
    )

    if "quality_gate_status" in summary:
        if quality_gate_status not in EXPECTED_GATE_STATUSES:
            errors.append(
                "Invalid quality_gate_status value."
            )

    integrity_verified = summary.get(
        "integrity_verified"
    )

    if "integrity_verified" in summary:
        if not isinstance(integrity_verified, bool):
            errors.append(
                "Integrity verified field must be a boolean."
            )

    numeric_fields = {
        "artifact_count",
        "verified_artifact_count",
        "validation_error_count",
    }

    for field in numeric_fields:
        if field not in summary:
            continue

        value = summary[field]

        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
        ):
            errors.append(
                f"{field} must be a non-negative integer."
            )

    return errors


def validate_summary_consistency(
    summary: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []

    overall_status = summary.get(
        "overall_status"
    )
    accepted = summary.get("accepted")

    if (
        isinstance(overall_status, str)
        and isinstance(accepted, bool)
    ):
        expected_accepted = (
            overall_status == "ACCEPTED"
        )

        if accepted != expected_accepted:
            errors.append(
                "Overall status and accepted value "
                "are inconsistent."
            )

    quality_gate_status = summary.get(
        "quality_gate_status"
    )

    if (
        isinstance(quality_gate_status, str)
        and isinstance(accepted, bool)
    ):
        expected_accepted = (
            quality_gate_status == "PASS"
        )

        if accepted != expected_accepted:
            errors.append(
                "Quality gate status and accepted value "
                "are inconsistent."
            )

    artifact_count = summary.get(
        "artifact_count"
    )
    verified_artifact_count = summary.get(
        "verified_artifact_count"
    )

    if (
        isinstance(artifact_count, int)
        and isinstance(verified_artifact_count, int)
    ):
        if verified_artifact_count > artifact_count:
            errors.append(
                "Verified artifact count cannot exceed "
                "artifact count."
            )

    return errors


def validate_evidence_quality_summary(
    summary: Dict[str, Any],
) -> Dict[str, Any]:
    structure_errors = validate_summary_structure(
        summary
    )

    if not isinstance(summary, dict):
        return {
            "valid": False,
            "errors": structure_errors,
        }

    value_errors = validate_summary_values(
        summary
    )

    consistency_errors = validate_summary_consistency(
        summary
    )

    errors = (
        structure_errors
        + value_errors
        + consistency_errors
    )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


def evidence_quality_summary_validation_status(
    validation: Dict[str, Any],
) -> str:
    if validation.get("valid") is True:
        return "PASS"

    return "FAIL"


def generate_evidence_quality_summary_validation(
    summary: Dict[str, Any],
) -> Dict[str, Any]:
    validation = validate_evidence_quality_summary(
        summary
    )

    return {
        "valid": validation["valid"],
        "status": evidence_quality_summary_validation_status(
            validation
        ),
        "errors": validation["errors"],
    }