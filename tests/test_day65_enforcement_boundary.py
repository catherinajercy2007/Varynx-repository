from __future__ import annotations

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
    REQUEST_ONLY,
    build_enforcement_evidence,
    determine_boundary_state,
    execution_is_performed_here,
    requires_external_enforcement,
)


# ---------------------------------------------------------------------------
# Boundary-state tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "decision",
    [
        DECISION_ALLOW,
        DECISION_MONITOR,
        DECISION_STEP_UP,
        DECISION_REDUCE_SCOPE,
    ],
)
def test_normal_decisions_are_boundary_ready(decision):
    assert determine_boundary_state(decision) == BOUNDARY_READY


@pytest.mark.parametrize(
    "decision",
    [
        DECISION_HUMAN_REVIEW,
        DECISION_BLOCK,
    ],
)
def test_escalated_decisions_are_boundary_escalated(decision):
    assert determine_boundary_state(decision) == BOUNDARY_ESCALATED


def test_all_decisions_require_external_enforcement_boundary():
    decisions = [
        DECISION_ALLOW,
        DECISION_MONITOR,
        DECISION_STEP_UP,
        DECISION_REDUCE_SCOPE,
        DECISION_HUMAN_REVIEW,
        DECISION_BLOCK,
    ]

    for decision in decisions:
        assert requires_external_enforcement(decision) is True


def test_execution_is_never_performed_here():
    assert execution_is_performed_here() is False


# ---------------------------------------------------------------------------
# Evidence tests
# ---------------------------------------------------------------------------


def test_evidence_contains_boundary_information():
    evidence = build_enforcement_evidence(
        decision=DECISION_BLOCK,
        boundary_state=BOUNDARY_ESCALATED,
        projected_score=92,
        slope=12,
        confidence="HIGH",
    )

    assert evidence["decision"] == DECISION_BLOCK
    assert evidence["boundary_state"] == BOUNDARY_ESCALATED
    assert evidence["execution_performed_here"] is False
    assert evidence["external_enforcement_required"] is True
    assert evidence["projected_score"] == 92.0
    assert evidence["slope"] == 12.0
    assert evidence["confidence"] == "HIGH"


def test_source_evidence_is_preserved():
    source = {
        "reason": "persistent behavioral deviation",
        "signals": ["deviation", "consequence"],
    }

    evidence = build_enforcement_evidence(
        decision=DECISION_REDUCE_SCOPE,
        boundary_state=BOUNDARY_READY,
        evidence=source,
    )

    assert evidence["source_evidence"] == source


def test_source_evidence_is_defensively_copied():
    source = {
        "signals": ["deviation"],
    }

    evidence = build_enforcement_evidence(
        decision=DECISION_MONITOR,
        boundary_state=BOUNDARY_READY,
        evidence=source,
    )

    source["signals"].append("modified")

    assert evidence["source_evidence"]["signals"] == ["deviation"]


# ---------------------------------------------------------------------------
# Request construction
# ---------------------------------------------------------------------------


def test_prepare_request_creates_immutable_request():
    adapter = EnforcementBoundaryAdapter()

    request = adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_MONITOR,
        projected_score=32,
        slope=4,
        confidence="MODERATE",
    )

    assert isinstance(request, EnforcementRequest)
    assert request.agent_id == "agent-1"
    assert request.decision == DECISION_MONITOR
    assert request.boundary_state == BOUNDARY_READY
    assert request.request_mode == REQUEST_ONLY
    assert request.enforcement_required is True


def test_block_request_is_escalated():
    adapter = EnforcementBoundaryAdapter()

    request = adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_BLOCK,
        projected_score=95,
        confidence="HIGH",
    )

    assert request.boundary_state == BOUNDARY_ESCALATED
    assert request.decision == DECISION_BLOCK


def test_human_review_request_is_escalated():
    adapter = EnforcementBoundaryAdapter()

    request = adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_HUMAN_REVIEW,
        projected_score=78,
        confidence="HIGH",
    )

    assert request.boundary_state == BOUNDARY_ESCALATED


# ---------------------------------------------------------------------------
# Request identifiers
# ---------------------------------------------------------------------------


def test_request_ids_are_deterministic_for_sequence():
    adapter = EnforcementBoundaryAdapter()

    first = adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_MONITOR,
    )

    second = adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_STEP_UP,
    )

    assert first.request_id == "agent-1-enforcement-1"
    assert second.request_id == "agent-1-enforcement-2"


