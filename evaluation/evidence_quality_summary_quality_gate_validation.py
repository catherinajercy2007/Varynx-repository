from typing import Any, Dict, List


EXPECTED_STATUSES = {
    "PASS",
    "FAIL",
}

REQUIRED_FIELDS = {
    "valid",
    "status",
    "validation_errors",
    "accepted",
    "artifact_count",
    "verified_artifact_count",
}


def validate_quality_gate_structure(
    quality_gate: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []

    if not isinstance(quality_gate, dict):
        return [
            "Quality gate must be a dictionary."
        ]

    for field in REQUIRED_FIELDS:
        if field not in quality_gate:
            errors.append(
                f"Missing quality gate field: {field}"
            )

    return errors


def validate_quality_gate_values(
    quality_gate: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []

    if not isinstance(quality_gate, dict):
        return [
            "Quality gate must be a dictionary."
        ]

    valid = quality_gate.get("valid")

    if "valid" in quality_gate:
        if not isinstance(valid, bool):
            errors.append(
                "Valid field must be a boolean."
            )

    status = quality_gate.get("status")

    if "status" in quality_gate:
        if status not in EXPECTED_STATUSES:
            errors.append(
                "Invalid quality gate status value."
            )

    validation_errors = quality_gate.get(
        "validation_errors"
    )

    if "validation_errors" in quality_gate:
        if not isinstance(validation_errors, list):
            errors.append(
                "Validation errors field must be a list."
            )

    accepted = quality_gate.get("accepted")

    if "accepted" in quality_gate:
        if not isinstance(accepted, bool):
            errors.append(
                "Accepted field must be a boolean."
            )

    numeric_fields = {
        "artifact_count",
        "verified_artifact_count",
    }

    for field in numeric_fields:
        if field not in quality_gate:
            continue

        value = quality_gate[field]

        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
        ):
            errors.append(
                f"{field} must be a non-negative integer."
            )

    return errors


def validate_quality_gate_consistency(
    quality_gate: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []

    if not isinstance(quality_gate, dict):
        return []

    valid = quality_gate.get("valid")
    status = quality_gate.get("status")
    accepted = quality_gate.get("accepted")
    validation_errors = quality_gate.get(
        "validation_errors"
    )

    if (
        isinstance(valid, bool)
        and isinstance(status, str)
    ):
        expected_status = "PASS" if valid else "FAIL"

        if status != expected_status:
            errors.append(
                "Valid and status values are inconsistent."
            )

    if (
        isinstance(status, str)
        and isinstance(accepted, bool)
    ):
        expected_accepted = status == "PASS"

        if accepted != expected_accepted:
            errors.append(
                "Status and accepted values are inconsistent."
            )

    if isinstance(valid, bool):
        if valid and isinstance(validation_errors, list):
            if validation_errors:
                errors.append(
                    "A valid quality gate cannot contain "
                    "validation errors."
                )

        if not valid and isinstance(validation_errors, list):
            if not validation_errors:
                errors.append(
                    "An invalid quality gate must contain "
                    "validation errors."
                )

    artifact_count = quality_gate.get(
        "artifact_count"
    )
    verified_artifact_count = quality_gate.get(
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


def validate_evidence_quality_summary_quality_gate(
    quality_gate: Dict[str, Any],
) -> Dict[str, Any]:
    structure_errors = validate_quality_gate_structure(
        quality_gate
    )

    if not isinstance(quality_gate, dict):
        return {
            "valid": False,
            "errors": structure_errors,
        }

    value_errors = validate_quality_gate_values(
        quality_gate
    )

    consistency_errors = validate_quality_gate_consistency(
        quality_gate
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


def evidence_quality_summary_quality_gate_validation_status(
    validation: Dict[str, Any],
) -> str:
    if validation.get("valid") is True:
        return "PASS"

    return "FAIL"


def generate_evidence_quality_summary_quality_gate_validation(
    quality_gate: Dict[str, Any],
) -> Dict[str, Any]:
    validation = (
        validate_evidence_quality_summary_quality_gate(
            quality_gate
        )
    )

    return {
        "valid": validation["valid"],
        "status": (
            evidence_quality_summary_quality_gate_validation_status(
                validation
            )
        ),
        "errors": validation["errors"],
    }