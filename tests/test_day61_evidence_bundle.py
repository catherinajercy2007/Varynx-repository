from pathlib import Path

from evaluation.evidence_bundle import (
    create_evidence_bundle,
    evidence_bundle_to_json,
    load_evidence_bundle,
    save_evidence_bundle,
    verify_evidence_bundle,
    verify_saved_evidence_bundle,
)


def create_test_artifact(path: Path) -> None:
    path.write_text(
        '{"overall_status": "PASS"}',
        encoding="utf-8",
    )


def test_create_evidence_bundle(tmp_path):
    artifact = tmp_path / "final_report.json"

    create_test_artifact(artifact)

    bundle = create_evidence_bundle(
        str(artifact)
    )

    assert "artifact" in bundle
    assert "verification" in bundle
    assert "bundle" in bundle


def test_bundle_contains_artifact_metadata(tmp_path):
    artifact = tmp_path / "final_report.json"

    create_test_artifact(artifact)

    bundle = create_evidence_bundle(
        str(artifact)
    )

    assert bundle["artifact"]["artifact"] == (
        "final_report.json"
    )
    assert bundle["artifact"]["size_bytes"] == (
        artifact.stat().st_size
    )
    assert len(bundle["artifact"]["sha256"]) == 64


def test_bundle_verification_is_valid(tmp_path):
    artifact = tmp_path / "final_report.json"

    create_test_artifact(artifact)

    bundle = create_evidence_bundle(
        str(artifact)
    )

    assert bundle["verification"]["verified"] is True


def test_bundle_format_version(tmp_path):
    artifact = tmp_path / "final_report.json"

    create_test_artifact(artifact)

    bundle = create_evidence_bundle(
        str(artifact)
    )

    assert (
        bundle["bundle"]["format"]
        == "evaluation-evidence-bundle-v1"
    )


def test_evidence_bundle_to_json(tmp_path):
    artifact = tmp_path / "final_report.json"

    create_test_artifact(artifact)

    bundle = create_evidence_bundle(
        str(artifact)
    )

    json_data = evidence_bundle_to_json(
        bundle
    )

    assert isinstance(json_data, str)
    assert "evaluation-evidence-bundle-v1" in json_data
    assert '"verified": true' in json_data


def test_save_and_load_evidence_bundle(tmp_path):
    artifact = tmp_path / "final_report.json"
    bundle_file = tmp_path / "evidence_bundle.json"

    create_test_artifact(artifact)

    saved_path = save_evidence_bundle(
        str(artifact),
        str(bundle_file),
    )

    assert saved_path == Path(bundle_file)
    assert bundle_file.exists()

    bundle = load_evidence_bundle(
        str(bundle_file)
    )

    assert bundle["verification"]["verified"] is True


def test_verify_evidence_bundle(tmp_path):
    artifact = tmp_path / "final_report.json"

    create_test_artifact(artifact)

    bundle = create_evidence_bundle(
        str(artifact)
    )

    assert verify_evidence_bundle(
        str(artifact),
        bundle,
    ) is True


def test_modified_artifact_fails_bundle_verification(
    tmp_path,
):
    artifact = tmp_path / "final_report.json"

    create_test_artifact(artifact)

    bundle = create_evidence_bundle(
        str(artifact)
    )

    artifact.write_text(
        '{"overall_status": "MODIFIED"}',
        encoding="utf-8",
    )

    assert verify_evidence_bundle(
        str(artifact),
        bundle,
    ) is False


def test_verify_saved_evidence_bundle(tmp_path):
    artifact = tmp_path / "final_report.json"
    bundle_file = tmp_path / "evidence_bundle.json"

    create_test_artifact(artifact)

    save_evidence_bundle(
        str(artifact),
        str(bundle_file),
    )

    assert verify_saved_evidence_bundle(
        str(artifact),
        str(bundle_file),
    ) is True


def test_missing_artifact_rejected(tmp_path):
    artifact = tmp_path / "missing_report.json"

    try:
        create_evidence_bundle(
            str(artifact)
        )
        assert False
    except FileNotFoundError:
        assert True