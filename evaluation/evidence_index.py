import json
from pathlib import Path
from typing import Any, Dict, List

from evaluation.artifact_integrity import (
    create_artifact_manifest,
    verify_artifact_integrity,
)


def create_evidence_index() -> Dict[str, Any]:
    """
    Create an empty evaluation evidence index.
    """
    return {
        "format": "evaluation-evidence-index-v1",
        "artifacts": [],
    }


def register_artifact(
    index: Dict[str, Any],
    file_path: str,
) -> Dict[str, Any]:
    """
    Register an evaluation artifact in the evidence index.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Artifact does not exist: {file_path}"
        )

    manifest = create_artifact_manifest(
        file_path
    )

    artifact = {
        "artifact": manifest["artifact"],
        "size_bytes": manifest["size_bytes"],
        "sha256": manifest["sha256"],
        "verified": verify_artifact_integrity(
            file_path,
            manifest,
        ),
    }

    index.setdefault(
        "artifacts",
        [],
    ).append(artifact)

    return artifact


def evidence_index_summary(
    index: Dict[str, Any],
) -> Dict[str, int]:
    """
    Return summary statistics for an evidence index.
    """
    artifacts = index.get(
        "artifacts",
        [],
    )

    verified_count = sum(
        1
        for artifact in artifacts
        if artifact.get("verified") is True
    )

    return {
        "total_artifacts": len(artifacts),
        "verified_artifacts": verified_count,
        "unverified_artifacts": (
            len(artifacts) - verified_count
        ),
    }


def verify_evidence_index(
    index: Dict[str, Any],
    base_directory: str = ".",
) -> bool:
    """
    Verify every registered artifact in an evidence index.
    """
    artifacts = index.get(
        "artifacts",
        [],
    )

    base_path = Path(base_directory)

    for artifact in artifacts:
        artifact_name = artifact.get("artifact")
        checksum = artifact.get("sha256")

        if not isinstance(artifact_name, str):
            return False

        if not isinstance(checksum, str):
            return False

        artifact_path = base_path / artifact_name

        if not artifact_path.exists():
            return False

        manifest = {
            "artifact": artifact_name,
            "size_bytes": artifact.get(
                "size_bytes",
                artifact_path.stat().st_size,
            ),
            "sha256": checksum,
        }

        if not verify_artifact_integrity(
            str(artifact_path),
            manifest,
        ):
            return False

    return True


def evidence_index_to_json(
    index: Dict[str, Any],
    indent: int = 2,
) -> str:
    """
    Serialize an evidence index to JSON.
    """
    return json.dumps(
        index,
        indent=indent,
        sort_keys=True,
    )


def save_evidence_index(
    index: Dict[str, Any],
    file_path: str,
    indent: int = 2,
) -> Path:
    """
    Save an evidence index as JSON.
    """
    path = Path(file_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        evidence_index_to_json(
            index,
            indent=indent,
        ),
        encoding="utf-8",
    )

    return path


def load_evidence_index(
    file_path: str,
) -> Dict[str, Any]:
    """
    Load an evidence index from JSON.
    """
    path = Path(file_path)

    return json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )


def generate_evidence_index(
    artifact_paths: List[str],
) -> Dict[str, Any]:
    """
    Create an evidence index and register multiple artifacts.
    """
    index = create_evidence_index()

    for artifact_path in artifact_paths:
        register_artifact(
            index,
            artifact_path,
        )

    return index