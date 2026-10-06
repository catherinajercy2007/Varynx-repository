from evaluation.evidence_quality_summary_quality_gate_validation import (
    evidence_quality_summary_quality_gate_validation_status,
    generate_evidence_quality_summary_quality_gate_validation,
    validate_evidence_quality_summary_quality_gate,
    validate_quality_gate_consistency,
    validate_quality_gate_structure,
    validate_quality_gate_values,
)


def create_valid_pass_quality_gate():
    return {
        "valid": True,
        "status": "PASS",
        "validation_errors": [],
        "accepted": True,
        "artifact_count": 2,
        "verified_artifact_count": 2,
    }


def create_valid_fail_quality_gate():
    return {
        "valid": False,
        "status": "FAIL",
        "validation_errors": [
            "Evidence artifact integrity verification failed."
        ],
        "accepted": False,
        "artifact_count": 2,
        "verified_artifact_count": 1,
    }


def test_valid_pass_quality_gate_structure():
    gate = create_valid_pass_quality_gate()

    assert validate_quality_gate_structure(gate) == []


def test_valid_fail_quality_gate_structure():
    gate = create_valid_fail_quality_gate()

    assert validate_quality_gate_structure(gate) == []


def test_missing_quality_gate_field_is_detected():
    gate = create_valid_pass_quality_gate()
    del gate["artifact_count"]

    errors = validate_quality_gate_structure(gate)

    assert (
        "Missing quality gate field: artifact_count"
        in errors
    )


def test_valid_quality_gate_values():
    gate = create_valid_pass_quality_gate()

    assert validate_quality_gate_values(gate) == []


def test_invalid_status_is_detected():
    gate = create_valid_pass_quality_gate()
    gate["status"] = "UNKNOWN"

    errors = validate_quality_gate_values(gate)

    assert "Invalid quality gate status value." in errors


def test_invalid_valid_field_is_detected():
    gate = create_valid_pass_quality_gate()
    gate["valid"] = "true"

    errors = validate_quality_gate_values(gate)

    assert "Valid field must be a boolean." in errors


def test_invalid_accepted_field_is_detected():
    gate = create_valid_pass_quality_gate()
    gate["accepted"] = "true"

    errors = validate_quality_gate_values(gate)

    assert "Accepted field must be a boolean." in errors


def test_invalid_validation_errors_field_is_detected():
    gate = create_valid_pass_quality_gate()
    gate["validation_errors"] = "none"

    errors = validate_quality_gate_values(gate)

    assert (
        "Validation errors field must be a list."
        in errors
    )


def test_invalid_numeric_value_is_detected():
    gate = create_valid_pass_quality_gate()
    gate["artifact_count"] = -1

    errors = validate_quality_gate_values(gate)

    assert (
        "artifact_count must be a non-negative integer."
        in errors
    )


def test_pass_quality_gate_is_consistent():
    gate = create_valid_pass_quality_gate()

    assert validate_quality_gate_consistency(gate) == []


def test_fail_quality_gate_is_consistent():
    gate = create_valid_fail_quality_gate()

    assert validate_quality_gate_consistency(gate) == []


def test_valid_status_mismatch_is_detected():
    gate = create_valid_pass_quality_gate()
    gate["valid"] = False

    errors = validate_quality_gate_consistency(gate)

    assert any(
        "valid and status" in error.lower()
        for error in errors
    )


def test_status_acceptance_mismatch_is_detected():
    gate = create_valid_pass_quality_gate()
    gate["accepted"] = False

    errors = validate_quality_gate_consistency(gate)

    assert any(
        "status and accepted" in error.lower()
        for error in errors
    )


def test_valid_gate_with_errors_is_detected():
    gate = create_valid_pass_quality_gate()
    gate["validation_errors"] = [
        "Unexpected validation error."
    ]

    errors = validate_quality_gate_consistency(gate)

    assert any(
        "valid quality gate" in error.lower()
        for error in errors
    )


def test_invalid_gate_without_errors_is_detected():
    gate = create_valid_fail_quality_gate()
    gate["validation_errors"] = []

    errors = validate_quality_gate_consistency(gate)

    assert any(
        "invalid quality gate" in error.lower()
        for error in errors
    )


def test_verified_artifacts_cannot_exceed_total():
    gate = create_valid_pass_quality_gate()
    gate["artifact_count"] = 1
    gate["verified_artifact_count"] = 2

    errors = validate_quality_gate_consistency(gate)

    assert any(
        "cannot exceed" in error
        for error in errors
    )


def test_full_pass_validation():
    gate = create_valid_pass_quality_gate()

    validation = (
        validate_evidence_quality_summary_quality_gate(
            gate
        )
    )

    assert validation["valid"] is True
    assert validation["errors"] == []


def test_full_fail_validation():
    gate = create_valid_fail_quality_gate()

    validation = (
        validate_evidence_quality_summary_quality_gate(
            gate
        )
    )

    assert validation["valid"] is True
    assert validation["errors"] == []


def test_invalid_gate_is_rejected():
    gate = create_valid_pass_quality_gate()
    gate["status"] = "UNKNOWN"

    validation = (
        validate_evidence_quality_summary_quality_gate(
            gate
        )
    )

    assert validation["valid"] is False
    assert validation["errors"]


def test_validation_status_pass():
    validation = {
        "valid": True,
        "errors": [],
    }

    assert (
        evidence_quality_summary_quality_gate_validation_status(
            validation
        )
        == "PASS"
    )


def test_validation_status_fail():
    validation = {
        "valid": False,
        "errors": ["Invalid quality gate."],
    }

    assert (
        evidence_quality_summary_quality_gate_validation_status(
            validation
        )
        == "FAIL"
    )


def test_generate_validation_report():
    gate = create_valid_pass_quality_gate()

    validation = (
        generate_evidence_quality_summary_quality_gate_validation(
            gate
        )
    )

    assert validation["valid"] is True
    assert validation["status"] == "PASS"
    assert validation["errors"] == []


def test_generate_validation_report_for_invalid_gate():
    gate = create_valid_pass_quality_gate()
    gate["accepted"] = False

    validation = (
        generate_evidence_quality_summary_quality_gate_validation(
            gate
        )
    )

    assert validation["valid"] is False
    assert validation["status"] == "FAIL"
    assert validation["errors"]


def test_non_dictionary_quality_gate_is_rejected():
    validation = (
        validate_evidence_quality_summary_quality_gate(
            "invalid"
        )
    )

    assert validation["valid"] is False
    assert validation["errors"]