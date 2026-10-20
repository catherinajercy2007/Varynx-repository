
import pytest

from app.runtime_control_validation import (
    STATUS_INVALID,
    STATUS_REVIEW,
    STATUS_VALID,
    VERSION,
    validate_runtime_control_handoff,
)


def artifacts():
    graph = {
        "version": "DAY89-V1",
        "graph_id": "graph-1",
        "agent_id": "agent-1",
        "case_id": "case-1",
        "nodes": [
            {"node_id": "node-1", "entry_id": "event-1"},
            {"node_id": "node-2", "entry_id": "event-2"},
        ],
        "edges": [],
        "findings": [{"finding_id": "finding-1"}],
        "input_entry_count": 2,
        "omitted_entries": 0,
        "evidence_complete": True,
    }

    manifest = {
        "version": "DAY83-V1",
        "correlation_id": "corr-1",
        "references": [
            {
                "correlation_id": "corr-1",
                "artifact_id": "event-1",
                "stage": "AGENT_ACTION",
                "source": "test",
            },
            {
                "correlation_id": "corr-1",
                "artifact_id": "event-2",
                "stage": "BEHAVIORAL",
                "source": "test",
            },
        ],
        "required_stages": ["AGENT_ACTION", "BEHAVIORAL"],
        "status": "BINDING_COMPLETE",
        "missing_stages": [],
        "reason_codes": [],
        "manifest_digest": "placeholder",
        "is_authorization_decision": False,
        "executes_enforcement": False,
        "verifies_source_truth": False,
    }

    alert = {
        "version": "DAY88-V1",
        "alert_id": "alert-1",
        "agent_id": "agent-1",
        "correlation_id": "corr-1",
        "severity": "HIGH",
        "evidence_complete": True,
        "evidence_references": ["event-1", "event-2"],
        "is_authorization_decision": False,
        "executes_enforcement": False,
    }

    response = {
        "action": "STEP_UP_VERIFICATION",
        "severity": "HIGH",
        "score": 70.0,
        "reasons": ["test reason"],
        "recommended_controls": ["verify_identity"],
        "is_authorization_decision": False,
        "executes_enforcement": False,
    }

    return graph, manifest, alert, response


def validate(graph, manifest, alert, response, **overrides):
    args = {
        "agent_id": "agent-1",
        "case_id": "case-1",
        "correlation_id": "corr-1",
        "evidence_manifest": manifest,
        "trajectory_graph": graph,
        "alert": alert,
        "response_decision": response,
    }
    args.update(overrides)
    return validate_runtime_control_handoff(**args)


def test_complete_consistent_artifacts_validate_for_handoff():
    graph, manifest, alert, response = artifacts()

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_VALID
    assert result.recommended_action == "STEP_UP_VERIFICATION"
    assert result.alert_severity == "HIGH"
    assert result.enforcement_confirmed is False


def test_missing_artifacts_require_review():
    result = validate(None, None, None, None)

    assert result.status == STATUS_REVIEW
    assert "MISSING_REQUIRED_ARTIFACT" in result.reason_codes


def test_graph_agent_mismatch_invalidates_handoff():
    graph, manifest, alert, response = artifacts()
    graph["agent_id"] = "agent-2"

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_INVALID
    assert "AGENT_ID_MISMATCH" in result.reason_codes


def test_graph_case_mismatch_invalidates_handoff():
    graph, manifest, alert, response = artifacts()
    graph["case_id"] = "case-2"

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_INVALID
    assert "CASE_ID_MISMATCH" in result.reason_codes


def test_manifest_correlation_mismatch_invalidates_handoff():
    graph, manifest, alert, response = artifacts()
    manifest["correlation_id"] = "corr-wrong"

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_INVALID
    assert "CORRELATION_ID_MISMATCH" in result.reason_codes


def test_alert_correlation_mismatch_invalidates_handoff():
    graph, manifest, alert, response = artifacts()
    alert["correlation_id"] = "corr-wrong"

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_INVALID
    assert "CORRELATION_ID_MISMATCH" in result.reason_codes


def test_graph_incomplete_evidence_requires_review():
    graph, manifest, alert, response = artifacts()
    graph["evidence_complete"] = False

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_REVIEW
    assert "EVIDENCE_INCOMPLETE" in result.reason_codes


def test_graph_omitted_entries_require_review():
    graph, manifest, alert, response = artifacts()
    graph["omitted_entries"] = 2

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_REVIEW


def test_partial_manifest_requires_review():
    graph, manifest, alert, response = artifacts()
    manifest["status"] = "BINDING_PARTIAL"
    manifest["missing_stages"] = ["DECISION"]

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_REVIEW


def test_invalid_manifest_status_requires_review():
    graph, manifest, alert, response = artifacts()
    manifest["status"] = "BINDING_INVALID"

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_REVIEW


def test_unknown_manifest_status_invalidates_handoff():
    graph, manifest, alert, response = artifacts()
    manifest["status"] = "UNKNOWN"

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_INVALID


def test_empty_graph_requires_review():
    graph, manifest, alert, response = artifacts()
    graph["nodes"] = []

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_REVIEW
    assert "EMPTY_TRAJECTORY" in result.reason_codes


def test_unmatched_manifest_artifact_requires_review():
    graph, manifest, alert, response = artifacts()
    manifest["references"] = [
        {
            "correlation_id": "corr-1",
            "artifact_id": "unrelated-artifact",
            "stage": "AGENT_ACTION",
            "source": "test",
        }
    ]

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_REVIEW
    assert "TRAJECTORY_EVIDENCE_NOT_BOUND" in result.reason_codes


