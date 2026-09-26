from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.enforcement_boundary import (
    BOUNDARY_ESCALATED,
    BOUNDARY_READY,
    DECISION_ALLOW,
    DECISION_BLOCK,
    DECISION_HUMAN_REVIEW,
    DECISION_MONITOR,
    DECISION_REDUCE_SCOPE,
    DECISION_STEP_UP,
    EnforcementBoundaryAdapter,
    EnforcementRequest,
)

from app.enforcement_validation import (
    EnforcementValidationGate,
    EnforcementValidationResult,
    VALIDATION_ERROR,
    VALIDATION_FAILED,
    VALIDATION_PASSED,
    VALIDATION_READY,
    VALIDATION_REQUIRES_REVIEW,
    enforcement_is_executed_here,
    validate_enforcement_request,
)


def make_request(
    decision=DECISION_MONITOR,
    **kwargs,
):
    adapter = EnforcementBoundaryAdapter()

    return adapter.prepare_request(
        agent_id="agent-1",
        decision=decision,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Basic validation
# ---------------------------------------------------------------------------


def test_valid_request_passes_validation():
    request = make_request(
        projected_score=35,
        slope=4,
        confidence="MODERATE",
    )

    result = validate_enforcement_request(request)

    assert isinstance(result, EnforcementValidationResult)
    assert result.validation_status == VALIDATION_PASSED
    assert result.validation_state == VALIDATION_READY
    assert result.safe_to_forward is True
    assert result.issues == ()


def test_validation_preserves_request_identity():
    request = make_request()

    result = validate_enforcement_request(request)

    assert result.request_id == request.request_id
    assert result.agent_id == request.agent_id
    assert result.decision == request.decision


def test_validation_never_executes_enforcement():
    assert enforcement_is_executed_here() is False


# ---------------------------------------------------------------------------
# Decision coverage
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "decision",
    [
        DECISION_ALLOW,
        DECISION_MONITOR,
        DECISION_STEP_UP,
        DECISION_REDUCE_SCOPE,
        DECISION_HUMAN_REVIEW,
        DECISION_BLOCK,
    ],
)
def test_all_supported_decisions_validate(decision):
    request = make_request(decision)

    result = validate_enforcement_request(request)

    assert result.validation_status == VALIDATION_PASSED
    assert result.safe_to_forward is True


# ---------------------------------------------------------------------------
# Escalation consistency
# ---------------------------------------------------------------------------


def test_block_requires_escalated_boundary():
    request = make_request(DECISION_BLOCK)

    assert request.boundary_state == BOUNDARY_ESCALATED

    result = validate_enforcement_request(request)

    assert result.validation_status == VALIDATION_PASSED


def test_human_review_requires_escalated_boundary():
    request = make_request(DECISION_HUMAN_REVIEW)

    assert request.boundary_state == BOUNDARY_ESCALATED

    result = validate_enforcement_request(request)

    assert result.validation_status == VALIDATION_PASSED


def test_normal_decision_has_ready_boundary():
    request = make_request(DECISION_MONITOR)

    assert request.boundary_state == BOUNDARY_READY

    result = validate_enforcement_request(request)

    assert result.validation_status == VALIDATION_PASSED


# ---------------------------------------------------------------------------
# Tampered request detection
# ---------------------------------------------------------------------------


def test_tampered_request_mode_fails_validation():
    request = make_request()

    tampered = EnforcementRequest(
        **{
            **request.__dict__,
            "request_mode": "EXECUTE_NOW",
        }
    )

    result = validate_enforcement_request(tampered)

    assert result.validation_status == VALIDATION_FAILED
    assert result.safe_to_forward is False
    assert any(
        issue.code == "INVALID_REQUEST_MODE"
        for issue in result.issues
    )


def test_tampered_enforcement_flag_fails_validation():
    request = make_request()

    tampered = EnforcementRequest(
        **{
            **request.__dict__,
            "enforcement_required": False,
        }
    )

    result = validate_enforcement_request(tampered)

    assert result.validation_status == VALIDATION_FAILED
    assert result.safe_to_forward is False


def test_tampered_execution_flag_fails_validation():
    request = make_request()

    tampered_evidence = dict(request.evidence)
    tampered_evidence["execution_performed_here"] = True

    tampered = EnforcementRequest(
        **{
            **request.__dict__,
            "evidence": tampered_evidence,
        }
    )

    result = validate_enforcement_request(tampered)

    assert result.validation_status == VALIDATION_FAILED
    assert result.safe_to_forward is False


