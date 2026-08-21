from app.adaptive_response import (
    ResponseAction,
    calculate_adaptive_response,
    calculate_adaptive_risk_score,
    determine_response_action,
    evaluate_events,
    summarize_responses,
)


def test_low_risk_allows():

    evidence = {
        "risk_score": 10,
        "anomaly_score": 5,
        "repeated_denial_score": 0,
        "cross_context_score": 5,
        "multi_resolution_score": 5,
    }

    result = calculate_adaptive_response(
        evidence
    )

    assert result["action"] == ResponseAction.ALLOW.value
    assert result["severity"] == "LOW"


def test_moderate_risk_enables_monitoring():

    evidence = {
        "risk_score": 75,
        "anomaly_score": 45,
    }

    result = calculate_adaptive_response(
        evidence
    )

    assert result["action"] in {
        ResponseAction.ALLOW_WITH_MONITORING.value,
        ResponseAction.STEP_UP_VERIFICATION.value,
    }


def test_high_anomaly_requires_step_up():

    evidence = {
        "risk_score": 40,
        "anomaly_score": 85,
    }

    result = calculate_adaptive_response(
        evidence
    )

    assert result["action"] in {
        ResponseAction.STEP_UP_VERIFICATION.value,
        ResponseAction.REDUCE_SCOPE.value,
        ResponseAction.HUMAN_REVIEW.value,
        ResponseAction.BLOCK.value,
    }


def test_critical_score_blocks():

    action = determine_response_action(
        95,
        {},
    )

    assert action == ResponseAction.BLOCK


def test_adaptive_score_is_bounded():

    score = calculate_adaptive_risk_score(
        {
            "risk_score": 100,
            "anomaly_score": 100,
            "repeated_denial_score": 100,
            "cross_context_score": 100,
            "multi_resolution_score": 100,
            "context_entropy_score": 100,
            "capability_resource_spread": 100,
        }
    )

    assert 0 <= score <= 100


def test_multiple_events_are_evaluated():

    events = [
        {
            "agent_id": "agent-1",
            "risk_score": 10,
        },
        {
            "agent_id": "agent-2",
            "risk_score": 95,
        },
    ]

    results = evaluate_events(
        events
    )

    assert len(results) == 2
    assert results[0]["agent_id"] == "agent-1"
    assert results[1]["agent_id"] == "agent-2"


def test_response_summary():

    responses = [
        {
            "action": "ALLOW",
        },
        {
            "action": "STEP_UP_VERIFICATION",
        },
        {
            "action": "BLOCK",
        },
    ]

    summary = summarize_responses(
        responses
    )

    assert summary["total_events"] == 3
    assert summary["blocked_events"] == 1
    assert summary["escalated_events"] == 2
    assert summary["response_counts"]["ALLOW"] == 1