import pytest

from app.predictive_forecast import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MODERATE,
    FORECAST_DETERIORATING,
    FORECAST_IMPROVING,
    FORECAST_INSUFFICIENT_DATA,
    FORECAST_STABLE,
    PredictiveForecastEngine,
    calculate_slope,
    calculate_volatility,
    classify_confidence,
    classify_forecast,
    project_value,
)


def test_calculate_slope_increasing():
    assert calculate_slope([20, 40, 60]) == pytest.approx(20.0)


def test_calculate_slope_decreasing():
    assert calculate_slope([80, 60, 40]) == pytest.approx(-20.0)


def test_calculate_slope_stable():
    assert calculate_slope([50, 50, 50]) == pytest.approx(0.0)


def test_calculate_slope_single_observation():
    assert calculate_slope([50]) == pytest.approx(0.0)


def test_calculate_volatility():
    assert calculate_volatility([20, 40, 60]) == pytest.approx(20.0)


def test_calculate_volatility_variable():
    assert calculate_volatility([20, 80, 30]) == pytest.approx(55.0)


def test_calculate_volatility_stable():
    assert calculate_volatility([50, 50, 50]) == pytest.approx(0.0)


def test_project_value_increasing():
    assert project_value(60, 10, 2) == pytest.approx(80.0)


def test_project_value_decreasing():
    assert project_value(60, -10, 2) == pytest.approx(40.0)


def test_project_value_is_bounded_at_upper_limit():
    assert project_value(90, 20, 2) == pytest.approx(100.0)


def test_project_value_is_bounded_at_lower_limit():
    assert project_value(10, -20, 2) == pytest.approx(0.0)


def test_classify_forecast_improving():
    assert classify_forecast(-10) == FORECAST_IMPROVING


def test_classify_forecast_stable():
    assert classify_forecast(5) == FORECAST_STABLE


def test_classify_forecast_deteriorating():
    assert classify_forecast(10) == FORECAST_DETERIORATING


def test_classify_forecast_custom_tolerance():
    assert classify_forecast(8, tolerance=10) == FORECAST_STABLE


def test_confidence_low_for_insufficient_data():
    assert classify_confidence(1, 10, 5) == CONFIDENCE_LOW


def test_confidence_low_for_two_observations():
    assert classify_confidence(2, 20, 10) == CONFIDENCE_LOW


def test_confidence_moderate_for_three_observations():
    assert classify_confidence(3, 10, 10) == CONFIDENCE_MODERATE


def test_confidence_high_for_long_consistent_trajectory():
    assert classify_confidence(
        5,
        10,
        10,
    ) == CONFIDENCE_HIGH


def test_engine_insufficient_data():
    engine = PredictiveForecastEngine()

    snapshot = engine.add_observation(
        "agent-1",
        50,
    )

    assert snapshot.direction == FORECAST_INSUFFICIENT_DATA
    assert snapshot.projected_value is None
    assert snapshot.confidence == CONFIDENCE_LOW


def test_engine_deteriorating_forecast():
    engine = PredictiveForecastEngine(
        horizon=2,
    )

    snapshot = engine.add_observations(
        "agent-1",
        [20, 40, 60, 80],
    )

    assert snapshot.direction == FORECAST_DETERIORATING
    assert snapshot.current_value == pytest.approx(80.0)
    assert snapshot.projected_value == pytest.approx(100.0)


def test_engine_improving_forecast():
    engine = PredictiveForecastEngine(
        horizon=2,
    )

    snapshot = engine.add_observations(
        "agent-1",
        [80, 60, 40, 20],
    )

    assert snapshot.direction == FORECAST_IMPROVING
    assert snapshot.projected_value == pytest.approx(0.0)


def test_engine_stable_forecast():
    engine = PredictiveForecastEngine(
        horizon=2,
    )

    snapshot = engine.add_observations(
        "agent-1",
        [50, 52, 49, 51],
    )

    assert snapshot.direction == FORECAST_STABLE


def test_engine_keeps_agents_isolated():
    engine = PredictiveForecastEngine()

    first = engine.add_observations(
        "agent-1",
        [20, 40, 60],
    )

    second = engine.add_observations(
        "agent-2",
        [80, 60, 40],
    )

    assert first.direction == FORECAST_DETERIORATING
    assert second.direction == FORECAST_IMPROVING


