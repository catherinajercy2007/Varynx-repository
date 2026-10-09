
import json

import pytest

from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation_report_export_validation_report_export_quality_gate_export_validation_report import (
    generate_exported_validation_quality_gate_validation_report,
)
from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation_report_export_validation_report_export_quality_gate_export_validation_report_export import (
    validation_report_to_json_dict,
    validation_report_to_json,
    save_exported_validation_quality_gate_validation_report,
    load_exported_validation_quality_gate_validation_report,
    generate_and_export_validation_quality_gate_report,
    export_validation_quality_gate_report_json,
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


def test_report_to_json_dict_contains_expected_fields():
    report = generate_exported_validation_quality_gate_validation_report(
        valid_pass_gate()
    )
    result = validation_report_to_json_dict(report)
    assert set(result) == {"quality_gate", "valid", "status", "errors"}


def test_report_to_json_dict_preserves_quality_gate():
    gate = valid_pass_gate()
    report = generate_exported_validation_quality_gate_validation_report(
        gate
    )
    assert validation_report_to_json_dict(report)["quality_gate"] == gate


def test_valid_report_serializes_to_json():
    report = generate_exported_validation_quality_gate_validation_report(
        valid_pass_gate()
    )
    result = json.loads(validation_report_to_json(report))
    assert result["valid"] is True
    assert result["status"] == "PASS"


def test_invalid_report_serializes_to_json():
    report = generate_exported_validation_quality_gate_validation_report(
        invalid_gate()
    )
    result = json.loads(validation_report_to_json(report))
    assert result["valid"] is False
    assert result["status"] == "FAIL"
    assert result["errors"]


def test_json_uses_requested_indentation():
    report = generate_exported_validation_quality_gate_validation_report(
        valid_pass_gate()
    )
    result = validation_report_to_json(report, indent=4)
    assert "\n    " in result


def test_json_output_is_deterministic():
    report = generate_exported_validation_quality_gate_validation_report(
        valid_pass_gate()
    )
    assert validation_report_to_json(report) == validation_report_to_json(
        report
    )


def test_save_creates_json_file(tmp_path):
    report = generate_exported_validation_quality_gate_validation_report(
        valid_pass_gate()
    )
    target = tmp_path / "report.json"
    result = save_exported_validation_quality_gate_validation_report(
        report, str(target)
    )
    assert result == target
    assert target.is_file()


def test_save_creates_parent_directories(tmp_path):
    report = generate_exported_validation_quality_gate_validation_report(
        valid_pass_gate()
    )
    target = tmp_path / "nested" / "reports" / "report.json"
    save_exported_validation_quality_gate_validation_report(
        report, str(target)
    )
    assert target.is_file()


def test_saved_file_contains_valid_json(tmp_path):
    report = generate_exported_validation_quality_gate_validation_report(
        valid_pass_gate()
    )
    target = tmp_path / "report.json"
    save_exported_validation_quality_gate_validation_report(
        report, str(target)
    )
    result = json.loads(target.read_text(encoding="utf-8"))
    assert result["valid"] is True


def test_load_returns_dictionary(tmp_path):
    target = tmp_path / "report.json"
    target.write_text(
        json.dumps({
            "quality_gate": valid_pass_gate(),
            "valid": True,
            "status": "PASS",
            "errors": [],
        }),
        encoding="utf-8",
    )
    result = load_exported_validation_quality_gate_validation_report(
        str(target)
    )
    assert isinstance(result, dict)


def test_save_and_load_round_trip(tmp_path):
    report = generate_exported_validation_quality_gate_validation_report(
        valid_pass_gate()
    )
    target = tmp_path / "report.json"
    save_exported_validation_quality_gate_validation_report(
        report, str(target)
    )
    loaded = load_exported_validation_quality_gate_validation_report(
        str(target)
    )
    assert loaded == validation_report_to_json_dict(report)


def test_failed_underlying_gate_can_have_valid_report(tmp_path):
    report = generate_exported_validation_quality_gate_validation_report(
        valid_fail_gate()
    )
    target = tmp_path / "failed-gate-report.json"
    save_exported_validation_quality_gate_validation_report(
        report, str(target)
    )
    loaded = load_exported_validation_quality_gate_validation_report(
        str(target)
    )
    assert loaded["valid"] is True
    assert loaded["status"] == "PASS"
    assert loaded["quality_gate"]["accepted"] is False


def test_invalid_record_report_is_exported(tmp_path):
    target = tmp_path / "invalid-report.json"
    result = generate_and_export_validation_quality_gate_report(
        invalid_gate(), str(target)
    )
    loaded = load_exported_validation_quality_gate_validation_report(
        str(result)
    )
    assert loaded["valid"] is False
    assert loaded["status"] == "FAIL"
    assert loaded["errors"]


def test_generate_and_export_returns_path(tmp_path):
    target = tmp_path / "generated.json"
    result = generate_and_export_validation_quality_gate_report(
        valid_pass_gate(), str(target)
    )
    assert result == target
    assert target.exists()


def test_direct_json_export_returns_json_string():
    result = export_validation_quality_gate_report_json(valid_pass_gate())
    decoded = json.loads(result)
    assert decoded["valid"] is True
    assert decoded["status"] == "PASS"


def test_direct_json_export_handles_invalid_record():
    result = export_validation_quality_gate_report_json(invalid_gate())
    decoded = json.loads(result)
    assert decoded["valid"] is False
    assert decoded["status"] == "FAIL"


def test_extra_metadata_is_preserved_in_export(tmp_path):
    gate = valid_pass_gate()
    gate["metadata"] = {"source": "day88"}
    target = tmp_path / "metadata.json"
    generate_and_export_validation_quality_gate_report(
        gate, str(target)
    )
    loaded = load_exported_validation_quality_gate_validation_report(
        str(target)
    )
    assert loaded["quality_gate"]["metadata"] == {"source": "day88"}


def test_custom_indentation_is_used_when_saving(tmp_path):
    report = generate_exported_validation_quality_gate_validation_report(
        valid_pass_gate()
    )
    target = tmp_path / "indented.json"
    save_exported_validation_quality_gate_validation_report(
        report, str(target), indent=4
    )
    assert "\n    " in target.read_text(encoding="utf-8")


def test_load_missing_file_raises_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_exported_validation_quality_gate_validation_report(
            str(tmp_path / "missing.json")
        )


def test_load_malformed_json_raises_error(tmp_path):
    target = tmp_path / "malformed.json"
    target.write_text("{not-json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        load_exported_validation_quality_gate_validation_report(
            str(target)
        )


def test_repeated_exports_are_identical():
    gate = valid_pass_gate()
    first = export_validation_quality_gate_report_json(gate)
    second = export_validation_quality_gate_report_json(gate)
    assert first == second