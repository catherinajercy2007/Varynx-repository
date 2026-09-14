import pytest

from app.predictive_runtime import (
    CONFIDENCE_HIGH,
    CONTROL_HUMAN_REVIEW,
    CONTROL_INCREASE_MONITORING,
    CONTROL_MAINTAIN,
    CONTROL_PREEMPTIVE_BLOCK,
    CONTROL_REDUCE_SCOPE,
    CONTROL_STEP_UP_VERIFICATION,
    DIRECTION_DETERIORATING,
    DIRECTION_IMPROVING,
    DIRECTION_INSUFFICIENT_DATA,
    DIRECTION_STABLE,
    RUNTIME_ESCALATED,
    RUNTIME_READY,
    PredictiveRuntimeIntegration,
    determine_runtime_state,
    requires_explicit_execution,
)


def test_maintain_is_runtime_ready():
    assert (
        determine_runtime_state(
            CONTROL_MAINTAIN
        )
        == RUNTIME_READY
    )


def test_monitoring_is_runtime_ready():
    assert (
        determine_runtime_state(
            CONTROL_INCREASE_MONITORING
        )
        == RUNTIME_READY
    )


def test_reduce_scope_is_runtime_ready():
    assert (
        determine_runtime_state(
            CONTROL_REDUCE_SCOPE
        )
        == RUNTIME_READY
    )


def test_step_up_is_runtime_ready():
    assert (
        determine_runtime_state(
            CONTROL_STEP_UP_VERIFICATION
        )
        == RUNTIME_READY
    )


def test_human_review_is_escalated():
    assert (
        determine_runtime_state(
            CONTROL_HUMAN_REVIEW
        )
        == RUNTIME_ESCALATED
    )


def test_preemptive_block_is_escalated():
    assert (
        determine_runtime_state(
            CONTROL_PREEMPTIVE_BLOCK
        )
        == RUNTIME_ESCALATED
    )


def test_every_recommendation_requires_explicit_execution():
    controls = [
        CONTROL_MAINTAIN,
        CONTROL_INCREASE_MONITORING,
        CONTROL_REDUCE_SCOPE,
        CONTROL_STEP_UP_VERIFICATION,
        CONTROL_HUMAN_REVIEW,
        CONTROL_PREEMPTIVE_BLOCK,
    ]

    for control in controls:
        assert (
            requires_explicit_execution(
                control
            )
            is True
        )


def test_prepare_runtime_decision():
    integration = PredictiveRuntimeIntegration()

    decision = integration.prepare_decision(
        agent_id="agent-1",
        projected_score=60,
        direction=DIRECTION_DETERIORATING,
        slope=10,
        confidence=CONFIDENCE_HIGH,
        recommendation=CONTROL_REDUCE_SCOPE,
    )

    assert decision.agent_id == "agent-1"
    assert decision.projected_score == 60
    assert decision.direction == DIRECTION_DETERIORATING
    assert decision.recommendation == CONTROL_REDUCE_SCOPE
    assert decision.runtime_state == RUNTIME_READY
    assert decision.execution_required is True


def test_critical_recommendation_is_escalated():
    integration = PredictiveRuntimeIntegration()

    decision = integration.prepare_decision(
        agent_id="agent-1",
        projected_score=90,
        direction=DIRECTION_DETERIORATING,
        slope=20,
        confidence=CONFIDENCE_HIGH,
        recommendation=CONTROL_PREEMPTIVE_BLOCK,
    )

    assert decision.runtime_state == RUNTIME_ESCALATED
    assert decision.recommendation == CONTROL_PREEMPTIVE_BLOCK


def test_human_review_is_escalated():
    integration = PredictiveRuntimeIntegration()

    decision = integration.prepare_decision(
        agent_id="agent-1",
        projected_score=90,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
        recommendation=CONTROL_HUMAN_REVIEW,
    )

    assert decision.runtime_state == RUNTIME_ESCALATED


def test_insufficient_data_can_maintain():
    integration = PredictiveRuntimeIntegration()

    decision = integration.prepare_decision(
        agent_id="agent-1",
        projected_score=80,
        direction=DIRECTION_INSUFFICIENT_DATA,
        slope=0,
        confidence="LOW",
        recommendation=CONTROL_MAINTAIN,
    )

    assert decision.runtime_state == RUNTIME_READY
    assert decision.recommendation == CONTROL_MAINTAIN


