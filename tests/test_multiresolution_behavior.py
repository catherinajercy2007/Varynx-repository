from app.multiresolution_behavior import (
    calculate_entropy,
    calculate_action_level_features,
    calculate_capability_features,
    calculate_resource_features,
    calculate_context_features,
    calculate_cross_context_features,
    calculate_multi_resolution_profile,
    calculate_behavioral_risk_index,
    build_agent_profiles,
)


def sample_events():
    return [
        {
            "agent_id": "agent-a",
            "action": "s3:GetObject",
            "resource": "public/sales.csv",
            "context": "sales-analysis",
            "risk_score": 20,
        },
        {
            "agent_id": "agent-a",
            "action": "s3:GetObject",
            "resource": "public/sales.csv",
            "context": "sales-analysis",
            "risk_score": 25,
        },
        {
            "agent_id": "agent-a",
            "action": "s3:DeleteObject",
            "resource": "private/customer.csv",
            "context": "customer-management",
            "risk_score": 90,
        },
        {
            "agent_id": "agent-a",
            "action": "iam:CreateUser",
            "resource": "public/users",
            "context": "identity-management",
            "risk_score": 85,
        },
    ]


def test_entropy_empty():

    assert calculate_entropy([]) == 0.0


def test_entropy_single_category():

    assert calculate_entropy(
        ["a", "a", "a"]
    ) == 0.0


def test_entropy_multiple_categories():

    result = calculate_entropy(
        ["a", "b", "a", "b"]
    )

    assert result > 0


def test_action_level_features():

    result = (
        calculate_action_level_features(
            sample_events()
        )
    )

    assert result["event_count"] == 4

    assert result["average_risk"] > 0

    assert result["maximum_risk"] == 90

    assert result["high_risk_ratio"] == 0.5


def test_capability_features():

    result = (
        calculate_capability_features(
            sample_events()
        )
    )

    assert result[
        "capability_count"
    ] == 3


def test_resource_features():

    result = (
        calculate_resource_features(
            sample_events()
        )
    )

    assert result[
        "resource_count"
    ] == 3


def test_context_features():

    result = (
        calculate_context_features(
            sample_events()
        )
    )

    assert result[
        "context_count"
    ] == 3


def test_cross_context_features():

    result = (
        calculate_cross_context_features(
            sample_events()
        )
    )

    assert result[
        "cross_context_activity"
    ] == 3

    assert result[
        "context_entropy"
    ] > 0


def test_multi_resolution_profile():

    result = (
        calculate_multi_resolution_profile(
            sample_events()
        )
    )

    assert result[
        "event_count"
    ] == 4

    assert (
        "action_level"
        in result
    )

    assert (
        "capability_level"
        in result
    )

    assert (
        "resource_level"
        in result
    )

    assert (
        "context_level"
        in result
    )

    assert (
        "cross_context"
        in result
    )


def test_behavioral_risk_index():

    profile = (
        calculate_multi_resolution_profile(
            sample_events()
        )
    )

    score = (
        calculate_behavioral_risk_index(
            profile
        )
    )

    assert 0 <= score <= 100


def test_agent_profiles():

    profiles = build_agent_profiles(
        sample_events()
    )

    assert len(profiles) == 1

    assert profiles[0][
        "agent_id"
    ] == "agent-a"

    assert (
        "behavioral_risk_index"
        in profiles[0]
    )


def test_multiple_agents():

    events = sample_events()

    events.append(
        {
            "agent_id": "agent-b",
            "action": "s3:GetObject",
            "resource": "public/data.csv",
            "context": "analysis",
            "risk_score": 10,
        }
    )

    profiles = build_agent_profiles(
        events
    )

    assert len(profiles) == 2