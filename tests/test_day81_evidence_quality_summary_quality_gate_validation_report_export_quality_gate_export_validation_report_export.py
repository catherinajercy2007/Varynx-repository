import json

from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation_report import (
    generate_exported_quality_gate_validation_report,
)

from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation_report_export import (
    export_quality_gate_validation_report_json,
    generate_and_export_quality_gate_validation_report,
    load_exported_quality_gate_validation_report,
    save_exported_quality_gate_validation_report,
    validation_report_to_json,
    validation_report_to_json_dict,
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


def test_json_dict_returns_dictionary():
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    result = validation_report_to_json_dict(report)

    assert isinstance(result, dict)


def test_json_dict_contains_expected_fields():
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    result = validation_report_to_json_dict(report)

    assert set(result.keys()) == {
        "quality_gate",
        "valid",
        "status",
        "errors",
    }


def test_json_dict_preserves_valid_values():
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    result = validation_report_to_json_dict(report)

    assert result["valid"] is True
    assert result["status"] == "PASS"
    assert result["errors"] == []


def test_json_dict_preserves_quality_gate():
    quality_gate = create_valid_pass_quality_gate()

    report = generate_exported_quality_gate_validation_report(
        quality_gate
    )

    result = validation_report_to_json_dict(report)

    assert result["quality_gate"] == quality_gate


def test_json_returns_string():
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    result = validation_report_to_json(report)

    assert isinstance(result, str)


def test_json_is_valid_json():
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    result = validation_report_to_json(report)

    parsed = json.loads(result)

    assert parsed["valid"] is True
    assert parsed["status"] == "PASS"


def test_json_supports_custom_indent():
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    result = validation_report_to_json(
        report,
        indent=4,
    )

    assert json.loads(result)["valid"] is True


def test_save_creates_file(tmp_path):
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    output = tmp_path / "validation_report.json"

    saved = save_exported_quality_gate_validation_report(
        report,
        str(output),
    )

    assert saved == output
    assert output.exists()


def test_save_creates_parent_directories(tmp_path):
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    output = (
        tmp_path
        / "reports"
        / "quality"
        / "validation"
        / "report.json"
    )

    save_exported_quality_gate_validation_report(
        report,
        str(output),
    )

    assert output.exists()


def test_saved_file_contains_valid_json(tmp_path):
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    output = tmp_path / "report.json"

    save_exported_quality_gate_validation_report(
        report,
        str(output),
    )

    parsed = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert parsed["status"] == "PASS"


def test_load_returns_dictionary(tmp_path):
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    output = tmp_path / "report.json"

    save_exported_quality_gate_validation_report(
        report,
        str(output),
    )

    loaded = load_exported_quality_gate_validation_report(
        str(output)
    )

    assert isinstance(loaded, dict)


def test_load_preserves_values(tmp_path):
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    output = tmp_path / "report.json"

    save_exported_quality_gate_validation_report(
        report,
        str(output),
    )

    loaded = load_exported_quality_gate_validation_report(
        str(output)
    )

    assert loaded["valid"] is True
    assert loaded["status"] == "PASS"
    assert loaded["errors"] == []


def test_round_trip_preserves_report(tmp_path):
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    output = tmp_path / "round_trip.json"

    save_exported_quality_gate_validation_report(
        report,
        str(output),
    )

    loaded = load_exported_quality_gate_validation_report(
        str(output)
    )

    assert loaded == validation_report_to_json_dict(
        report
    )


def test_fail_quality_gate_report_can_be_exported(tmp_path):
    report = generate_exported_quality_gate_validation_report(
        create_valid_fail_quality_gate()
    )

    output = tmp_path / "failed_underlying_gate.json"

    save_exported_quality_gate_validation_report(
        report,
        str(output),
    )

    loaded = load_exported_quality_gate_validation_report(
        str(output)
    )

    assert loaded["valid"] is True
    assert loaded["status"] == "PASS"
    assert loaded["errors"] == []
    assert loaded["quality_gate"]["valid"] is False
    assert loaded["quality_gate"]["status"] == "FAIL"


def test_invalid_report_can_be_exported(tmp_path):
    quality_gate = create_valid_pass_quality_gate()
    quality_gate["status"] = "INVALID"

    report = generate_exported_quality_gate_validation_report(
        quality_gate
    )

    output = tmp_path / "invalid_report.json"

    save_exported_quality_gate_validation_report(
        report,
        str(output),
    )

    loaded = load_exported_quality_gate_validation_report(
        str(output)
    )

    assert loaded["valid"] is False
    assert loaded["status"] == "FAIL"
    assert loaded["errors"]


def test_generate_and_export_creates_file(tmp_path):
    output = tmp_path / "generated.json"

    result = generate_and_export_quality_gate_validation_report(
        create_valid_pass_quality_gate(),
        str(output),
    )

    assert result == output
    assert output.exists()


def test_generate_and_export_preserves_result(tmp_path):
    output = tmp_path / "generated.json"

    generate_and_export_quality_gate_validation_report(
        create_valid_pass_quality_gate(),
        str(output),
    )

    loaded = load_exported_quality_gate_validation_report(
        str(output)
    )

    assert loaded["valid"] is True
    assert loaded["status"] == "PASS"


def test_direct_json_export_returns_valid_json():
    result = export_quality_gate_validation_report_json(
        create_valid_pass_quality_gate()
    )

    parsed = json.loads(result)

    assert parsed["valid"] is True
    assert parsed["status"] == "PASS"


def test_direct_json_export_supports_indent():
    result = export_quality_gate_validation_report_json(
        create_valid_pass_quality_gate(),
        indent=4,
    )

    parsed = json.loads(result)

    assert parsed["valid"] is True


def test_direct_export_preserves_fail_underlying_gate():
    result = export_quality_gate_validation_report_json(
        create_valid_fail_quality_gate()
    )

    parsed = json.loads(result)

    assert parsed["valid"] is True
    assert parsed["status"] == "PASS"
    assert parsed["quality_gate"]["valid"] is False
    assert parsed["quality_gate"]["status"] == "FAIL"


def test_json_output_is_deterministic():
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    first = validation_report_to_json(report)
    second = validation_report_to_json(report)

    assert first == second


def test_loaded_report_matches_direct_conversion(tmp_path):
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    output = tmp_path / "comparison.json"

    save_exported_quality_gate_validation_report(
        report,
        str(output),
    )

    loaded = load_exported_quality_gate_validation_report(
        str(output)
    )

    direct = validation_report_to_json_dict(report)

    assert loaded == direct