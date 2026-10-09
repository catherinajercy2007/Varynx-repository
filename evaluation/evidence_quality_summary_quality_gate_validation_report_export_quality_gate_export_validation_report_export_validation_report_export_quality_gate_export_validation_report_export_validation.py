"""Day 90: Validate exported quality-gate validation reports."""

import json
from pathlib import Path
from typing import Any, Dict, List


REQUIRED_FIELDS = {"quality_gate", "valid", "status", "errors"}
ALLOWED_STATUSES = {"PASS", "FAIL"}


def validate_exported_quality_gate_report_structure(
    report: Any,
) -> Dict[str, Any]:
    """Check that the report is a dictionary with the required fields."""
    errors: List[str] = []

    if not isinstance(report, dict):
        return {
            "valid": False,
            "errors": ["Report must be a dictionary."],
        }

    missing = sorted(REQUIRED_FIELDS - set(report.keys()))
    if missing:
        errors.append(
            "Missing required fields: " + ", ".join(missing) + "."
        )

    if errors:
        return {"valid": False, "errors": errors}

    return {"valid": True, "errors": []}


def validate_exported_quality_gate_report_values(
    report: Any,
) -> Dict[str, Any]:
    """Validate the types and allowed values of report fields."""
    structure = validate_exported_quality_gate_report_structure(report)
    errors = list(structure["errors"])

    if errors:
        return {"valid": False, "errors": errors}

    if not isinstance(report["quality_gate"], dict):
        errors.append("'quality_gate' must be a dictionary.")

    if not isinstance(report["valid"], bool):
        errors.append("'valid' must be a boolean.")

    if (
        not isinstance(report["status"], str)
        or report["status"] not in ALLOWED_STATUSES
    ):
        errors.append("'status' must be 'PASS' or 'FAIL'.")

    if not isinstance(report["errors"], list):
        errors.append("'errors' must be a list.")
    elif not all(isinstance(item, str) for item in report["errors"]):
        errors.append("Every item in 'errors' must be a string.")

    return {"valid": not errors, "errors": errors}


def validate_exported_quality_gate_report_consistency(
    report: Any,
) -> Dict[str, Any]:
    """Check that validity, status, and errors agree with one another."""
    values = validate_exported_quality_gate_report_values(report)
    errors = list(values["errors"])

    if errors:
        return {"valid": False, "errors": errors}

    is_valid = report["valid"]
    expected_status = "PASS" if is_valid else "FAIL"

    if report["status"] != expected_status:
        errors.append(
            f"Status must be '{expected_status}' when valid is {is_valid}."
        )

    if is_valid and report["errors"]:
        errors.append("A valid report must have an empty errors list.")

    if not is_valid and not report["errors"]:
        errors.append("An invalid report must include at least one error.")

    return {"valid": not errors, "errors": errors}


def validate_exported_quality_gate_report(
    report: Any,
) -> Dict[str, Any]:
    """Run structure, value, and consistency checks."""
    result = validate_exported_quality_gate_report_consistency(report)

    return {
        "valid": result["valid"],
        "status": "PASS" if result["valid"] else "FAIL",
        "errors": result["errors"],
    }


def validate_exported_quality_gate_report_json(
    file_path: str,
) -> Dict[str, Any]:
    """Load a JSON file and validate the report it contains."""
    path = Path(file_path)

    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "valid": False,
            "status": "FAIL",
            "errors": [f"Unable to load report: {exc}"],
        }

    return validate_exported_quality_gate_report(report)