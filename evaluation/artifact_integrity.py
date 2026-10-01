import hashlib
import json
from pathlib import Path
from typing import Any, Dict


def calculate_file_sha256(file_path: str) -> str:
    """
    Calculate the SHA-256 checksum of a file.
    """
    path = Path(file_path)

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            digest.update(chunk)

    return digest.hexdigest()


def create_artifact_manifest(
    file_path: str,
) -> Dict[str, Any]:
    """
    Create an integrity manifest for an evaluation artifact.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Artifact does not exist: {file_path}"
        )

    checksum = calculate_file_sha256(file_path)

    return {
        "artifact": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": checksum,
    }


def manifest_to_json(
    manifest: Dict[str, Any],
    indent: int = 2,
) -> str:
    """
    Serialize an artifact manifest to JSON.
    """
    return json.dumps(
        manifest,
        indent=indent,
        sort_keys=True,
    )


def save_artifact_manifest(
    file_path: str,
    manifest_path: str,
    indent: int = 2,
) -> Path:
    """
    Create and save an artifact integrity manifest.
    """
    manifest = create_artifact_manifest(file_path)

    path = Path(manifest_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        manifest_to_json(
            manifest,
            indent=indent,
        ),
        encoding="utf-8",
    )

    return path


def load_artifact_manifest(
    manifest_path: str,
) -> Dict[str, Any]:
    """
    Load an artifact integrity manifest.
    """
    path = Path(manifest_path)

    return json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )


def verify_artifact_integrity(
    file_path: str,
    manifest: Dict[str, Any],
) -> bool:
    """
    Verify an artifact against its stored SHA-256 checksum.
    """
    path = Path(file_path)

    if not path.exists():
        return False

    expected_checksum = manifest.get("sha256")

    if not isinstance(expected_checksum, str):
        return False

    actual_checksum = calculate_file_sha256(file_path)

    return actual_checksum == expected_checksum


def verify_saved_artifact(
    file_path: str,
    manifest_path: str,
) -> bool:
    """
    Load a saved manifest and verify the corresponding artifact.
    """
    manifest = load_artifact_manifest(manifest_path)

    return verify_artifact_integrity(
        file_path,
        manifest,
    )