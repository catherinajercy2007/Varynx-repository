"""
Tests for Varynx Day 62 - Behavioral Security Decision Bridge.
"""

import pytest

from app.security_decision_bridge import (
    BehavioralSecurityDecisionBridge,
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
    SecurityDecisionSnapshot,
    build_decision_evidence,
    calculate_decision_priority,
    classify_security_decision,
)


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


def test_low_score_allows():
    assert (
        classify_security_decision(
            10,
            DIRECTION_STABLE,
            CONFIDENCE_HIGH,
        )
        == DECISION_ALLOW
    )


def test_moderate_deteriorating_monitors():
    assert (
        classify_security_decision(
            30,
            DIRECTION_DETERIORATING,
            CONFIDENCE_MODERATE,
        )
        == DECISION_MONITOR
    )


def test_moderate_stable_allows():
    assert (
        classify_security_decision(
            30,
            DIRECTION_STABLE,
            CONFIDENCE_HIGH,
        )
        == DECISION_ALLOW
    )


def test_high_deteriorating_high_confidence_reduces_scope():
    assert (
        classify_security_decision(
            60,
            DIRECTION_DETERIORATING,
            CONFIDENCE_HIGH,
        )
        == DECISION_REDUCE_SCOPE
    )


def test_high_deteriorating_low_confidence_steps_up():
    assert (
        classify_security_decision(
            60,
            DIRECTION_DETERIORATING,
            CONFIDENCE_LOW,
        )
        == DECISION_STEP_UP
    )


def test_high_stable_high_confidence_steps_up():
    assert (
        classify_security_decision(
            60,
            DIRECTION_STABLE,
            CONFIDENCE_HIGH,
        )
        == DECISION_STEP_UP
    )


def test_critical_deteriorating_high_confidence_blocks():
    assert (
        classify_security_decision(
            85,
            DIRECTION_DETERIORATING,
            CONFIDENCE_HIGH,
        )
        == DECISION_BLOCK
    )


def test_critical_deteriorating_moderate_confidence_human_review():
    assert (
        classify_security_decision(
            85,
            DIRECTION_DETERIORATING,
            CONFIDENCE_MODERATE,
        )
        == DECISION_HUMAN_REVIEW
    )


def test_critical_stable_high_confidence_human_review():
    assert (
        classify_security_decision(
            85,
            DIRECTION_STABLE,
            CONFIDENCE_HIGH,
        )
        == DECISION_HUMAN_REVIEW
    )


def test_critical_improving_low_confidence_steps_up():
    assert (
        classify_security_decision(
            85,
            DIRECTION_IMPROVING,
            CONFIDENCE_LOW,
        )
        == DECISION_STEP_UP
    )


# ---------------------------------------------------------------------------
# Priority
# ---------------------------------------------------------------------------


def test_priority_increases_with_positive_slope():
    base = calculate_decision_priority(
        50,
        0,
        DECISION_STEP_UP,
    )

    rising = calculate_decision_priority(
        50,
        10,
        DECISION_STEP_UP,
    )

    assert rising > base


def test_negative_slope_does_not_add_escalation_pressure():
    assert (
        calculate_decision_priority(
            50,
            -10,
            DECISION_STEP_UP,
        )
        == 50
    )


def test_priority_is_bounded():
    result = calculate_decision_priority(
        100,
        100,
        DECISION_BLOCK,
    )

    assert result == 100


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


def test_decision_evidence_contains_core_fields():
    evidence = build_decision_evidence(
        projected_score=70,
        direction=DIRECTION_DETERIORATING,
        confidence=CONFIDENCE_HIGH,
        decision=DECISION_BLOCK,
        source_evidence=["high consequence exposure"],
    )

    assert any("Projected security score" in item for item in evidence)
    assert any("Behavioral direction" in item for item in evidence)
    assert any("Prediction confidence" in item for item in evidence)
    assert any("BLOCK" in item for item in evidence)
    assert "high consequence exposure" in evidence


def test_evidence_is_defensive_copy():
    source = ["evidence-a"]

    evidence = build_decision_evidence(
        30,
        DIRECTION_STABLE,
        CONFIDENCE_MODERATE,
        DECISION_ALLOW,
        source,
    )

    source.append("evidence-b")

    assert "evidence-b" not in evidence


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


