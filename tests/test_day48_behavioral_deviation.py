from app.behavioral_deviation import (
    BehavioralDeviationDetector,
    aggregate_deviation,
    calculate_deviation,
    calculate_relative_deviation,
    classify_deviation,
    identify_deviation_evidence,
)


def test_zero_deviation():
    assert calculate_deviation(50, 50) == 0


def test_absolute_deviation():
    assert calculate_deviation(20, 70) == 50


def test_deviation_is_symmetric():
    assert calculate_deviation(20, 70) == calculate_deviation(70, 20)


def test_relative_deviation():
    assert calculate_relative_deviation(50, 75) == 50


def test_relative_deviation_zero_baseline():
    assert calculate_relative_deviation(0, 0) == 0
    assert calculate_relative_deviation(0, 20) == 100


def test_relative_deviation_is_bounded():
    assert calculate_relative_deviation(1, 100) == 100


def test_empty_dimensions_produce_zero():
    assert aggregate_deviation({}) == 0


def test_weighted_aggregation():
    dimensions = {
        "action_deviation": 100,
        "resource_deviation": 0,
    }

    score = aggregate_deviation(
        dimensions,
        {
            "action_deviation": 0.5,
            "resource_deviation": 0.5,
        },
    )

    assert score == 50


def test_missing_dimensions_are_renormalized():
    score = aggregate_deviation(
        {"action_deviation": 100},
        {
            "action_deviation": 0.25,
            "resource_deviation": 0.75,
        },
    )

    assert score == 100


def test_classify_none():
    assert classify_deviation(0) == "NONE"


def test_classify_low():
    assert classify_deviation(20) == "LOW"


def test_classify_moderate():
    assert classify_deviation(40) == "MODERATE"


def test_classify_high():
    assert classify_deviation(60) == "HIGH"


def test_classify_critical():
    assert classify_deviation(80) == "CRITICAL"


def test_classification_upper_bound():
    assert classify_deviation(100) == "CRITICAL"


def test_evidence_generation():
    evidence = identify_deviation_evidence(
        {
            "action_deviation": 70,
            "resource_deviation": 10,
            "context_deviation": 50,
        }
    )

    assert len(evidence) == 2
    assert any("Action pattern changed" in item for item in evidence)
    assert any("Execution context changed" in item for item in evidence)


def test_detector_requires_baseline():
    detector = BehavioralDeviationDetector()

    try:
        detector.detect(
            "agent-1",
            {"action_deviation": 20},
        )
        assert False
    except ValueError as exc:
        assert "baseline" in str(exc)


def test_set_and_get_baseline():
    detector = BehavioralDeviationDetector()

    detector.set_baseline(
        "agent-1",
        {
            "action_deviation": 20,
            "resource_deviation": 30,
        },
    )

    assert detector.get_baseline("agent-1") == {
        "action_deviation": 20,
        "resource_deviation": 30,
    }


def test_get_baseline_returns_copy():
    detector = BehavioralDeviationDetector()

    detector.set_baseline(
        "agent-1",
        {"action_deviation": 20},
    )

    baseline = detector.get_baseline("agent-1")
    baseline["action_deviation"] = 100

    assert detector.get_baseline("agent-1")["action_deviation"] == 20


def test_detector_no_deviation():
    detector = BehavioralDeviationDetector()

    detector.set_baseline(
        "agent-1",
        {
            "action_deviation": 20,
            "resource_deviation": 30,
            "context_deviation": 40,
        },
    )

    snapshot = detector.detect(
        "agent-1",
        {
            "action_deviation": 20,
            "resource_deviation": 30,
            "context_deviation": 40,
        },
    )

    assert snapshot.deviation_score == 0
    assert snapshot.deviation_level == "NONE"
    assert snapshot.evidence == []


def test_detector_detects_change():
    detector = BehavioralDeviationDetector()

    detector.set_baseline(
        "agent-1",
        {
            "action_deviation": 20,
            "resource_deviation": 20,
            "context_deviation": 20,
            "authorization_deviation": 20,
            "temporal_deviation": 20,
        },
    )

    snapshot = detector.detect(
        "agent-1",
        {
            "action_deviation": 80,
            "resource_deviation": 20,
            "context_deviation": 20,
            "authorization_deviation": 20,
            "temporal_deviation": 20,
        },
    )

    assert snapshot.deviation_score == 15.0
    assert snapshot.deviation_level == "NONE"
    assert snapshot.evidence
    assert any(
        "Action pattern changed" in item
        for item in snapshot.evidence
    )


def test_detector_records_history():
    detector = BehavioralDeviationDetector()

    detector.set_baseline(
        "agent-1",
        {"action_deviation": 20},
    )

    detector.detect(
        "agent-1",
        {"action_deviation": 20},
    )

    detector.detect(
        "agent-1",
        {"action_deviation": 50},
    )

    history = detector.history("agent-1")

    assert len(history) == 2
    assert history[0].update_index == 1
    assert history[1].update_index == 2


def test_latest_snapshot():
    detector = BehavioralDeviationDetector()

    detector.set_baseline(
        "agent-1",
        {"action_deviation": 20},
    )

    detector.detect(
        "agent-1",
        {"action_deviation": 20},
    )

    latest = detector.latest("agent-1")

    assert latest is not None
    assert latest.update_index == 1


