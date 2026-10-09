
from typing import Any, Dict, List

EXPECTED_STATUSES = {"PASS", "FAIL"}

REQUIRED_FIELDS = {
    "valid",
    "status",
    "validation_errors",
    "accepted",
}


def validate_exported_validation_quality_gate_structure(
    quality_gate: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []

    if not isinstance(quality_gate, dict):
        return ["Exported validation quality gate must be a dictionary."]

    for field in sorted(REQUIRED_FIELDS):
        if field not in quality_gate:
            errors.append(
                f"Missing exported validation quality gate field: {field}"
            )

    return errors


def validate_exported_validation_quality_gate_values(
    quality_gate: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []

    if not isinstance(quality_gate, dict):
        return ["Exported validation quality gate must be a dictionary."]

    if "valid" in quality_gate and not isinstance(
        quality_gate["valid"], bool
    ):
        errors.append("Valid field must be a boolean.")

    if "status" in quality_gate:
        if not isinstance(quality_gate["status"], str) or (
            quality_gate["status"] not in EXPECTED_STATUSES
        ):
            errors.append("Invalid exported validation quality gate status.")

    if "validation_errors" in quality_gate:
        validation_errors = quality_gate["validation_errors"]
        if not isinstance(validation_errors, list):
            errors.append("Validation errors field must be a list.")
        elif not all(isinstance(item, str) for item in validation_errors):
            errors.append("Every validation error must be a string.")

    if "accepted" in quality_gate and not isinstance(
        quality_gate["accepted"], bool
    ):
        errors.append("Accepted field must be a boolean.")

    return errors


def validate_exported_validation_quality_gate_consistency(
    quality_gate: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []

    if not isinstance(quality_gate, dict):
        return errors

    valid = quality_gate.get("valid")
    status = quality_gate.get("status")
    validation_errors = quality_gate.get("validation_errors")
    accepted = quality_gate.get("accepted")

    if isinstance(valid, bool) and isinstance(status, str):
        expected_status = "PASS" if valid else "FAIL"
        if status != expected_status:
            errors.append("Valid and status values are inconsistent.")

    if isinstance(valid, bool) and isinstance(accepted, bool):
        if accepted != valid:
            errors.append("Valid and accepted values are inconsistent.")

    if isinstance(valid, bool) and isinstance(validation_errors, list):
        if valid and validation_errors:
            errors.append(
                "A valid quality gate cannot contain validation errors."
            )
        elif not valid and not validation_errors:
            errors.append(
                "An invalid quality gate must contain validation errors."
            )

    return errors


def validate_exported_validation_quality_gate(
    quality_gate: Dict[str, Any],
) -> Dict[str, Any]:
    structure_errors = (
        validate_exported_validation_quality_gate_structure(quality_gate)
    )

    if not isinstance(quality_gate, dict):
        return {"valid": False, "errors": structure_errors}

    value_errors = (
        validate_exported_validation_quality_gate_values(quality_gate)
    )
    consistency_errors = (
        validate_exported_validation_quality_gate_consistency(quality_gate)
    )

    errors = structure_errors + value_errors + consistency_errors

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


def exported_validation_quality_gate_validation_status(
    validation: Dict[str, Any],
) -> str:
    return "PASS" if validation.get("valid") is True else "FAIL"


def generate_exported_validation_quality_gate_validation(
    quality_gate: Dict[str, Any],
) -> Dict[str, Any]:
    validation = validate_exported_validation_quality_gate(quality_gate)

    return {
        "valid": validation["valid"],
        "status": exported_validation_quality_gate_validation_status(
            validation
        ),
        "errors": validation["errors"],
    }