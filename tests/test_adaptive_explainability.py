from app.adaptive_explainability import (
    SIGNAL_DEFINITIONS,
    build_audit_record,
    build_decision_rationale,
    build_evidence_summary,
    explain_adaptive_decision,
    evaluate_explainable_decision,
    identify_triggered_signals,
)


def test_evidence_summary_contains_all_security_dimensions():
    evidence = build_evidence_summary(
        {
            "risk_score": 50,
            "anomaly_score": 40,
            "repeated_denial_score": 30,
            "cross_context_score": 20,
            "multi_resolution_score": 10,
            "context_entropy_score": 5,
            "capability_resource_spread": 15,
        }
    )

    assert set(evidence.keys()) == set(
        SIGNAL_DEFINITIONS.keys()
    )


def test_evidence_summary_normalizes_scores():
    evidence = build_evidence_summary(
        {
            "risk_score": 0.5,
            "anomaly_score": 1.0,
        }
    )

    assert evidence["risk_score"] == 50.0
    assert evidence["anomaly_score"] == 100.0


def test_missing_evidence_is_zero():
    evidence = build_evidence_summary({})

    assert all(
        value == 0.0
        for value in evidence.values()
    )


def test_high_risk_is_identified_as_triggered_signal():
    triggered = identify_triggered_signals(
        {
            "risk_score": 80,
        }
    )

    signals = {
        item["signal"]
        for item in triggered
    }

    assert "risk_score" in signals


def test_low_risk_does_not_trigger_signal():
    triggered = identify_triggered_signals(
        {
            "risk_score": 20,
        }
    )

    assert triggered == []


def test_multiple_signals_are_identified():
    triggered = identify_triggered_signals(
        {
            "risk_score": 80,
            "anomaly_score": 75,
            "cross_context_score": 90,
        }
    )

    signals = {
        item["signal"]
        for item in triggered
    }

    assert signals == {
        "risk_score",
        "anomaly_score",
        "cross_context_score",
    }


def test_explanation_contains_decision():
    explanation = explain_adaptive_decision(
        {
            "risk_score": 75,
            "anomaly_score": 45,
        }
    )

    assert "decision" in explanation
    assert explanation["decision"]["action"] == (
        "ALLOW_WITH_MONITORING"
    )


def test_explanation_contains_evidence():
    explanation = explain_adaptive_decision(
        {
            "risk_score": 75,
            "anomaly_score": 45,
        }
    )

    assert "evidence" in explanation
    assert explanation["evidence"]["risk_score"] == 75.0
    assert explanation["evidence"]["anomaly_score"] == 45.0


def test_explanation_contains_rationale():
    explanation = explain_adaptive_decision(
        {
            "risk_score": 75,
            "anomaly_score": 45,
        }
    )

    assert isinstance(
        explanation["rationale"],
        str,
    )
    assert explanation["rationale"]


def test_explanation_contains_recommended_controls():
    explanation = explain_adaptive_decision(
        {
            "risk_score": 75,
            "anomaly_score": 45,
        }
    )

    assert isinstance(
        explanation["recommended_controls"],
        list,
    )
    assert explanation["recommended_controls"]


def test_high_risk_explanation_contains_risk_signal():
    explanation = evaluate_explainable_decision(
        {
            "risk_score": 95,
        }
    )

    assert explanation["decision"]["action"] == (
        "HUMAN_REVIEW"
    )

    signals = {
        item["signal"]
        for item in explanation["triggered_signals"]
    }

    assert "risk_score" in signals


def test_high_anomaly_explanation_contains_anomaly_signal():
    explanation = evaluate_explainable_decision(
        {
            "anomaly_score": 85,
        }
    )

    assert explanation["decision"]["action"] == (
        "STEP_UP_VERIFICATION"
    )

    signals = {
        item["signal"]
        for item in explanation["triggered_signals"]
    }

    assert "anomaly_score" in signals


def test_cross_context_explanation_does_not_claim_intent():
    explanation = evaluate_explainable_decision(
        {
            "cross_context_score": 80,
        }
    )

    rationale = explanation["rationale"].lower()

    assert "malicious intent" not in rationale
    assert "proves malicious" not in rationale


def test_decision_rationale_contains_score():
    rationale = build_decision_rationale(
        "ALLOW_WITH_MONITORING",
        {
            "risk_score": 75,
            "anomaly_score": 45,
        },
        {
            "score": 31.5,
            "severity": "MODERATE",
        },
    )

    assert "31.5" in rationale
    assert "MODERATE" in rationale


def test_supplied_response_can_be_explained_without_recalculation():
    response = {
        "action": "BLOCK",
        "severity": "CRITICAL",
        "score": 95.0,
        "reasons": [
            "Critical security signal."
        ],
        "recommended_controls": [
            "Reject requested action."
        ],
    }

    explanation = explain_adaptive_decision(
        {
            "risk_score": 100,
        },
        response,
    )

    assert explanation["decision"]["action"] == "BLOCK"
    assert explanation["decision"]["score"] == 95.0


def test_audit_record_contains_decision_and_evidence():
    explanation = evaluate_explainable_decision(
        {
            "risk_score": 75,
            "anomaly_score": 45,
        }
    )

    record = build_audit_record(
        {
            "risk_score": 75,
            "anomaly_score": 45,
        },
        explanation,
        agent_id="agent-1",
        event_id="event-1",
    )

    assert record["agent_id"] == "agent-1"
    assert record["event_id"] == "event-1"
    assert record["action"] == "ALLOW_WITH_MONITORING"
    assert record["severity"] == "MODERATE"
    assert record["adaptive_score"] == 31.5
    assert "evidence" in record
    assert "rationale" in record


def test_explanation_is_deterministic():
    evidence = {
        "risk_score": 65,
        "anomaly_score": 70,
        "repeated_denial_score": 40,
        "cross_context_score": 55,
    }

    first = evaluate_explainable_decision(evidence)
    second = evaluate_explainable_decision(evidence)

    assert first == second


def test_empty_evidence_produces_safe_explanation():
    explanation = evaluate_explainable_decision({})

    assert explanation["decision"]["action"] == "ALLOW"
    assert explanation["decision"]["severity"] == "LOW"
    assert explanation["evidence"]["risk_score"] == 0.0
    assert explanation["rationale"]