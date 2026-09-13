import pytest

from app.cross_context_correlation import (
    build_agent_profiles,
    build_cross_context_profile,
    build_research_summary,
    calculate_action_distribution,
    calculate_behavioral_diversity,
    calculate_capability_distribution,
    calculate_context_capability_matrix,
    calculate_context_correlations,
    calculate_context_distribution,
    calculate_context_resource_matrix,
    calculate_cross_context_entropy,
    calculate_cross_context_risk,
    calculate_entropy,
    calculate_resource_distribution,
    classify_cross_context_risk,
)


def sample_events():
    return [
        {
            "agent_id": "agent-1",
            "action": "read",
            "capability": "document.read",
            "resource": "document-A",
            "context": "context-A",
        },
        {
            "agent_id": "agent-1",
            "action": "read",
            "capability": "document.read",
            "resource": "document-B",
            "context": "context-A",
        },
        {
            "agent_id": "agent-1",
            "action": "api_call",
            "capability": "api.call",
            "resource": "service-A",
            "context": "context-B",
        },
        {
            "agent_id": "agent-1",
            "action": "api_call",
            "capability": "api.call",
            "resource": "service-B",
            "context": "context-B",
        },
        {
            "agent_id": "agent-1",
            "action": "execute",
            "capability": "command.execute",
            "resource": "system-A",
            "context": "context-C",
        },
    ]


def test_context_distribution():
    distribution = calculate_context_distribution(
        sample_events()
    )

    assert distribution == {
        "context-A": 2,
        "context-B": 2,
        "context-C": 1,
    }


def test_capability_distribution():
    distribution = calculate_capability_distribution(
        sample_events()
    )

    assert distribution["document.read"] == 2
    assert distribution["api.call"] == 2
    assert distribution["command.execute"] == 1


def test_resource_distribution():
    distribution = calculate_resource_distribution(
        sample_events()
    )

    assert len(distribution) == 5
    assert distribution["document-A"] == 1
    assert distribution["service-A"] == 1


def test_action_distribution():
    distribution = calculate_action_distribution(
        sample_events()
    )

    assert distribution["read"] == 2
    assert distribution["api_call"] == 2
    assert distribution["execute"] == 1


def test_entropy_empty_distribution():
    assert calculate_entropy({}) == 0.0


def test_entropy_single_category():
    assert calculate_entropy(
        {"context-A": 5}
    ) == pytest.approx(0.0)


def test_entropy_uniform_distribution():
    entropy = calculate_entropy(
        {
            "A": 1,
            "B": 1,
        }
    )

    assert entropy == pytest.approx(1.0)


def test_cross_context_entropy():
    entropy = calculate_cross_context_entropy(
        sample_events()
    )

    assert "context_entropy" in entropy
    assert "capability_entropy" in entropy
    assert "resource_entropy" in entropy

    assert entropy["context_entropy"] > 0
    assert entropy["capability_entropy"] > 0
    assert entropy["resource_entropy"] > 0


def test_context_capability_matrix():
    matrix = calculate_context_capability_matrix(
        sample_events()
    )

    assert matrix["context-A"][
        "document.read"
    ] == 2

    assert matrix["context-B"][
        "api.call"
    ] == 2


def test_context_resource_matrix():
    matrix = calculate_context_resource_matrix(
        sample_events()
    )

    assert matrix["context-A"][
        "document-A"
    ] == 1

    assert matrix["context-B"][
        "service-A"
    ] == 1


def test_context_correlations():
    events = [
        {
            "agent_id": "agent-1",
            "capability": "shared-capability",
            "resource": "shared-resource",
            "context": "context-A",
        },
        {
            "agent_id": "agent-1",
            "capability": "shared-capability",
            "resource": "shared-resource",
            "context": "context-B",
        },
    ]

    result = calculate_context_correlations(
        events
    )

    assert result["context_count"] == 2
    assert result["correlated_pairs"] == 1

    relationship = result[
        "relationships"
    ][0]

    assert relationship[
        "context_a"
    ] == "context-A"

    assert relationship[
        "context_b"
    ] == "context-B"

    assert relationship[
        "correlation_score"
    ] == pytest.approx(1.0)


def test_behavioral_diversity():
    diversity = calculate_behavioral_diversity(
        sample_events()
    )

    assert 0.0 <= diversity[
        "context_diversity"
    ] <= 1.0

    assert 0.0 <= diversity[
        "capability_diversity"
    ] <= 1.0

    assert 0.0 <= diversity[
        "resource_diversity"
    ] <= 1.0


def test_cross_context_risk_empty():
    assert calculate_cross_context_risk(
        []
    ) == 0.0


def test_cross_context_risk_range():
    score = calculate_cross_context_risk(
        sample_events()
    )

    assert 0.0 <= score <= 100.0


def test_single_context_has_no_context_diversity():
    events = [
        {
            "agent_id": "agent-1",
            "capability": "read",
            "resource": "file-A",
            "context": "context-A",
        },
        {
            "agent_id": "agent-1",
            "capability": "read",
            "resource": "file-B",
            "context": "context-A",
        },
    ]

    diversity = calculate_behavioral_diversity(
        events
    )

    assert diversity[
        "context_diversity"
    ] == pytest.approx(0.0)


def test_cross_context_behavior_has_multiple_contexts():
    profile = build_cross_context_profile(
        sample_events()
    )

    assert profile[
        "event_count"
    ] == 5

    assert len(
        profile[
            "context_distribution"
        ]
    ) == 3

    assert profile[
        "correlations"
    ]["context_count"] == 3


def test_agent_profiles():
    events = sample_events()

    events.append(
        {
            "agent_id": "agent-2",
            "action": "read",
            "capability": "document.read",
            "resource": "document-X",
            "context": "context-X",
        }
    )

    profiles = build_agent_profiles(
        events
    )

    assert "agent-1" in profiles
    assert "agent-2" in profiles

    assert profiles[
        "agent-1"
    ]["event_count"] == 5

    assert profiles[
        "agent-2"
    ]["event_count"] == 1


def test_risk_classification():
    assert classify_cross_context_risk(
        10
    ) == "LOW"

    assert classify_cross_context_risk(
        50
    ) == "ELEVATED"

    assert classify_cross_context_risk(
        90
    ) == "HIGH"


def test_research_summary():
    summary = build_research_summary(
        sample_events()
    )

    assert summary[
        "event_count"
    ] == 5

    assert summary[
        "context_count"
    ] == 3

    assert (
        0.0
        <= summary[
            "cross_context_risk"
        ]
        <= 100.0
    )

    assert summary[
        "risk_class"
    ] in {
        "LOW",
        "ELEVATED",
        "HIGH",
    }


def test_deterministic_results():
    events = sample_events()

    first = build_cross_context_profile(
        events
    )

    second = build_cross_context_profile(
        events
    )

    assert first == second


def test_malformed_events_do_not_crash():
    events = [
        {},
        None,
        {
            "agent_id": "agent-1",
        },
        {
            "context": "context-A",
        },
    ]

    profile = build_cross_context_profile(
        events
    )

    assert profile[
        "event_count"
    ] >= 0

    assert 0 <= profile[
        "cross_context_risk"
    ] <= 100