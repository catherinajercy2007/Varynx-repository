from app.behavioral_baseline import (
    AdaptiveBehavioralBaseline,
    calculate_baseline_update,
    calculate_dimension_deviation,
    calculate_mean_deviation,
)


def test_baseline_update_moves_toward_observation():
    result = calculate_baseline_update(
        20,
        40,
        learning_rate=0.10,
    )

    assert result == 22


def test_baseline_update_with_full_learning_rate():
    result = calculate_baseline_update(
        20,
        80,
        learning_rate=1.0,
    )

    assert result == 80


def test_baseline_update_is_bounded():
    assert 0 <= calculate_baseline_update(0, 100, 0.5) <= 100
    assert 0 <= calculate_baseline_update(100, 0, 0.5) <= 100


def test_dimension_deviation():
    deviations = calculate_dimension_deviation(
        {
            "action": 20,
            "resource": 30,
        },
        {
            "action": 50,
            "resource": 40,
        },
    )

    assert deviations == {
        "action": 30,
        "resource": 10,
    }


def test_mean_deviation():
    result = calculate_mean_deviation(
        {
            "action": 20,
            "resource": 30,
        },
        {
            "action": 40,
            "resource": 50,
        },
    )

    assert result == 20


def test_missing_dimensions_are_ignored():
    result = calculate_mean_deviation(
        {"action": 20},
        {
            "action": 30,
            "resource": 100,
        },
    )

    assert result == 10


def test_manager_requires_baseline():
    manager = AdaptiveBehavioralBaseline()

    try:
        manager.observe(
            "agent-1",
            {"action": 20},
        )
        assert False
    except ValueError as exc:
        assert "baseline" in str(exc)


def test_set_and_get_baseline():
    manager = AdaptiveBehavioralBaseline()

    manager.set_baseline(
        "agent-1",
        {
            "action": 20,
            "resource": 30,
        },
    )

    assert manager.get_baseline("agent-1") == {
        "action": 20,
        "resource": 30,
    }


def test_get_baseline_returns_copy():
    manager = AdaptiveBehavioralBaseline()

    manager.set_baseline(
        "agent-1",
        {"action": 20},
    )

    baseline = manager.get_baseline("agent-1")
    baseline["action"] = 100

    assert manager.get_baseline("agent-1")["action"] == 20


def test_normal_observation_is_accepted():
    manager = AdaptiveBehavioralBaseline(
        learning_rate=0.10,
        max_learning_deviation=30,
    )

    manager.set_baseline(
        "agent-1",
        {
            "action": 20,
            "resource": 20,
        },
    )

    result = manager.observe(
        "agent-1",
        {
            "action": 30,
            "resource": 30,
        },
    )

    assert result.accepted is True
    assert result.mean_deviation == 10


def test_accepted_observation_updates_baseline():
    manager = AdaptiveBehavioralBaseline(
        learning_rate=0.10,
        max_learning_deviation=30,
    )

    manager.set_baseline(
        "agent-1",
        {"action": 20},
    )

    result = manager.observe(
        "agent-1",
        {"action": 40},
    )

    assert result.accepted is True
    assert result.updated_baseline["action"] == 22


def test_high_deviation_observation_is_rejected():
    manager = AdaptiveBehavioralBaseline(
        learning_rate=0.10,
        max_learning_deviation=30,
    )

    manager.set_baseline(
        "agent-1",
        {
            "action": 20,
            "resource": 20,
        },
    )

    result = manager.observe(
        "agent-1",
        {
            "action": 100,
            "resource": 100,
        },
    )

    assert result.accepted is False
    assert result.mean_deviation == 80


def test_rejected_observation_does_not_change_baseline():
    manager = AdaptiveBehavioralBaseline(
        learning_rate=0.10,
        max_learning_deviation=30,
    )

    manager.set_baseline(
        "agent-1",
        {
            "action": 20,
            "resource": 20,
        },
    )

    manager.observe(
        "agent-1",
        {
            "action": 100,
            "resource": 100,
        },
    )

    assert manager.get_baseline("agent-1") == {
        "action": 20,
        "resource": 20,
    }


def test_repeated_normal_observations_adapt_gradually():
    manager = AdaptiveBehavioralBaseline(
        learning_rate=0.10,
        max_learning_deviation=30,
    )

    manager.set_baseline(
        "agent-1",
        {"action": 20},
    )

    manager.observe(
        "agent-1",
        {"action": 40},
    )

    manager.observe(
        "agent-1",
        {"action": 40},
    )

    baseline = manager.get_baseline("agent-1")

    assert baseline["action"] == 23.8


def test_history_is_recorded():
    manager = AdaptiveBehavioralBaseline()

    manager.set_baseline(
        "agent-1",
        {"action": 20},
    )

    manager.observe(
        "agent-1",
        {"action": 25},
    )

    manager.observe(
        "agent-1",
        {"action": 30},
    )

    history = manager.history("agent-1")

    assert len(history) == 2
    assert history[0].update_index == 1
    assert history[1].update_index == 2


def test_latest_update():
    manager = AdaptiveBehavioralBaseline()

    manager.set_baseline(
        "agent-1",
        {"action": 20},
    )

    manager.observe(
        "agent-1",
        {"action": 25},
    )

    latest = manager.latest("agent-1")

    assert latest is not None
    assert latest.update_index == 1


