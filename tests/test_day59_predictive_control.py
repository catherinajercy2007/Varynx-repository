import pytest

from app.predictive_control import (
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
    LEVEL_CRITICAL,
    LEVEL_HIGH,
    LEVEL_LOW,
    LEVEL_MODERATE,
    PredictiveControlEngine,
    calculate_control_priority,
    classify_signal_level,
    recommend_control,
)


def test_classify_low_signal():
    assert classify_signal_level(10) == LEVEL_LOW


def test_classify_moderate_signal():
    assert classify_signal_level(30) == LEVEL_MODERATE


def test_classify_high_signal():
    assert classify_signal_level(50) == LEVEL_HIGH


def test_classify_critical_signal():
    assert classify_signal_level(70) == LEVEL_CRITICAL


def test_priority_increases_with_deterioration():
    base = calculate_control_priority(
        projected_score=60,
        slope=0,
    )

    deteriorating = calculate_control_priority(
        projected_score=60,
        slope=10,
    )

    assert deteriorating > base


def test_priority_is_bounded():
    assert calculate_control_priority(
        projected_score=100,
        slope=100,
    ) == 100


def test_low_state_recommends_maintain():
    result = recommend_control(
        projected_score=10,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence="HIGH",
    )

    assert result == CONTROL_MAINTAIN


def test_moderate_deterioration_recommends_monitoring():
    result = recommend_control(
        projected_score=30,
        direction=DIRECTION_DETERIORATING,
        slope=10,
        confidence="MODERATE",
    )

    assert result == CONTROL_INCREASE_MONITORING


def test_moderate_improvement_recommends_maintain():
    result = recommend_control(
        projected_score=30,
        direction=DIRECTION_IMPROVING,
        slope=-10,
        confidence="HIGH",
    )

    assert result == CONTROL_MAINTAIN


def test_high_deterioration_recommends_reduce_scope():
    result = recommend_control(
        projected_score=60,
        direction=DIRECTION_DETERIORATING,
        slope=10,
        confidence="HIGH",
    )

    assert result == CONTROL_REDUCE_SCOPE


def test_high_state_without_deterioration_steps_up():
    result = recommend_control(
        projected_score=60,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence="HIGH",
    )

    assert result == CONTROL_STEP_UP_VERIFICATION


def test_critical_high_confidence_deterioration_preemptive_block():
    result = recommend_control(
        projected_score=90,
        direction=DIRECTION_DETERIORATING,
        slope=20,
        confidence="HIGH",
    )

    assert result == CONTROL_PREEMPTIVE_BLOCK


def test_critical_moderate_confidence_requests_human_review():
    result = recommend_control(
        projected_score=90,
        direction=DIRECTION_DETERIORATING,
        slope=20,
        confidence="MODERATE",
    )

    assert result == CONTROL_HUMAN_REVIEW


def test_critical_stable_state_requests_human_review():
    result = recommend_control(
        projected_score=90,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence="HIGH",
    )

    assert result == CONTROL_HUMAN_REVIEW


def test_insufficient_data_maintains_control():
    result = recommend_control(
        projected_score=80,
        direction=DIRECTION_INSUFFICIENT_DATA,
        slope=0,
        confidence="LOW",
    )

    assert result == CONTROL_MAINTAIN


def test_engine_creates_recommendation():
    engine = PredictiveControlEngine()

    snapshot = engine.recommend(
        agent_id="agent-1",
        projected_score=60,
        direction=DIRECTION_DETERIORATING,
        slope=10,
        confidence="HIGH",
    )

    assert snapshot.agent_id == "agent-1"
    assert snapshot.projected_score == 60
    assert snapshot.projected_level == LEVEL_HIGH
    assert snapshot.recommendation == CONTROL_REDUCE_SCOPE


def test_engine_latest():
    engine = PredictiveControlEngine()

    snapshot = engine.recommend(
        agent_id="agent-1",
        projected_score=60,
        direction=DIRECTION_DETERIORATING,
        slope=10,
        confidence="HIGH",
    )

    assert engine.latest("agent-1") == snapshot


def test_engine_keeps_agents_separate():
    engine = PredictiveControlEngine()

    first = engine.recommend(
        agent_id="agent-1",
        projected_score=20,
        direction=DIRECTION_STABLE,
        slope=0,
        confidence="HIGH",
    )

    second = engine.recommend(
        agent_id="agent-2",
        projected_score=90,
        direction=DIRECTION_DETERIORATING,
        slope=20,
        confidence="HIGH",
    )

    assert first.recommendation == CONTROL_MAINTAIN
    assert second.recommendation == CONTROL_PREEMPTIVE_BLOCK