def test_improving_behavior_can_maintain():
    integration = PredictiveRuntimeIntegration()

    decision = integration.prepare_decision(
        agent_id="agent-1",
        projected_score=30,
        direction=DIRECTION_IMPROVING,
        slope=-10,
        confidence=CONFIDENCE_HIGH,
        recommendation=CONTROL_MAINTAIN,
    )

    assert decision.runtime_state == RUNTIME_READY


def test_latest_returns_latest_decision():
    integration = PredictiveRuntimeIntegration()

    decision = integration.prepare_decision(
        agent_id="agent-1",
        projected_score=50,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
        recommendation=CONTROL_STEP_UP_VERIFICATION,
    )

    assert (
        integration.latest("agent-1")
        == decision
    )


def test_multiple_agents_are_isolated():
    integration = PredictiveRuntimeIntegration()

    first = integration.prepare_decision(
        agent_id="agent-1",
        projected_score=20,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence=CONFIDENCE_HIGH,
        recommendation=CONTROL_MAINTAIN,
    )

    second = integration.prepare_decision(
        agent_id="agent-2",
        projected_score=90,
        direction=DIRECTION_DETERIORATING,
        slope=20,
        confidence=CONFIDENCE_HIGH,
        recommendation=CONTROL_PREEMPTIVE_BLOCK,
    )

    assert (
        integration.latest("agent-1")
        == first
    )

    assert (
        integration.latest("agent-2")
        == second
    )


def test_snapshot_all():
    integration = PredictiveRuntimeIntegration()

    integration.prepare_decision(
        "agent-1",
        20,
        DIRECTION_STABLE,
        0,
        CONFIDENCE_HIGH,
        CONTROL_MAINTAIN,
    )

    integration.prepare_decision(
        "agent-2",
        80,
        DIRECTION_DETERIORATING,
        10,
        CONFIDENCE_HIGH,
        CONTROL_REDUCE_SCOPE,
    )

    snapshots = integration.snapshot_all()

    assert len(snapshots) == 2
    assert {
        item.agent_id
        for item in snapshots
    } == {
        "agent-1",
        "agent-2",
    }


def test_reset_single_agent():
    integration = PredictiveRuntimeIntegration()

    integration.prepare_decision(
        "agent-1",
        20,
        DIRECTION_STABLE,
        0,
        CONFIDENCE_HIGH,
        CONTROL_MAINTAIN,
    )

    integration.prepare_decision(
        "agent-2",
        80,
        DIRECTION_DETERIORATING,
        10,
        CONFIDENCE_HIGH,
        CONTROL_REDUCE_SCOPE,
    )

    integration.reset("agent-1")

    assert integration.latest("agent-1") is None
    assert integration.latest("agent-2") is not None


def test_reset_all():
    integration = PredictiveRuntimeIntegration()

    integration.prepare_decision(
        "agent-1",
        20,
        DIRECTION_STABLE,
        0,
        CONFIDENCE_HIGH,
        CONTROL_MAINTAIN,
    )

    integration.prepare_decision(
        "agent-2",
        80,
        DIRECTION_DETERIORATING,
        10,
        CONFIDENCE_HIGH,
        CONTROL_REDUCE_SCOPE,
    )

    integration.reset()

    assert integration.snapshot_all() == ()


def test_custom_evidence_is_preserved():
    integration = PredictiveRuntimeIntegration()

    decision = integration.prepare_decision(
        agent_id="agent-1",
        projected_score=60,
        direction=DIRECTION_DETERIORATING,
        slope=10,
        confidence=CONFIDENCE_HIGH,
        recommendation=CONTROL_REDUCE_SCOPE,
        evidence=[
            "External behavioral evidence",
            "Context evidence",
        ],
    )

    assert (
        "External behavioral evidence"
        in decision.evidence
    )

    assert (
        "Context evidence"
        in decision.evidence
    )


