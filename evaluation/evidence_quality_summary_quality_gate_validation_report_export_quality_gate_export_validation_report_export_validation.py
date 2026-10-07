from typing import Any, Dict, List


EXPECTED_STATUSES = {
    "PASS",
    "FAIL",
}

REQUIRED_FIELDS = {
    "quality_gate",
    "valid",
    "status",
    "errors",
}


def validate_exported_validation_report_structure(
    report: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []

    if not isinstance(report, dict):
        return [
            "Exported validation report must be a dictionary."
        ]

    for field in REQUIRED_FIELDS:
        if field not in report:
            errors.append(
                f"Missing exported validation report field: {field}"
            )

    return errors


def validate_exported_validation_report_values(
    report: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []

    if not isinstance(report, dict):
        return [
            "Exported validation report must be a dictionary."
        ]

    if "quality_gate" in report:
        if not isinstance(report["quality_gate"], dict):
            errors.append(
                "Quality gate field must be a dictionary."
            )

    if "valid" in report:
        if not isinstance(report["valid"], bool):
            errors.append(
                "Valid field must be a boolean."
            )

    if "status" in report:
        if report["status"] not in EXPECTED_STATUSES:
            errors.append(
                "Invalid exported validation report status value."
            )

    if "errors" in report:
        if not isinstance(report["errors"], list):
            errors.append(
                "Errors field must be a list."
            )

    return errors


def validate_exported_validation_report_consistency(
    report: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []

    if not isinstance(report, dict):
        return []

    valid = report.get("valid")
    status = report.get("status")
    errors_list = report.get("errors")
    quality_gate = report.get("quality_gate")

    if (
        isinstance(valid, bool)
        and isinstance(status, str)
    ):
        expected_status = "PASS" if valid else "FAIL"

        if status != expected_status:
            errors.append(
                "Valid and status values are inconsistent."
            )

    if isinstance(valid, bool) and isinstance(errors_list, list):
        if valid and errors_list:
            errors.append(
                "A valid exported validation report "
                "cannot contain errors."
            )

        if not valid and not errors_list:
            errors.append(
                "An invalid exported validation report "
                "must contain errors."
            )

    if isinstance(quality_gate, dict):
        quality_gate_valid = quality_gate.get("valid")
        quality_gate_status = quality_gate.get("status")

        if (
            isinstance(quality_gate_valid, bool)
            and isinstance(quality_gate_status, str)
        ):
            expected_gate_status = (
                "PASS"
                if quality_gate_valid
                else "FAIL"
            )

            if quality_gate_status != expected_gate_status:
                errors.append(
                    "Quality gate valid and status values "
                    "are inconsistent."
                )

    return errors


def validate_exported_validation_report(
    report: Dict[str, Any],
) -> Dict[str, Any]:
    structure_errors = (
        validate_exported_validation_report_structure(
            report
        )
    )

    if not isinstance(report, dict):
        return {
            "valid": False,
            "errors": structure_errors,
        }

    value_errors = (
        validate_exported_validation_report_values(
            report
        )
    )

    consistency_errors = (
        validate_exported_validation_report_consistency(
            report
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


def exported_validation_report_export_validation_status(
    validation: Dict[str, Any],
) -> str:
    if validation.get("valid") is True:
        return "PASS"

    return "FAIL"


def generate_exported_validation_report_export_validation(
    report: Dict[str, Any],
) -> Dict[str, Any]:
    validation = validate_exported_validation_report(
        report
    )

    return {
        "valid": validation["valid"],
        "status": (
            exported_validation_report_export_validation_status(
                validation
            )
        ),
        "errors": validation["errors"],
    }