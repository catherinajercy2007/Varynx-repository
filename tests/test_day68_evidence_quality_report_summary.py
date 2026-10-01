from evaluation.evidence_index import (
    create_evidence_index,
    register_artifact,
)
from evaluation.evidence_quality_report import (
    generate_evidence_quality_report,
)
from evaluation.evidence_quality_report_summary import (
    evidence_quality_report_summary_status,
    evidence_quality_report_summary_to_dict,
    generate_evidence_quality_report_summary,
    summarize_evidence_quality_report,
)


def create_rejected_report():
    index = create_evidence_index()

    return generate_evidence_quality_report(
        index
    )


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

    return generate_evidence_quality_report(
        index,
        base_directory=str(tmp_path),
    )


def test_rejected_report_summary():
    report = create_rejected_report()

    data = {
        "evidence_index": report.evidence_index,
        "quality_gate": report.quality_gate,
        "overall_status": report.overall_status,
        "accepted": report.accepted,
    }

    summary = summarize_evidence_quality_report(
        data
    )

    assert summary["overall_status"] == "REJECTED"
    assert summary["accepted"] is False
    assert summary["quality_gate_status"] == "FAIL"
    assert summary["artifact_count"] == 0
    assert summary["verified_artifact_count"] == 0


def test_accepted_report_summary(tmp_path):
    report = create_accepted_report(
        tmp_path
    )

    data = {
        "evidence_index": report.evidence_index,
        "quality_gate": report.quality_gate,
        "overall_status": report.overall_status,
        "accepted": report.accepted,
    }

    summary = summarize_evidence_quality_report(
        data
    )

    assert summary["overall_status"] == "ACCEPTED"
    assert summary["accepted"] is True
    assert summary["quality_gate_status"] == "PASS"
    assert summary["integrity_verified"] is True
    assert summary["artifact_count"] == 1
    assert summary["verified_artifact_count"] == 1
    assert summary["validation_error_count"] == 0


def test_summary_counts_verified_artifacts():
    report = {
        "evidence_index": {
            "artifacts": [
                {"verified": True},
                {"verified": False},
                {"verified": True},
            ]
        },
        "quality_gate": {
            "status": "FAIL",
            "integrity_verified": False,
            "validation_errors": [
                "example error"
            ],
        },
        "overall_status": "REJECTED",
        "accepted": False,
    }

    summary = summarize_evidence_quality_report(
        report
    )

    assert summary["artifact_count"] == 3
    assert summary["verified_artifact_count"] == 2
    assert summary["validation_error_count"] == 1


def test_summary_status_accepted():
    summary = {
        "accepted": True,
    }

    assert (
        evidence_quality_report_summary_status(
            summary
        )
        == "ACCEPTED"
    )


def test_summary_status_rejected():
    summary = {
        "accepted": False,
    }

    assert (
        evidence_quality_report_summary_status(
            summary
        )
        == "REJECTED"
    )


def test_summary_to_dict():
    summary = {
        "overall_status": "ACCEPTED",
        "accepted": True,
        "quality_gate_status": "PASS",
        "integrity_verified": True,
        "artifact_count": 2,
        "verified_artifact_count": 2,
        "validation_error_count": 0,
    }

    result = evidence_quality_report_summary_to_dict(
        summary
    )

    assert result == summary


def test_summary_to_dict_preserves_rejected_data():
    summary = {
        "overall_status": "REJECTED",
        "accepted": False,
        "quality_gate_status": "FAIL",
        "integrity_verified": False,
        "artifact_count": 0,
        "verified_artifact_count": 0,
        "validation_error_count": 1,
    }

    result = evidence_quality_report_summary_to_dict(
        summary
    )

    assert result["overall_status"] == "REJECTED"
    assert result["accepted"] is False
    assert result["quality_gate_status"] == "FAIL"


def test_generate_summary_returns_expected_structure(
    tmp_path,
):
    report = create_accepted_report(
        tmp_path
    )

    data = {
        "evidence_index": report.evidence_index,
        "quality_gate": report.quality_gate,
        "overall_status": report.overall_status,
        "accepted": report.accepted,
    }

    result = generate_evidence_quality_report_summary(
        data
    )

    assert "summary" in result
    assert "status" in result
    assert result["status"] == "ACCEPTED"


def test_generate_summary_for_rejected_report():
    report = create_rejected_report()

    data = {
        "evidence_index": report.evidence_index,
        "quality_gate": report.quality_gate,
        "overall_status": report.overall_status,
        "accepted": report.accepted,
    }

    result = generate_evidence_quality_report_summary(
        data
    )

    assert result["status"] == "REJECTED"
    assert result["summary"]["artifact_count"] == 0


def test_empty_evidence_index_is_handled():
    report = {
        "evidence_index": {},
        "quality_gate": {
            "status": "FAIL",
            "integrity_verified": False,
            "validation_errors": [],
        },
        "overall_status": "REJECTED",
        "accepted": False,
    }

    summary = summarize_evidence_quality_report(
        report
    )

    assert summary["artifact_count"] == 0
    assert summary["verified_artifact_count"] == 0


def test_missing_quality_gate_fields_are_handled():
    report = {
        "evidence_index": {
            "artifacts": []
        },
        "quality_gate": {},
        "overall_status": "REJECTED",
        "accepted": False,
    }

    summary = summarize_evidence_quality_report(
        report
    )

    assert summary["quality_gate_status"] is None
    assert summary["integrity_verified"] is None
    assert summary["validation_error_count"] == 0


def test_summary_contains_only_expected_fields():
    report = create_rejected_report()

    data = {
        "evidence_index": report.evidence_index,
        "quality_gate": report.quality_gate,
        "overall_status": report.overall_status,
        "accepted": report.accepted,
    }

    summary = summarize_evidence_quality_report(
        data
    )

    assert set(summary.keys()) == {
        "overall_status",
        "accepted",
        "quality_gate_status",
        "integrity_verified",
        "artifact_count",
        "verified_artifact_count",
        "validation_error_count",
    }