def test_generated_evidence_is_present():
    integration = PredictiveRuntimeIntegration()

    decision = integration.prepare_decision(
        agent_id="agent-1",
        projected_score=60,
        direction=DIRECTION_DETERIORATING,
        slope=10,
        confidence=CONFIDENCE_HIGH,
        recommendation=CONTROL_REDUCE_SCOPE,
    )

    assert any(
        "Projected security score"
        in item
        for item in decision.evidence
    )

    assert any(
        "Predictive recommendation"
        in item
        for item in decision.evidence
    )


def test_immutable_snapshot():
    integration = PredictiveRuntimeIntegration()

    decision = integration.prepare_decision(
        agent_id="agent-1",
        projected_score=60,
        direction=DIRECTION_DETERIORATING,
        slope=10,
        confidence=CONFIDENCE_HIGH,
        recommendation=CONTROL_REDUCE_SCOPE,
    )

    with pytest.raises(AttributeError):
        decision.recommendation = CONTROL_MAINTAIN


def test_invalid_agent_id():
    integration = PredictiveRuntimeIntegration()

    with pytest.raises(ValueError):
        integration.prepare_decision(
            "",
            50,
            DIRECTION_STABLE,
            0,
            CONFIDENCE_HIGH,
            CONTROL_MAINTAIN,
        )


def test_invalid_score():
    integration = PredictiveRuntimeIntegration()

    with pytest.raises(ValueError):
        integration.prepare_decision(
            "agent-1",
            101,
            DIRECTION_STABLE,
            0,
            CONFIDENCE_HIGH,
            CONTROL_MAINTAIN,
        )


def test_negative_score():
    integration = PredictiveRuntimeIntegration()

    with pytest.raises(ValueError):
        integration.prepare_decision(
            "agent-1",
            -1,
            DIRECTION_STABLE,
            0,
            CONFIDENCE_HIGH,
            CONTROL_MAINTAIN,
        )


def test_invalid_direction():
    integration = PredictiveRuntimeIntegration()

    with pytest.raises(ValueError):
        integration.prepare_decision(
            "agent-1",
            50,
            "INVALID",
            0,
            CONFIDENCE_HIGH,
            CONTROL_MAINTAIN,
        )


def test_invalid_confidence():
    integration = PredictiveRuntimeIntegration()

    with pytest.raises(ValueError):
        integration.prepare_decision(
            "agent-1",
            50,
            DIRECTION_STABLE,
            0,
            "INVALID",
            CONTROL_MAINTAIN,
        )


def test_invalid_recommendation():
    integration = PredictiveRuntimeIntegration()

    with pytest.raises(ValueError):
        integration.prepare_decision(
            "agent-1",
            50,
            DIRECTION_STABLE,
            0,
            CONFIDENCE_HIGH,
            "INVALID",
        )


def test_non_string_evidence_rejected():
    integration = PredictiveRuntimeIntegration()

    with pytest.raises(ValueError):
        integration.prepare_decision(
            "agent-1",
            50,
            DIRECTION_STABLE,
            0,
            CONFIDENCE_HIGH,
            CONTROL_MAINTAIN,
            evidence=[123],
        )


def test_runtime_layer_does_not_expose_authorization_state():
    integration = PredictiveRuntimeIntegration()

    decision = integration.prepare_decision(
        "agent-1",
        90,
        DIRECTION_DETERIORATING,
        20,
        CONFIDENCE_HIGH,
        CONTROL_PREEMPTIVE_BLOCK,
    )

    assert decision.recommendation == CONTROL_PREEMPTIVE_BLOCK
    assert not hasattr(decision, "authorized")
    assert not hasattr(decision, "blocked")


def test_runtime_layer_is_deterministic():
    integration = PredictiveRuntimeIntegration()

    first = integration.prepare_decision(
        "agent-1",
        60,
        DIRECTION_DETERIORATING,
        10,
        CONFIDENCE_HIGH,
        CONTROL_REDUCE_SCOPE,
    )

    second = integration.prepare_decision(
        "agent-1",
        60,
        DIRECTION_DETERIORATING,
        10,
        CONFIDENCE_HIGH,
        CONTROL_REDUCE_SCOPE,
    )

    assert first == second