from datetime import datetime, timedelta, timezone

import pytest

from app.behavioral_trust import (
    DEFAULT_WEIGHTS,
    DynamicBehavioralTrust,
    NEUTRAL_TRUST,
    TRUST_MAX,
    TRUST_MIN,
    aggregate_trust_evidence,
    apply_time_decay,
    calculate_time_decay,
    classify_trust,
)


def test_empty_evidence_is_neutral():
    assert (
        aggregate_trust_evidence({})
        == NEUTRAL_TRUST
    )


def test_missing_dimensions_are_not_treated_as_zero():
    score = aggregate_trust_evidence(
        {
            "behavioral_consistency": 80,
        }
    )

    assert score == 80.0


def test_weighted_evidence_is_bounded():
    score = aggregate_trust_evidence(
        {
            "behavioral_consistency": 100,
            "anomaly_resistance": 0,
            "authorization_consistency": 50,
        }
    )

    assert TRUST_MIN <= score <= TRUST_MAX


def test_default_weights_are_positive():
    assert DEFAULT_WEIGHTS
    assert all(
        weight > 0
        for weight in DEFAULT_WEIGHTS.values()
    )


def test_negative_weight_is_rejected():
    with pytest.raises(ValueError):
        aggregate_trust_evidence(
            {
                "behavioral_consistency": 80,
            },
            {
                "behavioral_consistency": -1,
            },
        )


def test_invalid_evidence_type_is_rejected():
    with pytest.raises(TypeError):
        aggregate_trust_evidence(
            []
        )


def test_evidence_above_upper_bound_is_rejected():
    with pytest.raises(ValueError):
        aggregate_trust_evidence(
            {
                "behavioral_consistency": 101,
            }
        )


def test_evidence_below_lower_bound_is_rejected():
    with pytest.raises(ValueError):
        aggregate_trust_evidence(
            {
                "behavioral_consistency": -1,
            }
        )


def test_non_finite_evidence_is_rejected():
    with pytest.raises(ValueError):
        aggregate_trust_evidence(
            {
                "behavioral_consistency": float("nan"),
            }
        )


def test_time_decay_at_zero_age_is_one():
    assert calculate_time_decay(
        age_hours=0,
        half_life_hours=72,
    ) == pytest.approx(1.0)


def test_time_decay_at_half_life_is_half():
    assert calculate_time_decay(
        age_hours=72,
        half_life_hours=72,
    ) == pytest.approx(0.5)


def test_time_decay_reduces_historical_distance_from_neutral():
    result = apply_time_decay(
        trust_score=90,
        age_hours=72,
        half_life_hours=72,
    )

    assert result == pytest.approx(70.0)


def test_low_trust_also_decays_toward_neutral():
    result = apply_time_decay(
        trust_score=10,
        age_hours=72,
        half_life_hours=72,
    )

    assert result == pytest.approx(30.0)


def test_invalid_half_life_is_rejected():
    with pytest.raises(ValueError):
        calculate_time_decay(
            age_hours=1,
            half_life_hours=0,
        )


def test_trust_band_boundaries():
    assert classify_trust(100) == "HIGH"
    assert classify_trust(80) == "HIGH"
    assert classify_trust(79.999) == "MODERATE"
    assert classify_trust(60) == "MODERATE"
    assert classify_trust(59.999) == "LOW"
    assert classify_trust(40) == "LOW"
    assert classify_trust(39.999) == "CRITICAL"
    assert classify_trust(0) == "CRITICAL"


def test_trust_engine_starts_at_neutral():
    engine = DynamicBehavioralTrust()

    assert (
        engine.get_trust("agent-a")
        == NEUTRAL_TRUST
    )


def test_positive_evidence_increases_trust():
    engine = DynamicBehavioralTrust(
        learning_rate=1.0
    )

    snapshot = engine.update(
        "agent-a",
        {
            "behavioral_consistency": 100,
            "anomaly_resistance": 100,
            "authorization_consistency": 100,
            "context_consistency": 100,
            "risk_stability": 100,
            "activity_stability": 100,
        },
    )

    assert snapshot.trust_score == 100.0
    assert snapshot.trust_band == "HIGH"


def test_negative_evidence_decreases_trust():
    engine = DynamicBehavioralTrust(
        learning_rate=1.0
    )

    snapshot = engine.update(
        "agent-a",
        {
            "behavioral_consistency": 0,
            "anomaly_resistance": 0,
            "authorization_consistency": 0,
            "context_consistency": 0,
            "risk_stability": 0,
            "activity_stability": 0,
        },
    )

    assert snapshot.trust_score == 0.0
    assert snapshot.trust_band == "CRITICAL"


