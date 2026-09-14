import pytest

from app.predictive_trajectory import (
    DIRECTION_DETERIORATING,
    DIRECTION_IMPROVING,
    DIRECTION_INSUFFICIENT_DATA,
    DIRECTION_STABLE,
    STABILITY_STABLE,
    STABILITY_VARIABLE,
    PredictiveBehavioralTrajectory,
    calculate_direction_confidence,
    calculate_mean_change,
    calculate_slope,
    calculate_volatility,
    classify_direction,
    classify_stability,
)


def test_calculate_slope_increasing():
    assert calculate_slope([20, 40, 60]) == pytest.approx(20.0)


def test_calculate_slope_decreasing():
    assert calculate_slope([80, 60, 40]) == pytest.approx(-20.0)


def test_calculate_slope_stable():
    assert calculate_slope([50, 50, 50]) == pytest.approx(0.0)


def test_calculate_slope_two_points():
    assert calculate_slope([30, 70]) == pytest.approx(40.0)


def test_calculate_slope_single_point():
    assert calculate_slope([50]) == pytest.approx(0.0)


def test_calculate_mean_change():
    assert calculate_mean_change([20, 40, 60]) == pytest.approx(20.0)


def test_calculate_mean_change_decreasing():
    assert calculate_mean_change([80, 60, 40]) == pytest.approx(-20.0)


def test_calculate_mean_change_stable():
    assert calculate_mean_change([50, 50, 50]) == pytest.approx(0.0)


def test_calculate_volatility():
    assert calculate_volatility([20, 40, 60]) == pytest.approx(20.0)


def test_calculate_volatility_variable():
    assert calculate_volatility([20, 80, 30]) == pytest.approx(55.0)


def test_calculate_volatility_stable():
    assert calculate_volatility([50, 50, 50]) == pytest.approx(0.0)


def test_classify_direction_improving():
    assert classify_direction(-10) == DIRECTION_IMPROVING


def test_classify_direction_stable():
    assert classify_direction(5) == DIRECTION_STABLE


def test_classify_direction_deteriorating():
    assert classify_direction(10) == DIRECTION_DETERIORATING


def test_classify_direction_custom_tolerance():
    assert classify_direction(8, tolerance=10) == DIRECTION_STABLE


def test_classify_stability_stable():
    assert classify_stability(5) == STABILITY_STABLE


def test_classify_stability_variable():
    assert classify_stability(10) == STABILITY_VARIABLE


def test_confidence_low_for_two_observations():
    assert calculate_direction_confidence(
        [20, 80],
        60,
    ) == "LOW"


def test_confidence_moderate_for_three_observations():
    assert calculate_direction_confidence(
        [20, 50, 80],
        30,
    ) == "MODERATE"


def test_confidence_high_for_long_strong_trajectory():
    assert calculate_direction_confidence(
        [10, 30, 50, 70, 90],
        20,
    ) == "HIGH"


def test_engine_insufficient_data():
    engine = PredictiveBehavioralTrajectory()

    snapshot = engine.add_observation("agent-1", 50)

    assert snapshot.direction == DIRECTION_INSUFFICIENT_DATA
    assert snapshot.observation_count == 1
    assert snapshot.latest_value == 50


def test_engine_detects_deteriorating_trajectory():
    engine = PredictiveBehavioralTrajectory()

    snapshot = engine.add_observations(
        "agent-1",
        [20, 40, 60, 80],
    )

    assert snapshot.direction == DIRECTION_DETERIORATING
    assert snapshot.slope == pytest.approx(20.0)
    assert snapshot.latest_value == 80


def test_engine_detects_improving_trajectory():
    engine = PredictiveBehavioralTrajectory()

    snapshot = engine.add_observations(
        "agent-1",
        [80, 60, 40, 20],
    )

    assert snapshot.direction == DIRECTION_IMPROVING
    assert snapshot.slope == pytest.approx(-20.0)


def test_engine_detects_stable_trajectory():
    engine = PredictiveBehavioralTrajectory()

    snapshot = engine.add_observations(
        "agent-1",
        [50, 52, 49, 51],
    )

    assert snapshot.direction == DIRECTION_STABLE
    assert snapshot.stability == STABILITY_STABLE


