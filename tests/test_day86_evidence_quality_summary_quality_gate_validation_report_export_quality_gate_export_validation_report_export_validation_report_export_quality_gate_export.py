import json

from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation_report_export_validation_report_export_quality_gate import (
    evaluate_exported_validation_report_export_quality_gate,
)

from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation_report_export_validation_report_export_quality_gate_export import (
    evaluate_and_export_validation_report_quality_gate,
    export_validation_report_quality_gate_json,
    load_exported_validation_report_export_quality_gate,
    quality_gate_to_json,
    quality_gate_to_json_dict,
    save_exported_validation_report_export_quality_gate,
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


def create_valid_fail_underlying_gate_report():
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


def create_invalid_report():
    return {
        "quality_gate": {
            "valid": True,
            "status": "PASS",
            "validation_errors": [],
            "accepted": True,
        },
        "valid": True,
        "status": "INVALID",
        "errors": [],
    }


def test_json_dict_returns_dictionary():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    converted = quality_gate_to_json_dict(result)

    assert isinstance(converted, dict)


def test_json_dict_contains_expected_fields():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    converted = quality_gate_to_json_dict(result)

    assert set(converted.keys()) == {
        "valid",
        "status",
        "validation_errors",
        "accepted",
    }


def test_json_dict_preserves_valid_value():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    converted = quality_gate_to_json_dict(result)

    assert converted["valid"] is True


def test_json_dict_preserves_status():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    converted = quality_gate_to_json_dict(result)

    assert converted["status"] == "PASS"


def test_json_dict_preserves_accepted_value():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    converted = quality_gate_to_json_dict(result)

    assert converted["accepted"] is True


def test_json_dict_preserves_validation_errors():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_invalid_report()
        )
    )

    converted = quality_gate_to_json_dict(result)

    assert converted["validation_errors"] == (
        result.validation_errors
    )


def test_json_returns_string():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    output = quality_gate_to_json(result)

    assert isinstance(output, str)


def test_json_is_valid_json():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    output = quality_gate_to_json(result)

    parsed = json.loads(output)

    assert parsed["valid"] is True
    assert parsed["status"] == "PASS"


def test_json_supports_custom_indent():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    output = quality_gate_to_json(
        result,
        indent=4,
    )

    parsed = json.loads(output)

    assert parsed["valid"] is True


def test_save_creates_file(tmp_path):
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    output = tmp_path / "quality_gate.json"

    saved = save_exported_validation_report_export_quality_gate(
        result,
        str(output),
    )

    assert saved == output
    assert output.exists()


def test_save_creates_parent_directories(tmp_path):
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    output = (
        tmp_path
        / "reports"
        / "quality"
        / "gate"
        / "result.json"
    )

    save_exported_validation_report_export_quality_gate(
        result,
        str(output),
    )

    assert output.exists()


def test_saved_file_contains_valid_json(tmp_path):
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    output = tmp_path / "quality_gate.json"

    save_exported_validation_report_export_quality_gate(
        result,
        str(output),
    )

    parsed = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert parsed["status"] == "PASS"


def test_load_returns_dictionary(tmp_path):
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    output = tmp_path / "quality_gate.json"

    save_exported_validation_report_export_quality_gate(
        result,
        str(output),
    )

    loaded = load_exported_validation_report_export_quality_gate(
        str(output)
    )

    assert isinstance(loaded, dict)


def test_load_preserves_values(tmp_path):
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    output = tmp_path / "quality_gate.json"

    save_exported_validation_report_export_quality_gate(
        result,
        str(output),
    )

    loaded = load_exported_validation_report_export_quality_gate(
        str(output)
    )

    assert loaded["valid"] is True
    assert loaded["status"] == "PASS"
    assert loaded["accepted"] is True
    assert loaded["validation_errors"] == []