def test_partial_evidence_is_supported():
    engine = DynamicBehavioralTrust(
        learning_rate=1.0
    )

    snapshot = engine.update(
        "agent-a",
        {
            "behavioral_consistency": 90,
        },
    )

    assert snapshot.trust_score == 90.0


def test_missing_evidence_does_not_penalize_agent():
    engine = DynamicBehavioralTrust(
        learning_rate=1.0
    )

    snapshot = engine.update(
        "agent-a",
        {},
    )

    assert snapshot.trust_score == 50.0


def test_learning_rate_controls_update_strength():
    engine = DynamicBehavioralTrust(
        learning_rate=0.5
    )

    snapshot = engine.update(
        "agent-a",
        {
            "behavioral_consistency": 100,
        },
    )

    assert snapshot.trust_score == 75.0


def test_trust_state_is_bounded():
    engine = DynamicBehavioralTrust(
        learning_rate=1.0
    )

    high = engine.update(
        "agent-a",
        {
            "behavioral_consistency": 100,
        },
    )

    assert 0 <= high.trust_score <= 100


def test_history_is_recorded():
    engine = DynamicBehavioralTrust(
        learning_rate=1.0
    )

    first_time = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    second_time = first_time + timedelta(
        hours=1
    )

    engine.update(
        "agent-a",
        {
            "behavioral_consistency": 80,
        },
        timestamp=first_time,
    )

    engine.update(
        "agent-a",
        {
            "behavioral_consistency": 60,
        },
        timestamp=second_time,
    )

    history = engine.get_history(
        "agent-a"
    )

    assert len(history) == 2
    assert history[0].update_index == 1
    assert history[1].update_index == 2


def test_history_is_immutable_tuple():
    engine = DynamicBehavioralTrust()

    history = engine.get_history(
        "agent-a"
    )

    assert isinstance(history, tuple)


def test_snapshot_contains_required_fields():
    engine = DynamicBehavioralTrust()

    snapshot = engine.update(
        "agent-a",
        {
            "behavioral_consistency": 75,
        },
    )

    data = snapshot.to_dict()

    assert data["agent_id"] == "agent-a"
    assert "trust_score" in data
    assert "trust_band" in data
    assert "evidence_score" in data
    assert "evidence" in data
    assert "timestamp" in data
    assert "update_index" in data


def test_snapshot_is_deterministic_for_same_inputs():
    timestamp = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    evidence = {
        "behavioral_consistency": 80,
        "anomaly_resistance": 70,
        "authorization_consistency": 90,
    }

    first_engine = DynamicBehavioralTrust(
        learning_rate=0.25
    )

    second_engine = DynamicBehavioralTrust(
        learning_rate=0.25
    )

    first = first_engine.update(
        "agent-a",
        evidence,
        timestamp=timestamp,
    )

    second = second_engine.update(
        "agent-a",
        evidence,
        timestamp=timestamp,
    )

    assert first.to_dict() == second.to_dict()


def test_timestamp_cannot_move_backward():
    engine = DynamicBehavioralTrust()

    first_time = datetime(
        2026,
        1,
        2,
        tzinfo=timezone.utc,
    )

    earlier_time = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    engine.update(
        "agent-a",
        {
            "behavioral_consistency": 70,
        },
        timestamp=first_time,
    )

    with pytest.raises(ValueError):
        engine.update(
            "agent-a",
            {
                "behavioral_consistency": 80,
            },
            timestamp=earlier_time,
        )


def test_multiple_agents_have_independent_state():
    engine = DynamicBehavioralTrust(
        learning_rate=1.0
    )

    engine.update(
        "agent-a",
        {
            "behavioral_consistency": 90,
        },
    )

    engine.update(
        "agent-b",
        {
            "behavioral_consistency": 20,
        },
    )

    assert (
        engine.get_trust("agent-a")
        == 90.0
    )

    assert (
        engine.get_trust("agent-b")
        == 20.0
    )


def test_reset_removes_state():
    engine = DynamicBehavioralTrust(
        learning_rate=1.0
    )

    engine.update(
        "agent-a",
        {
            "behavioral_consistency": 90,
        },
    )

    engine.reset("agent-a")

    assert (
        engine.get_trust("agent-a")
        == NEUTRAL_TRUST
    )

    assert (
        engine.get_snapshot("agent-a")
        is None
    )


def test_snapshot_all_returns_latest_state():
    engine = DynamicBehavioralTrust(
        learning_rate=1.0
    )

    engine.update(
        "agent-a",
        {
            "behavioral_consistency": 90,
        },
    )

    engine.update(
        "agent-b",
        {
            "behavioral_consistency": 30,
        },
    )

    result = engine.snapshot_all()

    assert set(result) == {
        "agent-a",
        "agent-b",
    }

    assert (
        result["agent-a"]["trust_score"]
        == 90.0
    )

    assert (
        result["agent-b"]["trust_score"]
        == 30.0
    )