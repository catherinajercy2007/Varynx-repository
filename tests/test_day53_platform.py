"""
Tests for the Day 53 context-aware BCSE platform integration.
"""

from app.bcse_context import (
    ContextAwareConsequenceEstimate,
    ContextAwareConsequenceModel,
)
from app.platform.bcse_context import (
    BCSEContextPlatformAdapter,
)


def _build_estimate(
    scenario_id: str = "agent-1-cf-1",
    consequence_score: float = 60.0,
) -> ContextAwareConsequenceEstimate:
    model = ContextAwareConsequenceModel()

    return model.estimate(
        scenario_id=scenario_id,
        consequence_score=consequence_score,
        context={
            "resource_sensitivity": 80,
            "privilege_context": 60,
            "scope_context": 40,
            "environment_context": 30,
            "persistence_context": 50,
        },
    )


def test_record_estimate():
    adapter = BCSEContextPlatformAdapter()

    estimate = _build_estimate()

    result = adapter.record_estimate(
        "agent-1",
        estimate,
    )

    assert result["scenario_id"] == estimate.scenario_id
    assert (
        result["base_consequence_score"]
        == estimate.base_consequence_score
    )
    assert (
        result["adjusted_consequence_score"]
        == estimate.adjusted_consequence_score
    )

    assert adapter.history_count("agent-1") == 1


def test_latest_estimate():
    adapter = BCSEContextPlatformAdapter()

    first = _build_estimate(
        "agent-1-cf-1",
        50,
    )

    second = _build_estimate(
        "agent-1-cf-2",
        70,
    )

    adapter.record_estimate("agent-1", first)
    adapter.record_estimate("agent-1", second)

    latest = adapter.latest_estimate("agent-1")

    assert latest is not None
    assert latest["scenario_id"] == "agent-1-cf-2"
    assert latest["base_consequence_score"] == 70.0


def test_history_preserves_all_fields():
    adapter = BCSEContextPlatformAdapter()

    estimate = _build_estimate()

    adapter.record_estimate(
        "agent-1",
        estimate,
    )

    history = adapter.estimate_history("agent-1")

    assert len(history) == 1

    stored = history[0]

    assert stored["scenario_id"] == estimate.scenario_id
    assert (
        stored["base_consequence_score"]
        == estimate.base_consequence_score
    )
    assert stored["context_index"] == estimate.context_index
    assert stored["context_level"] == estimate.context_level
    assert stored["context_modifier"] == estimate.context_modifier
    assert (
        stored["adjusted_consequence_score"]
        == estimate.adjusted_consequence_score
    )
    assert (
        stored["adjusted_consequence_level"]
        == estimate.adjusted_consequence_level
    )
    assert stored["context"] == estimate.context
    assert stored["evidence"] == list(estimate.evidence)


def test_context_is_serialized_as_copy():
    adapter = BCSEContextPlatformAdapter()

    estimate = _build_estimate()

    result = adapter.record_estimate(
        "agent-1",
        estimate,
    )

    result["context"]["resource_sensitivity"] = 0

    fresh = adapter.latest_estimate("agent-1")

    assert fresh is not None
    assert fresh["context"]["resource_sensitivity"] == 80.0


def test_evidence_is_serialized_as_copy():
    adapter = BCSEContextPlatformAdapter()

    estimate = _build_estimate()

    result = adapter.record_estimate(
        "agent-1",
        estimate,
    )

    result["evidence"].append(
        "local mutation"
    )

    fresh = adapter.latest_estimate("agent-1")

    assert fresh is not None
    assert "local mutation" not in fresh["evidence"]


def test_agent_histories_are_isolated():
    adapter = BCSEContextPlatformAdapter()

    estimate_a = _build_estimate(
        "agent-a-cf-1",
        40,
    )

    estimate_b = _build_estimate(
        "agent-b-cf-1",
        80,
    )

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

    latest_a = adapter.latest_estimate("agent-a")
    latest_b = adapter.latest_estimate("agent-b")

    assert latest_a is not None
    assert latest_b is not None

    assert latest_a["scenario_id"] == "agent-a-cf-1"
    assert latest_b["scenario_id"] == "agent-b-cf-1"


def test_missing_agent_has_no_history():
    adapter = BCSEContextPlatformAdapter()

    assert adapter.latest_estimate("unknown-agent") is None
    assert adapter.estimate_history("unknown-agent") == []
    assert adapter.history_count("unknown-agent") == 0


def test_reset_single_agent():
    adapter = BCSEContextPlatformAdapter()

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
    adapter = BCSEContextPlatformAdapter()

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
    adapter = BCSEContextPlatformAdapter()
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
    adapter = BCSEContextPlatformAdapter()

    try:
        adapter.record_estimate(
            "agent-1",
            "not-an-estimate",
        )
    except TypeError as exc:
        assert "ContextAwareConsequenceEstimate" in str(exc)
    else:
        raise AssertionError(
            "Expected TypeError for invalid estimate"
        )


def test_platform_result_has_no_security_decision():
    adapter = BCSEContextPlatformAdapter()

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


def test_record_does_not_change_estimate():
    adapter = BCSEContextPlatformAdapter()

    estimate = _build_estimate()

    before = (
        estimate.scenario_id,
        estimate.base_consequence_score,
        estimate.context_index,
        estimate.adjusted_consequence_score,
        estimate.context,
        estimate.evidence,
    )

    adapter.record_estimate(
        "agent-1",
        estimate,
    )

    after = (
        estimate.scenario_id,
        estimate.base_consequence_score,
        estimate.context_index,
        estimate.adjusted_consequence_score,
        estimate.context,
        estimate.evidence,
    )

    assert after == before


def test_multiple_estimates_preserve_order():
    adapter = BCSEContextPlatformAdapter()

    first = _build_estimate(
        "agent-1-cf-1",
        40,
    )

    second = _build_estimate(
        "agent-1-cf-2",
        60,
    )

    third = _build_estimate(
        "agent-1-cf-3",
        80,
    )

    adapter.record_estimate("agent-1", first)
    adapter.record_estimate("agent-1", second)
    adapter.record_estimate("agent-1", third)

    history = adapter.estimate_history("agent-1")

    assert [
        item["scenario_id"]
        for item in history
    ] == [
        "agent-1-cf-1",
        "agent-1-cf-2",
        "agent-1-cf-3",
    ]