from typing import Any, Dict, List


EXPECTED_STATUSES = {"ACCEPTED", "REJECTED"}
EXPECTED_GATE_STATUSES = {"PASS", "FAIL"}


def validate_report_structure(
    report: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []

    if not isinstance(report, dict):
        return ["Evidence quality report must be a dictionary."]

    required_fields = {
        "evidence_index",
        "quality_gate",
        "overall_status",
        "accepted",
    }

    for field in required_fields:
        if field not in report:
            errors.append(
                f"Missing report field: {field}"
            )

    return errors


def validate_report_values(
    report: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []

    overall_status = report.get("overall_status")

    if "overall_status" in report:
        if overall_status not in EXPECTED_STATUSES:
            errors.append(
                "Invalid overall_status value."
            )

    accepted = report.get("accepted")

    if "accepted" in report:
        if not isinstance(accepted, bool):
            errors.append(
                "Accepted field must be a boolean."
            )

    evidence_index = report.get("evidence_index")

    if "evidence_index" in report:
        if not isinstance(evidence_index, dict):
            errors.append(
                "Evidence index must be a dictionary."
            )

    quality_gate = report.get("quality_gate")

    if "quality_gate" in report:
        if not isinstance(quality_gate, dict):
            errors.append(
                "Quality gate must be a dictionary."
            )

    return errors


def validate_quality_gate(
    quality_gate: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []

    if not isinstance(quality_gate, dict):
        return ["Quality gate must be a dictionary."]

    required_fields = {
        "valid",
        "status",
        "validation_errors",
        "integrity_verified",
        "artifact_count",
        "accepted",
    }

    for field in required_fields:
        if field not in quality_gate:
            errors.append(
                f"Quality gate missing field: {field}"
            )

    if "valid" in quality_gate:
        if not isinstance(quality_gate["valid"], bool):
            errors.append(
                "Quality gate valid field must be a boolean."
            )

    if "status" in quality_gate:
        if quality_gate["status"] not in EXPECTED_GATE_STATUSES:
            errors.append(
                "Invalid quality gate status."
            )

    if "validation_errors" in quality_gate:
        if not isinstance(
            quality_gate["validation_errors"],
            list,
        ):
            errors.append(
                "Quality gate validation_errors must be a list."
            )

    if "integrity_verified" in quality_gate:
        if not isinstance(
            quality_gate["integrity_verified"],
            bool,
        ):
            errors.append(
                "Quality gate integrity_verified "
                "must be a boolean."
            )

    if "artifact_count" in quality_gate:
        artifact_count = quality_gate["artifact_count"]

        if (
            not isinstance(artifact_count, int)
            or isinstance(artifact_count, bool)
            or artifact_count < 0
        ):
            errors.append(
                "Quality gate artifact_count must be "
                "a non-negative integer."
            )

    if "accepted" in quality_gate:
        if not isinstance(
            quality_gate["accepted"],
            bool,
        ):
            errors.append(
                "Quality gate accepted field must be "
                "a boolean."
            )

    return errors
    errors: List[str] = []

    quality_gate = report.get("quality_gate")

    if not isinstance(quality_gate, dict):
        return errors

    required_fields = {
        "valid",
        "status",
        "validation_errors",
        "integrity_verified",
        "artifact_count",
        "accepted",
    }

    for field in required_fields:
        if field not in quality_gate:
            errors.append(
                f"Quality gate missing field: {field}"
            )

    if "valid" in quality_gate:
        if not isinstance(quality_gate["valid"], bool):
            errors.append(
                "Quality gate valid field must be a boolean."
            )

    if "status" in quality_gate:
        if quality_gate["status"] not in EXPECTED_GATE_STATUSES:
            errors.append(
                "Invalid quality gate status."
            )

    if "validation_errors" in quality_gate:
        if not isinstance(
            quality_gate["validation_errors"],
            list,
        ):
            errors.append(
                "Quality gate validation_errors must be a list."
            )

    if "integrity_verified" in quality_gate:
        if not isinstance(
            quality_gate["integrity_verified"],
            bool,
        ):
            errors.append(
                "Quality gate integrity_verified "
                "must be a boolean."
            )

    if "artifact_count" in quality_gate:
        artifact_count = quality_gate["artifact_count"]

        if (
            not isinstance(artifact_count, int)
            or isinstance(artifact_count, bool)
            or artifact_count < 0
        ):
            errors.append(
                "Quality gate artifact_count must be "
                "a non-negative integer."
            )

    if "accepted" in quality_gate:
        if not isinstance(
            quality_gate["accepted"],
            bool,
        ):
            errors.append(
                "Quality gate accepted field must be "
                "a boolean."
            )

    return errors


def validate_report_consistency(
    report: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []

    overall_status = report.get("overall_status")
    accepted = report.get("accepted")
    quality_gate = report.get("quality_gate")

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

    if isinstance(quality_gate, dict):
        gate_status = quality_gate.get("status")
        gate_accepted = quality_gate.get("accepted")

        if (
            isinstance(gate_status, str)
            and isinstance(gate_accepted, bool)
        ):
            expected_gate_accepted = (
                gate_status == "PASS"
            )

            if gate_accepted != expected_gate_accepted:
                errors.append(
                    "Quality gate status and accepted "
                    "value are inconsistent."
                )

        if (
            isinstance(accepted, bool)
            and isinstance(gate_accepted, bool)
        ):
            if accepted != gate_accepted:
                errors.append(
                    "Report acceptance and quality gate "
                    "acceptance are inconsistent."
                )

    return errors


def validate_evidence_quality_report(
    report: Dict[str, Any],
) -> Dict[str, Any]:
    structure_errors = validate_report_structure(
        report
    )

    value_errors = validate_report_values(
        report
    )

    quality_gate_errors = validate_quality_gate(
        report.get("quality_gate")
    )

    consistency_errors = validate_report_consistency(
        report
    )

    errors = (
        structure_errors
        + value_errors
        + quality_gate_errors
        + consistency_errors
    )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


def evidence_quality_report_validation_status(
    validation: Dict[str, Any],
) -> str:
    if validation.get("valid") is True:
        return "PASS"

    return "FAIL"


def generate_evidence_quality_report_validation(
    report: Dict[str, Any],
) -> Dict[str, Any]:
    validation = validate_evidence_quality_report(
        report
    )

    return {
        "valid": validation["valid"],
        "status": evidence_quality_report_validation_status(
            validation
        ),
        "errors": validation["errors"],
    }