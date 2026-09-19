import pytest

from app.platform.predictive_trajectory import (
    PredictiveTrajectoryPlatformAdapter,
)
from app.predictive_trajectory import (
    BehavioralTrajectorySnapshot,
    PredictiveBehavioralTrajectory,
)


def test_add_observation_returns_snapshot():
    adapter = PredictiveTrajectoryPlatformAdapter()

    snapshot = adapter.add_observation(
        "agent-1",
        50.0,
    )

    assert isinstance(snapshot, BehavioralTrajectorySnapshot)
    assert snapshot.agent_id == "agent-1"
    assert snapshot.observations == (50.0,)
    assert snapshot.observation_count == 1
    assert snapshot.initial_value == 50.0
    assert snapshot.latest_value == 50.0


def test_add_observation_builds_trajectory_after_minimum_observations():
    adapter = PredictiveTrajectoryPlatformAdapter(
        min_observations=2,
    )

    first = adapter.add_observation(
        "agent-1",
        20.0,
    )

    second = adapter.add_observation(
        "agent-1",
        40.0,
    )

    assert first.observation_count == 1
    assert second.observation_count == 2
    assert second.initial_value == 20.0
    assert second.latest_value == 40.0
    assert second.direction != "INSUFFICIENT_DATA"


def test_add_observations_preserves_chronological_order():
    adapter = PredictiveTrajectoryPlatformAdapter()

    snapshot = adapter.add_observations(
        "agent-1",
        [10.0, 20.0, 30.0],
    )

    assert snapshot.observations == (
        10.0,
        20.0,
        30.0,
    )

    assert snapshot.observation_count == 3
    assert snapshot.initial_value == 10.0
    assert snapshot.latest_value == 30.0


def test_add_observations_serialized_returns_api_safe_payload():
    adapter = PredictiveTrajectoryPlatformAdapter()

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

    assert isinstance(payload["observations"], list)
    assert isinstance(payload["evidence"], list)
    assert payload["observation_count"] == 3


def test_analyze_returns_current_trajectory():
    adapter = PredictiveTrajectoryPlatformAdapter()

    adapter.add_observations(
        "agent-1",
        [20.0, 30.0, 40.0],
    )

    snapshot = adapter.analyze("agent-1")

    assert snapshot.agent_id == "agent-1"
    assert snapshot.observation_count == 3
    assert snapshot.latest_value == 40.0


def test_analyze_serialized_returns_api_safe_payload():
    adapter = PredictiveTrajectoryPlatformAdapter()

    adapter.add_observations(
        "agent-1",
        [20.0, 30.0, 40.0],
    )

    payload = adapter.analyze_serialized("agent-1")

    assert payload["agent_id"] == "agent-1"
    assert isinstance(payload["observations"], list)
    assert isinstance(payload["evidence"], list)
    assert payload["observation_count"] == 3


def test_latest_returns_latest_snapshot():
    adapter = PredictiveTrajectoryPlatformAdapter()

    first = adapter.add_observation(
        "agent-1",
        20.0,
    )

    second = adapter.add_observation(
        "agent-1",
        50.0,
    )

    assert adapter.latest("agent-1") == second
    assert adapter.latest("agent-1") != first


def test_latest_returns_none_for_unknown_agent():
    adapter = PredictiveTrajectoryPlatformAdapter()

    assert adapter.latest("unknown-agent") is None


def test_latest_serialized_returns_api_safe_snapshot():
    adapter = PredictiveTrajectoryPlatformAdapter()

    adapter.add_observations(
        "agent-1",
        [10.0, 20.0],
    )

    payload = adapter.latest_serialized("agent-1")

    assert payload is not None
    assert payload["agent_id"] == "agent-1"
    assert isinstance(payload["observations"], list)
    assert isinstance(payload["evidence"], list)


def test_history_returns_chronological_observations():
    adapter = PredictiveTrajectoryPlatformAdapter()

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
    adapter = PredictiveTrajectoryPlatformAdapter()

    assert adapter.history_count("agent-1") == 0

    adapter.add_observation(
        "agent-1",
        10.0,
    )

    assert adapter.history_count("agent-1") == 1

    adapter.add_observations(
        "agent-1",
        [20.0, 30.0],
    )

    assert adapter.history_count("agent-1") == 3


