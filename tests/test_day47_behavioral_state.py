from datetime import datetime, timedelta, timezone

import pytest

from app.behavioral_state import (
    DEFAULT_STATE_WEIGHTS,
    NEUTRAL_STATE,
    BehavioralStateModel,
    aggregate_behavioral_state,
    calculate_deviation,
    calculate_stability,
    classify_behavioral_state,
)


def test_empty_dimensions_are_neutral():
    assert (
        aggregate_behavioral_state({})
        == NEUTRAL_STATE
    )


def test_missing_dimensions_are_neutral_not_negative():
    result = aggregate_behavioral_state(
        {
            "action_consistency": 80,
        }
    )

    assert result == 80.0


def test_default_weights_are_positive():
    assert DEFAULT_STATE_WEIGHTS
    assert all(
        value > 0
        for value in DEFAULT_STATE_WEIGHTS.values()
    )


def test_weighted_state_is_bounded():
    result = aggregate_behavioral_state(
        {
            "action_consistency": 100,
            "resource_consistency": 0,
            "context_consistency": 50,
        }
    )

    assert 0 <= result <= 100


def test_negative_weights_are_rejected():
    with pytest.raises(ValueError):
        aggregate_behavioral_state(
            {
                "action_consistency": 80,
            },
            {
                "action_consistency": -1,
            },
        )


def test_dimension_above_upper_bound_is_rejected():
    with pytest.raises(ValueError):
        aggregate_behavioral_state(
            {
                "action_consistency": 101,
            }
        )


def test_dimension_below_lower_bound_is_rejected():
    with pytest.raises(ValueError):
        aggregate_behavioral_state(
            {
                "action_consistency": -1,
            }
        )


def test_non_mapping_dimensions_are_rejected():
    with pytest.raises(TypeError):
        aggregate_behavioral_state([])


def test_deviation_zero_for_identical_scores():
    assert (
        calculate_deviation(
            50,
            50,
        )
        == 0
    )


def test_deviation_is_absolute():
    assert (
        calculate_deviation(
            20,
            80,
        )
        == 60
    )

    assert (
        calculate_deviation(
            80,
            20,
        )
        == 60
    )


def test_deviation_is_bounded():
    assert (
        calculate_deviation(
            0,
            100,
        )
        == 100
    )


def test_stability_is_perfect_for_constant_sequence():
    assert (
        calculate_stability(
            [80, 80, 80, 80]
        )
        == 100.0
    )


def test_single_observation_is_stable():
    assert (
        calculate_stability([75])
        == 100.0
    )


def test_empty_history_is_neutral():
    assert (
        calculate_stability([])
        == NEUTRAL_STATE
    )


def test_high_variability_reduces_stability():
    stable = calculate_stability(
        [70, 70, 70, 70]
    )

    variable = calculate_stability(
        [0, 100, 0, 100]
    )

    assert variable < stable


def test_stability_is_bounded():
    result = calculate_stability(
        [0, 100, 0, 100]
    )

    assert 0 <= result <= 100


def test_state_classification():
    assert classify_behavioral_state(
        100
    ) == "STABLE"

    assert classify_behavioral_state(
        80
    ) == "STABLE"

    assert classify_behavioral_state(
        70
    ) == "MOSTLY_STABLE"

    assert classify_behavioral_state(
        50
    ) == "VARIABLE"

    assert classify_behavioral_state(
        30
    ) == "UNSTABLE"

    assert classify_behavioral_state(
        10
    ) == "HIGHLY_UNSTABLE"


def test_model_starts_neutral():
    model = BehavioralStateModel()

    assert (
        model.get_state_score(
            "agent-a"
        )
        == 50
    )

    assert (
        model.get_stability(
            "agent-a"
        )
        == 50
    )


def test_positive_behavioral_state():
    model = BehavioralStateModel()

    snapshot = model.update(
        "agent-a",
        {
            "action_consistency": 100,
            "resource_consistency": 100,
            "context_consistency": 100,
            "authorization_consistency": 100,
            "temporal_consistency": 100,
            "behavioral_stability": 100,
        },
    )

    assert snapshot.state_score == 100.0
    assert snapshot.stability_score == 100.0
    assert snapshot.state_class == "STABLE"


def test_negative_behavioral_state():
    model = BehavioralStateModel()

    snapshot = model.update(
        "agent-a",
        {
            "action_consistency": 0,
            "resource_consistency": 0,
            "context_consistency": 0,
            "authorization_consistency": 0,
            "temporal_consistency": 0,
            "behavioral_stability": 0,
        },
    )

    assert snapshot.state_score == 0.0
    assert snapshot.state_class == "STABLE"