def test_round_trip_preserves_quality_gate(tmp_path):
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    output = tmp_path / "round_trip.json"

    save_exported_validation_report_export_quality_gate(
        result,
        str(output),
    )

    loaded = load_exported_validation_report_export_quality_gate(
        str(output)
    )

    assert loaded == quality_gate_to_json_dict(result)


def test_failed_underlying_gate_can_be_exported(tmp_path):
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_fail_underlying_gate_report()
        )
    )

    output = tmp_path / "failed_underlying_gate.json"

    save_exported_validation_report_export_quality_gate(
        result,
        str(output),
    )

    loaded = load_exported_validation_report_export_quality_gate(
        str(output)
    )

    assert loaded["valid"] is True
    assert loaded["status"] == "PASS"
    assert loaded["accepted"] is True
    assert loaded["validation_errors"] == []


def test_invalid_report_can_be_exported(tmp_path):
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_invalid_report()
        )
    )

    output = tmp_path / "invalid_quality_gate.json"

    save_exported_validation_report_export_quality_gate(
        result,
        str(output),
    )

    loaded = load_exported_validation_report_export_quality_gate(
        str(output)
    )

    assert loaded["valid"] is False
    assert loaded["status"] == "FAIL"
    assert loaded["accepted"] is False
    assert loaded["validation_errors"]


def test_generate_and_export_creates_file(tmp_path):
    output = tmp_path / "generated.json"

    result = evaluate_and_export_validation_report_quality_gate(
        create_valid_pass_report(),
        str(output),
    )

    assert result == output
    assert output.exists()


def test_generate_and_export_preserves_pass_result(tmp_path):
    output = tmp_path / "generated.json"

    evaluate_and_export_validation_report_quality_gate(
        create_valid_pass_report(),
        str(output),
    )

    loaded = load_exported_validation_report_export_quality_gate(
        str(output)
    )

    assert loaded["valid"] is True
    assert loaded["status"] == "PASS"
    assert loaded["accepted"] is True


def test_generate_and_export_preserves_fail_result(tmp_path):
    output = tmp_path / "generated.json"

    evaluate_and_export_validation_report_quality_gate(
        create_invalid_report(),
        str(output),
    )

    loaded = load_exported_validation_report_export_quality_gate(
        str(output)
    )

    assert loaded["valid"] is False
    assert loaded["status"] == "FAIL"
    assert loaded["accepted"] is False


def test_direct_json_export_returns_valid_json():
    output = export_validation_report_quality_gate_json(
        create_valid_pass_report()
    )

    parsed = json.loads(output)

    assert parsed["valid"] is True
    assert parsed["status"] == "PASS"


def test_direct_json_export_supports_indent():
    output = export_validation_report_quality_gate_json(
        create_valid_pass_report(),
        indent=4,
    )

    parsed = json.loads(output)

    assert parsed["valid"] is True


def test_direct_export_preserves_failed_underlying_gate():
    output = export_validation_report_quality_gate_json(
        create_valid_fail_underlying_gate_report()
    )

    parsed = json.loads(output)

    assert parsed["valid"] is True
    assert parsed["status"] == "PASS"
    assert parsed["accepted"] is True


def test_direct_export_preserves_invalid_report():
    output = export_validation_report_quality_gate_json(
        create_invalid_report()
    )

    parsed = json.loads(output)

    assert parsed["valid"] is False
    assert parsed["status"] == "FAIL"
    assert parsed["accepted"] is False
    assert parsed["validation_errors"]


def test_json_output_is_deterministic():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    first = quality_gate_to_json(result)
    second = quality_gate_to_json(result)

    assert first == second


def test_loaded_result_matches_direct_conversion(tmp_path):
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    output = tmp_path / "comparison.json"

    save_exported_validation_report_export_quality_gate(
        result,
        str(output),
    )

    loaded = load_exported_validation_report_export_quality_gate(
        str(output)
    )

    direct = quality_gate_to_json_dict(result)

    assert loaded == direct