from evaluation.evidence_quality_summary_quality_gate_validation_report_export_validation import (
    exported_validation_report_validation_status,
    generate_exported_validation_report_validation,
    validate_exported_report_consistency,
    validate_exported_report_structure,
    validate_exported_report_values,
    validate_exported_validation_report,
)


def create_valid_pass_report():
    return {
        "quality_gate": {
            "valid": True,
            "status": "PASS",
            "validation_errors": [],
            "accepted": True,
            "artifact_count": 2,
            "verified_artifact_count": 2,
        },
        "valid": True,
        "status": "PASS",
        "errors": [],
    }


def create_valid_rejected_gate_report():
    return {
        "quality_gate": {
            "valid": False,
            "status": "FAIL",
            "validation_errors": [
                "Evidence artifact integrity verification failed."
            ],
            "accepted": False,
            "artifact_count": 2,
            "verified_artifact_count": 1,
        },
        "valid": True,
        "status": "PASS",
        "errors": [],
    }


def test_valid_report_has_no_structure_errors():
    errors = validate_exported_report_structure(
        create_valid_pass_report()
    )

    assert errors == []


def test_missing_quality_gate_is_detected():
    report = create_valid_pass_report()
    del report["quality_gate"]

    errors = validate_exported_report_structure(report)

    assert any(
        "quality_gate" in error
        for error in errors
    )


def test_missing_valid_is_detected():
    report = create_valid_pass_report()
    del report["valid"]

    errors = validate_exported_report_structure(report)

    assert any(
        "valid" in error
        for error in errors
    )


def test_missing_status_is_detected():
    report = create_valid_pass_report()
    del report["status"]

    errors = validate_exported_report_structure(report)

    assert any(
        "status" in error
        for error in errors
    )


def test_missing_errors_is_detected():
    report = create_valid_pass_report()
    del report["errors"]

    errors = validate_exported_report_structure(report)

    assert any(
        "errors" in error
        for error in errors
    )


def test_non_dictionary_report_is_rejected():
    errors = validate_exported_report_structure(
        ["invalid"]
    )

    assert errors


def test_valid_values_have_no_errors():
    errors = validate_exported_report_values(
        create_valid_pass_report()
    )

    assert errors == []


def test_invalid_valid_value_is_detected():
    report = create_valid_pass_report()
    report["valid"] = "true"

    errors = validate_exported_report_values(report)

    assert any(
        "boolean" in error
        for error in errors
    )


def test_invalid_status_is_detected():
    report = create_valid_pass_report()
    report["status"] = "UNKNOWN"

    errors = validate_exported_report_values(report)

    assert any(
        "status" in error
        for error in errors
    )


def test_invalid_errors_value_is_detected():
    report = create_valid_pass_report()
    report["errors"] = "none"

    errors = validate_exported_report_values(report)

    assert any(
        "list" in error
        for error in errors
    )


def test_invalid_quality_gate_value_is_detected():
    report = create_valid_pass_report()
    report["quality_gate"] = "invalid"

    errors = validate_exported_report_values(report)

    assert any(
        "dictionary" in error
        for error in errors
    )


def test_valid_pass_report_is_consistent():
    errors = validate_exported_report_consistency(
        create_valid_pass_report()
    )

    assert errors == []


def test_valid_rejected_gate_report_is_consistent():
    errors = validate_exported_report_consistency(
        create_valid_rejected_gate_report()
    )

    assert errors == []


def test_valid_fail_status_mismatch_is_detected():
    report = create_valid_pass_report()
    report["status"] = "FAIL"

    errors = validate_exported_report_consistency(report)

    assert any(
        "inconsistent" in error
        for error in errors
    )


def test_invalid_report_without_errors_is_detected():
    report = create_valid_pass_report()
    report["valid"] = False
    report["status"] = "FAIL"

    errors = validate_exported_report_consistency(report)

    assert any(
        "must contain errors" in error
        for error in errors
    )


def test_valid_report_with_errors_is_detected():
    report = create_valid_pass_report()
    report["errors"] = ["unexpected error"]

    errors = validate_exported_report_consistency(report)

    assert any(
        "cannot contain errors" in error
        for error in errors
    )


def test_quality_gate_status_mismatch_is_detected():
    report = create_valid_pass_report()
    report["quality_gate"]["status"] = "FAIL"

    errors = validate_exported_report_consistency(report)

    assert any(
        "Quality gate" in error
        for error in errors
    )


def test_complete_validation_passes():
    result = validate_exported_validation_report(
        create_valid_pass_report()
    )

    assert result["valid"] is True
    assert result["errors"] == []


def test_rejected_quality_gate_record_can_be_valid():
    result = validate_exported_validation_report(
        create_valid_rejected_gate_report()
    )

    assert result["valid"] is True
    assert result["errors"] == []


def test_invalid_report_fails_validation():
    report = create_valid_pass_report()
    report["status"] = "INVALID"

    result = validate_exported_validation_report(report)

    assert result["valid"] is False
    assert result["errors"]


def test_validation_status_pass():
    validation = {
        "valid": True,
        "errors": [],
    }

    assert (
        exported_validation_report_validation_status(
            validation
        )
        == "PASS"
    )


def test_validation_status_fail():
    validation = {
        "valid": False,
        "errors": ["invalid report"],
    }

    assert (
        exported_validation_report_validation_status(
            validation
        )
        == "FAIL"
    )


def test_generated_validation_contains_expected_fields():
    result = generate_exported_validation_report_validation(
        create_valid_pass_report()
    )

    assert set(result.keys()) == {
        "valid",
        "status",
        "errors",
    }


def test_generated_validation_passes():
    result = generate_exported_validation_report_validation(
        create_valid_pass_report()
    )

    assert result["valid"] is True
    assert result["status"] == "PASS"
    assert result["errors"] == []


def test_generated_validation_rejects_invalid_record():
    report = create_valid_pass_report()
    report["valid"] = "yes"

    result = generate_exported_validation_report_validation(
        report
    )

    assert result["valid"] is False
    assert result["status"] == "FAIL"
    assert result["errors"]