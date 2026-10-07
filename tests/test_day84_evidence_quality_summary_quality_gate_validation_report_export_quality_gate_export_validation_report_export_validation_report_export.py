import json

from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation_report_export_validation_report import (
    generate_exported_validation_report_export_validation_report,
)

from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation_report_export_validation_report_export import (
    export_validation_report_json,
    generate_and_export_validation_report,
    load_exported_validation_report_export_validation_report,
    save_exported_validation_report_export_validation_report,
    validation_report_to_json,
    validation_report_to_json_dict,
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
    report = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    result = validation_report_to_json_dict(report)

    assert isinstance(result, dict)


def test_json_dict_contains_expected_fields():
    report = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    result = validation_report_to_json_dict(report)

    assert set(result.keys()) == {
        "report",
        "valid",
        "status",
        "errors",
    }


def test_json_dict_preserves_report():
    source = create_valid_pass_report()

    report = (
        generate_exported_validation_report_export_validation_report(
            source
        )
    )

    result = validation_report_to_json_dict(report)

    assert result["report"] == source


def test_json_dict_preserves_valid_value():
    report = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    result = validation_report_to_json_dict(report)

    assert result["valid"] is True


def test_json_dict_preserves_status():
    report = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    result = validation_report_to_json_dict(report)

    assert result["status"] == "PASS"


def test_json_dict_preserves_errors():
    report = (
        generate_exported_validation_report_export_validation_report(
            create_invalid_report()
        )
    )

    result = validation_report_to_json_dict(report)

    assert result["errors"] == report.errors


def test_json_returns_string():
    report = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    result = validation_report_to_json(report)

    assert isinstance(result, str)


def test_json_is_valid_json():
    report = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    result = validation_report_to_json(report)

    parsed = json.loads(result)

    assert parsed["valid"] is True
    assert parsed["status"] == "PASS"


def test_json_supports_custom_indent():
    report = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    result = validation_report_to_json(
        report,
        indent=4,
    )

    parsed = json.loads(result)

    assert parsed["valid"] is True


def test_save_creates_file(tmp_path):
    report = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    output = tmp_path / "validation_report.json"

    saved = (
        save_exported_validation_report_export_validation_report(
            report,
            str(output),
        )
    )

    assert saved == output
    assert output.exists()


def test_save_creates_parent_directories(tmp_path):
    report = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    output = (
        tmp_path
        / "reports"
        / "validation"
        / "export"
        / "report.json"
    )

    save_exported_validation_report_export_validation_report(
        report,
        str(output),
    )

    assert output.exists()


def test_saved_file_contains_valid_json(tmp_path):
    report = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    output = tmp_path / "report.json"

    save_exported_validation_report_export_validation_report(
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
    report = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    output = tmp_path / "report.json"

    save_exported_validation_report_export_validation_report(
        report,
        str(output),
    )

    loaded = (
        load_exported_validation_report_export_validation_report(
            str(output)
        )
    )

    assert isinstance(loaded, dict)


def test_load_preserves_values(tmp_path):
    report = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    output = tmp_path / "report.json"

    save_exported_validation_report_export_validation_report(
        report,
        str(output),
    )

    loaded = (
        load_exported_validation_report_export_validation_report(
            str(output)
        )
    )

    assert loaded["valid"] is True
    assert loaded["status"] == "PASS"
    assert loaded["errors"] == []


def test_round_trip_preserves_report(tmp_path):
    report = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    output = tmp_path / "round_trip.json"

    save_exported_validation_report_export_validation_report(
        report,
        str(output),
    )

    loaded = (
        load_exported_validation_report_export_validation_report(
            str(output)
        )
    )

    assert loaded == validation_report_to_json_dict(
        report
    )


def test_failed_underlying_gate_can_be_exported(tmp_path):
    report = (
        generate_exported_validation_report_export_validation_report(
            create_valid_fail_underlying_gate_report()
        )
    )

    output = tmp_path / "failed_underlying_gate.json"

    save_exported_validation_report_export_validation_report(
        report,
        str(output),
    )

    loaded = (
        load_exported_validation_report_export_validation_report(
            str(output)
        )
    )

    assert loaded["valid"] is True
    assert loaded["status"] == "PASS"
    assert loaded["errors"] == []
    assert loaded["report"]["quality_gate"]["valid"] is False
    assert loaded["report"]["quality_gate"]["status"] == "FAIL"


def test_invalid_report_can_be_exported(tmp_path):
    report = (
        generate_exported_validation_report_export_validation_report(
            create_invalid_report()
        )
    )

    output = tmp_path / "invalid_report.json"

    save_exported_validation_report_export_validation_report(
        report,
        str(output),
    )

    loaded = (
        load_exported_validation_report_export_validation_report(
            str(output)
        )
    )

    assert loaded["valid"] is False
    assert loaded["status"] == "FAIL"
    assert loaded["errors"]


def test_generate_and_export_creates_file(tmp_path):
    output = tmp_path / "generated.json"

    result = generate_and_export_validation_report(
        create_valid_pass_report(),
        str(output),
    )

    assert result == output
    assert output.exists()


def test_generate_and_export_preserves_result(tmp_path):
    output = tmp_path / "generated.json"

    generate_and_export_validation_report(
        create_valid_pass_report(),
        str(output),
    )

    loaded = (
        load_exported_validation_report_export_validation_report(
            str(output)
        )
    )

    assert loaded["valid"] is True
    assert loaded["status"] == "PASS"


def test_direct_json_export_returns_valid_json():
    result = export_validation_report_json(
        create_valid_pass_report()
    )

    parsed = json.loads(result)

    assert parsed["valid"] is True
    assert parsed["status"] == "PASS"


def test_direct_json_export_supports_indent():
    result = export_validation_report_json(
        create_valid_pass_report(),
        indent=4,
    )

    parsed = json.loads(result)

    assert parsed["valid"] is True


def test_direct_export_preserves_failed_underlying_gate():
    result = export_validation_report_json(
        create_valid_fail_underlying_gate_report()
    )

    parsed = json.loads(result)

    assert parsed["valid"] is True
    assert parsed["status"] == "PASS"
    assert parsed["report"]["quality_gate"]["valid"] is False
    assert parsed["report"]["quality_gate"]["status"] == "FAIL"


def test_json_output_is_deterministic():
    report = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    first = validation_report_to_json(report)
    second = validation_report_to_json(report)

    assert first == second


def test_loaded_report_matches_direct_conversion(tmp_path):
    report = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    output = tmp_path / "comparison.json"

    save_exported_validation_report_export_validation_report(
        report,
        str(output),
    )

    loaded = (
        load_exported_validation_report_export_validation_report(
            str(output)
        )
    )

    direct = validation_report_to_json_dict(report)

    assert loaded == direct


def test_nested_report_is_preserved_after_round_trip(tmp_path):
    report = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    output = tmp_path / "nested.json"

    save_exported_validation_report_export_validation_report(
        report,
        str(output),
    )

    loaded = (
        load_exported_validation_report_export_validation_report(
            str(output)
        )
    )

    assert loaded["report"]["quality_gate"]["accepted"] is True