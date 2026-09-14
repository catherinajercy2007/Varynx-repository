"""
Day 56 tests:
Predictive Security Signal Engine.
"""

import pytest

from app.predictive_security import (
    DEFAULT_WEIGHTS,
    PredictiveSecurityEngine,
    PredictiveSecuritySnapshot,
    build_predictive_evidence,
    calculate_acceleration,
    calculate_confidence,
    calculate_predictive_signal,
    calculate_trajectory,
    classify_signal,
)


def build_dimensions():
    return {
        "behavioral_deviation": 30,
        "trust_decline": 20,
        "state_instability": 25,
        "consequence_exposure": 40,
        "behavioral_acceleration": 20,
    }


def test_default_weights_are_valid():
    assert DEFAULT_WEIGHTS
    assert sum(DEFAULT_WEIGHTS.values()) == pytest.approx(1.0)


def test_classify_signal():
    assert classify_signal(10) == "LOW"
    assert classify_signal(30) == "MODERATE"
    assert classify_signal(50) == "HIGH"
    assert classify_signal(80) == "CRITICAL"


def test_classify_signal_boundaries():
    assert classify_signal(0) == "LOW"
    assert classify_signal(19.99) == "LOW"
    assert classify_signal(20) == "MODERATE"
    assert classify_signal(40) == "HIGH"
    assert classify_signal(70) == "CRITICAL"
    assert classify_signal(100) == "CRITICAL"


def test_calculate_predictive_signal():
    score = calculate_predictive_signal(
        build_dimensions()
    )

    assert 0 <= score <= 100


def test_calculate_predictive_signal_is_deterministic():
    dimensions = build_dimensions()

    first = calculate_predictive_signal(
        dimensions
    )

    second = calculate_predictive_signal(
        dimensions
    )

    assert first == second


def test_missing_dimensions_are_renormalized():
    dimensions = {
        "behavioral_deviation": 80,
        "trust_decline": 20,
    }

    score = calculate_predictive_signal(
        dimensions
    )

    expected = (
        (80 * 0.25) +
        (20 * 0.20)
    ) / (
        0.25 + 0.20
    )

    assert score == pytest.approx(expected)


def test_invalid_dimension_score():
    with pytest.raises(ValueError):
        calculate_predictive_signal(
            {
                "behavioral_deviation": 101,
            }
        )


def test_invalid_dimension_type():
    with pytest.raises(TypeError):
        calculate_predictive_signal(
            {
                "behavioral_deviation": "high",
            }
        )


def test_trajectory_stable():
    assert (
        calculate_trajectory(50, 52)
        == "STABLE"
    )


def test_trajectory_deteriorating():
    assert (
        calculate_trajectory(40, 60)
        == "DETERIORATING"
    )


def test_trajectory_improving():
    assert (
        calculate_trajectory(70, 50)
        == "IMPROVING"
    )


def test_acceleration_two_points():
    assert (
        calculate_acceleration(40, 60)
        == pytest.approx(20)
    )


def test_acceleration_three_points():
    assert (
        calculate_acceleration(
            40,
            70,
            50,
        )
        == pytest.approx(20)
    )


def test_positive_acceleration():
    result = calculate_acceleration(
        20,
        60,
        30,
    )

    assert result == pytest.approx(30)


def test_negative_acceleration():
    result = calculate_acceleration(
        70,
        40,
        80,
    )

    assert result == pytest.approx(-40)


def test_confidence():
    assert calculate_confidence(1) == "LOW"
    assert calculate_confidence(2) == "MODERATE"
    assert calculate_confidence(3) == "HIGH"
    assert calculate_confidence(10) == "HIGH"


def test_invalid_confidence_count():
    with pytest.raises(ValueError):
        calculate_confidence(0)


def test_evidence_generation():
    evidence = build_predictive_evidence(
        {
            "behavioral_deviation": 80,
            "trust_decline": 20,
        },
        "DETERIORATING",
    )

    assert evidence

    assert any(
        "behavioral_deviation" in item
        for item in evidence
    )


def test_engine_returns_snapshot():
    engine = PredictiveSecurityEngine()

    result = engine.predict(
        agent_id="agent-1",
        dimensions=build_dimensions(),
    )

    assert isinstance(
        result,
        PredictiveSecuritySnapshot,
    )


def test_engine_score_is_bounded():
    engine = PredictiveSecurityEngine()

    result = engine.predict(
        agent_id="agent-1",
        dimensions={
            key: 100
            for key in build_dimensions()
        },
    )

    assert 0 <= result.predictive_score <= 100


def test_engine_first_prediction_is_stable():
    engine = PredictiveSecurityEngine()

    result = engine.predict(
        agent_id="agent-1",
        dimensions=build_dimensions(),
    )

    assert result.trajectory == "STABLE"
    assert result.observation_count == 1