def test_latest_without_history():
    manager = AdaptiveBehavioralBaseline()

    assert manager.latest("agent-1") is None


def test_multiple_agents_are_isolated():
    manager = AdaptiveBehavioralBaseline()

    manager.set_baseline(
        "agent-a",
        {"action": 10},
    )

    manager.set_baseline(
        "agent-b",
        {"action": 90},
    )

    manager.observe(
        "agent-a",
        {"action": 20},
    )

    assert manager.get_baseline("agent-b") == {
        "action": 90,
    }


def test_reset_single_agent():
    manager = AdaptiveBehavioralBaseline()

    manager.set_baseline(
        "agent-1",
        {"action": 20},
    )

    manager.observe(
        "agent-1",
        {"action": 25},
    )

    manager.reset("agent-1")

    assert manager.get_baseline("agent-1") is None
    assert manager.history("agent-1") == []


def test_reset_all_agents():
    manager = AdaptiveBehavioralBaseline()

    manager.set_baseline(
        "agent-1",
        {"action": 20},
    )

    manager.set_baseline(
        "agent-2",
        {"action": 30},
    )

    manager.reset()

    assert manager.get_baseline("agent-1") is None
    assert manager.get_baseline("agent-2") is None


def test_update_record_contains_explanation():
    manager = AdaptiveBehavioralBaseline()

    manager.set_baseline(
        "agent-1",
        {"action": 20},
    )

    result = manager.observe(
        "agent-1",
        {"action": 25},
    )

    assert result.reason
    assert "baseline" in result.reason.lower()


def test_rejected_update_contains_reason():
    manager = AdaptiveBehavioralBaseline(
        max_learning_deviation=10,
    )

    manager.set_baseline(
        "agent-1",
        {"action": 20},
    )

    result = manager.observe(
        "agent-1",
        {"action": 80},
    )

    assert result.accepted is False
    assert "rejected" in result.reason.lower()


def test_learning_threshold_boundary_is_accepted():
    manager = AdaptiveBehavioralBaseline(
        max_learning_deviation=30,
    )

    manager.set_baseline(
        "agent-1",
        {"action": 20},
    )

    result = manager.observe(
        "agent-1",
        {"action": 50},
    )

    assert result.accepted is True


def test_learning_threshold_above_boundary_is_rejected():
    manager = AdaptiveBehavioralBaseline(
        max_learning_deviation=30,
    )

    manager.set_baseline(
        "agent-1",
        {"action": 20},
    )

    result = manager.observe(
        "agent-1",
        {"action": 51,
        },
    )

    assert result.accepted is False


def test_snapshot_preserves_previous_baseline():
    manager = AdaptiveBehavioralBaseline(
        learning_rate=0.10,
    )

    manager.set_baseline(
        "agent-1",
        {"action": 20},
    )

    result = manager.observe(
        "agent-1",
        {"action": 30},
    )

    assert result.previous_baseline == {
        "action": 20,
    }


def test_observation_is_preserved():
    manager = AdaptiveBehavioralBaseline()

    manager.set_baseline(
        "agent-1",
        {"action": 20},
    )

    result = manager.observe(
        "agent-1",
        {"action": 30},
    )

    assert result.observation == {
        "action": 30,
    }


def test_observation_does_not_modify_input():
    manager = AdaptiveBehavioralBaseline()

    manager.set_baseline(
        "agent-1",
        {"action": 20},
    )

    observation = {"action": 30}

    manager.observe(
        "agent-1",
        observation,
    )

    assert observation == {
        "action": 30,
    }


def test_baseline_does_not_exceed_bounds():
    manager = AdaptiveBehavioralBaseline(
        learning_rate=0.5,
    )

    manager.set_baseline(
        "agent-1",
        {"action": 100},
    )

    result = manager.observe(
        "agent-1",
        {"action": 100},
    )

    assert result.updated_baseline["action"] == 100


def test_zero_deviation_is_safe_to_learn():
    manager = AdaptiveBehavioralBaseline()

    manager.set_baseline(
        "agent-1",
        {"action": 50},
    )

    result = manager.observe(
        "agent-1",
        {"action": 50},
    )

    assert result.accepted is True
    assert result.mean_deviation == 0
    assert result.updated_baseline["action"] == 50


def test_manager_is_not_a_security_decision_engine():
    manager = AdaptiveBehavioralBaseline()

    manager.set_baseline(
        "agent-1",
        {"action": 20},
    )

    result = manager.observe(
        "agent-1",
        {"action": 100},
    )

    assert hasattr(result, "accepted")
    assert hasattr(result, "mean_deviation")
    assert hasattr(result, "updated_baseline")

    assert not hasattr(result, "decision")
    assert not hasattr(result, "response")
    assert not hasattr(result, "action")


def test_update_indices_are_monotonic():
    manager = AdaptiveBehavioralBaseline()

    manager.set_baseline(
        "agent-1",
        {"action": 20},
    )

    first = manager.observe(
        "agent-1",
        {"action": 25},
    )

    second = manager.observe(
        "agent-1",
        {"action": 30},
    )

    third = manager.observe(
        "agent-1",
        {"action": 35},
    )

    assert first.update_index == 1
    assert second.update_index == 2
    assert third.update_index == 3