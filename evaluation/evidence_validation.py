from typing import Any, Dict, List


EXPECTED_FORMAT = "evaluation-evidence-index-v1"


def validate_index_structure(
    index: Dict[str, Any],
) -> List[str]:
    """
    Validate the basic structure of an evidence index.
    """
    errors: List[str] = []

    if not isinstance(index, dict):
        return ["Evidence index must be a dictionary."]

    if index.get("format") != EXPECTED_FORMAT:
        errors.append(
            "Invalid evidence index format."
        )

    if "artifacts" not in index:
        errors.append(
            "Missing artifacts field."
        )
    elif not isinstance(
        index["artifacts"],
        list,
    ):
        errors.append(
            "Artifacts field must be a list."
        )

    return errors


def validate_artifact_entry(
    artifact: Dict[str, Any],
    position: int,
) -> List[str]:
    """
    Validate one artifact entry.
    """
    errors: List[str] = []

    if not isinstance(artifact, dict):
        return [
            f"Artifact {position} must be a dictionary."
        ]

    required_fields = {
        "artifact",
        "size_bytes",
        "sha256",
        "verified",
    }

    for field in required_fields:
        if field not in artifact:
            errors.append(
                f"Artifact {position} missing field: {field}"
            )

    artifact_name = artifact.get("artifact")

    if "artifact" in artifact:
        if not isinstance(
            artifact_name,
            str,
        ) or not artifact_name:
            errors.append(
                f"Artifact {position} has invalid name."
            )

    size_bytes = artifact.get("size_bytes")

    if "size_bytes" in artifact:
        if (
            not isinstance(size_bytes, int)
            or isinstance(size_bytes, bool)
            or size_bytes < 0
        ):
            errors.append(
                f"Artifact {position} has invalid size_bytes."
            )

    checksum = artifact.get("sha256")

    if "sha256" in artifact:
        if (
            not isinstance(checksum, str)
            or len(checksum) != 64
        ):
            errors.append(
                f"Artifact {position} has invalid SHA-256 checksum."
            )

    verified = artifact.get("verified")

    if "verified" in artifact:
        if not isinstance(
            verified,
            bool,
        ):
            errors.append(
                f"Artifact {position} has invalid verified value."
            )

    return errors


def validate_artifacts(
    index: Dict[str, Any],
) -> List[str]:
    """
    Validate all artifact entries.
    """
    errors: List[str] = []

    artifacts = index.get(
        "artifacts",
        [],
    )

    if not isinstance(artifacts, list):
        return errors

    for position, artifact in enumerate(
        artifacts,
        start=1,
    ):
        errors.extend(
            validate_artifact_entry(
                artifact,
                position,
            )
        )

    return errors


def validate_evidence_index(
    index: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate the complete evidence index.
    """
    structure_errors = validate_index_structure(
        index
    )

    artifact_errors = validate_artifacts(
        index
    )

    errors = (
        structure_errors
        + artifact_errors
    )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "artifact_count": len(
            index.get("artifacts", [])
        )
        if isinstance(index, dict)
        and isinstance(
            index.get("artifacts", []),
            list,
        )
        else 0,
    }


def evidence_validation_status(
    validation: Dict[str, Any],
) -> str:
    """
    Return PASS or FAIL for validation result.
    """
    return (
        "PASS"
        if validation.get("valid") is True
        else "FAIL"
    )


def generate_validation_report(
    index: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate a compact validation report.
    """
    validation = validate_evidence_index(
        index
    )

    return {
        "valid": validation["valid"],
        "status": evidence_validation_status(
            validation
        ),
        "artifact_count": validation[
            "artifact_count"
        ],
        "errors": validation["errors"],
    }