def test_engine_detects_deterioration():
    engine = PredictiveSecurityEngine()

    engine.predict(
        agent_id="agent-1",
        dimensions={
            key: 20
            for key in build_dimensions()
        },
    )

    result = engine.predict(
        agent_id="agent-1",
        dimensions={
            key: 80
            for key in build_dimensions()
        },
    )

    assert result.trajectory == "DETERIORATING"


def test_engine_detects_improvement():
    engine = PredictiveSecurityEngine()

    engine.predict(
        agent_id="agent-1",
        dimensions={
            key: 80
            for key in build_dimensions()
        },
    )

    result = engine.predict(
        agent_id="agent-1",
        dimensions={
            key: 20
            for key in build_dimensions()
        },
    )

    assert result.trajectory == "IMPROVING"


def test_engine_confidence_increases():
    engine = PredictiveSecurityEngine()

    first = engine.predict(
        agent_id="agent-1",
        dimensions=build_dimensions(),
    )

    second = engine.predict(
        agent_id="agent-1",
        dimensions=build_dimensions(),
    )

    third = engine.predict(
        agent_id="agent-1",
        dimensions=build_dimensions(),
    )

    assert first.confidence == "LOW"
    assert second.confidence == "MODERATE"
    assert third.confidence == "HIGH"


def test_history():
    engine = PredictiveSecurityEngine()

    engine.predict(
        agent_id="agent-1",
        dimensions=build_dimensions(),
    )

    engine.predict(
        agent_id="agent-1",
        dimensions=build_dimensions(),
    )

    assert engine.history_count(
        "agent-1"
    ) == 2

    assert len(
        engine.history("agent-1")
    ) == 2


def test_latest():
    engine = PredictiveSecurityEngine()

    first = engine.predict(
        agent_id="agent-1",
        dimensions=build_dimensions(),
    )

    second = engine.predict(
        agent_id="agent-1",
        dimensions={
            key: 80
            for key in build_dimensions()
        },
    )

    assert engine.latest(
        "agent-1"
    ) == second

    assert engine.latest(
        "agent-1"
    ) != first


def test_multiple_agents_are_independent():
    engine = PredictiveSecurityEngine()

    first = engine.predict(
        agent_id="agent-1",
        dimensions=build_dimensions(),
    )

    second = engine.predict(
        agent_id="agent-2",
        dimensions=build_dimensions(),
    )

    assert first.agent_id == "agent-1"
    assert second.agent_id == "agent-2"

    assert engine.history_count(
        "agent-1"
    ) == 1

    assert engine.history_count(
        "agent-2"
    ) == 1


def test_reset_single_agent():
    engine = PredictiveSecurityEngine()

    engine.predict(
        agent_id="agent-1",
        dimensions=build_dimensions(),
    )

    engine.predict(
        agent_id="agent-2",
        dimensions=build_dimensions(),
    )

    engine.reset("agent-1")

    assert engine.history_count(
        "agent-1"
    ) == 0

    assert engine.history_count(
        "agent-2"
    ) == 1


def test_reset_all():
    engine = PredictiveSecurityEngine()

    engine.predict(
        agent_id="agent-1",
        dimensions=build_dimensions(),
    )

    engine.predict(
        agent_id="agent-2",
        dimensions=build_dimensions(),
    )

    engine.reset()

    assert engine.history_count(
        "agent-1"
    ) == 0

    assert engine.history_count(
        "agent-2"
    ) == 0


def test_consequence_exposure_can_be_supplied():
    engine = PredictiveSecurityEngine()

    dimensions = {
        "behavioral_deviation": 40,
        "trust_decline": 40,
        "state_instability": 40,
        "behavioral_acceleration": 40,
    }

    result = engine.predict(
        agent_id="agent-1",
        dimensions=dimensions,
        consequence_exposure=80,
    )

    assert 0 <= result.predictive_score <= 100

    dimension_names = dict(
        result.dimensions
    )

    assert (
        dimension_names[
            "consequence_exposure"
        ]
        == 80
    )


def test_result_is_immutable():
    engine = PredictiveSecurityEngine()

    result = engine.predict(
        agent_id="agent-1",
        dimensions=build_dimensions(),
    )

    with pytest.raises(AttributeError):
        result.agent_id = "changed"


def test_repeated_prediction_is_deterministic():
    engine = PredictiveSecurityEngine()

    first = engine.predict(
        agent_id="agent-1",
        dimensions=build_dimensions(),
    )

    second = engine.predict(
        agent_id="agent-2",
        dimensions=build_dimensions(),
    )

    assert (
        first.predictive_score
        == second.predictive_score
    )

    assert (
        first.signal_level
        == second.signal_level
    )


def test_empty_dimensions_rejected():
    engine = PredictiveSecurityEngine()

    with pytest.raises(ValueError):
        engine.predict(
            agent_id="agent-1",
            dimensions={},
        )


def test_empty_agent_id_rejected():
    engine = PredictiveSecurityEngine()

    with pytest.raises(ValueError):
        engine.predict(
            agent_id="",
            dimensions=build_dimensions(),
        )