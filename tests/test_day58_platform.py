import pytest

from app.predictive_forecast import (
    CONFIDENCE_LOW,
    FORECAST_DETERIORATING,
    FORECAST_IMPROVING,
    FORECAST_INSUFFICIENT_DATA,
    PredictiveForecastEngine,
)
from app.platform.predictive_forecast import (
    PredictiveForecastPlatformAdapter,
)


def test_add_observation_returns_snapshot():
    adapter = PredictiveForecastPlatformAdapter()

    snapshot = adapter.add_observation(
        "agent-1",
        50.0,
    )

    assert snapshot.agent_id == "agent-1"
    assert snapshot.observations == (50.0,)
    assert snapshot.observation_count == 1
    assert snapshot.direction == FORECAST_INSUFFICIENT_DATA


def test_add_observations_preserves_chronological_order():
    adapter = PredictiveForecastPlatformAdapter()

    snapshot = adapter.add_observations(
        "agent-1",
        [10.0, 20.0, 30.0],
    )

    assert snapshot.observations == (
        10.0,
        20.0,
        30.0,
    )


def test_add_observations_serialized_returns_api_safe_payload():
    adapter = PredictiveForecastPlatformAdapter()

    payload = adapter.add_observations_serialized(
        "agent-1",
        [10.0, 20.0, 30.0],
    )

    assert payload["agent_id"] == "agent-1"
    assert payload["observations"] == [
        10.0,
        20.0,
        30.0,
    ]
    assert isinstance(payload["evidence"], list)


def test_forecast_returns_current_forecast():
    adapter = PredictiveForecastPlatformAdapter(
        horizon=2,
    )

    snapshot = adapter.add_observations(
        "agent-1",
        [20.0, 40.0, 60.0, 80.0],
    )

    result = adapter.forecast("agent-1")

    assert result == snapshot
    assert result.projected_value == pytest.approx(100.0)
    assert result.direction == FORECAST_DETERIORATING


def test_forecast_serialized_returns_api_safe_payload():
    adapter = PredictiveForecastPlatformAdapter(
        horizon=2,
    )

    adapter.add_observations(
        "agent-1",
        [20.0, 40.0, 60.0, 80.0],
    )

    payload = adapter.forecast_serialized("agent-1")

    assert payload["agent_id"] == "agent-1"
    assert payload["current_value"] == pytest.approx(80.0)
    assert payload["projected_value"] == pytest.approx(100.0)
    assert isinstance(payload["observations"], list)
    assert isinstance(payload["evidence"], list)


def test_latest_returns_latest_snapshot():
    adapter = PredictiveForecastPlatformAdapter()

    first = adapter.add_observations(
        "agent-1",
        [20.0, 40.0],
    )

    second = adapter.add_observation(
        "agent-1",
        60.0,
    )

    assert first.observation_count == 2
    assert second.observation_count == 3
    assert adapter.latest("agent-1") == second


def test_latest_returns_none_for_unknown_agent():
    adapter = PredictiveForecastPlatformAdapter()

    assert adapter.latest("unknown-agent") is None


def test_latest_serialized_returns_api_safe_snapshot():
    adapter = PredictiveForecastPlatformAdapter()

    adapter.add_observations(
        "agent-1",
        [10.0, 20.0, 30.0],
    )

    payload = adapter.latest_serialized("agent-1")

    assert payload is not None
    assert payload["agent_id"] == "agent-1"
    assert payload["observations"] == [
        10.0,
        20.0,
        30.0,
    ]


def test_history_returns_chronological_observations():
    adapter = PredictiveForecastPlatformAdapter()

    adapter.add_observations(
        "agent-1",
        [10.0, 20.0, 30.0],
    )

    assert adapter.history("agent-1") == (
        10.0,
        20.0,
        30.0,
    )


def test_history_count_matches_observations():
    adapter = PredictiveForecastPlatformAdapter()

    assert adapter.history_count("agent-1") == 0

    adapter.add_observations(
        "agent-1",
        [10.0, 20.0, 30.0],
    )

    assert adapter.history_count("agent-1") == 3


def test_history_isolated_per_agent():
    adapter = PredictiveForecastPlatformAdapter()

    adapter.add_observations(
        "agent-1",
        [10.0, 20.0],
    )

    adapter.add_observations(
        "agent-2",
        [80.0, 70.0, 60.0],
    )

    assert adapter.history("agent-1") == (
        10.0,
        20.0,
    )

    assert adapter.history("agent-2") == (
        80.0,
        70.0,
        60.0,
    )


