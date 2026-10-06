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
}


def validate_exported_quality_gate_structure(
    quality_gate: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []

    if not isinstance(quality_gate, dict):
        return [
            "Exported quality gate must be a dictionary."
        ]

    for field in REQUIRED_FIELDS:
        if field not in quality_gate:
            errors.append(
                f"Missing exported quality gate field: {field}"
            )

    return errors


def validate_exported_quality_gate_values(
    quality_gate: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []

    if not isinstance(quality_gate, dict):
        return [
            "Exported quality gate must be a dictionary."
        ]

    if "valid" in quality_gate:
        if not isinstance(quality_gate["valid"], bool):
            errors.append(
                "Valid field must be a boolean."
            )

    if "status" in quality_gate:
        if quality_gate["status"] not in EXPECTED_STATUSES:
            errors.append(
                "Invalid exported quality gate status value."
            )

    if "validation_errors" in quality_gate:
        if not isinstance(
            quality_gate["validation_errors"],
            list,
        ):
            errors.append(
                "Validation errors field must be a list."
            )

    if "accepted" in quality_gate:
        if not isinstance(
            quality_gate["accepted"],
            bool,
        ):
            errors.append(
                "Accepted field must be a boolean."
            )

    return errors


def validate_exported_quality_gate_consistency(
    quality_gate: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []

    if not isinstance(quality_gate, dict):
        return []

    valid = quality_gate.get("valid")
    status = quality_gate.get("status")
    validation_errors = quality_gate.get(
        "validation_errors"
    )
    accepted = quality_gate.get("accepted")

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

    if (
        isinstance(valid, bool)
        and isinstance(validation_errors, list)
    ):
        if valid and validation_errors:
            errors.append(
                "A valid exported quality gate "
                "cannot contain validation errors."
            )

        if not valid and not validation_errors:
            errors.append(
                "An invalid exported quality gate "
                "must contain validation errors."
            )

    return errors


def validate_exported_quality_gate(
    quality_gate: Dict[str, Any],
) -> Dict[str, Any]:
    structure_errors = (
        validate_exported_quality_gate_structure(
            quality_gate
        )
    )

    if not isinstance(quality_gate, dict):
        return {
            "valid": False,
            "errors": structure_errors,
        }

    value_errors = (
        validate_exported_quality_gate_values(
            quality_gate
        )
    )

    consistency_errors = (
        validate_exported_quality_gate_consistency(
            quality_gate
        )
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


def exported_quality_gate_validation_status(
    validation: Dict[str, Any],
) -> str:
    if validation.get("valid") is True:
        return "PASS"

    return "FAIL"


def generate_exported_quality_gate_validation(
    quality_gate: Dict[str, Any],
) -> Dict[str, Any]:
    validation = validate_exported_quality_gate(
        quality_gate
    )

    return {
        "valid": validation["valid"],
        "status": (
            exported_quality_gate_validation_status(
                validation
            )
        ),
        "errors": validation["errors"],
    }