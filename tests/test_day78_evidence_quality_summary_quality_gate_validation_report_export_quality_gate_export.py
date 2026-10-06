import json

from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate import (
    evaluate_exported_validation_report_quality_gate,
)
from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export import (
    evaluate_and_export_validation_quality_gate,
    export_validation_quality_gate_json,
    load_export_validation_quality_gate,
    quality_gate_to_json,
    quality_gate_to_json_dict,
    save_export_validation_quality_gate,
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


def test_quality_gate_to_json_dict_returns_dictionary():
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    data = quality_gate_to_json_dict(result)

    assert isinstance(data, dict)


def test_quality_gate_to_json_dict_contains_expected_fields():
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    data = quality_gate_to_json_dict(result)

    assert set(data.keys()) == {
        "valid",
        "status",
        "validation_errors",
        "accepted",
    }


def test_quality_gate_to_json_dict_preserves_values():
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    data = quality_gate_to_json_dict(result)

    assert data["valid"] is True
    assert data["status"] == "PASS"
    assert data["validation_errors"] == []
    assert data["accepted"] is True


def test_quality_gate_to_json_returns_string():
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    output = quality_gate_to_json(result)

    assert isinstance(output, str)


def test_quality_gate_to_json_is_valid_json():
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    output = quality_gate_to_json(result)

    parsed = json.loads(output)

    assert parsed["status"] == "PASS"


def test_quality_gate_to_json_supports_custom_indent():
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    output = quality_gate_to_json(
        result,
        indent=4,
    )

    assert json.loads(output)["valid"] is True


def test_save_quality_gate_creates_file(tmp_path):
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    output = tmp_path / "quality_gate.json"

    saved = save_export_validation_quality_gate(
        result,
        str(output),
    )

    assert saved == output
    assert output.exists()


def test_save_quality_gate_creates_parent_directories(tmp_path):
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    output = (
        tmp_path
        / "reports"
        / "quality"
        / "gate.json"
    )

    save_export_validation_quality_gate(
        result,
        str(output),
    )

    assert output.exists()


def test_saved_quality_gate_contains_valid_json(tmp_path):
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    output = tmp_path / "quality_gate.json"

    save_export_validation_quality_gate(
        result,
        str(output),
    )

    parsed = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert parsed["status"] == "PASS"


def test_load_quality_gate_returns_dictionary(tmp_path):
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    output = tmp_path / "quality_gate.json"

    save_export_validation_quality_gate(
        result,
        str(output),
    )

    loaded = load_export_validation_quality_gate(
        str(output)
    )

    assert isinstance(loaded, dict)


def test_load_quality_gate_preserves_values(tmp_path):
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    output = tmp_path / "quality_gate.json"

    save_export_validation_quality_gate(
        result,
        str(output),
    )

    loaded = load_export_validation_quality_gate(
        str(output)
    )

    assert loaded["valid"] is True
    assert loaded["status"] == "PASS"
    assert loaded["accepted"] is True


def test_round_trip_preserves_quality_gate(tmp_path):
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    output = tmp_path / "round_trip.json"

    save_export_validation_quality_gate(
        result,
        str(output),
    )

    loaded = load_export_validation_quality_gate(
        str(output)
    )

    assert loaded == quality_gate_to_json_dict(
        result
    )


def test_rejected_underlying_gate_round_trip(tmp_path):
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_rejected_gate_report()
    )

    output = tmp_path / "rejected_gate.json"

    save_export_validation_quality_gate(
        result,
        str(output),
    )

    loaded = load_export_validation_quality_gate(
        str(output)
    )

    assert loaded["valid"] is True
    assert loaded["status"] == "PASS"
    assert loaded["accepted"] is True


def test_failed_quality_gate_can_be_exported(tmp_path):
    report = create_valid_pass_report()
    report["status"] = "INVALID"

    result = evaluate_exported_validation_report_quality_gate(
        report
    )

    output = tmp_path / "failed_gate.json"

    save_export_validation_quality_gate(
        result,
        str(output),
    )

    loaded = load_export_validation_quality_gate(
        str(output)
    )

    assert loaded["valid"] is False
    assert loaded["status"] == "FAIL"
    assert loaded["accepted"] is False
    assert loaded["validation_errors"]


def test_evaluate_and_export_creates_file(tmp_path):
    output = tmp_path / "generated.json"

    result = evaluate_and_export_validation_quality_gate(
        create_valid_pass_report(),
        str(output),
    )

    assert result == output
    assert output.exists()


def test_evaluate_and_export_preserves_pass_result(tmp_path):
    output = tmp_path / "generated.json"

    evaluate_and_export_validation_quality_gate(
        create_valid_pass_report(),
        str(output),
    )

    loaded = load_export_validation_quality_gate(
        str(output)
    )

    assert loaded["valid"] is True
    assert loaded["status"] == "PASS"


def test_export_validation_quality_gate_json_returns_json():
    output = export_validation_quality_gate_json(
        create_valid_pass_report()
    )

    parsed = json.loads(output)

    assert parsed["valid"] is True
    assert parsed["status"] == "PASS"


def test_export_validation_quality_gate_json_supports_indent():
    output = export_validation_quality_gate_json(
        create_valid_pass_report(),
        indent=4,
    )

    parsed = json.loads(output)

    assert parsed["accepted"] is True


def test_export_rejected_underlying_gate():
    output = export_validation_quality_gate_json(
        create_valid_rejected_gate_report()
    )

    parsed = json.loads(output)

    assert parsed["valid"] is True
    assert parsed["status"] == "PASS"


def test_json_output_is_deterministic():
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    first = quality_gate_to_json(result)
    second = quality_gate_to_json(result)

    assert first == second