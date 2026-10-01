from evaluation.evidence_index import (
    create_evidence_index,
    register_artifact,
)
from evaluation.evidence_validation import (
    evidence_validation_status,
    generate_validation_report,
    validate_artifact_entry,
    validate_artifacts,
    validate_evidence_index,
    validate_index_structure,
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


def test_valid_index_structure():
    index = create_evidence_index()

    errors = validate_index_structure(index)

    assert errors == []


def test_invalid_index_format():
    index = {
        "format": "wrong-format",
        "artifacts": [],
    }

    errors = validate_index_structure(index)

    assert len(errors) == 1
    assert "format" in errors[0].lower()


def test_missing_artifacts_field():
    index = {
        "format": "evaluation-evidence-index-v1"
    }

    errors = validate_index_structure(index)

    assert "Missing artifacts field." in errors


def test_valid_artifact_entry():
    artifact = {
        "artifact": "report.json",
        "size_bytes": 100,
        "sha256": "a" * 64,
        "verified": True,
    }

    errors = validate_artifact_entry(
        artifact,
        1,
    )

    assert errors == []


def test_invalid_artifact_checksum():
    artifact = {
        "artifact": "report.json",
        "size_bytes": 100,
        "sha256": "invalid",
        "verified": True,
    }

    errors = validate_artifact_entry(
        artifact,
        1,
    )

    assert any(
        "SHA-256" in error
        for error in errors
    )


def test_invalid_artifact_size():
    artifact = {
        "artifact": "report.json",
        "size_bytes": -1,
        "sha256": "a" * 64,
        "verified": True,
    }

    errors = validate_artifact_entry(
        artifact,
        1,
    )

    assert any(
        "size_bytes" in error
        for error in errors
    )


def test_invalid_verified_value():
    artifact = {
        "artifact": "report.json",
        "size_bytes": 100,
        "sha256": "a" * 64,
        "verified": "true",
    }

    errors = validate_artifact_entry(
        artifact,
        1,
    )

    assert any(
        "verified" in error
        for error in errors
    )


def test_valid_artifacts(tmp_path):
    index = create_valid_index(tmp_path)

    errors = validate_artifacts(index)

    assert errors == []


def test_complete_validation(tmp_path):
    index = create_valid_index(tmp_path)

    result = validate_evidence_index(index)

    assert result["valid"] is True
    assert result["errors"] == []
    assert result["artifact_count"] == 1


def test_invalid_index_fails_validation():
    index = {
        "format": "wrong-format",
        "artifacts": [
            {
                "artifact": "report.json",
                "size_bytes": -1,
                "sha256": "bad",
                "verified": "yes",
            }
        ],
    }

    result = validate_evidence_index(index)

    assert result["valid"] is False
    assert len(result["errors"]) >= 3


def test_validation_status():
    assert (
        evidence_validation_status(
            {"valid": True}
        )
        == "PASS"
    )

    assert (
        evidence_validation_status(
            {"valid": False}
        )
        == "FAIL"
    )


def test_generate_validation_report(tmp_path):
    index = create_valid_index(tmp_path)

    report = generate_validation_report(
        index
    )

    assert report["valid"] is True
    assert report["status"] == "PASS"
    assert report["artifact_count"] == 1
    assert report["errors"] == []