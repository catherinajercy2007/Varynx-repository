from evaluation.evidence_index import (
    create_evidence_index,
    register_artifact,
)
from evaluation.evidence_quality_gate import (
    evidence_quality_gate_status,
    evidence_quality_gate_to_dict,
    evaluate_evidence_quality_gate,
    generate_evidence_quality_gate,
)


def create_valid_index(tmp_path):
    artifact = tmp_path / "report.json"

    artifact.write_text(
        '{"overall_status": "PASS"}',
        encoding="utf-8",
    )

    index = create_evidence_index()
    register_artifact(index, str(artifact))

    return index


def test_valid_evidence_passes_quality_gate(tmp_path):
    index = create_valid_index(tmp_path)

    result = evaluate_evidence_quality_gate(
        index,
        base_directory=str(tmp_path),
    )

    assert result.valid is True
    assert result.status == "PASS"
    assert result.integrity_verified is True
    assert result.artifact_count == 1
    assert result.accepted is True
    assert result.validation_errors == []


def test_empty_index_fails_quality_gate():
    index = create_evidence_index()

    result = evaluate_evidence_quality_gate(index)

    assert result.valid is False
    assert result.status == "FAIL"
    assert result.accepted is False
    assert result.artifact_count == 0

    assert any(
        "at least one artifact" in error
        for error in result.validation_errors
    )


def test_invalid_format_fails_quality_gate():
    index = {
        "format": "wrong-format",
        "artifacts": [],
    }

    result = evaluate_evidence_quality_gate(index)

    assert result.status == "FAIL"
    assert result.accepted is False

    assert any(
        "format" in error.lower()
        for error in result.validation_errors
    )


def test_invalid_artifact_metadata_fails_quality_gate():
    index = {
        "format": "evaluation-evidence-index-v1",
        "artifacts": [
            {
                "artifact": "report.json",
                "size_bytes": -1,
                "sha256": "bad",
                "verified": "yes",
            }
        ],
    }

    result = evaluate_evidence_quality_gate(index)

    assert result.valid is False
    assert result.status == "FAIL"
    assert result.accepted is False
    assert len(result.validation_errors) >= 3


def test_missing_artifact_fails_integrity_check(tmp_path):
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

    result = evaluate_evidence_quality_gate(
        index,
        base_directory=str(tmp_path),
    )

    assert result.status == "FAIL"
    assert result.accepted is False
    assert result.integrity_verified is False


def test_tampered_artifact_fails_quality_gate(tmp_path):
    index = create_valid_index(tmp_path)

    artifact = tmp_path / "report.json"

    artifact.write_text(
        '{"overall_status": "TAMPERED"}',
        encoding="utf-8",
    )

    result = evaluate_evidence_quality_gate(
        index,
        base_directory=str(tmp_path),
    )

    assert result.status == "FAIL"
    assert result.integrity_verified is False
    assert result.accepted is False


def test_quality_gate_status_for_valid_result(tmp_path):
    index = create_valid_index(tmp_path)

    result = generate_evidence_quality_gate(
        index,
        base_directory=str(tmp_path),
    )

    assert evidence_quality_gate_status(result) == "PASS"


def test_quality_gate_status_for_invalid_result():
    index = create_evidence_index()

    result = generate_evidence_quality_gate(index)

    assert evidence_quality_gate_status(result) == "FAIL"


def test_quality_gate_to_dict(tmp_path):
    index = create_valid_index(tmp_path)

    result = evaluate_evidence_quality_gate(
        index,
        base_directory=str(tmp_path),
    )

    data = evidence_quality_gate_to_dict(result)

    assert data["valid"] is True
    assert data["status"] == "PASS"
    assert data["integrity_verified"] is True
    assert data["artifact_count"] == 1
    assert data["accepted"] is True
    assert data["validation_errors"] == []


def test_generated_quality_gate_matches_direct_evaluation(tmp_path):
    index = create_valid_index(tmp_path)

    direct = evaluate_evidence_quality_gate(
        index,
        base_directory=str(tmp_path),
    )

    generated = generate_evidence_quality_gate(
        index,
        base_directory=str(tmp_path),
    )

    assert generated == direct


def test_multiple_valid_artifacts_are_accepted(tmp_path):
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

    result = evaluate_evidence_quality_gate(
        index,
        base_directory=str(tmp_path),
    )

    assert result.valid is True
    assert result.status == "PASS"
    assert result.integrity_verified is True
    assert result.artifact_count == 2
    assert result.accepted is True


def test_quality_gate_rejects_checksum_mismatch(tmp_path):
    artifact = tmp_path / "report.json"

    artifact.write_text(
        '{"status": "PASS"}',
        encoding="utf-8",
    )

    index = create_evidence_index()

    register_artifact(index, str(artifact))

    index["artifacts"][0]["sha256"] = "b" * 64

    result = evaluate_evidence_quality_gate(
        index,
        base_directory=str(tmp_path),
    )

    assert result.status == "FAIL"
    assert result.integrity_verified is False
    assert result.accepted is False