from app.adversarial_evaluation import (
    build_evaluation_record,
    evaluate_adversarial_scenario,
)


def test_adversarial_scenario_evaluation_preserves_ground_truth():
    result = evaluate_adversarial_scenario(
        "ADV-003",
        {
            "risk_score": 95,
        },
    )

    assert result["ground_truth"] == "ADVERSARIAL"
    assert result["scenario"]["scenario_id"] == "ADV-003"


def test_adversarial_evaluation_contains_decision():
    result = evaluate_adversarial_scenario(
        "ADV-001",
        {
            "risk_score": 75,
            "anomaly_score": 70,
        },
    )

    assert "decision" in result
    assert "decision" in result["decision"]
    assert "evidence" in result["decision"]


def test_critical_scenario_can_trigger_escalation():
    result = evaluate_adversarial_scenario(
        "ADV-003",
        {
            "risk_score": 95,
        },
    )

    assert result["decision"]["decision"]["action"] == (
        "HUMAN_REVIEW"
    )


def test_evaluation_record_is_flat():
    record = build_evaluation_record(
        "ADV-004",
        {
            "risk_score": 80,
            "repeated_denial_score": 85,
        },
    )

    assert record["scenario_id"] == "ADV-004"
    assert record["ground_truth"] == "ADVERSARIAL"
    assert "adaptive_action" in record
    assert "adaptive_score" in record


def test_evaluation_is_deterministic():
    evidence = {
        "risk_score": 65,
        "anomaly_score": 70,
        "repeated_denial_score": 50,
    }

    first = build_evaluation_record(
        "ADV-004",
        evidence,
    )

    second = build_evaluation_record(
        "ADV-004",
        evidence,
    )

    assert first == second