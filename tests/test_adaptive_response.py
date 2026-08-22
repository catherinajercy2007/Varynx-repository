from app.adaptive_response import (
    ResponseAction,
    calculate_adaptive_response,
    calculate_adaptive_risk_score,
    determine_response_action,
    evaluate_events,
    generate_response_reasons,
    recommend_controls,
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

    result = calculate_adaptive_response(evidence)

    assert result["action"] == ResponseAction.ALLOW.value
    assert result["severity"] == "LOW"


def test_moderate_risk_enables_monitoring():
    evidence = {
        "risk_score": 75,
        "anomaly_score": 45,
    }

    result = calculate_adaptive_response(evidence)

    assert result["action"] in {
        ResponseAction.ALLOW_WITH_MONITORING.value,
        ResponseAction.STEP_UP_VERIFICATION.value,
    }


def test_high_anomaly_requires_step_up():
    evidence = {
        "risk_score": 40,
        "anomaly_score": 85,
    }

    result = calculate_adaptive_response(evidence)

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

    results = evaluate_events(events)

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

    summary = summarize_responses(responses)

    assert summary["total_events"] == 3
    assert summary["blocked_events"] == 1
    assert summary["escalated_events"] == 2
    assert summary["response_counts"]["ALLOW"] == 1


# ---------------------------------------------------------------------------
# DAY 31 — SCORE BOUNDARY TESTS
# ---------------------------------------------------------------------------


def test_score_below_monitoring_threshold_allows():
    action = determine_response_action(
        29.9999,
        {},
    )

    assert action == ResponseAction.ALLOW


def test_score_at_monitoring_threshold_enables_monitoring():
    action = determine_response_action(
        30,
        {},
    )

    assert action == ResponseAction.ALLOW_WITH_MONITORING


def test_score_below_step_up_threshold_monitors():
    action = determine_response_action(
        54.9999,
        {},
    )

    assert action == ResponseAction.ALLOW_WITH_MONITORING


def test_score_at_step_up_threshold_requires_verification():
    action = determine_response_action(
        55,
        {},
    )

    assert action == ResponseAction.STEP_UP_VERIFICATION


def test_score_below_reduce_scope_threshold_requires_step_up():
    action = determine_response_action(
        69.9999,
        {},
    )

    assert action == ResponseAction.STEP_UP_VERIFICATION


def test_score_at_reduce_scope_threshold_reduces_scope():
    action = determine_response_action(
        70,
        {},
    )

    assert action == ResponseAction.REDUCE_SCOPE


def test_score_below_human_review_threshold_reduces_scope():
    action = determine_response_action(
        79.9999,
        {},
    )

    assert action == ResponseAction.REDUCE_SCOPE


def test_score_at_human_review_threshold_requires_human_review():
    action = determine_response_action(
        80,
        {},
    )

    assert action == ResponseAction.HUMAN_REVIEW


def test_score_below_block_threshold_requires_human_review():
    action = determine_response_action(
        89.9999,
        {},
    )

    assert action == ResponseAction.HUMAN_REVIEW


def test_score_at_block_threshold_blocks():
    action = determine_response_action(
        90,
        {},
    )

    assert action == ResponseAction.BLOCK


# ---------------------------------------------------------------------------
# DAY 31 — DIRECT EVIDENCE ESCALATION TESTS
# ---------------------------------------------------------------------------


def test_critical_primary_risk_escalates_even_when_weighted_score_is_lower():
    evidence = {
        "risk_score": 95,
    }

    result = calculate_adaptive_response(evidence)

    assert result["action"] == ResponseAction.HUMAN_REVIEW.value


def test_high_anomaly_escalates_even_when_weighted_score_is_lower():
    evidence = {
        "anomaly_score": 80,
    }

    result = calculate_adaptive_response(evidence)

    assert result["action"] == ResponseAction.STEP_UP_VERIFICATION.value


def test_high_repeated_denial_escalates():
    evidence = {
        "repeated_denial_score": 80,
    }

    result = calculate_adaptive_response(evidence)

    assert result["action"] == ResponseAction.STEP_UP_VERIFICATION.value


def test_cross_context_and_denial_combination_reduces_scope():
    evidence = {
        "cross_context_score": 85,
        "repeated_denial_score": 60,
    }

    result = calculate_adaptive_response(evidence)

    assert result["action"] == ResponseAction.REDUCE_SCOPE.value


def test_extreme_anomaly_and_cross_context_requires_human_review():
    evidence = {
        "anomaly_score": 90,
        "cross_context_score": 75,
    }

    result = calculate_adaptive_response(evidence)

    assert result["action"] == ResponseAction.HUMAN_REVIEW.value


# ---------------------------------------------------------------------------
# DAY 31 — INPUT NORMALIZATION TESTS
# ---------------------------------------------------------------------------


def test_zero_to_one_scores_are_normalized():
    score = calculate_adaptive_risk_score(
        {
            "risk_score": 1.0,
        }
    )

    assert score == 30.0


def test_scores_above_100_are_clamped():
    score = calculate_adaptive_risk_score(
        {
            "risk_score": 150,
        }
    )

    assert score == 30.0


def test_negative_scores_are_clamped():
    score = calculate_adaptive_risk_score(
        {
            "risk_score": -50,
        }
    )

    assert score == 0.0


def test_invalid_numeric_values_do_not_crash():
    score = calculate_adaptive_risk_score(
        {
            "risk_score": "invalid",
            "anomaly_score": None,
        }
    )

    assert score == 0.0


def test_nan_score_is_safe():
    score = calculate_adaptive_risk_score(
        {
            "risk_score": float("nan"),
        }
    )

    assert score == 0.0


# ---------------------------------------------------------------------------
# DAY 31 — MISSING / EMPTY EVIDENCE
# ---------------------------------------------------------------------------


def test_empty_evidence_defaults_to_allow():
    result = calculate_adaptive_response({})

    assert result["action"] == ResponseAction.ALLOW.value
    assert result["severity"] == "LOW"


def test_partial_evidence_is_deterministic():
    evidence = {
        "risk_score": 40,
    }

    first = calculate_adaptive_response(evidence)
    second = calculate_adaptive_response(evidence)

    assert first == second


# ---------------------------------------------------------------------------
# DAY 31 — EXPLAINABILITY
# ---------------------------------------------------------------------------


def test_response_contains_explanation_fields():
    result = calculate_adaptive_response(
        {
            "risk_score": 75,
            "anomaly_score": 45,
        }
    )

    assert "action" in result
    assert "severity" in result
    assert "score" in result
    assert "reasons" in result
    assert "recommended_controls" in result

    assert isinstance(result["reasons"], list)
    assert isinstance(result["recommended_controls"], list)
    assert len(result["reasons"]) >= 1
    assert len(result["recommended_controls"]) >= 1


def test_high_risk_generates_specific_reason():
    reasons = generate_response_reasons(
        {
            "risk_score": 85,
        }
    )

    assert any(
        "risk score" in reason.lower()
        for reason in reasons
    )


def test_high_anomaly_generates_specific_reason():
    reasons = generate_response_reasons(
        {
            "anomaly_score": 85,
        }
    )

    assert any(
        "anomaly" in reason.lower()
        for reason in reasons
    )


# ---------------------------------------------------------------------------
# DAY 31 — RESPONSE CONTROL CONTRACT
# ---------------------------------------------------------------------------


def test_every_response_action_has_recommended_controls():
    for action in ResponseAction:
        controls = recommend_controls(action)

        assert isinstance(controls, list)
        assert len(controls) > 0


# ---------------------------------------------------------------------------
# DAY 31 — DETERMINISM
# ---------------------------------------------------------------------------


def test_adaptive_response_is_deterministic():
    evidence = {
        "risk_score": 65,
        "anomaly_score": 70,
        "repeated_denial_score": 40,
        "cross_context_score": 55,
        "multi_resolution_score": 30,
    }

    results = [
        calculate_adaptive_response(evidence)
        for _ in range(10)
    ]

    assert all(
        result == results[0]
        for result in results
    )


# ---------------------------------------------------------------------------
# DAY 31 — FULL EVIDENCE INTEGRATION
# ---------------------------------------------------------------------------


def test_all_evidence_dimensions_contribute_to_score():
    evidence = {
        "risk_score": 50,
        "anomaly_score": 50,
        "repeated_denial_score": 50,
        "cross_context_score": 50,
        "multi_resolution_score": 50,
        "context_entropy_score": 50,
        "capability_resource_spread": 50,
    }

    score = calculate_adaptive_risk_score(evidence)

    assert score == 50.0


def test_no_evidence_does_not_create_artificial_risk():
    score = calculate_adaptive_risk_score({})

    assert score == 0.0