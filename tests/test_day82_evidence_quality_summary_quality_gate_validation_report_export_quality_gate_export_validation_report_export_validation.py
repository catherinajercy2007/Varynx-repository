from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation_report_export_validation import (
    exported_validation_report_export_validation_status,
    generate_exported_validation_report_export_validation,
    validate_exported_validation_report,
    validate_exported_validation_report_consistency,
    validate_exported_validation_report_structure,
    validate_exported_validation_report_values,
)


def create_valid_pass_report():
    return {
        "quality_gate": {
            "valid": True,
            "status": "PASS",
            "validation_errors": [],
            "accepted": True,
        },
        "valid": True,
        "status": "PASS",
        "errors": [],
    }


def create_valid_fail_report():
    return {
        "quality_gate": {
            "valid": False,
            "status": "FAIL",
            "validation_errors": [
                "Evidence artifact integrity verification failed."
            ],
            "accepted": False,
        },
        "valid": True,
        "status": "PASS",
        "errors": [],
    }


def test_valid_pass_report_is_valid():
    result = validate_exported_validation_report(
        create_valid_pass_report()
    )

    assert result["valid"] is True
    assert result["errors"] == []


def test_valid_fail_underlying_gate_report_is_valid():
    result = validate_exported_validation_report(
        create_valid_fail_report()
    )

    assert result["valid"] is True
    assert result["errors"] == []


def test_structure_validation_returns_list():
    result = validate_exported_validation_report_structure(
        create_valid_pass_report()
    )

    assert isinstance(result, list)
    assert result == []


def test_values_validation_returns_list():
    result = validate_exported_validation_report_values(
        create_valid_pass_report()
    )

    assert isinstance(result, list)
    assert result == []


def test_consistency_validation_returns_list():
    result = validate_exported_validation_report_consistency(
        create_valid_pass_report()
    )

    assert isinstance(result, list)
    assert result == []


def test_missing_quality_gate_is_rejected():
    report = create_valid_pass_report()
    del report["quality_gate"]

    result = validate_exported_validation_report(report)

    assert result["valid"] is False
    assert result["errors"]


def test_missing_valid_field_is_rejected():
    report = create_valid_pass_report()
    del report["valid"]

    result = validate_exported_validation_report(report)

    assert result["valid"] is False


def test_missing_status_field_is_rejected():
    report = create_valid_pass_report()
    del report["status"]

    result = validate_exported_validation_report(report)

    assert result["valid"] is False


def test_missing_errors_field_is_rejected():
    report = create_valid_pass_report()
    del report["errors"]

    result = validate_exported_validation_report(report)

    assert result["valid"] is False


def test_invalid_quality_gate_type_is_rejected():
    report = create_valid_pass_report()
    report["quality_gate"] = "invalid"

    result = validate_exported_validation_report(report)

    assert result["valid"] is False


def test_invalid_valid_type_is_rejected():
    report = create_valid_pass_report()
    report["valid"] = "true"

    result = validate_exported_validation_report(report)

    assert result["valid"] is False


def test_invalid_status_is_rejected():
    report = create_valid_pass_report()
    report["status"] = "INVALID"

    result = validate_exported_validation_report(report)

    assert result["valid"] is False


def test_invalid_errors_type_is_rejected():
    report = create_valid_pass_report()
    report["errors"] = "no errors"

    result = validate_exported_validation_report(report)

    assert result["valid"] is False


def test_valid_true_with_errors_is_inconsistent():
    report = create_valid_pass_report()
    report["errors"] = ["unexpected error"]

    result = validate_exported_validation_report(report)

    assert result["valid"] is False


def test_invalid_false_without_errors_is_inconsistent():
    report = create_valid_pass_report()
    report["valid"] = False
    report["status"] = "FAIL"
    report["errors"] = []

    result = validate_exported_validation_report(report)

    assert result["valid"] is False


def test_status_must_match_valid_true():
    report = create_valid_pass_report()
    report["status"] = "FAIL"

    result = validate_exported_validation_report(report)

    assert result["valid"] is False


def test_status_must_match_valid_false():
    report = create_valid_pass_report()
    report["valid"] = False
    report["status"] = "PASS"
    report["errors"] = ["invalid exported report"]

    result = validate_exported_validation_report(report)

    assert result["valid"] is False


def test_quality_gate_status_must_match_quality_gate_valid():
    report = create_valid_pass_report()
    report["quality_gate"]["status"] = "FAIL"

    result = validate_exported_validation_report(report)

    assert result["valid"] is False


def test_quality_gate_valid_false_can_be_valid_record():
    report = create_valid_fail_report()

    result = validate_exported_validation_report(report)

    assert result["valid"] is True


def test_non_dictionary_report_is_rejected():
    result = validate_exported_validation_report(
        "invalid"
    )

    assert result["valid"] is False
    assert result["errors"]


def test_structure_rejects_non_dictionary():
    result = validate_exported_validation_report_structure(
        []
    )

    assert result


def test_values_rejects_non_dictionary():
    result = validate_exported_validation_report_values(
        []
    )

    assert result


def test_consistency_ignores_non_dictionary():
    result = validate_exported_validation_report_consistency(
        []
    )

    assert result == []


def test_status_helper_returns_pass():
    validation = {
        "valid": True,
        "errors": [],
    }

    assert (
        exported_validation_report_export_validation_status(
            validation
        )
        == "PASS"
    )


def test_status_helper_returns_fail():
    validation = {
        "valid": False,
        "errors": ["invalid report"],
    }

    assert (
        exported_validation_report_export_validation_status(
            validation
        )
        == "FAIL"
    )


def test_generate_validation_returns_expected_structure():
    result = (
        generate_exported_validation_report_export_validation(
            create_valid_pass_report()
        )
    )

    assert set(result.keys()) == {
        "valid",
        "status",
        "errors",
    }


def test_generate_validation_for_valid_report():
    result = (
        generate_exported_validation_report_export_validation(
            create_valid_pass_report()
        )
    )

    assert result["valid"] is True
    assert result["status"] == "PASS"
    assert result["errors"] == []


def test_generate_validation_for_invalid_report():
    report = create_valid_pass_report()
    report["status"] = "INVALID"

    result = (
        generate_exported_validation_report_export_validation(
            report
        )
    )

    assert result["valid"] is False
    assert result["status"] == "FAIL"
    assert result["errors"]


def test_generate_validation_preserves_failed_underlying_gate():
    result = (
        generate_exported_validation_report_export_validation(
            create_valid_fail_report()
        )
    )

    assert result["valid"] is True
    assert result["status"] == "PASS"
    assert result["errors"] == []