def test_alert_without_matching_evidence_requires_review():
    graph, manifest, alert, response = artifacts()
    alert["evidence_references"] = ["unrelated-artifact"]

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_REVIEW
    assert "ALERT_EVIDENCE_MISMATCH" in result.reason_codes


def test_missing_response_action_requires_review():
    graph, manifest, alert, response = artifacts()
    response.pop("action")

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_REVIEW
    assert "RESPONSE_RECOMMENDATION_MISSING" in result.reason_codes


@pytest.mark.parametrize(
    "action",
    [
        "ALLOW",
        "ALLOW_WITH_MONITORING",
        "STEP_UP_VERIFICATION",
        "REDUCE_SCOPE",
        "HUMAN_REVIEW",
        "BLOCK",
    ],
)
def test_supported_adaptive_response_actions_are_recognized(action):
    graph, manifest, alert, response = artifacts()
    response["action"] = action

    result = validate(graph, manifest, alert, response)

    assert result.recommended_action == action


def test_unknown_response_action_requires_review():
    graph, manifest, alert, response = artifacts()
    response["action"] = "EXECUTE_ARBITRARY_CODE"

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_REVIEW
    assert result.recommended_action is None


def test_claimed_enforcement_invalidates_handoff():
    graph, manifest, alert, response = artifacts()
    response["executes_enforcement"] = True

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_INVALID
    assert "UNSUPPORTED_EXECUTION_CLAIM" in result.reason_codes


def test_claimed_authorization_authority_invalidates_handoff():
    graph, manifest, alert, response = artifacts()
    response["is_authorization_decision"] = True

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_INVALID


def test_invalid_alert_severity_invalidates_handoff():
    graph, manifest, alert, response = artifacts()
    alert["severity"] = "EXTREME"

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_INVALID


def test_duplicate_manifest_artifact_ids_require_review():
    graph, manifest, alert, response = artifacts()
    manifest["references"].append(dict(manifest["references"][0]))

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_REVIEW
    assert "DUPLICATE_EVIDENCE_REFERENCE" in result.reason_codes


def test_malformed_graph_node_invalidates_handoff():
    graph, manifest, alert, response = artifacts()
    graph["nodes"] = ["not-a-node"]

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_INVALID
    assert "INVALID_ARTIFACT_SHAPE" in result.reason_codes


def test_malformed_manifest_reference_invalidates_handoff():
    graph, manifest, alert, response = artifacts()
    manifest["references"] = ["not-a-reference"]

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_INVALID


def test_malformed_alert_reference_invalidates_handoff():
    graph, manifest, alert, response = artifacts()
    alert["evidence_references"] = ["event-1", ""]

    result = validate(graph, manifest, alert, response)

    assert result.status == STATUS_INVALID


def test_deterministic_result_for_identical_inputs():
    graph, manifest, alert, response = artifacts()

    first = validate(graph, manifest, alert, response).to_dict()
    second = validate(graph, manifest, alert, response).to_dict()

    assert first == second


def test_serialized_report_preserves_security_boundaries():
    graph, manifest, alert, response = artifacts()

    result = validate(graph, manifest, alert, response).to_dict()

    assert result["version"] == VERSION
    assert result["is_authorization_decision"] is False
    assert result["executes_enforcement"] is False
    assert result["enforcement_confirmed"] is False


def test_validation_does_not_mutate_input_artifacts():
    graph, manifest, alert, response = artifacts()
    before = (
        repr(graph),
        repr(manifest),
        repr(alert),
        repr(response),
    )

    validate(graph, manifest, alert, response)

    after = (
        repr(graph),
        repr(manifest),
        repr(alert),
        repr(response),
    )

    assert before == after


@pytest.mark.parametrize("bad_agent_id", ["", " ", None])
def test_invalid_agent_id_is_rejected(bad_agent_id):
    graph, manifest, alert, response = artifacts()

    with pytest.raises(ValueError):
        validate(
            graph,
            manifest,
            alert,
            response,
            agent_id=bad_agent_id,
        )


@pytest.mark.parametrize("bad_case_id", ["", " ", None])
def test_invalid_case_id_is_rejected(bad_case_id):
    graph, manifest, alert, response = artifacts()

    with pytest.raises(ValueError):
        validate(
            graph,
            manifest,
            alert,
            response,
            case_id=bad_case_id,
        )


def test_blank_correlation_id_is_rejected():
    graph, manifest, alert, response = artifacts()

    with pytest.raises(ValueError):
        validate(
            graph,
            manifest,
            alert,
            response,
            correlation_id=" ",
        )


def test_absent_optional_correlation_id_is_supported():
    graph, manifest, alert, response = artifacts()

    result = validate(
        graph,
        manifest,
        alert,
        response,
        correlation_id=None,
    )

    assert result.correlation_id is None
    assert result.status in {STATUS_VALID, STATUS_REVIEW, STATUS_INVALID}


def test_non_mapping_artifact_is_rejected():
    with pytest.raises(TypeError):
        validate_runtime_control_handoff(
            agent_id="agent-1",
            case_id="case-1",
            correlation_id="corr-1",
            evidence_manifest=[],
            trajectory_graph=None,
            alert=None,
            response_decision=None,
        )
