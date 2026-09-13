from app.adaptive_integration import (
    EVIDENCE_KEYS,
    build_adaptive_evidence,
    evaluate_adaptive_evidence,
    integrate_security_evidence,
)


def test_canonical_evidence_contains_all_expected_dimensions():
    evidence = build_adaptive_evidence(
        {
            "risk_score": 40,
            "anomaly_score": 20,
            "repeated_denial_score": 10,
            "cross_context_score": 15,
            "multi_resolution_score": 5,
            "context_entropy_score": 30,
            "capability_resource_spread": 25,
        }
    )

    assert set(evidence.keys()) == set(EVIDENCE_KEYS)


def test_existing_evidence_values_are_preserved():
    evidence = build_adaptive_evidence(
        {
            "risk_score": 40,
            "anomaly_score": 20,
            "repeated_denial_score": 10,
            "cross_context_score": 15,
            "multi_resolution_score": 5,
            "context_entropy_score": 30,
            "capability_resource_spread": 25,
        }
    )

    assert evidence["risk_score"] == 40
    assert evidence["anomaly_score"] == 20
    assert evidence["repeated_denial_score"] == 10
    assert evidence["cross_context_score"] == 15
    assert evidence["multi_resolution_score"] == 5
    assert evidence["context_entropy_score"] == 30
    assert evidence["capability_resource_spread"] == 25


def test_missing_evidence_defaults_to_zero():
    evidence = build_adaptive_evidence(
        {
            "risk_score": 50,
        }
    )

    assert evidence["risk_score"] == 50
    assert evidence["anomaly_score"] == 0
    assert evidence["repeated_denial_score"] == 0
    assert evidence["cross_context_score"] == 0
    assert evidence["multi_resolution_score"] == 0
    assert evidence["context_entropy_score"] == 0
    assert evidence["capability_resource_spread"] == 0


def test_none_values_use_defaults():
    evidence = build_adaptive_evidence(
        {
            "risk_score": None,
            "anomaly_score": None,
        }
    )

    assert evidence["risk_score"] == 0
    assert evidence["anomaly_score"] == 0


def test_aliases_are_supported():
    evidence = build_adaptive_evidence(
        {
            "behavioral_risk_index": 50,
            "behavioral_anomaly_score": 40,
            "denial_score": 30,
            "correlation_score": 20,
            "resolution_risk": 10,
            "context_entropy": 15,
            "behavioral_spread": 25,
        }
    )

    assert evidence["risk_score"] == 50
    assert evidence["anomaly_score"] == 40
    assert evidence["repeated_denial_score"] == 30
    assert evidence["cross_context_score"] == 20
    assert evidence["multi_resolution_score"] == 10
    assert evidence["context_entropy_score"] == 15
    assert evidence["capability_resource_spread"] == 25


def test_primary_keys_take_precedence_over_aliases():
    evidence = build_adaptive_evidence(
        {
            "risk_score": 70,
            "behavioral_risk_index": 20,
        }
    )

    assert evidence["risk_score"] == 70


def test_adaptive_evidence_is_passed_to_response_engine():
    result = evaluate_adaptive_evidence(
        {
            "risk_score": 75,
            "anomaly_score": 45,
        }
    )

    assert "evidence" in result
    assert "response" in result

    assert result["evidence"]["risk_score"] == 75
    assert result["evidence"]["anomaly_score"] == 45

    assert "action" in result["response"]
    assert "severity" in result["response"]
    assert "score" in result["response"]


def test_high_risk_evidence_escalates_response():
    result = evaluate_adaptive_evidence(
        {
            "risk_score": 95,
        }
    )

    assert result["response"]["action"] == "HUMAN_REVIEW"


def test_high_anomaly_evidence_escalates_response():
    result = evaluate_adaptive_evidence(
        {
            "anomaly_score": 80,
        }
    )

    assert result["response"]["action"] == "STEP_UP_VERIFICATION"


def test_combined_behavioral_evidence_reaches_adaptive_response():
    result = evaluate_adaptive_evidence(
        {
            "risk_score": 50,
            "anomaly_score": 50,
            "repeated_denial_score": 50,
            "cross_context_score": 50,
            "multi_resolution_score": 50,
            "context_entropy_score": 50,
            "capability_resource_spread": 50,
        }
    )

    assert result["response"]["score"] == 50.0
    assert result["response"]["action"] == "ALLOW_WITH_MONITORING"


def test_empty_evidence_is_safe():
    result = evaluate_adaptive_evidence({})

    assert result["evidence"]["risk_score"] == 0
    assert result["response"]["action"] == "ALLOW"


def test_integration_metadata_is_preserved():
    result = integrate_security_evidence(
        risk_score=40,
        anomaly_score=20,
        agent_id="agent-1",
        event_id="event-1",
    )

    assert result["metadata"]["agent_id"] == "agent-1"
    assert result["metadata"]["event_id"] == "event-1"


def test_integration_is_deterministic():
    kwargs = {
        "risk_score": 65,
        "anomaly_score": 70,
        "repeated_denial_score": 40,
        "cross_context_score": 55,
        "multi_resolution_score": 30,
    }

    first = integrate_security_evidence(**kwargs)
    second = integrate_security_evidence(**kwargs)

    assert first == second