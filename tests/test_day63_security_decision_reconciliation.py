"""
Tests for Varynx Day 63 - Security Decision Reconciliation Engine.
"""

import pytest

from app.security_decision_reconciliation import (
    DECISION_ALLOW,
    DECISION_BLOCK,
    DECISION_HUMAN_REVIEW,
    DECISION_MONITOR,
    DECISION_REDUCE_SCOPE,
    DECISION_STEP_UP,
    DIRECTION_DETERIORATING,
    DIRECTION_IMPROVING,
    DIRECTION_STABLE,
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MODERATE,
    RECONCILIATION_ESCALATED,
    RECONCILIATION_SUPPORTED,
    RECONCILIATION_WEAKENED,
    SecurityDecisionReconciliation,
    SecurityDecisionReconciliationEngine,
    build_reconciliation_evidence,
    reconcile_decision,
)


def test_supported_decision_is_preserved():
    decision, status = reconcile_decision(
        proposed_decision=DECISION_MONITOR,
        projected_score=30,
        direction=DIRECTION_STABLE,
        confidence=CONFIDENCE_HIGH,
    )

    assert decision == DECISION_MONITOR
    assert status == RECONCILIATION_SUPPORTED


def test_deteriorating_high_confidence_critical_evidence_escalates():
    decision, status = reconcile_decision(
        proposed_decision=DECISION_HUMAN_REVIEW,
        projected_score=90,
        direction=DIRECTION_DETERIORATING,
        confidence=CONFIDENCE_HIGH,
        consequence_score=85,
        deviation_score=80,
    )

    assert decision == DECISION_BLOCK
    assert status == RECONCILIATION_ESCALATED


def test_critical_deterioration_can_escalate_step_up():
    decision, status = reconcile_decision(
        proposed_decision=DECISION_STEP_UP,
        projected_score=75,
        direction=DIRECTION_DETERIORATING,
        confidence=CONFIDENCE_HIGH,
        consequence_score=80,
    )

    assert decision == DECISION_REDUCE_SCOPE
    assert status == RECONCILIATION_ESCALATED


def test_low_confidence_improving_evidence_can_weaken_review():
    decision, status = reconcile_decision(
        proposed_decision=DECISION_BLOCK,
        projected_score=75,
        direction=DIRECTION_IMPROVING,
        confidence=CONFIDENCE_LOW,
        consequence_score=10,
        deviation_score=10,
    )

    assert decision == DECISION_HUMAN_REVIEW
    assert status == RECONCILIATION_WEAKENED


def test_stable_behavior_does_not_escalate_by_itself():
    decision, status = reconcile_decision(
        proposed_decision=DECISION_STEP_UP,
        projected_score=60,
        direction=DIRECTION_STABLE,
        confidence=CONFIDENCE_HIGH,
        consequence_score=40,
        deviation_score=35,
    )

    assert decision == DECISION_STEP_UP
    assert status == RECONCILIATION_SUPPORTED


def test_improving_behavior_without_strong_decision_stays_supported():
    decision, status = reconcile_decision(
        proposed_decision=DECISION_ALLOW,
        projected_score=20,
        direction=DIRECTION_IMPROVING,
        confidence=CONFIDENCE_HIGH,
        consequence_score=10,
        deviation_score=10,
    )

    assert decision == DECISION_ALLOW
    assert status == RECONCILIATION_SUPPORTED


def test_consequence_score_is_optional():
    decision, status = reconcile_decision(
        proposed_decision=DECISION_MONITOR,
        projected_score=30,
        direction=DIRECTION_DETERIORATING,
        confidence=CONFIDENCE_MODERATE,
    )

    assert decision == DECISION_MONITOR
    assert status == RECONCILIATION_SUPPORTED


def test_deviation_score_is_optional():
    decision, status = reconcile_decision(
        proposed_decision=DECISION_STEP_UP,
        projected_score=50,
        direction=DIRECTION_STABLE,
        confidence=CONFIDENCE_HIGH,
        deviation_score=40,
    )

    assert decision == DECISION_STEP_UP
    assert status == RECONCILIATION_SUPPORTED


def test_engine_creates_snapshot():
    engine = SecurityDecisionReconciliationEngine()

    snapshot = engine.reconcile(
        agent_id="agent-1",
        proposed_decision=DECISION_STEP_UP,
        projected_score=60,
        direction=DIRECTION_DETERIORATING,
        slope=8,
        confidence=CONFIDENCE_HIGH,
        consequence_score=75,
        deviation_score=72,
    )

    assert isinstance(snapshot, SecurityDecisionReconciliation)
    assert snapshot.agent_id == "agent-1"
    assert snapshot.reconciled_decision == DECISION_REDUCE_SCOPE