def test_tampered_decision_evidence_fails_validation():
    request = make_request()

    tampered_evidence = dict(request.evidence)
    tampered_evidence["decision"] = DECISION_BLOCK

    tampered = EnforcementRequest(
        **{
            **request.__dict__,
            "evidence": tampered_evidence,
        }
    )

    result = validate_enforcement_request(tampered)

    assert result.validation_status == VALIDATION_FAILED
    assert any(
        issue.code == "EVIDENCE_DECISION_MISMATCH"
        for issue in result.issues
    )


def test_tampered_boundary_evidence_fails_validation():
    request = make_request()

    tampered_evidence = dict(request.evidence)
    tampered_evidence["boundary_state"] = BOUNDARY_ESCALATED

    tampered = EnforcementRequest(
        **{
            **request.__dict__,
            "evidence": tampered_evidence,
        }
    )

    result = validate_enforcement_request(tampered)

    assert result.validation_status == VALIDATION_FAILED
    assert any(
        issue.code == "EVIDENCE_BOUNDARY_MISMATCH"
        for issue in result.issues
    )


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


def test_validation_evidence_contains_request_identity():
    request = make_request(
        projected_score=55,
        consequence_score=65,
        deviation_score=70,
    )

    result = validate_enforcement_request(request)

    assert result.evidence["request_id"] == request.request_id
    assert result.evidence["agent_id"] == "agent-1"
    assert result.evidence["decision"] == DECISION_MONITOR


def test_validation_evidence_preserves_source_evidence():
    request = make_request(
        evidence={
            "reason": "behavioral deterioration",
            "signals": ["deviation", "trajectory"],
        }
    )

    result = validate_enforcement_request(request)

    assert (
        result.evidence["source_evidence"]["reason"]
        == "behavioral deterioration"
    )


def test_validation_evidence_is_defensively_copied():
    source = {
        "signals": ["deviation"],
    }

    request = make_request(evidence=source)

    result = validate_enforcement_request(request)

    source["signals"].append("modified")

    assert result.evidence["source_evidence"]["signals"] == [
        "deviation"
    ]


# ---------------------------------------------------------------------------
# Score validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field_name",
    [
        "projected_score",
        "consequence_score",
        "deviation_score",
    ],
)
@pytest.mark.parametrize(
    "value",
    [-1, 101],
)
def test_invalid_scores_fail_validation(field_name, value):
    request = make_request()

    tampered = EnforcementRequest(
        **{
            **request.__dict__,
            field_name: value,
        }
    )

    result = validate_enforcement_request(tampered)

    assert result.validation_status == VALIDATION_FAILED
    assert result.safe_to_forward is False


# ---------------------------------------------------------------------------
# Invalid input object
# ---------------------------------------------------------------------------


def test_non_request_object_is_rejected():
    with pytest.raises(TypeError):
        validate_enforcement_request(object())


# ---------------------------------------------------------------------------
# Gate state management
# ---------------------------------------------------------------------------


def test_gate_stores_validation_result():
    gate = EnforcementValidationGate()

    request = make_request()

    result = gate.validate(request)

    assert gate.latest("agent-1") == result
    assert gate.history("agent-1") == (result,)


def test_gate_preserves_validation_order():
    gate = EnforcementValidationGate()

    first = gate.validate(
        make_request(DECISION_ALLOW)
    )

    second = gate.validate(
        make_request(DECISION_BLOCK)
    )

    assert gate.history("agent-1") == (
        first,
        second,
    )


def test_gate_latest_returns_none_for_unknown_agent():
    gate = EnforcementValidationGate()

    assert gate.latest("unknown") is None


def test_gate_snapshot_all_is_agent_isolated():
    gate = EnforcementValidationGate()

    gate.validate(
        make_request(DECISION_ALLOW)
    )

    adapter = EnforcementBoundaryAdapter()

    request2 = adapter.prepare_request(
        agent_id="agent-2",
        decision=DECISION_BLOCK,
    )

    gate.validate(request2)

    snapshot = gate.snapshot_all()

    assert set(snapshot) == {
        "agent-1",
        "agent-2",
    }

    assert len(snapshot["agent-1"]) == 1
    assert len(snapshot["agent-2"]) == 1