def test_partial_dimensions_are_supported():
    model = BehavioralStateModel()

    snapshot = model.update(
        "agent-a",
        {
            "action_consistency": 90,
        },
    )

    assert snapshot.state_score == 90.0


def test_state_history_is_recorded():
    model = BehavioralStateModel()

    timestamp = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    model.update(
        "agent-a",
        {
            "action_consistency": 80,
        },
        timestamp=timestamp,
    )

    model.update(
        "agent-a",
        {
            "action_consistency": 60,
        },
        timestamp=timestamp + timedelta(hours=1),
    )

    history = model.get_history(
        "agent-a"
    )

    assert len(history) == 2
    assert history[0].update_index == 1
    assert history[1].update_index == 2


def test_history_window_is_bounded():
    model = BehavioralStateModel(
        history_window=3
    )

    timestamp = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    for index in range(5):
        model.update(
            "agent-a",
            {
                "action_consistency": (
                    50 + index * 10
                ),
            },
            timestamp=timestamp
            + timedelta(hours=index),
        )

    history = model.get_history(
        "agent-a"
    )

    assert len(history) == 5


def test_stability_uses_recent_history_window():
    model = BehavioralStateModel(
        history_window=3
    )

    timestamp = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    values = [10, 90, 90, 90]

    for index, value in enumerate(values):
        model.update(
            "agent-a",
            {
                "action_consistency": value,
            },
            timestamp=timestamp
            + timedelta(hours=index),
        )

    snapshot = model.get_snapshot(
        "agent-a"
    )

    assert snapshot is not None
    assert snapshot.state_score == 90.0


def test_reference_deviation_is_recorded():
    model = BehavioralStateModel(
        reference_score=50
    )

    snapshot = model.update(
        "agent-a",
        {
            "action_consistency": 90,
        },
    )

    assert (
        snapshot.deviation_from_reference
        == 40.0
    )


def test_custom_reference_can_be_used():
    model = BehavioralStateModel()

    snapshot = model.update(
        "agent-a",
        {
            "action_consistency": 80,
        },
        reference_score=70,
    )

    assert (
        snapshot.deviation_from_reference
        == 10.0
    )


def test_snapshot_contains_expected_fields():
    model = BehavioralStateModel()

    snapshot = model.update(
        "agent-a",
        {
            "action_consistency": 80,
        },
    )

    data = snapshot.to_dict()

    assert data["agent_id"] == "agent-a"
    assert "state_score" in data
    assert "state_class" in data
    assert "dimensions" in data
    assert "stability_score" in data
    assert "deviation_from_reference" in data
    assert "timestamp" in data
    assert "update_index" in data


def test_snapshots_are_deterministic():
    timestamp = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    dimensions = {
        "action_consistency": 80,
        "resource_consistency": 70,
        "context_consistency": 90,
    }

    first = BehavioralStateModel().update(
        "agent-a",
        dimensions,
        timestamp=timestamp,
    )

    second = BehavioralStateModel().update(
        "agent-a",
        dimensions,
        timestamp=timestamp,
    )

    assert first.to_dict() == second.to_dict()


def test_multiple_agents_are_independent():
    model = BehavioralStateModel()

    model.update(
        "agent-a",
        {
            "action_consistency": 90,
        },
    )

    model.update(
        "agent-b",
        {
            "action_consistency": 20,
        },
    )

    assert (
        model.get_state_score(
            "agent-a"
        )
        == 90
    )

    assert (
        model.get_state_score(
            "agent-b"
        )
        == 20
    )


def test_timestamp_cannot_move_backward():
    model = BehavioralStateModel()

    first = datetime(
        2026,
        1,
        2,
        tzinfo=timezone.utc,
    )

    earlier = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    model.update(
        "agent-a",
        {
            "action_consistency": 80,
        },
        timestamp=first,
    )

    with pytest.raises(ValueError):
        model.update(
            "agent-a",
            {
                "action_consistency": 90,
            },
            timestamp=earlier,
        )


def test_reset_removes_state():
    model = BehavioralStateModel()

    model.update(
        "agent-a",
        {
            "action_consistency": 90,
        },
    )

    model.reset("agent-a")

    assert (
        model.get_state_score(
            "agent-a"
        )
        == NEUTRAL_STATE
    )

    assert (
        model.get_snapshot(
            "agent-a"
        )
        is None
    )


def test_invalid_history_window_is_rejected():
    with pytest.raises(ValueError):
        BehavioralStateModel(
            history_window=0
        )


def test_invalid_reference_score_is_rejected():
    with pytest.raises(ValueError):
        BehavioralStateModel(
            reference_score=101
        )