def test_history_isolated_per_agent():
    adapter = PredictiveTrajectoryPlatformAdapter()

    adapter.add_observations(
        "agent-1",
        [10.0, 20.0],
    )

    adapter.add_observations(
        "agent-2",
        [80.0, 70.0],
    )

    assert adapter.history("agent-1") == (
        10.0,
        20.0,
    )

    assert adapter.history("agent-2") == (
        80.0,
        70.0,
    )

    assert adapter.history_count("agent-1") == 2
    assert adapter.history_count("agent-2") == 2


def test_reset_clears_only_requested_agent():
    adapter = PredictiveTrajectoryPlatformAdapter()

    adapter.add_observations(
        "agent-1",
        [10.0, 20.0],
    )

    adapter.add_observations(
        "agent-2",
        [80.0, 70.0],
    )

    adapter.reset("agent-1")

    assert adapter.history_count("agent-1") == 0
    assert adapter.latest("agent-1") is None

    assert adapter.history_count("agent-2") == 2
    assert adapter.latest("agent-2") is not None


def test_reset_without_agent_clears_all_agents():
    adapter = PredictiveTrajectoryPlatformAdapter()

    adapter.add_observations(
        "agent-1",
        [10.0, 20.0],
    )

    adapter.add_observations(
        "agent-2",
        [80.0, 70.0],
    )

    adapter.reset()

    assert adapter.history_count("agent-1") == 0
    assert adapter.history_count("agent-2") == 0

    assert adapter.latest("agent-1") is None
    assert adapter.latest("agent-2") is None


def test_invalid_agent_id_is_rejected():
    adapter = PredictiveTrajectoryPlatformAdapter()

    with pytest.raises(
        ValueError,
        match="agent_id must be a non-empty string",
    ):
        adapter.add_observation(
            "",
            50.0,
        )


def test_invalid_observation_is_rejected():
    adapter = PredictiveTrajectoryPlatformAdapter()

    with pytest.raises((TypeError, ValueError)):
        adapter.add_observation(
            "agent-1",
            -1.0,
        )


def test_custom_engine_can_be_injected():
    engine = PredictiveBehavioralTrajectory(
        tolerance=1.0,
        min_observations=2,
    )

    adapter = PredictiveTrajectoryPlatformAdapter(
        engine=engine,
    )

    snapshot = adapter.add_observations(
        "agent-1",
        [10.0, 20.0],
    )

    assert adapter.engine is engine
    assert adapter.latest("agent-1") == snapshot
    assert engine.latest("agent-1") == snapshot


def test_adapter_instances_do_not_share_state():
    first = PredictiveTrajectoryPlatformAdapter()
    second = PredictiveTrajectoryPlatformAdapter()

    first.add_observations(
        "agent-1",
        [10.0, 20.0],
    )

    assert first.history_count("agent-1") == 2
    assert second.history_count("agent-1") == 0


def test_serialization_does_not_mutate_immutable_snapshot():
    adapter = PredictiveTrajectoryPlatformAdapter()

    snapshot = adapter.add_observations(
        "agent-1",
        [10.0, 20.0, 30.0],
    )

    payload = adapter.latest_serialized("agent-1")

    assert payload is not None

    assert isinstance(snapshot.observations, tuple)
    assert isinstance(snapshot.evidence, tuple)

    assert isinstance(payload["observations"], list)
    assert isinstance(payload["evidence"], list)


def test_improving_trajectory_is_preserved():
    adapter = PredictiveTrajectoryPlatformAdapter()

    snapshot = adapter.add_observations(
        "agent-improving",
        [80.0, 70.0, 60.0, 50.0],
    )

    assert snapshot.direction == "IMPROVING"


def test_deteriorating_trajectory_is_preserved():
    adapter = PredictiveTrajectoryPlatformAdapter()

    snapshot = adapter.add_observations(
        "agent-deteriorating",
        [20.0, 30.0, 40.0, 50.0],
    )

    assert snapshot.direction == "DETERIORATING"


def test_insufficient_data_is_preserved():
    adapter = PredictiveTrajectoryPlatformAdapter(
        min_observations=3,
    )

    snapshot = adapter.add_observation(
        "agent-1",
        50.0,
    )

    assert snapshot.direction == "INSUFFICIENT_DATA"
    assert snapshot.confidence == "LOW"
    assert snapshot.observation_count == 1