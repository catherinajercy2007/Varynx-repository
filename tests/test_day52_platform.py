"""
Tests for the Day 52 BCSE consequence platform integration.
"""

from app.bcse_consequence import (
    ConsequenceEstimate,
    SecurityConsequenceEstimator,
)
from app.platform.bcse_consequence import (
    BCSEConsequencePlatformAdapter,
)


def _build_estimate(
    scenario_id: str = "agent-1-cf-1",
) -> ConsequenceEstimate:
    estimator = SecurityConsequenceEstimator()

    return estimator.estimate(
        scenario_id,
        {
            "confidentiality": 80,
            "integrity": 60,
            "availability": 40,
            "scope": 50,
            "privilege": 70,
            "persistence": 20,
        },
        evidence=[
            "Resource sensitivity increased",
        ],
        assumptions=[
            "Hypothetical access is permitted",
        ],
    )


def test_record_estimate():
    adapter = BCSEConsequencePlatformAdapter()

    estimate = _build_estimate()

    result = adapter.record_estimate(
        "agent-1",
        estimate,
    )

    assert result["scenario_id"] == "agent-1-cf-1"
    assert result["consequence_score"] == estimate.consequence_score
    assert result["consequence_level"] == estimate.consequence_level
    assert result["confidence"] == estimate.confidence

    assert adapter.history_count("agent-1") == 1


def test_latest_estimate():
    adapter = BCSEConsequencePlatformAdapter()

    first = _build_estimate("agent-1-cf-1")
    second = _build_estimate("agent-1-cf-2")

    adapter.record_estimate("agent-1", first)
    adapter.record_estimate("agent-1", second)

    latest = adapter.latest_estimate("agent-1")

    assert latest is not None
    assert latest["scenario_id"] == "agent-1-cf-2"


def test_estimate_history_preserves_all_fields():
    adapter = BCSEConsequencePlatformAdapter()

    estimate = _build_estimate()

    adapter.record_estimate(
        "agent-1",
        estimate,
    )

    history = adapter.estimate_history("agent-1")

    assert len(history) == 1

    stored = history[0]

    assert stored["scenario_id"] == estimate.scenario_id
    assert stored["consequence_score"] == estimate.consequence_score
    assert stored["consequence_level"] == estimate.consequence_level
    assert stored["confidence"] == estimate.confidence
    assert stored["dimensions"] == estimate.dimensions
    assert stored["evidence"] == estimate.evidence
    assert stored["assumptions"] == estimate.assumptions


def test_dimensions_are_serialized_as_copy():
    adapter = BCSEConsequencePlatformAdapter()

    estimate = _build_estimate()

    result = adapter.record_estimate(
        "agent-1",
        estimate,
    )

    result["dimensions"]["confidentiality"] = 0

    fresh = adapter.latest_estimate("agent-1")

    assert fresh is not None
    assert fresh["dimensions"]["confidentiality"] == 80.0


def test_evidence_and_assumptions_are_preserved():
    adapter = BCSEConsequencePlatformAdapter()

    estimate = _build_estimate()

    result = adapter.record_estimate(
        "agent-1",
        estimate,
    )

    assert result["evidence"] == [
        "Resource sensitivity increased",
        "Potential confidentiality impact (magnitude=80.00)",
        "Potential integrity impact (magnitude=60.00)",
        "Potential availability impact (magnitude=40.00)",
        "Potential scope expansion (magnitude=50.00)",
        "Potential privilege impact (magnitude=70.00)",
    ]

    assert result["assumptions"] == [
        "Hypothetical access is permitted",
    ]


def test_agent_histories_are_isolated():
    adapter = BCSEConsequencePlatformAdapter()

    estimate_a = _build_estimate("agent-a-cf-1")
    estimate_b = _build_estimate("agent-b-cf-1")

    adapter.record_estimate(
        "agent-a",
        estimate_a,
    )

    adapter.record_estimate(
        "agent-b",
        estimate_b,
    )

    assert adapter.history_count("agent-a") == 1
    assert adapter.history_count("agent-b") == 1

    assert (
        adapter.latest_estimate("agent-a")["scenario_id"]
        == "agent-a-cf-1"
    )

    assert (
        adapter.latest_estimate("agent-b")["scenario_id"]
        == "agent-b-cf-1"
    )


def test_missing_agent_has_no_history():
    adapter = BCSEConsequencePlatformAdapter()

    assert adapter.latest_estimate("unknown-agent") is None
    assert adapter.estimate_history("unknown-agent") == []
    assert adapter.history_count("unknown-agent") == 0


def test_reset_single_agent():
    adapter = BCSEConsequencePlatformAdapter()

    adapter.record_estimate(
        "agent-a",
        _build_estimate("agent-a-cf-1"),
    )

    adapter.record_estimate(
        "agent-b",
        _build_estimate("agent-b-cf-1"),
    )

    adapter.reset_estimates("agent-a")

    assert adapter.history_count("agent-a") == 0
    assert adapter.history_count("agent-b") == 1


def test_reset_all_agents():
    adapter = BCSEConsequencePlatformAdapter()

    adapter.record_estimate(
        "agent-a",
        _build_estimate("agent-a-cf-1"),
    )

    adapter.record_estimate(
        "agent-b",
        _build_estimate("agent-b-cf-1"),
    )

    adapter.reset_estimates()

    assert adapter.history_count("agent-a") == 0
    assert adapter.history_count("agent-b") == 0


def test_invalid_agent_id_is_rejected():
    adapter = BCSEConsequencePlatformAdapter()
    estimate = _build_estimate()

    try:
        adapter.record_estimate(
            "",
            estimate,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError for empty agent_id"
        )


def test_invalid_estimate_is_rejected():
    adapter = BCSEConsequencePlatformAdapter()

    try:
        adapter.record_estimate(
            "agent-1",
            "not-an-estimate",
        )
    except TypeError as exc:
        assert "ConsequenceEstimate" in str(exc)
    else:
        raise AssertionError(
            "Expected TypeError for invalid estimate"
        )


def test_result_is_not_security_decision():
    adapter = BCSEConsequencePlatformAdapter()

    result = adapter.record_estimate(
        "agent-1",
        _build_estimate(),
    )

    assert "decision" not in result
    assert "action" not in result
    assert "response" not in result
    assert "authorized" not in result
    assert "blocked" not in result
    assert "risk_score" not in result


def test_history_returns_fresh_serialized_data():
    adapter = BCSEConsequencePlatformAdapter()

    adapter.record_estimate(
        "agent-1",
        _build_estimate(),
    )

    history = adapter.estimate_history("agent-1")

    history[0]["evidence"].append(
        "local mutation"
    )
    history[0]["assumptions"].append(
        "local assumption"
    )

    fresh = adapter.latest_estimate("agent-1")

    assert fresh is not None

    assert "local mutation" not in fresh["evidence"]
    assert "local assumption" not in fresh["assumptions"]