def test_engine_latest():
    engine = SecurityDecisionReconciliationEngine()

    snapshot = engine.reconcile(
        agent_id="agent-1",
        proposed_decision=DECISION_MONITOR,
        projected_score=30,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    assert engine.latest("agent-1") == snapshot


def test_engine_history():
    engine = SecurityDecisionReconciliationEngine()

    engine.reconcile(
        agent_id="agent-1",
        proposed_decision=DECISION_ALLOW,
        projected_score=10,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    engine.reconcile(
        agent_id="agent-1",
        proposed_decision=DECISION_STEP_UP,
        projected_score=60,
        direction=DIRECTION_DETERIORATING,
        slope=10,
        confidence=CONFIDENCE_HIGH,
    )

    assert len(engine.history("agent-1")) == 2


def test_agent_state_isolated():
    engine = SecurityDecisionReconciliationEngine()

    first = engine.reconcile(
        agent_id="agent-1",
        proposed_decision=DECISION_ALLOW,
        projected_score=10,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    second = engine.reconcile(
        agent_id="agent-2",
        proposed_decision=DECISION_HUMAN_REVIEW,
        projected_score=90,
        direction=DIRECTION_DETERIORATING,
        slope=10,
        confidence=CONFIDENCE_HIGH,
        consequence_score=90,
    )

    assert engine.latest("agent-1") == first
    assert engine.latest("agent-2") == second


def test_snapshot_all_is_defensive():
    engine = SecurityDecisionReconciliationEngine()

    engine.reconcile(
        agent_id="agent-1",
        proposed_decision=DECISION_ALLOW,
        projected_score=10,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    snapshots = engine.snapshot_all()
    snapshots.clear()

    assert engine.latest("agent-1") is not None


def test_history_is_defensive():
    engine = SecurityDecisionReconciliationEngine()

    engine.reconcile(
        agent_id="agent-1",
        proposed_decision=DECISION_ALLOW,
        projected_score=10,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    history = engine.history("agent-1")
    history.clear()

    assert len(engine.history("agent-1")) == 1


def test_reset_agent():
    engine = SecurityDecisionReconciliationEngine()

    engine.reconcile(
        agent_id="agent-1",
        proposed_decision=DECISION_ALLOW,
        projected_score=10,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    engine.reset("agent-1")

    assert engine.latest("agent-1") is None
    assert engine.history("agent-1") == []


def test_reset_all():
    engine = SecurityDecisionReconciliationEngine()

    engine.reconcile(
        agent_id="agent-1",
        proposed_decision=DECISION_ALLOW,
        projected_score=10,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    engine.reconcile(
        agent_id="agent-2",
        proposed_decision=DECISION_MONITOR,
        projected_score=25,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    engine.reset()

    assert engine.snapshot_all() == {}


def test_evidence_contains_reconciliation_fields():
    evidence = build_reconciliation_evidence(
        proposed_decision=DECISION_STEP_UP,
        reconciled_decision=DECISION_REDUCE_SCOPE,
        status=RECONCILIATION_ESCALATED,
        projected_score=70,
        direction=DIRECTION_DETERIORATING,
        confidence=CONFIDENCE_HIGH,
        consequence_score=80,
        deviation_score=75,
        source_evidence=["high consequence exposure"],
    )

    assert any("Proposed decision" in item for item in evidence)
    assert any("Reconciled decision" in item for item in evidence)
    assert any("ESCALATED" in item for item in evidence)
    assert "high consequence exposure" in evidence


def test_source_evidence_is_preserved():
    engine = SecurityDecisionReconciliationEngine()

    snapshot = engine.reconcile(
        agent_id="agent-1",
        proposed_decision=DECISION_STEP_UP,
        projected_score=60,
        direction=DIRECTION_DETERIORATING,
        slope=5,
        confidence=CONFIDENCE_HIGH,
        evidence=[
            "trust decline",
            "resource deviation",
        ],
    )

    assert "trust decline" in snapshot.evidence
    assert "resource deviation" in snapshot.evidence


def test_snapshot_is_immutable():
    engine = SecurityDecisionReconciliationEngine()

    snapshot = engine.reconcile(
        agent_id="agent-1",
        proposed_decision=DECISION_ALLOW,
        projected_score=10,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    with pytest.raises(Exception):
        snapshot.reconciled_decision = DECISION_BLOCK


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
def test_all_decisions_are_supported(decision):
    result, status = reconcile_decision(
        proposed_decision=decision,
        projected_score=50,
        direction=DIRECTION_STABLE,
        confidence=CONFIDENCE_HIGH,
    )

    assert result == decision
    assert status == RECONCILIATION_SUPPORTED


def test_invalid_projected_score_rejected():
    with pytest.raises(ValueError):
        reconcile_decision(
            proposed_decision=DECISION_ALLOW,
            projected_score=101,
            direction=DIRECTION_STABLE,
            confidence=CONFIDENCE_HIGH,
        )


def test_invalid_consequence_score_rejected():
    with pytest.raises(ValueError):
        reconcile_decision(
            proposed_decision=DECISION_ALLOW,
            projected_score=20,
            direction=DIRECTION_STABLE,
            confidence=CONFIDENCE_HIGH,
            consequence_score=101,
        )


def test_invalid_deviation_score_rejected():
    with pytest.raises(ValueError):
        reconcile_decision(
            proposed_decision=DECISION_ALLOW,
            projected_score=20,
            direction=DIRECTION_STABLE,
            confidence=CONFIDENCE_HIGH,
            deviation_score=-1,
        )


def test_invalid_decision_rejected():
    with pytest.raises(ValueError):
        reconcile_decision(
            proposed_decision="INVALID",
            projected_score=20,
            direction=DIRECTION_STABLE,
            confidence=CONFIDENCE_HIGH,
        )


def test_invalid_direction_rejected():
    with pytest.raises(ValueError):
        reconcile_decision(
            proposed_decision=DECISION_ALLOW,
            projected_score=20,
            direction="INVALID",
            confidence=CONFIDENCE_HIGH,
        )


def test_invalid_confidence_rejected():
    with pytest.raises(ValueError):
        reconcile_decision(
            proposed_decision=DECISION_ALLOW,
            projected_score=20,
            direction=DIRECTION_STABLE,
            confidence="INVALID",
        )


def test_invalid_slope_rejected():
    engine = SecurityDecisionReconciliationEngine()

    with pytest.raises(ValueError):
        engine.reconcile(
            agent_id="agent-1",
            proposed_decision=DECISION_ALLOW,
            projected_score=20,
            direction=DIRECTION_STABLE,
            slope="invalid",
            confidence=CONFIDENCE_HIGH,
        )


def test_deterministic_reconciliation():
    kwargs = dict(
        proposed_decision=DECISION_STEP_UP,
        projected_score=75,
        direction=DIRECTION_DETERIORATING,
        confidence=CONFIDENCE_HIGH,
        consequence_score=80,
        deviation_score=75,
    )

    first = reconcile_decision(**kwargs)
    second = reconcile_decision(**kwargs)

    assert first == second


def test_reconciler_does_not_execute_action():
    engine = SecurityDecisionReconciliationEngine()

    snapshot = engine.reconcile(
        agent_id="agent-1",
        proposed_decision=DECISION_BLOCK,
        projected_score=95,
        direction=DIRECTION_DETERIORATING,
        slope=20,
        confidence=CONFIDENCE_HIGH,
        consequence_score=95,
        deviation_score=90,
    )

    assert snapshot.reconciled_decision == DECISION_BLOCK
    assert not hasattr(snapshot, "executed")
    assert not hasattr(snapshot, "authorization_result")


def test_reconciler_does_not_create_universal_score():
    engine = SecurityDecisionReconciliationEngine()

    snapshot = engine.reconcile(
        agent_id="agent-1",
        proposed_decision=DECISION_MONITOR,
        projected_score=30,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    assert not hasattr(snapshot, "overall_score")
    assert not hasattr(snapshot, "varynx_score")


def test_boundary_projected_score():
    decision, status = reconcile_decision(
        proposed_decision=DECISION_ALLOW,
        projected_score=0,
        direction=DIRECTION_STABLE,
        confidence=CONFIDENCE_HIGH,
    )

    assert decision == DECISION_ALLOW
    assert status == RECONCILIATION_SUPPORTED


def test_boundary_projected_score_100():
    decision, status = reconcile_decision(
        proposed_decision=DECISION_BLOCK,
        projected_score=100,
        direction=DIRECTION_DETERIORATING,
        confidence=CONFIDENCE_HIGH,
        consequence_score=100,
        deviation_score=100,
    )

    assert decision == DECISION_BLOCK
    assert status == RECONCILIATION_ESCALATED