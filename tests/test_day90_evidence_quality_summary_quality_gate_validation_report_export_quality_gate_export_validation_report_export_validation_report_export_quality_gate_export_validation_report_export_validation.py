import json

from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation_report_export_validation_report_export_quality_gate_export_validation_report_export_validation import (
    validate_exported_quality_gate_report_structure,
    validate_exported_quality_gate_report_values,
    validate_exported_quality_gate_report_consistency,
    validate_exported_quality_gate_report,
    validate_exported_quality_gate_report_json,
)


def valid_pass_report():
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


def valid_fail_report():
    return {
        "quality_gate": {
            "valid": False,
            "status": "FAIL",
            "validation_errors": ["Evidence verification failed."],
            "accepted": False,
        },
        "valid": True,
        "status": "PASS",
        "errors": [],
    }


def test_valid_report_structure():
    assert validate_exported_quality_gate_report_structure(
        valid_pass_report()
    )["valid"] is True


def test_non_dictionary_structure_rejected():
    result = validate_exported_quality_gate_report_structure([])
    assert result["valid"] is False


def test_missing_required_field_rejected():
    report = valid_pass_report()
    del report["status"]

    result = validate_exported_quality_gate_report_structure(report)
    assert result["valid"] is False
    assert any("status" in error for error in result["errors"])


def test_valid_report_values():
    assert validate_exported_quality_gate_report_values(
        valid_pass_report()
    )["valid"] is True


def test_quality_gate_must_be_dictionary():
    report = valid_pass_report()
    report["quality_gate"] = []

    assert validate_exported_quality_gate_report_values(
        report
    )["valid"] is False


def test_valid_field_must_be_boolean():
    report = valid_pass_report()
    report["valid"] = "true"

    assert validate_exported_quality_gate_report_values(
        report
    )["valid"] is False


def test_status_must_be_allowed_value():
    report = valid_pass_report()
    report["status"] = "UNKNOWN"

    assert validate_exported_quality_gate_report_values(
        report
    )["valid"] is False


def test_errors_must_be_list():
    report = valid_pass_report()
    report["errors"] = "none"

    assert validate_exported_quality_gate_report_values(
        report
    )["valid"] is False


def test_error_items_must_be_strings():
    report = valid_pass_report()
    report["errors"] = [123]

    assert validate_exported_quality_gate_report_values(
        report
    )["valid"] is False


def test_consistent_pass_report():
    assert validate_exported_quality_gate_report_consistency(
        valid_pass_report()
    )["valid"] is True


def test_consistent_report_with_failed_underlying_gate():
    assert validate_exported_quality_gate_report_consistency(
        valid_fail_report()
    )["valid"] is True


def test_pass_status_with_invalid_report_rejected():
    report = valid_pass_report()
    report["valid"] = False

    assert validate_exported_quality_gate_report_consistency(
        report
    )["valid"] is False


def test_fail_status_with_valid_report_rejected():
    report = valid_pass_report()
    report["status"] = "FAIL"

    assert validate_exported_quality_gate_report_consistency(
        report
    )["valid"] is False


def test_valid_report_cannot_contain_errors():
    report = valid_pass_report()
    report["errors"] = ["Unexpected error."]

    assert validate_exported_quality_gate_report_consistency(
        report
    )["valid"] is False


def test_invalid_report_requires_errors():
    report = valid_pass_report()
    report["valid"] = False
    report["status"] = "FAIL"

    assert validate_exported_quality_gate_report_consistency(
        report
    )["valid"] is False


def test_complete_validation_returns_pass():
    result = validate_exported_quality_gate_report(valid_pass_report())

    assert result == {"valid": True, "status": "PASS", "errors": []}


def test_complete_validation_returns_fail_for_invalid_record():
    report = valid_pass_report()
    report["status"] = "UNKNOWN"

    result = validate_exported_quality_gate_report(report)
    assert result["valid"] is False
    assert result["status"] == "FAIL"
    assert result["errors"]


def test_validate_json_file(tmp_path):
    path = tmp_path / "report.json"
    path.write_text(json.dumps(valid_pass_report()), encoding="utf-8")

    result = validate_exported_quality_gate_report_json(str(path))
    assert result["valid"] is True
    assert result["status"] == "PASS"


def test_missing_json_file_returns_fail(tmp_path):
    path = tmp_path / "missing.json"

    result = validate_exported_quality_gate_report_json(str(path))
    assert result["valid"] is False
    assert result["status"] == "FAIL"


def test_malformed_json_returns_fail(tmp_path):
    path = tmp_path / "malformed.json"
    path.write_text("{not valid json", encoding="utf-8")

    result = validate_exported_quality_gate_report_json(str(path))
    assert result["valid"] is False
    assert result["status"] == "FAIL"


def test_json_validation_rejects_wrong_top_level_type(tmp_path):
    path = tmp_path / "list.json"
    path.write_text(json.dumps(["not", "a", "report"]), encoding="utf-8")

    result = validate_exported_quality_gate_report_json(str(path))
    assert result["valid"] is False
    assert result["status"] == "FAIL"