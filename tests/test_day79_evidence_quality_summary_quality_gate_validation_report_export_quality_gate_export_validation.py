from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation import (
    exported_quality_gate_validation_status,
    generate_exported_quality_gate_validation,
    validate_exported_quality_gate,
    validate_exported_quality_gate_consistency,
    validate_exported_quality_gate_structure,
    validate_exported_quality_gate_values,
)


def create_valid_pass_quality_gate():
    return {
        "valid": True,
        "status": "PASS",
        "validation_errors": [],
        "accepted": True,
    }


def create_valid_fail_quality_gate():
    return {
        "valid": False,
        "status": "FAIL",
        "validation_errors": [
            "Evidence artifact integrity verification failed."
        ],
        "accepted": False,
    }


def test_valid_pass_quality_gate_is_valid():
    result = validate_exported_quality_gate(
        create_valid_pass_quality_gate()
    )

    assert result["valid"] is True
    assert result["errors"] == []


def test_valid_fail_quality_gate_record_is_valid():
    result = validate_exported_quality_gate(
        create_valid_fail_quality_gate()
    )

    assert result["valid"] is True
    assert result["errors"] == []


def test_structure_validation_accepts_valid_record():
    errors = validate_exported_quality_gate_structure(
        create_valid_pass_quality_gate()
    )

    assert errors == []


def test_values_validation_accepts_valid_record():
    errors = validate_exported_quality_gate_values(
        create_valid_pass_quality_gate()
    )

    assert errors == []


def test_consistency_validation_accepts_valid_pass():
    errors = validate_exported_quality_gate_consistency(
        create_valid_pass_quality_gate()
    )

    assert errors == []


def test_consistency_validation_accepts_valid_fail():
    errors = validate_exported_quality_gate_consistency(
        create_valid_fail_quality_gate()
    )

    assert errors == []


def test_missing_valid_field_is_rejected():
    quality_gate = create_valid_pass_quality_gate()
    del quality_gate["valid"]

    result = validate_exported_quality_gate(
        quality_gate
    )

    assert result["valid"] is False


def test_missing_status_field_is_rejected():
    quality_gate = create_valid_pass_quality_gate()
    del quality_gate["status"]

    result = validate_exported_quality_gate(
        quality_gate
    )

    assert result["valid"] is False


def test_missing_validation_errors_field_is_rejected():
    quality_gate = create_valid_pass_quality_gate()
    del quality_gate["validation_errors"]

    result = validate_exported_quality_gate(
        quality_gate
    )

    assert result["valid"] is False


def test_missing_accepted_field_is_rejected():
    quality_gate = create_valid_pass_quality_gate()
    del quality_gate["accepted"]

    result = validate_exported_quality_gate(
        quality_gate
    )

    assert result["valid"] is False


def test_invalid_valid_type_is_rejected():
    quality_gate = create_valid_pass_quality_gate()
    quality_gate["valid"] = "true"

    result = validate_exported_quality_gate(
        quality_gate
    )

    assert result["valid"] is False


def test_invalid_status_is_rejected():
    quality_gate = create_valid_pass_quality_gate()
    quality_gate["status"] = "INVALID"

    result = validate_exported_quality_gate(
        quality_gate
    )

    assert result["valid"] is False


def test_invalid_validation_errors_type_is_rejected():
    quality_gate = create_valid_pass_quality_gate()
    quality_gate["validation_errors"] = "none"

    result = validate_exported_quality_gate(
        quality_gate
    )

    assert result["valid"] is False


def test_invalid_accepted_type_is_rejected():
    quality_gate = create_valid_pass_quality_gate()
    quality_gate["accepted"] = "true"

    result = validate_exported_quality_gate(
        quality_gate
    )

    assert result["valid"] is False


def test_valid_true_with_fail_status_is_rejected():
    quality_gate = create_valid_pass_quality_gate()
    quality_gate["status"] = "FAIL"

    result = validate_exported_quality_gate(
        quality_gate
    )

    assert result["valid"] is False


def test_valid_false_with_pass_status_is_rejected():
    quality_gate = create_valid_fail_quality_gate()
    quality_gate["status"] = "PASS"

    result = validate_exported_quality_gate(
        quality_gate
    )

    assert result["valid"] is False


def test_pass_status_with_false_accepted_is_rejected():
    quality_gate = create_valid_pass_quality_gate()
    quality_gate["accepted"] = False

    result = validate_exported_quality_gate(
        quality_gate
    )

    assert result["valid"] is False


def test_fail_status_with_true_accepted_is_rejected():
    quality_gate = create_valid_fail_quality_gate()
    quality_gate["accepted"] = True

    result = validate_exported_quality_gate(
        quality_gate
    )

    assert result["valid"] is False


def test_valid_quality_gate_with_errors_is_rejected():
    quality_gate = create_valid_pass_quality_gate()
    quality_gate["validation_errors"] = [
        "Unexpected error."
    ]

    result = validate_exported_quality_gate(
        quality_gate
    )

    assert result["valid"] is False


def test_invalid_quality_gate_without_errors_is_rejected():
    quality_gate = create_valid_fail_quality_gate()
    quality_gate["validation_errors"] = []

    result = validate_exported_quality_gate(
        quality_gate
    )

    assert result["valid"] is False


def test_non_dictionary_input_is_rejected():
    result = validate_exported_quality_gate(
        ["invalid"]
    )

    assert result["valid"] is False


def test_validation_status_returns_pass():
    validation = validate_exported_quality_gate(
        create_valid_pass_quality_gate()
    )

    assert (
        exported_quality_gate_validation_status(
            validation
        )
        == "PASS"
    )


def test_validation_status_returns_fail():
    quality_gate = create_valid_pass_quality_gate()
    quality_gate["status"] = "INVALID"

    validation = validate_exported_quality_gate(
        quality_gate
    )

    assert (
        exported_quality_gate_validation_status(
            validation
        )
        == "FAIL"
    )


def test_generated_validation_contains_expected_fields():
    result = generate_exported_quality_gate_validation(
        create_valid_pass_quality_gate()
    )

    assert set(result.keys()) == {
        "valid",
        "status",
        "errors",
    }


def test_generated_validation_passes_valid_record():
    result = generate_exported_quality_gate_validation(
        create_valid_pass_quality_gate()
    )

    assert result["valid"] is True
    assert result["status"] == "PASS"
    assert result["errors"] == []


def test_generated_validation_fails_invalid_record():
    quality_gate = create_valid_pass_quality_gate()
    quality_gate["status"] = "INVALID"

    result = generate_exported_quality_gate_validation(
        quality_gate
    )

    assert result["valid"] is False
    assert result["status"] == "FAIL"
    assert result["errors"]


def test_fail_record_can_be_valid_exported_record():
    result = generate_exported_quality_gate_validation(
        create_valid_fail_quality_gate()
    )

    assert result["valid"] is True
    assert result["status"] == "PASS"
    assert result["errors"] == []