def test_engine_detects_variable_trajectory():
    engine = PredictiveBehavioralTrajectory()

    snapshot = engine.add_observations(
        "agent-1",
        [20, 80, 30, 90],
    )

    assert snapshot.stability == STABILITY_VARIABLE


def test_engine_keeps_agents_separate():
    engine = PredictiveBehavioralTrajectory()

    engine.add_observations("agent-1", [20, 40, 60])
    engine.add_observations("agent-2", [80, 60, 40])

    first = engine.latest("agent-1")
    second = engine.latest("agent-2")

    assert first is not None
    assert second is not None

    assert first.direction == DIRECTION_DETERIORATING
    assert second.direction == DIRECTION_IMPROVING


def test_engine_history_is_chronological():
    engine = PredictiveBehavioralTrajectory()

    engine.add_observations(
        "agent-1",
        [20, 40, 60],
    )

    assert engine.get_history("agent-1") == (20.0, 40.0, 60.0)


def test_engine_latest_updates():
    engine = PredictiveBehavioralTrajectory()

    first = engine.add_observations(
        "agent-1",
        [20, 40],
    )

    second = engine.add_observation(
        "agent-1",
        60,
    )

    assert first.observation_count == 2
    assert second.observation_count == 3
    assert engine.latest("agent-1") == second


def test_engine_snapshot_all():
    engine = PredictiveBehavioralTrajectory()

    engine.add_observations("agent-1", [20, 40])
    engine.add_observations("agent-2", [80, 60])

    snapshots = engine.snapshot_all()

    assert len(snapshots) == 2
    assert {item.agent_id for item in snapshots} == {
        "agent-1",
        "agent-2",
    }


def test_engine_reset_single_agent():
    engine = PredictiveBehavioralTrajectory()

    engine.add_observations("agent-1", [20, 40])
    engine.add_observations("agent-2", [80, 60])

    engine.reset("agent-1")

    assert engine.get_history("agent-1") == ()
    assert engine.latest("agent-1") is None
    assert engine.latest("agent-2") is not None


def test_engine_reset_all():
    engine = PredictiveBehavioralTrajectory()

    engine.add_observations("agent-1", [20, 40])
    engine.add_observations("agent-2", [80, 60])

    engine.reset()

    assert engine.snapshot_all() == ()
    assert engine.get_history("agent-1") == ()
    assert engine.get_history("agent-2") == ()


def test_invalid_score_rejected():
    engine = PredictiveBehavioralTrajectory()

    with pytest.raises(ValueError):
        engine.add_observation("agent-1", 101)


def test_negative_score_rejected():
    engine = PredictiveBehavioralTrajectory()

    with pytest.raises(ValueError):
        engine.add_observation("agent-1", -1)


def test_invalid_agent_id_rejected():
    engine = PredictiveBehavioralTrajectory()

    with pytest.raises(ValueError):
        engine.add_observation("", 50)


def test_invalid_tolerance_rejected():
    with pytest.raises(ValueError):
        PredictiveBehavioralTrajectory(tolerance=-1)


def test_invalid_min_observations_rejected():
    with pytest.raises(ValueError):
        PredictiveBehavioralTrajectory(min_observations=1)


def test_none_observations_rejected():
    with pytest.raises(ValueError):
        calculate_slope(None)


def test_non_finite_observation_rejected():
    with pytest.raises(ValueError):
        calculate_slope([20, float("nan")])


def test_evidence_is_deterministic():
    engine = PredictiveBehavioralTrajectory()

    first = engine.add_observations(
        "agent-1",
        [20, 40, 60],
    )

    second = engine.analyze("agent-1")

    assert first.evidence == second.evidence


def test_snapshot_is_immutable():
    engine = PredictiveBehavioralTrajectory()

    snapshot = engine.add_observations(
        "agent-1",
        [20, 40, 60],
    )

    with pytest.raises(AttributeError):
        snapshot.direction = "INVALID"


def test_no_authorization_side_effects():
    engine = PredictiveBehavioralTrajectory()

    snapshot = engine.add_observations(
        "agent-1",
        [20, 40, 60],
    )

    assert snapshot.agent_id == "agent-1"
    assert snapshot.direction == DIRECTION_DETERIORATING