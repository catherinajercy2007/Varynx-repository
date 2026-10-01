from pathlib import Path

from evaluation.artifact_integrity import (
    calculate_file_sha256,
    create_artifact_manifest,
    load_artifact_manifest,
    manifest_to_json,
    save_artifact_manifest,
    verify_artifact_integrity,
    verify_saved_artifact,
)


def create_test_artifact(path: Path) -> None:
    path.write_text(
        '{"overall_status": "PASS"}',
        encoding="utf-8",
    )


def test_calculate_file_sha256(tmp_path):
    artifact = tmp_path / "report.json"

    create_test_artifact(artifact)

    checksum = calculate_file_sha256(
        str(artifact)
    )

    assert isinstance(checksum, str)
    assert len(checksum) == 64


def test_sha256_is_deterministic(tmp_path):
    artifact = tmp_path / "report.json"

    create_test_artifact(artifact)

    first = calculate_file_sha256(
        str(artifact)
    )

    second = calculate_file_sha256(
        str(artifact)
    )

    assert first == second


def test_create_artifact_manifest(tmp_path):
    artifact = tmp_path / "report.json"

    create_test_artifact(artifact)

    manifest = create_artifact_manifest(
        str(artifact)
    )

    assert manifest["artifact"] == "report.json"
    assert manifest["size_bytes"] == artifact.stat().st_size
    assert len(manifest["sha256"]) == 64


def test_manifest_to_json(tmp_path):
    artifact = tmp_path / "report.json"

    create_test_artifact(artifact)

    manifest = create_artifact_manifest(
        str(artifact)
    )

    json_data = manifest_to_json(manifest)

    assert isinstance(json_data, str)
    assert '"artifact": "report.json"' in json_data
    assert '"sha256"' in json_data


def test_save_and_load_manifest(tmp_path):
    artifact = tmp_path / "report.json"
    manifest_file = tmp_path / "report.manifest.json"

    create_test_artifact(artifact)

    saved_path = save_artifact_manifest(
        str(artifact),
        str(manifest_file),
    )

    assert saved_path == Path(manifest_file)
    assert manifest_file.exists()

    manifest = load_artifact_manifest(
        str(manifest_file)
    )

    assert manifest["artifact"] == "report.json"
    assert len(manifest["sha256"]) == 64


def test_verify_valid_artifact(tmp_path):
    artifact = tmp_path / "report.json"

    create_test_artifact(artifact)

    manifest = create_artifact_manifest(
        str(artifact)
    )

    assert verify_artifact_integrity(
        str(artifact),
        manifest,
    ) is True


def test_modified_artifact_fails_verification(tmp_path):
    artifact = tmp_path / "report.json"

    create_test_artifact(artifact)

    manifest = create_artifact_manifest(
        str(artifact)
    )

    artifact.write_text(
        '{"overall_status": "MODIFIED"}',
        encoding="utf-8",
    )

    assert verify_artifact_integrity(
        str(artifact),
        manifest,
    ) is False


def test_verify_saved_artifact(tmp_path):
    artifact = tmp_path / "report.json"
    manifest_file = tmp_path / "report.manifest.json"

    create_test_artifact(artifact)

    save_artifact_manifest(
        str(artifact),
        str(manifest_file),
    )

    assert verify_saved_artifact(
        str(artifact),
        str(manifest_file),
    ) is True


def test_missing_artifact_fails_verification(tmp_path):
    artifact = tmp_path / "missing.json"

    manifest = {
        "artifact": "missing.json",
        "size_bytes": 10,
        "sha256": "a" * 64,
    }

    assert verify_artifact_integrity(
        str(artifact),
        manifest,
    ) is False