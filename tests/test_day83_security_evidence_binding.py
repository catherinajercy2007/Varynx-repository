
import pytest

from app.security_evidence_binding import (
    EvidenceReference,
    STATUS_COMPLETE,
    STATUS_INVALID,
    STATUS_PARTIAL,
    STAGE_AGENT_ACTION,
    STAGE_BCSE,
    STAGE_BEHAVIORAL,
    STAGE_DECISION,
    STAGE_ENFORCEMENT,
    bind_security_evidence,
    payload_sha256,
    verify_manifest_digest,
)


def reference(stage, artifact_id=None, correlation_id="request-83"):
    return EvidenceReference(
        correlation_id=correlation_id,
        artifact_id=artifact_id or f"artifact-{stage.lower()}",
        stage=stage,
        source="test-simulator",
    )


def complete_references():
    return [
        reference(STAGE_AGENT_ACTION),
        reference(STAGE_BEHAVIORAL),
        reference(STAGE_BCSE),
        reference(STAGE_DECISION),
        reference(STAGE_ENFORCEMENT),
    ]


def test_complete_manifest():
    manifest = bind_security_evidence(
        correlation_id="request-83",
        references=complete_references(),
        required_stages=(
            STAGE_AGENT_ACTION,
            STAGE_BEHAVIORAL,
            STAGE_DECISION,
        ),
    )

    assert manifest.status == STATUS_COMPLETE
    assert manifest.missing_stages == ()


def test_missing_required_stage_is_partial():
    manifest = bind_security_evidence(
        correlation_id="request-83",
        references=[reference(STAGE_AGENT_ACTION)],
    )

    assert manifest.status == STATUS_PARTIAL
    assert STAGE_BEHAVIORAL in manifest.missing_stages
    assert STAGE_DECISION in manifest.missing_stages


def test_empty_references_produce_partial_manifest():
    manifest = bind_security_evidence(
        correlation_id="request-83",
        references=[],
    )

    assert manifest.status == STATUS_PARTIAL


def test_wrong_correlation_id_is_rejected():
    with pytest.raises(ValueError, match="correlation_id"):
        bind_security_evidence(
            correlation_id="request-83",
            references=[reference(STAGE_AGENT_ACTION, correlation_id="other")],
        )


def test_duplicate_artifact_id_makes_manifest_invalid():
    refs = [
        reference(STAGE_AGENT_ACTION, artifact_id="duplicate"),
        reference(STAGE_BEHAVIORAL, artifact_id="duplicate"),
    ]

    manifest = bind_security_evidence(
        correlation_id="request-83",
        references=refs,
    )

    assert manifest.status == STATUS_INVALID


def test_duplicate_required_stage_is_rejected():
    with pytest.raises(ValueError, match="duplicates"):
        bind_security_evidence(
            correlation_id="request-83",
            references=[],
            required_stages=(STAGE_DECISION, STAGE_DECISION),
        )


def test_unsupported_stage_is_rejected():
    with pytest.raises(ValueError, match="Unsupported evidence stage"):
        reference("UNKNOWN_STAGE")


def test_empty_correlation_id_is_rejected():
    with pytest.raises(ValueError):
        bind_security_evidence(correlation_id=" ", references=[])


def test_invalid_reference_type_is_rejected():
    with pytest.raises(TypeError):
        bind_security_evidence(
            correlation_id="request-83",
            references=["not-a-reference"],
        )


def test_manifest_is_deterministic():
    refs = complete_references()

    first = bind_security_evidence(
        correlation_id="request-83",
        references=refs,
    )
    second = bind_security_evidence(
        correlation_id="request-83",
        references=list(reversed(refs)),
    )

    assert first.manifest_digest == second.manifest_digest
    assert first.to_dict() == second.to_dict()


def test_digest_verification_succeeds_for_unchanged_manifest():
    manifest = bind_security_evidence(
        correlation_id="request-83",
        references=complete_references(),
    )

    assert verify_manifest_digest(manifest) is True


def test_digest_changes_when_payload_changes():
    assert payload_sha256({"a": 1, "b": 2}) == payload_sha256(
        {"b": 2, "a": 1}
    )
    assert payload_sha256({"a": 1}) != payload_sha256({"a": 2})


def test_optional_payload_digest_must_be_valid_sha256():
    with pytest.raises(ValueError, match="SHA-256"):
        EvidenceReference(
            correlation_id="request-83",
            artifact_id="artifact-1",
            stage=STAGE_AGENT_ACTION,
            source="test",
            payload_digest="invalid",
        )


def test_valid_payload_digest_is_normalized():
    digest = payload_sha256({"event": "action"})

    item = EvidenceReference(
        correlation_id="request-83",
        artifact_id="artifact-1",
        stage=STAGE_AGENT_ACTION,
        source="test",
        payload_digest=digest.upper(),
    )

    assert item.payload_digest == digest


def test_manifest_declares_security_boundaries():
    manifest = bind_security_evidence(
        correlation_id="request-83",
        references=complete_references(),
    ).to_dict()

    assert manifest["is_authorization_decision"] is False
    assert manifest["executes_enforcement"] is False
    assert manifest["verifies_source_truth"] is False


def test_serialization_preserves_source_and_stage():
    manifest = bind_security_evidence(
        correlation_id="request-83",
        references=[reference(STAGE_AGENT_ACTION)],
    ).to_dict()

    assert manifest["references"][0]["source"] == "test-simulator"
    assert manifest["references"][0]["stage"] == STAGE_AGENT_ACTION


def test_manifest_rejects_mapping_as_reference_iterable():
    with pytest.raises(TypeError):
        bind_security_evidence(
            correlation_id="request-83",
            references={"unexpected": "mapping"},
        )