def test_request_counters_are_isolated_by_agent():
    adapter = EnforcementBoundaryAdapter()

    first = adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_MONITOR,
    )

    second = adapter.prepare_request(
        agent_id="agent-2",
        decision=DECISION_MONITOR,
    )

    assert first.request_id == "agent-1-enforcement-1"
    assert second.request_id == "agent-2-enforcement-1"


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


def test_latest_returns_latest_request():
    adapter = EnforcementBoundaryAdapter()

    adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_MONITOR,
    )

    latest = adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_STEP_UP,
    )

    assert adapter.latest("agent-1") == latest


def test_latest_returns_none_for_unknown_agent():
    adapter = EnforcementBoundaryAdapter()

    assert adapter.latest("unknown") is None


def test_history_preserves_order():
    adapter = EnforcementBoundaryAdapter()

    first = adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_ALLOW,
    )

    second = adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_MONITOR,
    )

    third = adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_BLOCK,
    )

    assert adapter.history("agent-1") == (
        first,
        second,
        third,
    )


def test_history_is_isolated_between_agents():
    adapter = EnforcementBoundaryAdapter()

    adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_MONITOR,
    )

    adapter.prepare_request(
        agent_id="agent-2",
        decision=DECISION_BLOCK,
    )

    assert len(adapter.history("agent-1")) == 1
    assert len(adapter.history("agent-2")) == 1


def test_snapshot_all_returns_all_agents():
    adapter = EnforcementBoundaryAdapter()

    adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_MONITOR,
    )

    adapter.prepare_request(
        agent_id="agent-2",
        decision=DECISION_BLOCK,
    )

    snapshot = adapter.snapshot_all()

    assert set(snapshot.keys()) == {"agent-1", "agent-2"}
    assert len(snapshot["agent-1"]) == 1
    assert len(snapshot["agent-2"]) == 1


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


def test_reset_one_agent():
    adapter = EnforcementBoundaryAdapter()

    adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_MONITOR,
    )

    adapter.prepare_request(
        agent_id="agent-2",
        decision=DECISION_BLOCK,
    )

    adapter.reset("agent-1")

    assert adapter.latest("agent-1") is None
    assert adapter.latest("agent-2") is not None


def test_reset_all_agents():
    adapter = EnforcementBoundaryAdapter()

    adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_MONITOR,
    )

    adapter.prepare_request(
        agent_id="agent-2",
        decision=DECISION_BLOCK,
    )

    adapter.reset()

    assert adapter.latest("agent-1") is None
    assert adapter.latest("agent-2") is None
    assert adapter.snapshot_all() == {}


def test_reset_restarts_request_counter():
    adapter = EnforcementBoundaryAdapter()

    adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_MONITOR,
    )

    adapter.reset("agent-1")

    request = adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_ALLOW,
    )

    assert request.request_id == "agent-1-enforcement-1"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_invalid_agent_id_is_rejected():
    adapter = EnforcementBoundaryAdapter()

    with pytest.raises((TypeError, ValueError)):
        adapter.prepare_request(
            agent_id="",
            decision=DECISION_ALLOW,
        )


def test_invalid_decision_is_rejected():
    adapter = EnforcementBoundaryAdapter()

    with pytest.raises(ValueError):
        adapter.prepare_request(
            agent_id="agent-1",
            decision="INVALID",
        )


@pytest.mark.parametrize(
    "score",
    [-1, 101, float("inf"), float("-inf")],
)
def test_invalid_projected_score_is_rejected(score):
    adapter = EnforcementBoundaryAdapter()

    with pytest.raises((TypeError, ValueError)):
        adapter.prepare_request(
            agent_id="agent-1",
            decision=DECISION_MONITOR,
            projected_score=score,
        )


def test_invalid_slope_type_is_rejected():
    adapter = EnforcementBoundaryAdapter()

    with pytest.raises(TypeError):
        adapter.prepare_request(
            agent_id="agent-1",
            decision=DECISION_MONITOR,
            slope="bad",
        )


