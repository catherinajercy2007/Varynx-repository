from evaluation.evidence_quality_report_summary_validation import (
    evidence_quality_summary_validation_status,
    generate_evidence_quality_summary_validation,
    validate_evidence_quality_summary,
    validate_summary_consistency,
    validate_summary_structure,
    validate_summary_values,
)


def create_valid_accepted_summary():
    return {
        "overall_status": "ACCEPTED",
        "accepted": True,
        "quality_gate_status": "PASS",
        "integrity_verified": True,
        "artifact_count": 2,
        "verified_artifact_count": 2,
        "validation_error_count": 0,
    }


def create_valid_rejected_summary():
    return {
        "overall_status": "REJECTED",
        "accepted": False,
        "quality_gate_status": "FAIL",
        "integrity_verified": False,
        "artifact_count": 0,
        "verified_artifact_count": 0,
        "validation_error_count": 1,
    }


def test_valid_accepted_summary_structure():
    summary = create_valid_accepted_summary()

    errors = validate_summary_structure(
        summary
    )

    assert errors == []


def test_valid_rejected_summary_structure():
    summary = create_valid_rejected_summary()

    errors = validate_summary_structure(
        summary
    )

    assert errors == []


def test_missing_summary_field_is_detected():
    summary = create_valid_accepted_summary()

    del summary["artifact_count"]

    errors = validate_summary_structure(
        summary
    )

    assert (
        "Missing summary field: artifact_count"
        in errors
    )


def test_valid_summary_values():
    summary = create_valid_accepted_summary()

    errors = validate_summary_values(
        summary
    )

    assert errors == []


def test_invalid_overall_status_is_detected():
    summary = create_valid_accepted_summary()

    summary["overall_status"] = "UNKNOWN"

    errors = validate_summary_values(
        summary
    )

    assert "Invalid overall_status value." in errors


def test_invalid_quality_gate_status_is_detected():
    summary = create_valid_accepted_summary()

    summary["quality_gate_status"] = "UNKNOWN"

    errors = validate_summary_values(
        summary
    )

    assert (
        "Invalid quality_gate_status value."
        in errors
    )


def test_invalid_boolean_is_detected():
    summary = create_valid_accepted_summary()

    summary["accepted"] = "true"

    errors = validate_summary_values(
        summary
    )

    assert (
        "Accepted field must be a boolean."
        in errors
    )


def test_invalid_numeric_value_is_detected():
    summary = create_valid_accepted_summary()

    summary["artifact_count"] = -1

    errors = validate_summary_values(
        summary
    )

    assert (
        "artifact_count must be a non-negative integer."
        in errors
    )


def test_consistent_accepted_summary():
    summary = create_valid_accepted_summary()

    errors = validate_summary_consistency(
        summary
    )

    assert errors == []


def test_consistent_rejected_summary():
    summary = create_valid_rejected_summary()

    errors = validate_summary_consistency(
        summary
    )

    assert errors == []


def test_status_acceptance_mismatch_is_detected():
    summary = create_valid_accepted_summary()

    summary["accepted"] = False

    errors = validate_summary_consistency(
        summary
    )

    assert any(
        "inconsistent" in error.lower()
        for error in errors
    )


def test_quality_gate_acceptance_mismatch_is_detected():
    summary = create_valid_accepted_summary()

    summary["quality_gate_status"] = "FAIL"

    errors = validate_summary_consistency(
        summary
    )

    assert any(
        "quality gate" in error.lower()
        for error in errors
    )


def test_verified_artifacts_cannot_exceed_total():
    summary = create_valid_accepted_summary()

    summary["artifact_count"] = 1
    summary["verified_artifact_count"] = 2

    errors = validate_summary_consistency(
        summary
    )

    assert any(
        "cannot exceed" in error
        for error in errors
    )


def test_full_validation_passes():
    summary = create_valid_accepted_summary()

    validation = validate_evidence_quality_summary(
        summary
    )

    assert validation["valid"] is True
    assert validation["errors"] == []


def test_full_validation_rejects_invalid_summary():
    summary = create_valid_accepted_summary()

    summary["overall_status"] = "UNKNOWN"

    validation = validate_evidence_quality_summary(
        summary
    )

    assert validation["valid"] is False
    assert validation["errors"]


def test_validation_status_pass():
    validation = {
        "valid": True,
        "errors": [],
    }

    assert (
        evidence_quality_summary_validation_status(
            validation
        )
        == "PASS"
    )


def test_validation_status_fail():
    validation = {
        "valid": False,
        "errors": [
            "Invalid summary."
        ],
    }

    assert (
        evidence_quality_summary_validation_status(
            validation
        )
        == "FAIL"
    )


def test_generate_validation_report():
    summary = create_valid_accepted_summary()

    validation = (
        generate_evidence_quality_summary_validation(
            summary
        )
    )

    assert validation["valid"] is True
    assert validation["status"] == "PASS"
    assert validation["errors"] == []


def test_generate_validation_report_for_rejected_summary():
    summary = create_valid_rejected_summary()

    validation = (
        generate_evidence_quality_summary_validation(
            summary
        )
    )

    assert validation["valid"] is True
    assert validation["status"] == "PASS"


def test_non_dictionary_summary_is_rejected():
    validation = validate_evidence_quality_summary(
        "invalid"
    )

    assert validation["valid"] is False
    assert validation["errors"]