def test_latest_without_history():
    detector = BehavioralDeviationDetector()

    assert detector.latest("agent-1") is None


def test_multiple_agents_are_isolated():
    detector = BehavioralDeviationDetector()

    detector.set_baseline(
        "agent-a",
        {"action_deviation": 10},
    )

    detector.set_baseline(
        "agent-b",
        {"action_deviation": 90},
    )

    result_a = detector.detect(
        "agent-a",
        {"action_deviation": 20},
    )

    result_b = detector.detect(
        "agent-b",
        {"action_deviation": 80},
    )

    assert result_a.deviation_score == 10
    assert result_b.deviation_score == 10


def test_unknown_dimensions_are_ignored():
    detector = BehavioralDeviationDetector()

    detector.set_baseline(
        "agent-1",
        {"action_deviation": 20},
    )

    snapshot = detector.detect(
        "agent-1",
        {
            "action_deviation": 40,
            "unknown_dimension": 100,
        },
    )

    assert "unknown_dimension" not in snapshot.dimensions
    assert snapshot.deviation_score == 20


def test_reset_single_agent():
    detector = BehavioralDeviationDetector()

    detector.set_baseline(
        "agent-1",
        {"action_deviation": 20},
    )

    detector.detect(
        "agent-1",
        {"action_deviation": 30},
    )

    detector.reset("agent-1")

    assert detector.get_baseline("agent-1") is None
    assert detector.history("agent-1") == []


def test_reset_all_agents():
    detector = BehavioralDeviationDetector()

    detector.set_baseline(
        "agent-1",
        {"action_deviation": 20},
    )

    detector.set_baseline(
        "agent-2",
        {"action_deviation": 30},
    )

    detector.reset()

    assert detector.get_baseline("agent-1") is None
    assert detector.get_baseline("agent-2") is None


def test_snapshot_is_immutable():
    detector = BehavioralDeviationDetector()

    detector.set_baseline(
        "agent-1",
        {"action_deviation": 20},
    )

    snapshot = detector.detect(
        "agent-1",
        {"action_deviation": 40},
    )

    assert snapshot.agent_id == "agent-1"

    try:
        snapshot.deviation_score = 99
        assert False
    except AttributeError:
        pass


def test_score_is_bounded():
    detector = BehavioralDeviationDetector()

    detector.set_baseline(
        "agent-1",
        {
            "action_deviation": 0,
            "resource_deviation": 0,
            "context_deviation": 0,
        },
    )

    snapshot = detector.detect(
        "agent-1",
        {
            "action_deviation": 100,
            "resource_deviation": 100,
            "context_deviation": 100,
        },
    )

    assert 0 <= snapshot.deviation_score <= 100


def test_evidence_threshold_can_be_customized():
    detector = BehavioralDeviationDetector(
        evidence_threshold=70,
    )

    detector.set_baseline(
        "agent-1",
        {
            "action_deviation": 20,
            "resource_deviation": 20,
        },
    )

    snapshot = detector.detect(
        "agent-1",
        {
            "action_deviation": 60,
            "resource_deviation": 100,
        },
    )

    assert any(
        "Resource usage pattern changed" in item
        for item in snapshot.evidence
    )


def test_custom_weights():
    detector = BehavioralDeviationDetector(
        weights={
            "action_deviation": 1.0,
        }
    )

    detector.set_baseline(
        "agent-1",
        {"action_deviation": 10},
    )

    snapshot = detector.detect(
        "agent-1",
        {"action_deviation": 90},
    )

    assert snapshot.deviation_score == 80


def test_detector_does_not_make_security_decision():
    detector = BehavioralDeviationDetector()

    detector.set_baseline(
        "agent-1",
        {"action_deviation": 20},
    )

    snapshot = detector.detect(
        "agent-1",
        {"action_deviation": 100},
    )

    assert hasattr(snapshot, "deviation_score")
    assert hasattr(snapshot, "deviation_level")
    assert hasattr(snapshot, "evidence")

    assert not hasattr(snapshot, "decision")
    assert not hasattr(snapshot, "action")


def test_repeated_detection_increments_index():
    detector = BehavioralDeviationDetector()

    detector.set_baseline(
        "agent-1",
        {"action_deviation": 10},
    )

    first = detector.detect(
        "agent-1",
        {"action_deviation": 20},
    )

    second = detector.detect(
        "agent-1",
        {"action_deviation": 30},
    )

    third = detector.detect(
        "agent-1",
        {"action_deviation": 40},
    )

    assert first.update_index == 1
    assert second.update_index == 2
    assert third.update_index == 3


def test_deviation_evidence_is_explainable():
    detector = BehavioralDeviationDetector()

    detector.set_baseline(
        "agent-1",
        {
            "action_deviation": 10,
            "resource_deviation": 10,
            "context_deviation": 10,
        },
    )

    snapshot = detector.detect(
        "agent-1",
        {
            "action_deviation": 90,
            "resource_deviation": 90,
            "context_deviation": 10,
        },
    )

    assert snapshot.evidence
    assert all(
        "deviation=" in evidence
        for evidence in snapshot.evidence
    )