import pytest

from app.platform.predictive_security import (
    PredictiveSecurityPlatformAdapter,
)
from app.predictive_security import PredictiveSecurityEngine


def test_predict_returns_predictive_security_snapshot():
    adapter = PredictiveSecurityPlatformAdapter()

    snapshot = adapter.predict(
        agent_id="agent-1",
        dimensions={
            "behavioral_deviation": 40.0,
            "trajectory_risk": 30.0,
        },
    )

    assert snapshot.agent_id == "agent-1"
    assert isinstance(snapshot.predictive_score, float)
    assert snapshot.signal_level
    assert snapshot.trajectory == "STABLE"
    assert snapshot.confidence
    assert snapshot.dimensions
    assert snapshot.evidence
    assert snapshot.observation_count == 1


def test_predict_passes_consequence_exposure_to_core_engine():
    adapter = PredictiveSecurityPlatformAdapter()

    snapshot = adapter.predict(
        agent_id="agent-1",
        dimensions={
            "behavioral_deviation": 20.0,
        },
        consequence_exposure=80.0,
    )

    dimension_names = dict(snapshot.dimensions)

    assert dimension_names["consequence_exposure"] == 80.0


def test_predict_serialized_returns_api_safe_payload():
    adapter = PredictiveSecurityPlatformAdapter()

    payload = adapter.predict_serialized(
        agent_id="agent-1",
        dimensions={
            "behavioral_deviation": 40.0,
            "trajectory_risk": 60.0,
        },
    )

    assert payload["agent_id"] == "agent-1"
    assert isinstance(payload["predictive_score"], float)
    assert isinstance(payload["dimensions"], list)
    assert isinstance(payload["evidence"], list)

    assert all(
        isinstance(item, dict)
        and "name" in item
        and "value" in item
        for item in payload["dimensions"]
    )


def test_latest_returns_latest_prediction():
    adapter = PredictiveSecurityPlatformAdapter()

    first = adapter.predict(
        agent_id="agent-1",
        dimensions={"behavioral_deviation": 20.0},
    )

    second = adapter.predict(
        agent_id="agent-1",
        dimensions={"behavioral_deviation": 80.0},
    )

    assert adapter.latest("agent-1") == second
    assert adapter.latest("agent-1") != first


def test_latest_returns_none_for_unknown_agent():
    adapter = PredictiveSecurityPlatformAdapter()

    assert adapter.latest("unknown-agent") is None


def test_latest_serialized_returns_api_safe_payload():
    adapter = PredictiveSecurityPlatformAdapter()

    adapter.predict(
        agent_id="agent-1",
        dimensions={"behavioral_deviation": 50.0},
    )

    payload = adapter.latest_serialized("agent-1")

    assert payload is not None
    assert payload["agent_id"] == "agent-1"
    assert isinstance(payload["dimensions"], list)
    assert isinstance(payload["evidence"], list)


def test_history_preserves_prediction_order():
    adapter = PredictiveSecurityPlatformAdapter()

    first = adapter.predict(
        agent_id="agent-1",
        dimensions={"behavioral_deviation": 20.0},
    )

    second = adapter.predict(
        agent_id="agent-1",
        dimensions={"behavioral_deviation": 40.0},
    )

    third = adapter.predict(
        agent_id="agent-1",
        dimensions={"behavioral_deviation": 60.0},
    )

    history = adapter.history("agent-1")

    assert history == (first, second, third)


def test_history_is_agent_isolated():
    adapter = PredictiveSecurityPlatformAdapter()

    adapter.predict(
        agent_id="agent-1",
        dimensions={"behavioral_deviation": 20.0},
    )

    adapter.predict(
        agent_id="agent-2",
        dimensions={"behavioral_deviation": 80.0},
    )

    assert len(adapter.history("agent-1")) == 1
    assert len(adapter.history("agent-2")) == 1

    assert adapter.history("agent-1")[0].agent_id == "agent-1"
    assert adapter.history("agent-2")[0].agent_id == "agent-2"


