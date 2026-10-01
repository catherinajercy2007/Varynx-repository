from evaluation.evidence_index import (
    create_evidence_index,
    register_artifact,
)
from evaluation.evidence_quality_report import (
    determine_evidence_report_status,
    evidence_quality_report_status,
    evidence_quality_report_to_dict,
    generate_evidence_quality_report,
)


def create_valid_index(tmp_path):
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

    return index


def test_valid_evidence_report_is_accepted(tmp_path):
    index = create_valid_index(tmp_path)

    report = generate_evidence_quality_report(
        index,
        base_directory=str(tmp_path),
    )

    assert report.overall_status == "ACCEPTED"
    assert report.accepted is True
    assert report.quality_gate["status"] == "PASS"
    assert report.quality_gate["integrity_verified"] is True
    assert report.quality_gate["artifact_count"] == 1


def test_invalid_evidence_report_is_rejected():
    index = create_evidence_index()

    report = generate_evidence_quality_report(index)

    assert report.overall_status == "REJECTED"
    assert report.accepted is False
    assert report.quality_gate["status"] == "FAIL"


def test_missing_artifact_is_rejected(tmp_path):
    index = {
        "format": "evaluation-evidence-index-v1",
        "artifacts": [
            {
                "artifact": "missing.json",
                "size_bytes": 10,
                "sha256": "a" * 64,
                "verified": True,
            }
        ],
    }

    report = generate_evidence_quality_report(
        index,
        base_directory=str(tmp_path),
    )

    assert report.overall_status == "REJECTED"
    assert report.accepted is False
    assert report.quality_gate["integrity_verified"] is False


def test_tampered_artifact_is_rejected(tmp_path):
    index = create_valid_index(tmp_path)

    artifact = tmp_path / "report.json"

    artifact.write_text(
        '{"overall_status": "TAMPERED"}',
        encoding="utf-8",
    )

    report = generate_evidence_quality_report(
        index,
        base_directory=str(tmp_path),
    )

    assert report.overall_status == "REJECTED"
    assert report.accepted is False
    assert report.quality_gate["status"] == "FAIL"


def test_report_contains_original_evidence_index(tmp_path):
    index = create_valid_index(tmp_path)

    report = generate_evidence_quality_report(
        index,
        base_directory=str(tmp_path),
    )

    assert report.evidence_index == index


def test_report_contains_quality_gate_result(tmp_path):
    index = create_valid_index(tmp_path)

    report = generate_evidence_quality_report(
        index,
        base_directory=str(tmp_path),
    )

    gate = report.quality_gate

    assert gate["valid"] is True
    assert gate["status"] == "PASS"
    assert gate["integrity_verified"] is True
    assert gate["accepted"] is True


def test_report_to_dict(tmp_path):
    index = create_valid_index(tmp_path)

    report = generate_evidence_quality_report(
        index,
        base_directory=str(tmp_path),
    )

    data = evidence_quality_report_to_dict(report)

    assert data["evidence_index"] == index
    assert data["overall_status"] == "ACCEPTED"
    assert data["accepted"] is True
    assert data["quality_gate"]["status"] == "PASS"


def test_report_status_helper(tmp_path):
    index = create_valid_index(tmp_path)

    report = generate_evidence_quality_report(
        index,
        base_directory=str(tmp_path),
    )

    assert evidence_quality_report_status(report) == "ACCEPTED"


def test_rejected_report_status_helper():
    index = create_evidence_index()

    report = generate_evidence_quality_report(index)

    assert evidence_quality_report_status(report) == "REJECTED"


def test_determine_status_for_accepted_gate():
    class Gate:
        accepted = True

    assert (
        determine_evidence_report_status(Gate())
        == "ACCEPTED"
    )


def test_determine_status_for_rejected_gate():
    class Gate:
        accepted = False

    assert (
        determine_evidence_report_status(Gate())
        == "REJECTED"
    )


def test_multiple_valid_artifacts_are_reported(tmp_path):
    first = tmp_path / "report1.json"
    second = tmp_path / "report2.json"

    first.write_text(
        '{"status": "PASS"}',
        encoding="utf-8",
    )

    second.write_text(
        '{"status": "PASS"}',
        encoding="utf-8",
    )

    index = create_evidence_index()

    register_artifact(index, str(first))
    register_artifact(index, str(second))

    report = generate_evidence_quality_report(
        index,
        base_directory=str(tmp_path),
    )

    assert report.overall_status == "ACCEPTED"
    assert report.accepted is True
    assert report.quality_gate["artifact_count"] == 2
    assert report.quality_gate["integrity_verified"] is True