def test_snapshot_all_returns_all_agents():
    adapter = PredictiveForecastPlatformAdapter()

    adapter.add_observations(
        "agent-1",
        [20.0, 40.0],
    )

    adapter.add_observations(
        "agent-2",
        [80.0, 60.0],
    )

    snapshots = adapter.snapshot_all()

    assert len(snapshots) == 2
    assert {snapshot.agent_id for snapshot in snapshots} == {
        "agent-1",
        "agent-2",
    }


def test_snapshot_all_serialized_returns_api_safe_payloads():
    adapter = PredictiveForecastPlatformAdapter()

    adapter.add_observations(
        "agent-1",
        [20.0, 40.0],
    )

    adapter.add_observations(
        "agent-2",
        [80.0, 60.0],
    )

    payloads = adapter.snapshot_all_serialized()

    assert len(payloads) == 2
    assert {
        payload["agent_id"]
        for payload in payloads
    } == {
        "agent-1",
        "agent-2",
    }


def test_reset_clears_only_requested_agent():
    adapter = PredictiveForecastPlatformAdapter()

    adapter.add_observations(
        "agent-1",
        [20.0, 40.0],
    )

    adapter.add_observations(
        "agent-2",
        [80.0, 60.0],
    )

    adapter.reset("agent-1")

    assert adapter.history("agent-1") == ()
    assert adapter.latest("agent-1") is None
    assert adapter.latest("agent-2") is not None


def test_reset_without_agent_clears_all_agents():
    adapter = PredictiveForecastPlatformAdapter()

    adapter.add_observations(
        "agent-1",
        [20.0, 40.0],
    )

    adapter.add_observations(
        "agent-2",
        [80.0, 60.0],
    )

    adapter.reset()

    assert adapter.snapshot_all() == ()
    assert adapter.history("agent-1") == ()
    assert adapter.history("agent-2") == ()


def test_invalid_agent_id_is_rejected():
    adapter = PredictiveForecastPlatformAdapter()

    with pytest.raises(
        ValueError,
        match="agent_id must be a non-empty string",
    ):
        adapter.add_observation(
            "",
            50.0,
        )


def test_invalid_score_is_rejected():
    adapter = PredictiveForecastPlatformAdapter()

    with pytest.raises(ValueError):
        adapter.add_observation(
            "agent-1",
            101.0,
        )


def test_negative_score_is_rejected():
    adapter = PredictiveForecastPlatformAdapter()

    with pytest.raises(ValueError):
        adapter.add_observation(
            "agent-1",
            -1.0,
        )


def test_custom_engine_can_be_injected():
    engine = PredictiveForecastEngine(
        horizon=3,
        tolerance=10.0,
    )

    adapter = PredictiveForecastPlatformAdapter(
        engine=engine,
    )

    snapshot = adapter.add_observations(
        "agent-1",
        [10.0, 20.0, 30.0],
    )

    assert snapshot.horizon == 3
    assert adapter.engine is engine


def test_adapter_instances_do_not_share_state():
    first = PredictiveForecastPlatformAdapter()
    second = PredictiveForecastPlatformAdapter()

    first.add_observations(
        "agent-1",
        [10.0, 20.0],
    )

    assert first.history("agent-1") == (
        10.0,
        20.0,
    )

    assert second.history("agent-1") == ()


def test_serialization_does_not_mutate_immutable_snapshot():
    adapter = PredictiveForecastPlatformAdapter()

    snapshot = adapter.add_observations(
        "agent-1",
        [10.0, 20.0, 30.0],
    )

    payload = adapter.latest_serialized("agent-1")

    assert isinstance(payload["observations"], list)
    assert isinstance(payload["evidence"], list)

    assert snapshot.observations == (
        10.0,
        20.0,
        30.0,
    )


def test_insufficient_data_is_preserved():
    adapter = PredictiveForecastPlatformAdapter()

    snapshot = adapter.add_observation(
        "agent-1",
        50.0,
    )

    assert snapshot.direction == FORECAST_INSUFFICIENT_DATA
    assert snapshot.projected_value is None
    assert snapshot.confidence == CONFIDENCE_LOW