import json

from evaluation.evidence_quality_summary_quality_gate_validation_report import (
    generate_evidence_quality_summary_quality_gate_validation_report,
)
from evaluation.evidence_quality_summary_quality_gate_validation_report_export import (
    export_quality_gate_validation_report_json,
    generate_and_export_quality_gate_validation_report,
    load_quality_gate_validation_report,
    save_quality_gate_validation_report,
    validation_report_to_json,
    validation_report_to_json_dict,
)


def create_valid_pass_quality_gate():
    return {
        "valid": True,
        "status": "PASS",
        "validation_errors": [],
        "accepted": True,
        "artifact_count": 2,
        "verified_artifact_count": 2,
    }


def create_valid_fail_quality_gate():
    return {
        "valid": False,
        "status": "FAIL",
        "validation_errors": [
            "Evidence artifact integrity verification failed."
        ],
        "accepted": False,
        "artifact_count": 2,
        "verified_artifact_count": 1,
    }


def test_validation_report_to_json_dict_contains_expected_fields():
    quality_gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            quality_gate
        )
    )

    data = validation_report_to_json_dict(report)

    assert data["quality_gate"] == quality_gate
    assert data["valid"] is True
    assert data["status"] == "PASS"
    assert data["errors"] == []


def test_validation_report_to_json_dict_returns_dict():
    quality_gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            quality_gate
        )
    )

    result = validation_report_to_json_dict(report)

    assert isinstance(result, dict)


def test_validation_report_to_json_is_valid_json():
    quality_gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            quality_gate
        )
    )

    result = validation_report_to_json(report)

    parsed = json.loads(result)

    assert parsed["status"] == "PASS"


def test_validation_report_to_json_supports_custom_indent():
    quality_gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            quality_gate
        )
    )

    result = validation_report_to_json(
        report,
        indent=4,
    )

    assert isinstance(result, str)
    assert json.loads(result)["valid"] is True


def test_save_quality_gate_validation_report_creates_file(tmp_path):
    quality_gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            quality_gate
        )
    )

    output = tmp_path / "validation_report.json"

    saved = save_quality_gate_validation_report(
        report,
        str(output),
    )

    assert saved == output
    assert output.exists()


def test_saved_report_contains_valid_json(tmp_path):
    quality_gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            quality_gate
        )
    )

    output = tmp_path / "nested" / "validation_report.json"

    save_quality_gate_validation_report(
        report,
        str(output),
    )

    loaded = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert loaded["status"] == "PASS"


def test_save_report_creates_parent_directories(tmp_path):
    quality_gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            quality_gate
        )
    )

    output = (
        tmp_path
        / "reports"
        / "quality"
        / "validation.json"
    )

    save_quality_gate_validation_report(
        report,
        str(output),
    )

    assert output.exists()


def test_load_quality_gate_validation_report(tmp_path):
    quality_gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            quality_gate
        )
    )

    output = tmp_path / "validation.json"

    save_quality_gate_validation_report(
        report,
        str(output),
    )

    loaded = load_quality_gate_validation_report(
        str(output)
    )

    assert loaded["quality_gate"] == quality_gate
    assert loaded["valid"] is True
    assert loaded["status"] == "PASS"


def test_load_returns_dictionary(tmp_path):
    quality_gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            quality_gate
        )
    )

    output = tmp_path / "validation.json"

    save_quality_gate_validation_report(
        report,
        str(output),
    )

    loaded = load_quality_gate_validation_report(
        str(output)
    )

    assert isinstance(loaded, dict)


def test_round_trip_preserves_report(tmp_path):
    quality_gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            quality_gate
        )
    )

    output = tmp_path / "round_trip.json"

    save_quality_gate_validation_report(
        report,
        str(output),
    )

    loaded = load_quality_gate_validation_report(
        str(output)
    )

    assert loaded == validation_report_to_json_dict(
        report
    )


def test_fail_quality_gate_round_trip(tmp_path):
    quality_gate = create_valid_fail_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            quality_gate
        )
    )

    output = tmp_path / "fail_report.json"

    save_quality_gate_validation_report(
        report,
        str(output),
    )

    loaded = load_quality_gate_validation_report(
        str(output)
    )

    assert loaded["quality_gate"] == quality_gate
    assert loaded["valid"] is True
    assert loaded["status"] == "PASS"


def test_generate_and_export_creates_report(tmp_path):
    quality_gate = create_valid_pass_quality_gate()

    output = tmp_path / "generated.json"

    result = generate_and_export_quality_gate_validation_report(
        quality_gate,
        str(output),
    )

    assert result == output
    assert output.exists()


def test_generate_and_export_preserves_quality_gate(tmp_path):
    quality_gate = create_valid_pass_quality_gate()

    output = tmp_path / "generated.json"

    generate_and_export_quality_gate_validation_report(
        quality_gate,
        str(output),
    )

    loaded = load_quality_gate_validation_report(
        str(output)
    )

    assert loaded["quality_gate"] == quality_gate


def test_export_quality_gate_validation_report_json():
    quality_gate = create_valid_pass_quality_gate()

    result = export_quality_gate_validation_report_json(
        quality_gate
    )

    parsed = json.loads(result)

    assert parsed["quality_gate"] == quality_gate
    assert parsed["valid"] is True
    assert parsed["status"] == "PASS"


def test_export_json_supports_custom_indent():
    quality_gate = create_valid_pass_quality_gate()

    result = export_quality_gate_validation_report_json(
        quality_gate,
        indent=4,
    )

    parsed = json.loads(result)

    assert parsed["valid"] is True


def test_export_fail_quality_gate():
    quality_gate = create_valid_fail_quality_gate()

    result = export_quality_gate_validation_report_json(
        quality_gate
    )

    parsed = json.loads(result)

    assert parsed["quality_gate"] == quality_gate
    assert parsed["valid"] is True
    assert parsed["status"] == "PASS"


def test_json_output_is_sorted_and_stable():
    quality_gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            quality_gate
        )
    )

    first = validation_report_to_json(report)
    second = validation_report_to_json(report)

    assert first == second


def test_json_contains_quality_gate():
    quality_gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            quality_gate
        )
    )

    result = json.loads(
        validation_report_to_json(report)
    )

    assert "quality_gate" in result


def test_json_contains_validation_status():
    quality_gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            quality_gate
        )
    )

    result = json.loads(
        validation_report_to_json(report)
    )

    assert result["valid"] is True
    assert result["status"] == "PASS"


def test_json_contains_errors_list():
    quality_gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            quality_gate
        )
    )

    result = json.loads(
        validation_report_to_json(report)
    )

    assert isinstance(result["errors"], list)