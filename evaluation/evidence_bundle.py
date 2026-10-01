import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from evaluation.artifact_integrity import (
    create_artifact_manifest,
    verify_artifact_integrity,
)


def create_evidence_bundle(
    artifact_path: str,
) -> Dict[str, Any]:
    """
    Create an evidence bundle for a final evaluation artifact.

    The bundle contains artifact metadata, integrity information,
    and a verification result.
    """
    path = Path(artifact_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Evaluation artifact does not exist: {artifact_path}"
        )

    manifest = create_artifact_manifest(
        artifact_path
    )

    verified = verify_artifact_integrity(
        artifact_path,
        manifest,
    )

    return {
        "artifact": manifest,
        "verification": {
            "verified": verified,
        },
        "bundle": {
            "format": "evaluation-evidence-bundle-v1",
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    }


def evidence_bundle_to_json(
    bundle: Dict[str, Any],
    indent: int = 2,
) -> str:
    """
    Serialize an evidence bundle to JSON.
    """
    return json.dumps(
        bundle,
        indent=indent,
        sort_keys=True,
    )


def save_evidence_bundle(
    artifact_path: str,
    bundle_path: str,
    indent: int = 2,
) -> Path:
    """
    Create and save an evaluation evidence bundle.
    """
    bundle = create_evidence_bundle(
        artifact_path
    )

    path = Path(bundle_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        evidence_bundle_to_json(
            bundle,
            indent=indent,
        ),
        encoding="utf-8",
    )

    return path


def load_evidence_bundle(
    bundle_path: str,
) -> Dict[str, Any]:
    """
    Load an evidence bundle from disk.
    """
    path = Path(bundle_path)

    return json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )


def verify_evidence_bundle(
    artifact_path: str,
    bundle: Dict[str, Any],
) -> bool:
    """
    Verify an artifact using the checksum stored in an evidence bundle.
    """
    artifact = bundle.get("artifact")

    if not isinstance(artifact, dict):
        return False

    return verify_artifact_integrity(
        artifact_path,
        artifact,
    )


def verify_saved_evidence_bundle(
    artifact_path: str,
    bundle_path: str,
) -> bool:
    """
    Load an evidence bundle and verify its artifact.
    """
    bundle = load_evidence_bundle(
        bundle_path
    )

    return verify_evidence_bundle(
        artifact_path,
        bundle,
    )