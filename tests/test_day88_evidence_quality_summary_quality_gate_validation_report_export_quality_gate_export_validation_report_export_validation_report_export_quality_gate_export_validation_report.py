
import pytest

from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation_report_export_validation_report_export_quality_gate_export_validation_report import (
    ExportedValidationQualityGateValidationReport,
    determine_exported_validation_quality_gate_validation_report_status,
    generate_exported_validation_quality_gate_validation_report,
    exported_validation_quality_gate_validation_report_to_dict,
    exported_validation_quality_gate_validation_report_status,
    generate_default_exported_validation_quality_gate_validation_report,
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


def invalid_gate():
    return {
        "valid": True,
        "status": "INVALID",
        "validation_errors": [],
        "accepted": True,
    }


def test_generate_report_for_valid_pass_gate():
    report = generate_exported_validation_quality_gate_validation_report(
        valid_pass_gate()
    )
    assert report.valid is True
    assert report.status == "PASS"
    assert report.errors == []


def test_original_quality_gate_is_preserved():
    gate = valid_pass_gate()
    report = generate_exported_validation_quality_gate_validation_report(
        gate
    )
    assert report.quality_gate == gate


def test_valid_fail_gate_record_passes_record_validation():
    report = generate_exported_validation_quality_gate_validation_report(
        valid_fail_gate()
    )
    assert report.valid is True
    assert report.status == "PASS"
    assert report.errors == []


def test_invalid_gate_record_produces_failed_report():
    report = generate_exported_validation_quality_gate_validation_report(
        invalid_gate()
    )
    assert report.valid is False
    assert report.status == "FAIL"
    assert report.errors


def test_report_is_dataclass_instance():
    report = generate_exported_validation_quality_gate_validation_report(
        valid_pass_gate()
    )
    assert isinstance(report, ExportedValidationQualityGateValidationReport)


def test_status_helper_for_valid_report():
    assert (
        determine_exported_validation_quality_gate_validation_report_status(
            True
        )
        == "PASS"
    )


def test_status_helper_for_invalid_report():
    assert (
        determine_exported_validation_quality_gate_validation_report_status(
            False
        )
        == "FAIL"
    )


def test_report_status_accessor():
    report = generate_exported_validation_quality_gate_validation_report(
        valid_pass_gate()
    )
    assert (
        exported_validation_quality_gate_validation_report_status(report)
        == "PASS"
    )


def test_report_to_dict_has_expected_fields():
    report = generate_exported_validation_quality_gate_validation_report(
        valid_pass_gate()
    )
    result = exported_validation_quality_gate_validation_report_to_dict(
        report
    )
    assert set(result) == {"quality_gate", "valid", "status", "errors"}


def test_report_to_dict_preserves_gate():
    gate = valid_pass_gate()
    report = generate_exported_validation_quality_gate_validation_report(
        gate
    )
    result = exported_validation_quality_gate_validation_report_to_dict(
        report
    )
    assert result["quality_gate"] == gate


def test_report_to_dict_preserves_pass_status():
    report = generate_exported_validation_quality_gate_validation_report(
        valid_pass_gate()
    )
    result = exported_validation_quality_gate_validation_report_to_dict(
        report
    )
    assert result["valid"] is True
    assert result["status"] == "PASS"
    assert result["errors"] == []


def test_report_to_dict_preserves_validation_errors():
    report = generate_exported_validation_quality_gate_validation_report(
        invalid_gate()
    )
    result = exported_validation_quality_gate_validation_report_to_dict(
        report
    )
    assert result["valid"] is False
    assert result["status"] == "FAIL"
    assert result["errors"]


def test_default_report_generator_matches_standard_generator():
    gate = valid_pass_gate()
    standard = generate_exported_validation_quality_gate_validation_report(
        gate
    )
    default = generate_default_exported_validation_quality_gate_validation_report(
        gate
    )
    assert (
        exported_validation_quality_gate_validation_report_to_dict(default)
        == exported_validation_quality_gate_validation_report_to_dict(
            standard
        )
    )


def test_report_does_not_mutate_input_gate():
    gate = valid_pass_gate()
    original = gate.copy()
    generate_exported_validation_quality_gate_validation_report(gate)
    assert gate == original


def test_empty_dictionary_produces_failed_report():
    report = generate_exported_validation_quality_gate_validation_report({})
    assert report.valid is False
    assert report.status == "FAIL"
    assert report.errors


def test_missing_field_produces_failed_report():
    gate = valid_pass_gate()
    del gate["accepted"]
    report = generate_exported_validation_quality_gate_validation_report(
        gate
    )
    assert report.valid is False
    assert report.status == "FAIL"


def test_inconsistent_accepted_value_produces_failed_report():
    gate = valid_pass_gate()
    gate["accepted"] = False
    report = generate_exported_validation_quality_gate_validation_report(
        gate
    )
    assert report.valid is False
    assert report.status == "FAIL"


def test_invalid_status_produces_failed_report():
    gate = valid_pass_gate()
    gate["status"] = "UNKNOWN"
    report = generate_exported_validation_quality_gate_validation_report(
        gate
    )
    assert report.valid is False
    assert report.status == "FAIL"


def test_report_contains_list_of_errors():
    report = generate_exported_validation_quality_gate_validation_report(
        invalid_gate()
    )
    assert isinstance(report.errors, list)


def test_extra_gate_metadata_is_preserved():
    gate = valid_pass_gate()
    gate["metadata"] = {"source": "day87"}
    report = generate_exported_validation_quality_gate_validation_report(
        gate
    )
    assert report.quality_gate["metadata"] == {"source": "day87"}


def test_report_to_dict_does_not_drop_extra_gate_metadata():
    gate = valid_pass_gate()
    gate["metadata"] = {"source": "day87"}
    report = generate_exported_validation_quality_gate_validation_report(
        gate
    )
    result = exported_validation_quality_gate_validation_report_to_dict(
        report
    )
    assert result["quality_gate"]["metadata"] == {"source": "day87"}


def test_repeated_generation_is_deterministic():
    gate = valid_pass_gate()
    first = generate_exported_validation_quality_gate_validation_report(
        gate
    )
    second = generate_exported_validation_quality_gate_validation_report(
        gate
    )
    assert (
        exported_validation_quality_gate_validation_report_to_dict(first)
        == exported_validation_quality_gate_validation_report_to_dict(
            second
        )
    )