def test_engine_creates_snapshot():
    engine = BehavioralSecurityDecisionBridge()

    snapshot = engine.evaluate(
        agent_id="agent-1",
        projected_score=60,
        direction=DIRECTION_DETERIORATING,
        slope=8,
        confidence=CONFIDENCE_HIGH,
    )

    assert isinstance(snapshot, SecurityDecisionSnapshot)
    assert snapshot.agent_id == "agent-1"
    assert snapshot.decision == DECISION_REDUCE_SCOPE


def test_engine_records_latest():
    engine = BehavioralSecurityDecisionBridge()

    created = engine.evaluate(
        agent_id="agent-1",
        projected_score=20,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    assert engine.latest("agent-1") == created


def test_engine_records_history():
    engine = BehavioralSecurityDecisionBridge()

    engine.evaluate(
        agent_id="agent-1",
        projected_score=20,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    engine.evaluate(
        agent_id="agent-1",
        projected_score=60,
        direction=DIRECTION_DETERIORATING,
        slope=10,
        confidence=CONFIDENCE_HIGH,
    )

    assert len(engine.history("agent-1")) == 2


def test_agent_state_is_isolated():
    engine = BehavioralSecurityDecisionBridge()

    first = engine.evaluate(
        agent_id="agent-1",
        projected_score=10,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    second = engine.evaluate(
        agent_id="agent-2",
        projected_score=85,
        direction=DIRECTION_DETERIORATING,
        slope=10,
        confidence=CONFIDENCE_HIGH,
    )

    assert engine.latest("agent-1") == first
    assert engine.latest("agent-2") == second
    assert len(engine.history("agent-1")) == 1
    assert len(engine.history("agent-2")) == 1


def test_snapshot_all_is_defensive():
    engine = BehavioralSecurityDecisionBridge()

    engine.evaluate(
        agent_id="agent-1",
        projected_score=10,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    snapshots = engine.snapshot_all()

    snapshots.clear()

    assert engine.latest("agent-1") is not None


def test_history_is_defensive():
    engine = BehavioralSecurityDecisionBridge()

    engine.evaluate(
        agent_id="agent-1",
        projected_score=10,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    history = engine.history("agent-1")
    history.clear()

    assert len(engine.history("agent-1")) == 1


def test_reset_single_agent():
    engine = BehavioralSecurityDecisionBridge()

    engine.evaluate(
        agent_id="agent-1",
        projected_score=10,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    engine.evaluate(
        agent_id="agent-2",
        projected_score=20,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    engine.reset("agent-1")

    assert engine.latest("agent-1") is None
    assert engine.latest("agent-2") is not None


def test_reset_all():
    engine = BehavioralSecurityDecisionBridge()

    engine.evaluate(
        agent_id="agent-1",
        projected_score=10,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    engine.evaluate(
        agent_id="agent-2",
        projected_score=20,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    engine.reset()

    assert engine.snapshot_all() == {}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "score",
    [-1, 101, "invalid"],
)
def test_invalid_score_rejected(score):
    with pytest.raises(ValueError):
        classify_security_decision(
            score,
            DIRECTION_STABLE,
            CONFIDENCE_HIGH,
        )


def test_invalid_direction_rejected():
    with pytest.raises(ValueError):
        classify_security_decision(
            50,
            "UNKNOWN",
            CONFIDENCE_HIGH,
        )


def test_invalid_confidence_rejected():
    with pytest.raises(ValueError):
        classify_security_decision(
            50,
            DIRECTION_STABLE,
            "UNKNOWN",
        )


def test_invalid_agent_id_rejected():
    engine = BehavioralSecurityDecisionBridge()

    with pytest.raises(ValueError):
        engine.evaluate(
            agent_id="",
            projected_score=20,
            direction=DIRECTION_STABLE,
            slope=0,
            confidence=CONFIDENCE_HIGH,
        )


def test_invalid_evidence_rejected():
    engine = BehavioralSecurityDecisionBridge()

    with pytest.raises(ValueError):
        engine.evaluate(
            agent_id="agent-1",
            projected_score=20,
            direction=DIRECTION_STABLE,
            slope=0,
            confidence=CONFIDENCE_HIGH,
            evidence="not-a-list",
        )


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_same_input_produces_same_decision():
    engine = BehavioralSecurityDecisionBridge()

    first = engine.evaluate(
        agent_id="agent-1",
        projected_score=65,
        direction=DIRECTION_DETERIORATING,
        slope=7,
        confidence=CONFIDENCE_HIGH,
    )

    second = engine.evaluate(
        agent_id="agent-2",
        projected_score=65,
        direction=DIRECTION_DETERIORATING,
        slope=7,
        confidence=CONFIDENCE_HIGH,
    )

    assert first.decision == second.decision
    assert first.priority == second.priority


def test_snapshot_is_immutable():
    engine = BehavioralSecurityDecisionBridge()

    snapshot = engine.evaluate(
        agent_id="agent-1",
        projected_score=20,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    with pytest.raises(Exception):
        snapshot.decision = DECISION_BLOCK


# ---------------------------------------------------------------------------
# Architectural boundaries
# ---------------------------------------------------------------------------


def test_bridge_does_not_execute_security_action():
    engine = BehavioralSecurityDecisionBridge()

    snapshot = engine.evaluate(
        agent_id="agent-1",
        projected_score=90,
        direction=DIRECTION_DETERIORATING,
        slope=20,
        confidence=CONFIDENCE_HIGH,
    )

    assert snapshot.decision == DECISION_BLOCK

    # The bridge only recommends a decision.
    assert not hasattr(snapshot, "executed")
    assert not hasattr(snapshot, "authorization_result")


def test_bridge_does_not_create_universal_score():
    engine = BehavioralSecurityDecisionBridge()

    snapshot = engine.evaluate(
        agent_id="agent-1",
        projected_score=60,
        direction=DIRECTION_DETERIORATING,
        slope=10,
        confidence=CONFIDENCE_HIGH,
    )

    assert hasattr(snapshot, "projected_score")
    assert hasattr(snapshot, "decision")

    # No "overall Varynx score" is produced.
    assert not hasattr(snapshot, "overall_score")
    assert not hasattr(snapshot, "varynx_score")


def test_improving_behavior_can_reduce_escalation():
    engine = BehavioralSecurityDecisionBridge()

    snapshot = engine.evaluate(
        agent_id="agent-1",
        projected_score=60,
        direction=DIRECTION_IMPROVING,
        slope=-8,
        confidence=CONFIDENCE_HIGH,
    )

    assert snapshot.decision == DECISION_STEP_UP


def test_boundary_score_20():
    assert (
        classify_security_decision(
            20,
            DIRECTION_STABLE,
            CONFIDENCE_HIGH,
        )
        == DECISION_ALLOW
    )


def test_boundary_score_40():
    assert (
        classify_security_decision(
            40,
            DIRECTION_STABLE,
            CONFIDENCE_HIGH,
        )
        == DECISION_STEP_UP
    )


def test_boundary_score_70():
    assert (
        classify_security_decision(
            70,
            DIRECTION_DETERIORATING,
            CONFIDENCE_HIGH,
        )
        == DECISION_BLOCK
    )


def test_boundary_score_100():
    snapshot = BehavioralSecurityDecisionBridge().evaluate(
        agent_id="agent-1",
        projected_score=100,
        direction=DIRECTION_DETERIORATING,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    assert snapshot.decision == DECISION_BLOCK
    assert snapshot.priority == 100


def test_source_evidence_is_preserved():
    engine = BehavioralSecurityDecisionBridge()

    snapshot = engine.evaluate(
        agent_id="agent-1",
        projected_score=75,
        direction=DIRECTION_DETERIORATING,
        slope=5,
        confidence=CONFIDENCE_HIGH,
        evidence=[
            "high behavioral deviation",
            "declining trust",
        ],
    )

    assert "high behavioral deviation" in snapshot.evidence
    assert "declining trust" in snapshot.evidence


def test_latest_changes_after_new_evaluation():
    engine = BehavioralSecurityDecisionBridge()

    first = engine.evaluate(
        agent_id="agent-1",
        projected_score=10,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
    )

    second = engine.evaluate(
        agent_id="agent-1",
        projected_score=85,
        direction=DIRECTION_DETERIORATING,
        slope=10,
        confidence=CONFIDENCE_HIGH,
    )

    assert engine.latest("agent-1") == second
    assert engine.latest("agent-1") != first