def test_engine_snapshot_all():
    engine = PredictiveControlEngine()

    engine.recommend(
        "agent-1",
        20,
        DIRECTION_STABLE,
        0,
        "HIGH",
    )

    engine.recommend(
        "agent-2",
        80,
        DIRECTION_DETERIORATING,
        10,
        "HIGH",
    )

    snapshots = engine.snapshot_all()

    assert len(snapshots) == 2
    assert {item.agent_id for item in snapshots} == {
        "agent-1",
        "agent-2",
    }


def test_engine_reset_single_agent():
    engine = PredictiveControlEngine()

    engine.recommend(
        "agent-1",
        20,
        DIRECTION_STABLE,
        0,
        "HIGH",
    )

    engine.recommend(
        "agent-2",
        80,
        DIRECTION_DETERIORATING,
        10,
        "HIGH",
    )

    engine.reset("agent-1")

    assert engine.latest("agent-1") is None
    assert engine.latest("agent-2") is not None


def test_engine_reset_all():
    engine = PredictiveControlEngine()

    engine.recommend(
        "agent-1",
        20,
        DIRECTION_STABLE,
        0,
        "HIGH",
    )

    engine.recommend(
        "agent-2",
        80,
        DIRECTION_DETERIORATING,
        10,
        "HIGH",
    )

    engine.reset()

    assert engine.snapshot_all() == ()


def test_invalid_agent_id():
    engine = PredictiveControlEngine()

    with pytest.raises(ValueError):
        engine.recommend(
            "",
            50,
            DIRECTION_STABLE,
            0,
            "HIGH",
        )


def test_invalid_score():
    engine = PredictiveControlEngine()

    with pytest.raises(ValueError):
        engine.recommend(
            "agent-1",
            101,
            DIRECTION_STABLE,
            0,
            "HIGH",
        )


def test_negative_score():
    engine = PredictiveControlEngine()

    with pytest.raises(ValueError):
        engine.recommend(
            "agent-1",
            -1,
            DIRECTION_STABLE,
            0,
            "HIGH",
        )


def test_invalid_direction():
    engine = PredictiveControlEngine()

    with pytest.raises(ValueError):
        engine.recommend(
            "agent-1",
            50,
            "INVALID",
            0,
            "HIGH",
        )


def test_invalid_confidence():
    engine = PredictiveControlEngine()

    with pytest.raises(ValueError):
        engine.recommend(
            "agent-1",
            50,
            DIRECTION_STABLE,
            0,
            "INVALID",
        )


def test_invalid_threshold_configuration():
    with pytest.raises(ValueError):
        PredictiveControlEngine(
            high_threshold=90,
            critical_threshold=80,
        )


def test_snapshot_is_immutable():
    engine = PredictiveControlEngine()

    snapshot = engine.recommend(
        "agent-1",
        60,
        DIRECTION_DETERIORATING,
        10,
        "HIGH",
    )

    with pytest.raises(AttributeError):
        snapshot.recommendation = CONTROL_MAINTAIN


def test_evidence_is_present():
    engine = PredictiveControlEngine()

    snapshot = engine.recommend(
        "agent-1",
        60,
        DIRECTION_DETERIORATING,
        10,
        "HIGH",
    )

    assert len(snapshot.evidence) >= 5
    assert any(
        "Recommended control" in item
        for item in snapshot.evidence
    )


def test_recommendation_is_deterministic():
    engine = PredictiveControlEngine()

    first = engine.recommend(
        "agent-1",
        60,
        DIRECTION_DETERIORATING,
        10,
        "HIGH",
    )

    second = engine.recommend(
        "agent-1",
        60,
        DIRECTION_DETERIORATING,
        10,
        "HIGH",
    )

    assert first == second


def test_recommendation_has_no_runtime_side_effect():
    engine = PredictiveControlEngine()

    snapshot = engine.recommend(
        "agent-1",
        90,
        DIRECTION_DETERIORATING,
        20,
        "HIGH",
    )

    # The engine only returns a recommendation.
    # It does not expose an authorization/block execution state.
    assert snapshot.recommendation == CONTROL_PREEMPTIVE_BLOCK
    assert not hasattr(snapshot, "authorized")
    assert not hasattr(snapshot, "blocked")