@pytest.mark.parametrize(
    "score",
    [-1, 101],
)
def test_invalid_consequence_score_is_rejected(score):
    adapter = EnforcementBoundaryAdapter()

    with pytest.raises(ValueError):
        adapter.prepare_request(
            agent_id="agent-1",
            decision=DECISION_MONITOR,
            consequence_score=score,
        )


@pytest.mark.parametrize(
    "score",
    [-1, 101],
)
def test_invalid_deviation_score_is_rejected(score):
    adapter = EnforcementBoundaryAdapter()

    with pytest.raises(ValueError):
        adapter.prepare_request(
            agent_id="agent-1",
            decision=DECISION_MONITOR,
            deviation_score=score,
        )


# ---------------------------------------------------------------------------
# Optional values
# ---------------------------------------------------------------------------


def test_optional_values_can_be_omitted():
    adapter = EnforcementBoundaryAdapter()

    request = adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_ALLOW,
    )

    assert request.projected_score is None
    assert request.slope is None
    assert request.confidence is None
    assert request.reconciliation_status is None
    assert request.consequence_score is None
    assert request.deviation_score is None


def test_all_security_context_values_are_preserved():
    adapter = EnforcementBoundaryAdapter()

    request = adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_REDUCE_SCOPE,
        projected_score=68,
        slope=8,
        confidence="HIGH",
        reconciliation_status="ESCALATED",
        consequence_score=82,
        deviation_score=74,
        evidence={
            "source": "day63",
            "reason": "independent evidence",
        },
    )

    assert request.projected_score == 68.0
    assert request.slope == 8.0
    assert request.confidence == "HIGH"
    assert request.reconciliation_status == "ESCALATED"
    assert request.consequence_score == 82.0
    assert request.deviation_score == 74.0

    assert request.evidence["source_evidence"]["source"] == "day63"


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


def test_request_is_frozen():
    adapter = EnforcementBoundaryAdapter()

    request = adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_MONITOR,
    )

    with pytest.raises(AttributeError):
        request.decision = DECISION_BLOCK


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_same_input_produces_same_security_fields():
    adapter1 = EnforcementBoundaryAdapter()
    adapter2 = EnforcementBoundaryAdapter()

    request1 = adapter1.prepare_request(
        agent_id="agent-1",
        decision=DECISION_REDUCE_SCOPE,
        projected_score=65,
        slope=7,
        confidence="HIGH",
        consequence_score=72,
        deviation_score=68,
    )

    request2 = adapter2.prepare_request(
        agent_id="agent-1",
        decision=DECISION_REDUCE_SCOPE,
        projected_score=65,
        slope=7,
        confidence="HIGH",
        consequence_score=72,
        deviation_score=68,
    )

    assert request1.decision == request2.decision
    assert request1.boundary_state == request2.boundary_state
    assert request1.projected_score == request2.projected_score
    assert request1.slope == request2.slope
    assert request1.confidence == request2.confidence
    assert request1.consequence_score == request2.consequence_score
    assert request1.deviation_score == request2.deviation_score
    assert request1.evidence == request2.evidence


# ---------------------------------------------------------------------------
# Security boundary invariants
# ---------------------------------------------------------------------------


def test_allow_is_still_explicitly_request_only():
    adapter = EnforcementBoundaryAdapter()

    request = adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_ALLOW,
    )

    assert request.request_mode == REQUEST_ONLY
    assert request.enforcement_required is True
    assert request.evidence["execution_performed_here"] is False


def test_block_is_not_executed_by_adapter():
    adapter = EnforcementBoundaryAdapter()

    request = adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_BLOCK,
    )

    assert request.decision == DECISION_BLOCK
    assert request.request_mode == REQUEST_ONLY
    assert request.evidence["execution_performed_here"] is False


def test_adapter_does_not_create_universal_risk_score():
    adapter = EnforcementBoundaryAdapter()

    request = adapter.prepare_request(
        agent_id="agent-1",
        decision=DECISION_HUMAN_REVIEW,
        projected_score=75,
        consequence_score=80,
        deviation_score=70,
    )

    assert not hasattr(request, "overall_risk_score")
    assert not hasattr(request, "security_score")


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
def test_all_supported_decisions_create_requests(decision):
    adapter = EnforcementBoundaryAdapter()

    request = adapter.prepare_request(
        agent_id="agent-1",
        decision=decision,
    )

    assert request.decision == decision
    assert request.request_mode == REQUEST_ONLY
    assert request.enforcement_required is True