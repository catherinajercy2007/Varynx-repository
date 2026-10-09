
import pytest

from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation_report_export_validation_report_export_quality_gate_export_validation import (
    validate_exported_validation_quality_gate_structure,
    validate_exported_validation_quality_gate_values,
    validate_exported_validation_quality_gate_consistency,
    validate_exported_validation_quality_gate,
    exported_validation_quality_gate_validation_status,
    generate_exported_validation_quality_gate_validation,
)


def valid_pass_gate():
    return {
        "valid": True,
        "status": "PASS",
        "validation_errors": [],
        "accepted": True,
    }


def valid_fail_gate():
    return {
        "valid": False,
        "status": "FAIL",
        "validation_errors": ["Evidence verification failed."],
        "accepted": False,
    }


def test_valid_pass_gate_is_valid():
    assert validate_exported_validation_quality_gate(valid_pass_gate()) == {
        "valid": True,
        "errors": [],
    }


def test_valid_fail_gate_is_valid_record():
    result = validate_exported_validation_quality_gate(valid_fail_gate())
    assert result["valid"] is True
    assert result["errors"] == []


def test_non_dictionary_is_rejected():
    result = validate_exported_validation_quality_gate([])
    assert result["valid"] is False
    assert "must be a dictionary" in result["errors"][0]


@pytest.mark.parametrize("field", [
    "valid", "status", "validation_errors", "accepted"
])
def test_missing_required_field_is_reported(field):
    gate = valid_pass_gate()
    del gate[field]
    errors = validate_exported_validation_quality_gate_structure(gate)
    assert f"Missing exported validation quality gate field: {field}" in errors


@pytest.mark.parametrize("value", [0, 1, "true", None, []])
def test_valid_must_be_boolean(value):
    gate = valid_pass_gate()
    gate["valid"] = value
    assert "Valid field must be a boolean." in (
        validate_exported_validation_quality_gate_values(gate)
    )


@pytest.mark.parametrize("status", ["UNKNOWN", "pass", "", None, 1])
def test_status_must_be_pass_or_fail(status):
    gate = valid_pass_gate()
    gate["status"] = status
    assert "Invalid exported validation quality gate status." in (
        validate_exported_validation_quality_gate_values(gate)
    )


@pytest.mark.parametrize("value", ["false", 0, None, []])
def test_accepted_must_be_boolean(value):
    gate = valid_pass_gate()
    gate["accepted"] = value
    assert "Accepted field must be a boolean." in (
        validate_exported_validation_quality_gate_values(gate)
    )


@pytest.mark.parametrize("value", ["error", None, {}])
def test_validation_errors_must_be_list(value):
    gate = valid_pass_gate()
    gate["validation_errors"] = value
    assert "Validation errors field must be a list." in (
        validate_exported_validation_quality_gate_values(gate)
    )


def test_each_validation_error_must_be_string():
    gate = valid_pass_gate()
    gate["validation_errors"] = ["valid error", 42]
    assert "Every validation error must be a string." in (
        validate_exported_validation_quality_gate_values(gate)
    )


def test_valid_and_fail_status_are_inconsistent():
    gate = valid_pass_gate()
    gate["status"] = "FAIL"
    assert "Valid and status values are inconsistent." in (
        validate_exported_validation_quality_gate_consistency(gate)
    )


def test_invalid_and_pass_status_are_inconsistent():
    gate = valid_fail_gate()
    gate["status"] = "PASS"
    assert "Valid and status values are inconsistent." in (
        validate_exported_validation_quality_gate_consistency(gate)
    )


def test_valid_and_accepted_must_match():
    gate = valid_pass_gate()
    gate["accepted"] = False
    assert "Valid and accepted values are inconsistent." in (
        validate_exported_validation_quality_gate_consistency(gate)
    )


def test_invalid_and_accepted_must_match():
    gate = valid_fail_gate()
    gate["accepted"] = True
    assert "Valid and accepted values are inconsistent." in (
        validate_exported_validation_quality_gate_consistency(gate)
    )


def test_valid_gate_cannot_have_validation_errors():
    gate = valid_pass_gate()
    gate["validation_errors"] = ["Unexpected error"]
    assert "A valid quality gate cannot contain validation errors." in (
        validate_exported_validation_quality_gate_consistency(gate)
    )


def test_invalid_gate_requires_validation_errors():
    gate = valid_fail_gate()
    gate["validation_errors"] = []
    assert "An invalid quality gate must contain validation errors." in (
        validate_exported_validation_quality_gate_consistency(gate)
    )


def test_status_helper_returns_pass():
    assert exported_validation_quality_gate_validation_status(
        {"valid": True}
    ) == "PASS"


def test_status_helper_returns_fail():
    assert exported_validation_quality_gate_validation_status(
        {"valid": False}
    ) == "FAIL"


def test_generated_validation_for_valid_gate():
    result = generate_exported_validation_quality_gate_validation(
        valid_pass_gate()
    )
    assert result == {"valid": True, "status": "PASS", "errors": []}


def test_generated_validation_for_invalid_gate():
    gate = valid_pass_gate()
    gate["status"] = "FAIL"
    result = generate_exported_validation_quality_gate_validation(gate)
    assert result["valid"] is False
    assert result["status"] == "FAIL"
    assert result["errors"]


def test_extra_fields_are_allowed():
    gate = valid_pass_gate()
    gate["metadata"] = {"source": "day86"}
    assert validate_exported_validation_quality_gate(gate)["valid"] is True


def test_multiple_validation_errors_are_preserved():
    gate = valid_fail_gate()
    gate["validation_errors"] = ["First error", "Second error"]
    assert validate_exported_validation_quality_gate(gate)["valid"] is True


def test_structure_validator_rejects_non_dictionary():
    assert validate_exported_validation_quality_gate_structure(None)


def test_value_validator_rejects_non_dictionary():
    assert validate_exported_validation_quality_gate_values(None)


def test_consistency_validator_handles_non_dictionary():
    assert validate_exported_validation_quality_gate_consistency(None) == []


def test_validation_result_has_expected_keys():
    result = validate_exported_validation_quality_gate(valid_pass_gate())
    assert set(result) == {"valid", "errors"}


def test_generated_result_has_expected_keys():
    result = generate_exported_validation_quality_gate_validation(
        valid_pass_gate()
    )
    assert set(result) == {"valid", "status", "errors"}