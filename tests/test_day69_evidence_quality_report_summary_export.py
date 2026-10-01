from evaluation.evidence_index import (
    create_evidence_index,
    register_artifact,
)
from evaluation.evidence_quality_report import (
    generate_evidence_quality_report,
)
from evaluation.evidence_quality_report_summary import (
    generate_evidence_quality_report_summary,
)
from evaluation.evidence_quality_report_summary_export import (
    export_summary_json,
    generate_and_export_evidence_quality_summary,
    load_evidence_quality_summary,
    save_evidence_quality_summary,
    summary_to_json,
    summary_to_json_dict,
)


def create_rejected_report():
    index = create_evidence_index()

    report = generate_evidence_quality_report(
        index
    )

    return {
        "evidence_index": report.evidence_index,
        "quality_gate": report.quality_gate,
        "overall_status": report.overall_status,
        "accepted": report.accepted,
    }


def create_accepted_report(tmp_path):
    artifact = tmp_path / "artifact.json"

    artifact.write_text(
        '{"status": "valid"}',
        encoding="utf-8",
    )

    index = create_evidence_index()

    register_artifact(
        index,
        str(artifact),
    )

    report = generate_evidence_quality_report(
        index,
        base_directory=str(tmp_path),
    )

    return {
        "evidence_index": report.evidence_index,
        "quality_gate": report.quality_gate,
        "overall_status": report.overall_status,
        "accepted": report.accepted,
    }


def test_summary_to_json_dict():
    report = create_rejected_report()

    generated = (
        generate_evidence_quality_report_summary(
            report
        )
    )

    summary = generated["summary"]

    result = summary_to_json_dict(summary)

    assert result == summary


def test_summary_to_json_returns_string():
    report = create_rejected_report()

    generated = (
        generate_evidence_quality_report_summary(
            report
        )
    )

    output = summary_to_json(
        generated["summary"]
    )

    assert isinstance(output, str)
    assert '"accepted": false' in output


def test_summary_to_json_is_valid_json():
    import json

    report = create_rejected_report()

    generated = (
        generate_evidence_quality_report_summary(
            report
        )
    )

    output = summary_to_json(
        generated["summary"]
    )

    data = json.loads(output)

    assert data["overall_status"] == "REJECTED"
    assert data["accepted"] is False


def test_summary_supports_custom_indent():
    report = create_rejected_report()

    generated = (
        generate_evidence_quality_report_summary(
            report
        )
    )

    output = summary_to_json(
        generated["summary"],
        indent=4,
    )

    assert "    " in output


def test_save_summary_creates_file(tmp_path):
    report = create_rejected_report()

    generated = (
        generate_evidence_quality_report_summary(
            report
        )
    )

    output_path = (
        tmp_path
        / "exports"
        / "summary.json"
    )

    saved = save_evidence_quality_summary(
        generated["summary"],
        str(output_path),
    )

    assert saved == output_path
    assert output_path.exists()


def test_load_summary_returns_dictionary(tmp_path):
    report = create_rejected_report()

    generated = (
        generate_evidence_quality_report_summary(
            report
        )
    )

    output_path = (
        tmp_path / "summary.json"
    )

    save_evidence_quality_summary(
        generated["summary"],
        str(output_path),
    )

    loaded = load_evidence_quality_summary(
        str(output_path)
    )

    assert isinstance(loaded, dict)


def test_save_load_round_trip(tmp_path):
    report = create_rejected_report()

    generated = (
        generate_evidence_quality_report_summary(
            report
        )
    )

    summary = generated["summary"]

    output_path = (
        tmp_path / "summary.json"
    )

    save_evidence_quality_summary(
        summary,
        str(output_path),
    )

    loaded = load_evidence_quality_summary(
        str(output_path)
    )

    assert loaded == summary


def test_accepted_summary_export(tmp_path):
    report = create_accepted_report(
        tmp_path
    )

    generated = (
        generate_evidence_quality_report_summary(
            report
        )
    )

    output_path = (
        tmp_path / "accepted.json"
    )

    save_evidence_quality_summary(
        generated["summary"],
        str(output_path),
    )

    loaded = load_evidence_quality_summary(
        str(output_path)
    )

    assert loaded["overall_status"] == "ACCEPTED"
    assert loaded["accepted"] is True
    assert loaded["artifact_count"] == 1
    assert loaded["verified_artifact_count"] == 1


def test_generate_and_export_creates_file(tmp_path):
    report = create_accepted_report(
        tmp_path
    )

    output_path = (
        tmp_path
        / "results"
        / "evidence"
        / "summary.json"
    )

    saved = (
        generate_and_export_evidence_quality_summary(
            report,
            str(output_path),
        )
    )

    assert saved == output_path
    assert output_path.exists()


def test_generate_and_export_contains_summary(
    tmp_path,
):
    report = create_accepted_report(
        tmp_path
    )

    output_path = (
        tmp_path / "summary.json"
    )

    generate_and_export_evidence_quality_summary(
        report,
        str(output_path),
    )

    loaded = load_evidence_quality_summary(
        str(output_path)
    )

    assert loaded["overall_status"] == "ACCEPTED"
    assert loaded["quality_gate_status"] == "PASS"


def test_export_summary_json():
    report = create_rejected_report()

    output = export_summary_json(
        report
    )

    assert isinstance(output, str)
    assert '"overall_status": "REJECTED"' in output
    assert '"artifact_count": 0' in output


def test_export_summary_json_for_accepted_report(
    tmp_path,
):
    report = create_accepted_report(
        tmp_path
    )

    output = export_summary_json(
        report
    )

    assert '"overall_status": "ACCEPTED"' in output
    assert '"accepted": true' in output
    assert '"artifact_count": 1' in output


def test_nested_directories_are_created(tmp_path):
    report = create_rejected_report()

    generated = (
        generate_evidence_quality_report_summary(
            report
        )
    )

    output_path = (
        tmp_path
        / "a"
        / "b"
        / "c"
        / "summary.json"
    )

    save_evidence_quality_summary(
        generated["summary"],
        str(output_path),
    )

    assert output_path.exists()