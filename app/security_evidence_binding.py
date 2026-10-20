
"""Day 83: Correlation ID and Evidence Binding for Varynx.

Creates a deterministic, immutable manifest linking security artifacts
to a request correlation ID. It records references and their provenance;
it does not verify that external artifacts are truthful or authorize
or enforce an action.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Iterable


VERSION = "DAY83-V1"

STAGE_AGENT_ACTION = "AGENT_ACTION"
STAGE_BEHAVIORAL = "BEHAVIORAL"
STAGE_BCSE = "BCSE"
STAGE_DECISION = "DECISION"
STAGE_ENFORCEMENT = "ENFORCEMENT"

VALID_STAGES = frozenset({
    STAGE_AGENT_ACTION,
    STAGE_BEHAVIORAL,
    STAGE_BCSE,
    STAGE_DECISION,
    STAGE_ENFORCEMENT,
})

STATUS_COMPLETE = "BINDING_COMPLETE"
STATUS_PARTIAL = "BINDING_PARTIAL"
STATUS_INVALID = "BINDING_INVALID"

REASON_REQUIRED_STAGE_MISSING = "REQUIRED_STAGE_MISSING"
REASON_DUPLICATE_REFERENCE = "DUPLICATE_REFERENCE"
REASON_CORRELATION_MISMATCH = "CORRELATION_MISMATCH"


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _canonical_json(payload: Any) -> str:
    """Serialize supported JSON-like data deterministically."""
    try:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "payload must contain only finite JSON-serializable values"
        ) from exc


def payload_sha256(payload: Any) -> str:
    """Return a SHA-256 digest of canonical JSON payload content."""
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EvidenceReference:
    """Reference to one recorded artifact associated with a request."""

    correlation_id: str
    artifact_id: str
    stage: str
    source: str
    payload_digest: str | None = None

    def __post_init__(self) -> None:
        for field in ("correlation_id", "artifact_id", "source"):
            object.__setattr__(
                self, field, _text(getattr(self, field), field)
            )

        stage = _text(self.stage, "stage").upper()
        if stage not in VALID_STAGES:
            raise ValueError(f"Unsupported evidence stage: {stage}")
        object.__setattr__(self, "stage", stage)

        if self.payload_digest is not None:
            digest = _text(self.payload_digest, "payload_digest").lower()
            if len(digest) != 64 or any(
                char not in "0123456789abcdef" for char in digest
            ):
                raise ValueError(
                    "payload_digest must be a 64-character SHA-256 hex digest"
                )
            object.__setattr__(self, "payload_digest", digest)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceBindingManifest:
    """Immutable evidence binding for one request."""

    correlation_id: str
    references: tuple[EvidenceReference, ...]
    required_stages: tuple[str, ...]
    status: str
    missing_stages: tuple[str, ...]
    reason_codes: tuple[str, ...]
    manifest_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": VERSION,
            "correlation_id": self.correlation_id,
            "references": [
                reference.to_dict() for reference in self.references
            ],
            "required_stages": list(self.required_stages),
            "status": self.status,
            "missing_stages": list(self.missing_stages),
            "reason_codes": list(self.reason_codes),
            "manifest_digest": self.manifest_digest,
            "is_authorization_decision": False,
            "executes_enforcement": False,
            "verifies_source_truth": False,
        }


def bind_security_evidence(
    *,
    correlation_id: str,
    references: Iterable[EvidenceReference],
    required_stages: Iterable[str] = (
        STAGE_AGENT_ACTION,
        STAGE_BEHAVIORAL,
        STAGE_DECISION,
    ),
) -> EvidenceBindingManifest:
    """Build a deterministic manifest for one request.

    References with a different correlation ID are rejected instead of
    silently attaching evidence from another request.

    Missing required stages produce a partial manifest. Duplicate
    artifact IDs are reported and make the manifest invalid.
    """
    correlation_id = _text(correlation_id, "correlation_id")

    if isinstance(references, (str, bytes, dict)):
        raise TypeError("references must be an iterable of EvidenceReference")

    try:
        items = tuple(references)
    except TypeError as exc:
        raise TypeError(
            "references must be an iterable of EvidenceReference"
        ) from exc

    if any(not isinstance(item, EvidenceReference) for item in items):
        raise TypeError(
            "references must contain only EvidenceReference objects"
        )

    if isinstance(required_stages, (str, bytes, dict)):
        raise TypeError("required_stages must be an iterable of stage names")

    stages = tuple(
        _text(stage, "required_stage").upper()
        for stage in required_stages
    )

    if any(stage not in VALID_STAGES for stage in stages):
        raise ValueError("required_stages contains an unsupported stage")

    if len(set(stages)) != len(stages):
        raise ValueError("required_stages must not contain duplicates")

    mismatched = [
        reference for reference in items
        if reference.correlation_id != correlation_id
    ]
    if mismatched:
        raise ValueError(
            "Every reference must match the manifest correlation_id"
        )

    artifact_ids = [reference.artifact_id for reference in items]
    duplicates = len(artifact_ids) != len(set(artifact_ids))

    # Sort by stable fields so ordering of input references does not affect
    # the manifest digest or output ordering.
    ordered = tuple(sorted(
        items,
        key=lambda item: (
            item.stage,
            item.artifact_id,
            item.source,
            item.payload_digest or "",
        ),
    ))

    available_stages = {item.stage for item in ordered}
    missing = tuple(stage for stage in stages if stage not in available_stages)

    reasons: list[str] = []
    if missing:
        reasons.append(REASON_REQUIRED_STAGE_MISSING)
    if duplicates:
        reasons.append(REASON_DUPLICATE_REFERENCE)

    if duplicates:
        status = STATUS_INVALID
    elif missing:
        status = STATUS_PARTIAL
    else:
        status = STATUS_COMPLETE

    manifest_payload = {
        "version": VERSION,
        "correlation_id": correlation_id,
        "references": [item.to_dict() for item in ordered],
        "required_stages": list(stages),
        "status": status,
        "missing_stages": list(missing),
        "reason_codes": reasons,
    }

    digest = payload_sha256(manifest_payload)

    return EvidenceBindingManifest(
        correlation_id=correlation_id,
        references=ordered,
        required_stages=stages,
        status=status,
        missing_stages=missing,
        reason_codes=tuple(reasons),
        manifest_digest=digest,
    )


def verify_manifest_digest(manifest: EvidenceBindingManifest) -> bool:
    """Check manifest integrity against its stored digest.

    This detects changes to manifest content; it does not authenticate
    the source or prove that the referenced evidence is truthful.
    """
    if not isinstance(manifest, EvidenceBindingManifest):
        raise TypeError("manifest must be an EvidenceBindingManifest")

    payload = manifest.to_dict()
    for field in (
        "manifest_digest",
        "is_authorization_decision",
        "executes_enforcement",
        "verifies_source_truth",
    ):
        payload.pop(field, None)

    return payload_sha256(payload) == manifest.manifest_digest


__all__ = [
    "VERSION",
    "EvidenceReference",
    "EvidenceBindingManifest",
    "bind_security_evidence",
    "payload_sha256",
    "verify_manifest_digest",
    "STATUS_COMPLETE",
    "STATUS_PARTIAL",
    "STATUS_INVALID",
]
