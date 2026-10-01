from pathlib import Path

from evaluation.evidence_index import (
    create_evidence_index,
    evidence_index_summary,
    evidence_index_to_json,
    generate_evidence_index,
    load_evidence_index,
    register_artifact,
    save_evidence_index,
    verify_evidence_index,
)


def create_test_artifact(
    path: Path,
    content: str,
) -> None:
    path.write_text(
        content,
        encoding="utf-8",
    )


def test_create_empty_evidence_index():
    index = create_evidence_index()

    assert index["format"] == (
        "evaluation-evidence-index-v1"
    )
    assert index["artifacts"] == []


def test_register_artifact(tmp_path):
    artifact = tmp_path / "report.json"

    create_test_artifact(
        artifact,
        '{"status": "PASS"}',
    )

    index = create_evidence_index()

    registered = register_artifact(
        index,
        str(artifact),
    )

    assert registered["artifact"] == "report.json"
    assert registered["size_bytes"] > 0
    assert len(registered["sha256"]) == 64
    assert registered["verified"] is True


def test_multiple_artifacts(tmp_path):
    first = tmp_path / "report.json"
    second = tmp_path / "manifest.json"

    create_test_artifact(
        first,
        '{"status": "PASS"}',
    )

    create_test_artifact(
        second,
        '{"verified": true}',
    )

    index = generate_evidence_index(
        [
            str(first),
            str(second),
        ]
    )

    assert len(index["artifacts"]) == 2
    assert index["artifacts"][0]["verified"] is True
    assert index["artifacts"][1]["verified"] is True


def test_evidence_index_summary(tmp_path):
    artifact = tmp_path / "report.json"

    create_test_artifact(
        artifact,
        '{"status": "PASS"}',
    )

    index = generate_evidence_index(
        [str(artifact)]
    )

    summary = evidence_index_summary(index)

    assert summary["total_artifacts"] == 1
    assert summary["verified_artifacts"] == 1
    assert summary["unverified_artifacts"] == 0


def test_evidence_index_to_json(tmp_path):
    artifact = tmp_path / "report.json"

    create_test_artifact(
        artifact,
        '{"status": "PASS"}',
    )

    index = generate_evidence_index(
        [str(artifact)]
    )

    json_data = evidence_index_to_json(index)

    assert isinstance(json_data, str)
    assert "evaluation-evidence-index-v1" in json_data
    assert "report.json" in json_data


def test_save_and_load_index(tmp_path):
    artifact = tmp_path / "report.json"
    index_file = tmp_path / "evidence_index.json"

    create_test_artifact(
        artifact,
        '{"status": "PASS"}',
    )

    index = generate_evidence_index(
        [str(artifact)]
    )

    saved_path = save_evidence_index(
        index,
        str(index_file),
    )

    assert saved_path == Path(index_file)
    assert index_file.exists()

    loaded = load_evidence_index(
        str(index_file)
    )

    assert loaded == index


def test_verify_evidence_index(tmp_path):
    artifact = tmp_path / "report.json"

    create_test_artifact(
        artifact,
        '{"status": "PASS"}',
    )

    index = generate_evidence_index(
        [str(artifact)]
    )

    assert verify_evidence_index(
        index,
        str(tmp_path),
    ) is True


def test_modified_artifact_fails_index_verification(
    tmp_path,
):
    artifact = tmp_path / "report.json"

    create_test_artifact(
        artifact,
        '{"status": "PASS"}',
    )

    index = generate_evidence_index(
        [str(artifact)]
    )

    artifact.write_text(
        '{"status": "MODIFIED"}',
        encoding="utf-8",
    )

    assert verify_evidence_index(
        index,
        str(tmp_path),
    ) is False


def test_missing_artifact_fails_index_verification(
    tmp_path,
):
    artifact = tmp_path / "report.json"

    create_test_artifact(
        artifact,
        '{"status": "PASS"}',
    )

    index = generate_evidence_index(
        [str(artifact)]
    )

    artifact.unlink()

    assert verify_evidence_index(
        index,
        str(tmp_path),
    ) is False


def test_register_missing_artifact_rejected(
    tmp_path,
):
    missing = tmp_path / "missing.json"

    index = create_evidence_index()

    try:
        register_artifact(
            index,
            str(missing),
        )
        assert False
    except FileNotFoundError:
        assert True