def test_engine_history_is_chronological():
    engine = PredictiveForecastEngine()

    engine.add_observations(
        "agent-1",
        [20, 40, 60],
    )

    assert engine.get_history("agent-1") == (
        20.0,
        40.0,
        60.0,
    )


def test_engine_latest_updates():
    engine = PredictiveForecastEngine()

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


def test_snapshot_all():
    engine = PredictiveForecastEngine()

    engine.add_observations(
        "agent-1",
        [20, 40],
    )

    engine.add_observations(
        "agent-2",
        [80, 60],
    )

    snapshots = engine.snapshot_all()

    assert len(snapshots) == 2
    assert {item.agent_id for item in snapshots} == {
        "agent-1",
        "agent-2",
    }


def test_reset_single_agent():
    engine = PredictiveForecastEngine()

    engine.add_observations(
        "agent-1",
        [20, 40],
    )

    engine.add_observations(
        "agent-2",
        [80, 60],
    )

    engine.reset("agent-1")

    assert engine.get_history("agent-1") == ()
    assert engine.latest("agent-1") is None
    assert engine.latest("agent-2") is not None


def test_reset_all_agents():
    engine = PredictiveForecastEngine()

    engine.add_observations(
        "agent-1",
        [20, 40],
    )

    engine.add_observations(
        "agent-2",
        [80, 60],
    )

    engine.reset()

    assert engine.snapshot_all() == ()


def test_invalid_score_rejected():
    engine = PredictiveForecastEngine()

    with pytest.raises(ValueError):
        engine.add_observation(
            "agent-1",
            101,
        )


def test_negative_score_rejected():
    engine = PredictiveForecastEngine()

    with pytest.raises(ValueError):
        engine.add_observation(
            "agent-1",
            -1,
        )


def test_invalid_agent_id_rejected():
    engine = PredictiveForecastEngine()

    with pytest.raises(ValueError):
        engine.add_observation(
            "",
            50,
        )


def test_invalid_horizon_rejected():
    with pytest.raises(ValueError):
        PredictiveForecastEngine(horizon=0)


def test_horizon_upper_bound_rejected():
    with pytest.raises(ValueError):
        PredictiveForecastEngine(horizon=11)


def test_invalid_tolerance_rejected():
    with pytest.raises(ValueError):
        PredictiveForecastEngine(tolerance=-1)


def test_none_observations_rejected():
    with pytest.raises(ValueError):
        calculate_slope(None)


def test_nan_observation_rejected():
    with pytest.raises(ValueError):
        calculate_slope(
            [20, float("nan")]
        )


def test_infinite_observation_rejected():
    with pytest.raises(ValueError):
        calculate_slope(
            [20, float("inf")]
        )


def test_snapshot_is_immutable():
    engine = PredictiveForecastEngine()

    snapshot = engine.add_observations(
        "agent-1",
        [20, 40, 60],
    )

    with pytest.raises(AttributeError):
        snapshot.direction = "INVALID"


def test_evidence_is_deterministic():
    engine = PredictiveForecastEngine()

    first = engine.add_observations(
        "agent-1",
        [20, 40, 60],
    )

    second = engine.forecast("agent-1")

    assert first.evidence == second.evidence


def test_forecast_does_not_modify_existing_observations():
    engine = PredictiveForecastEngine()

    engine.add_observations(
        "agent-1",
        [20, 40, 60],
    )

    before = engine.get_history("agent-1")

    engine.forecast("agent-1")

    after = engine.get_history("agent-1")

    assert before == after


def test_forecast_is_deterministic():
    engine = PredictiveForecastEngine(
        horizon=3,
    )

    engine.add_observations(
        "agent-1",
        [30, 40, 50, 60],
    )

    first = engine.forecast("agent-1")
    second = engine.forecast("agent-1")

    assert first == second


def test_forecast_has_bounded_projected_value():
    engine = PredictiveForecastEngine(
        horizon=10,
    )

    snapshot = engine.add_observations(
        "agent-1",
        [80, 90, 100],
    )

    assert 0 <= snapshot.projected_value <= 100


def test_forecast_does_not_perform_authorization():
    engine = PredictiveForecastEngine()

    snapshot = engine.add_observations(
        "agent-1",
        [20, 40, 60],
    )

    assert snapshot.agent_id == "agent-1"
    assert snapshot.direction == FORECAST_DETERIORATING