def test_history_serialized_returns_api_safe_history():
    adapter = PredictiveSecurityPlatformAdapter()

    adapter.predict(
        agent_id="agent-1",
        dimensions={"behavioral_deviation": 20.0},
    )

    adapter.predict(
        agent_id="agent-1",
        dimensions={"behavioral_deviation": 70.0},
    )

    history = adapter.history_serialized("agent-1")

    assert len(history) == 2
    assert all(
        isinstance(item["dimensions"], list)
        for item in history
    )
    assert all(
        isinstance(item["evidence"], list)
        for item in history
    )


def test_history_count_matches_predictions():
    adapter = PredictiveSecurityPlatformAdapter()

    assert adapter.history_count("agent-1") == 0

    adapter.predict(
        agent_id="agent-1",
        dimensions={"behavioral_deviation": 20.0},
    )

    assert adapter.history_count("agent-1") == 1

    adapter.predict(
        agent_id="agent-1",
        dimensions={"behavioral_deviation": 40.0},
    )

    assert adapter.history_count("agent-1") == 2


def test_reset_clears_only_requested_agent():
    adapter = PredictiveSecurityPlatformAdapter()

    adapter.predict(
        agent_id="agent-1",
        dimensions={"behavioral_deviation": 20.0},
    )

    adapter.predict(
        agent_id="agent-2",
        dimensions={"behavioral_deviation": 80.0},
    )

    adapter.reset("agent-1")

    assert adapter.history_count("agent-1") == 0
    assert adapter.history_count("agent-2") == 1


def test_reset_without_agent_clears_all_history():
    adapter = PredictiveSecurityPlatformAdapter()

    adapter.predict(
        agent_id="agent-1",
        dimensions={"behavioral_deviation": 20.0},
    )

    adapter.predict(
        agent_id="agent-2",
        dimensions={"behavioral_deviation": 80.0},
    )

    adapter.reset()

    assert adapter.history_count("agent-1") == 0
    assert adapter.history_count("agent-2") == 0


def test_invalid_dimensions_are_rejected_by_core_engine():
    adapter = PredictiveSecurityPlatformAdapter()

    with pytest.raises(ValueError, match="dimensions must not be empty"):
        adapter.predict(
            agent_id="agent-1",
            dimensions={},
        )


def test_invalid_agent_id_is_rejected_by_core_engine():
    adapter = PredictiveSecurityPlatformAdapter()

    with pytest.raises(ValueError, match="agent_id must not be empty"):
        adapter.predict(
            agent_id="",
            dimensions={"behavioral_deviation": 50.0},
        )


def test_custom_engine_can_be_injected():
    engine = PredictiveSecurityEngine()

    adapter = PredictiveSecurityPlatformAdapter(engine=engine)

    snapshot = adapter.predict(
        agent_id="agent-1",
        dimensions={"behavioral_deviation": 50.0},
    )

    assert adapter.engine is engine
    assert adapter.latest("agent-1") == snapshot
    assert engine.latest("agent-1") == snapshot


def test_platform_adapter_does_not_share_history_between_instances():
    first_adapter = PredictiveSecurityPlatformAdapter()
    second_adapter = PredictiveSecurityPlatformAdapter()

    first_adapter.predict(
        agent_id="agent-1",
        dimensions={"behavioral_deviation": 50.0},
    )

    assert first_adapter.history_count("agent-1") == 1
    assert second_adapter.history_count("agent-1") == 0


def test_serialization_does_not_mutate_snapshot():
    adapter = PredictiveSecurityPlatformAdapter()

    snapshot = adapter.predict(
        agent_id="agent-1",
        dimensions={"behavioral_deviation": 50.0},
    )

    payload = adapter.latest_serialized("agent-1")

    assert payload is not None
    assert isinstance(snapshot.dimensions, tuple)
    assert isinstance(snapshot.evidence, tuple)

    assert isinstance(payload["dimensions"], list)
    assert isinstance(payload["evidence"], list)


def test_multiple_predictions_increment_observation_count():
    adapter = PredictiveSecurityPlatformAdapter()

    first = adapter.predict(
        agent_id="agent-1",
        dimensions={"behavioral_deviation": 20.0},
    )

    second = adapter.predict(
        agent_id="agent-1",
        dimensions={"behavioral_deviation": 40.0},
    )

    third = adapter.predict(
        agent_id="agent-1",
        dimensions={"behavioral_deviation": 60.0},
    )

    assert first.observation_count == 1
    assert second.observation_count == 2
    assert third.observation_count == 3