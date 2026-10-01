from evaluation.evidence_index import (
    create_evidence_index,
    register_artifact,
)
from evaluation.evidence_quality_report import (
    generate_evidence_quality_report,
)
from evaluation.evidence_quality_report_export import (
    generate_default_evidence_quality_report,
    load_evidence_quality_report,
    report_to_json,
    report_to_json_dict,
    save_default_evidence_quality_report,
    save_evidence_quality_report,
)


def create_valid_report(tmp_path):
    artifact = tmp_path / "report.json"

    artifact.write_text(
        '{"overall_status": "PASS"}',
        encoding="utf-8",
    )

    index = create_evidence_index()

    register_artifact(
        index,
        str(artifact),
    )

    return generate_evidence_quality_report(
        index,
        base_directory=str(tmp_path),
    )


def test_report_to_json_dict(tmp_path):
    report = create_valid_report(tmp_path)

    data = report_to_json_dict(report)

    assert data["overall_status"] == "ACCEPTED"
    assert data["accepted"] is True
    assert data["quality_gate"]["status"] == "PASS"


def test_report_to_json_returns_valid_json(tmp_path):
    report = create_valid_report(tmp_path)

    output = report_to_json(report)

    assert isinstance(output, str)

    import json

    data = json.loads(output)

    assert data["overall_status"] == "ACCEPTED"
    assert data["accepted"] is True


def test_report_to_json_supports_custom_indent(tmp_path):
    report = create_valid_report(tmp_path)

    output = report_to_json(
        report,
        indent=4,
    )

    assert isinstance(output, str)
    assert "    " in output


def test_save_report_creates_file(tmp_path):
    report = create_valid_report(tmp_path)

    output_path = tmp_path / "exports" / "quality_report.json"

    saved = save_evidence_quality_report(
        report,
        str(output_path),
    )

    assert saved == output_path
    assert output_path.exists()


def test_saved_report_contains_expected_data(tmp_path):
    report = create_valid_report(tmp_path)

    output_path = tmp_path / "quality_report.json"

    save_evidence_quality_report(
        report,
        str(output_path),
    )

    data = load_evidence_quality_report(
        str(output_path),
    )

    assert data["overall_status"] == "ACCEPTED"
    assert data["accepted"] is True
    assert data["quality_gate"]["integrity_verified"] is True


def test_load_report_returns_dictionary(tmp_path):
    report = create_valid_report(tmp_path)

    output_path = tmp_path / "quality_report.json"

    save_evidence_quality_report(
        report,
        str(output_path),
    )

    loaded = load_evidence_quality_report(
        str(output_path),
    )

    assert isinstance(loaded, dict)


def test_report_round_trip_preserves_data(tmp_path):
    report = create_valid_report(tmp_path)

    output_path = tmp_path / "quality_report.json"

    save_evidence_quality_report(
        report,
        str(output_path),
    )

    loaded = load_evidence_quality_report(
        str(output_path),
    )

    assert loaded == report_to_json_dict(report)


def test_generate_default_report_returns_report():
    report = generate_default_evidence_quality_report()

    assert report.overall_status == "REJECTED"
    assert report.accepted is False
    assert report.quality_gate["status"] == "FAIL"


def test_default_report_has_empty_evidence_index():
    report = generate_default_evidence_quality_report()

    assert report.evidence_index["format"] == (
        "evaluation-evidence-index-v1"
    )

    assert report.evidence_index["artifacts"] == []


def test_save_default_report(tmp_path):
    output_path = tmp_path / "default_report.json"

    saved = save_default_evidence_quality_report(
        str(output_path),
    )

    assert saved == output_path
    assert output_path.exists()


def test_save_default_report_contains_rejection(tmp_path):
    output_path = tmp_path / "default_report.json"

    save_default_evidence_quality_report(
        str(output_path),
    )

    data = load_evidence_quality_report(
        str(output_path),
    )

    assert data["overall_status"] == "REJECTED"
    assert data["accepted"] is False
    assert data["quality_gate"]["status"] == "FAIL"


def test_save_report_creates_nested_directories(tmp_path):
    report = create_valid_report(tmp_path)

    output_path = (
        tmp_path
        / "results"
        / "evidence"
        / "quality_report.json"
    )

    save_evidence_quality_report(
        report,
        str(output_path),
    )

    assert output_path.exists()

    data = load_evidence_quality_report(
        str(output_path),
    )

    assert data["accepted"] is True