def test_gate_reset_one_agent():
    gate = EnforcementValidationGate()

    gate.validate(
        make_request()
    )

    adapter = EnforcementBoundaryAdapter()

    gate.validate(
        adapter.prepare_request(
            agent_id="agent-2",
            decision=DECISION_BLOCK,
        )
    )

    gate.reset("agent-1")

    assert gate.latest("agent-1") is None
    assert gate.latest("agent-2") is not None


def test_gate_reset_all():
    gate = EnforcementValidationGate()

    gate.validate(make_request())

    gate.reset()

    assert gate.snapshot_all() == {}


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


def test_validation_result_is_immutable():
    request = make_request()

    result = validate_enforcement_request(request)

    with pytest.raises(FrozenInstanceError):
        result.decision = DECISION_BLOCK


def test_validation_issue_is_immutable():
    request = make_request()

    result = validate_enforcement_request(request)

    assert result.issues == ()

    # The type itself is frozen and therefore safe for audit records.
    from app.enforcement_validation import ValidationIssue

    issue = ValidationIssue(
        code="TEST",
        severity=VALIDATION_ERROR,
        message="test",
    )

    with pytest.raises(FrozenInstanceError):
        issue.message = "modified"


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_identical_request_produces_identical_validation():
    adapter1 = EnforcementBoundaryAdapter()
    adapter2 = EnforcementBoundaryAdapter()

    request1 = adapter1.prepare_request(
        agent_id="agent-1",
        decision=DECISION_REDUCE_SCOPE,
        projected_score=65,
        slope=8,
        confidence="HIGH",
        consequence_score=75,
        deviation_score=70,
    )

    request2 = adapter2.prepare_request(
        agent_id="agent-1",
        decision=DECISION_REDUCE_SCOPE,
        projected_score=65,
        slope=8,
        confidence="HIGH",
        consequence_score=75,
        deviation_score=70,
    )

    result1 = validate_enforcement_request(request1)
    result2 = validate_enforcement_request(request2)

    assert result1.validation_status == result2.validation_status
    assert result1.validation_state == result2.validation_state
    assert result1.safe_to_forward == result2.safe_to_forward
    assert result1.issues == result2.issues
    assert result1.evidence == result2.evidence


# ---------------------------------------------------------------------------
# Security invariants
# ---------------------------------------------------------------------------


def test_validation_does_not_change_original_request():
    request = make_request(
        decision=DECISION_BLOCK,
        projected_score=90,
    )

    before = request

    result = validate_enforcement_request(request)

    assert request == before
    assert result.decision == DECISION_BLOCK


def test_block_validation_does_not_execute_block():
    request = make_request(
        decision=DECISION_BLOCK,
        projected_score=95,
        confidence="HIGH",
    )

    result = validate_enforcement_request(request)

    assert result.safe_to_forward is True
    assert result.decision == DECISION_BLOCK
    assert result.evidence["execution_performed_here"] is False


def test_allow_validation_does_not_execute_allow():
    request = make_request(
        decision=DECISION_ALLOW,
    )

    result = validate_enforcement_request(request)

    assert result.safe_to_forward is True
    assert result.decision == DECISION_ALLOW
    assert result.evidence["execution_performed_here"] is False


def test_no_universal_security_score_is_created():
    request = make_request(
        projected_score=70,
        consequence_score=80,
        deviation_score=75,
    )

    result = validate_enforcement_request(request)

    assert not hasattr(result, "overall_risk_score")
    assert not hasattr(result, "security_score")


# ---------------------------------------------------------------------------
# Optional values
# ---------------------------------------------------------------------------


def test_request_without_optional_scores_can_validate():
    request = make_request()

    result = validate_enforcement_request(request)

    assert result.validation_status == VALIDATION_PASSED
    assert result.safe_to_forward is True


# ---------------------------------------------------------------------------
# Validation state semantics
# ---------------------------------------------------------------------------


def test_clean_request_is_ready():
    request = make_request()

    result = validate_enforcement_request(request)

    assert result.validation_state == VALIDATION_READY


def test_warning_does_not_execute_enforcement():
    request = make_request()

    # A normal valid request remains ready. This test documents the
    # architectural invariant that validation itself has no execution path.
    result = validate_enforcement_request(request)

    assert result.evidence["execution_performed_here"] is False