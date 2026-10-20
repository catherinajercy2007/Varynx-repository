
from datetime import datetime, timedelta, timezone

import pytest

from app.behavioral_runtime_rate_limit import (
    RateLimitEvent,
    RateLimitPolicy,
    STATUS_LIMIT_EXCEEDED,
    STATUS_LIMIT_REACHED,
    STATUS_WITHIN_LIMIT,
    RECOMMEND_CONTINUE_MONITORING,
    RECOMMEND_REVIEW_RATE_LIMIT,
    RECOMMEND_RESTRICT_RATE,
    assess_runtime_rate_limit,
)

NOW = datetime(2026, 10, 20, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def policy():
    return RateLimitPolicy(
        policy_id="agent-read-limit",
        max_requests=3,
        window_seconds=60,
    )


def event(
    seconds_ago=10,
    *,
    agent_id="agent-a",
    capability="storage.read",
    resource="public/report.csv",
    correlation_id=None,
):
    return RateLimitEvent(
        agent_id=agent_id,
        capability=capability,
        resource=resource,
        timestamp=NOW - timedelta(seconds=seconds_ago),
        correlation_id=correlation_id or f"event-{seconds_ago}",
    )


def assess(policy, events=(), **overrides):
    values = {
        "policy": policy,
        "agent_id": "agent-a",
        "capability": "storage.read",
        "resource": "public/report.csv",
        "correlation_id": "current-request",
        "now": NOW,
        "prior_events": events,
    }
    values.update(overrides)
    return assess_runtime_rate_limit(**values)


def test_request_below_limit(policy):
    result = assess(policy, [event(seconds_ago=10)])

    assert result.status == STATUS_WITHIN_LIMIT
    assert result.projected_requests_in_window == 2
    assert result.recommendation == RECOMMEND_CONTINUE_MONITORING


def test_request_reaches_limit(policy):
    result = assess(
        policy,
        [event(seconds_ago=10), event(seconds_ago=20)],
    )

    assert result.status == STATUS_LIMIT_REACHED
    assert result.projected_requests_in_window == 3
    assert result.recommendation == RECOMMEND_REVIEW_RATE_LIMIT


def test_request_exceeds_limit(policy):
    result = assess(
        policy,
        [
            event(seconds_ago=10),
            event(seconds_ago=20),
            event(seconds_ago=30),
        ],
    )

    assert result.status == STATUS_LIMIT_EXCEEDED
    assert result.projected_requests_in_window == 4
    assert result.recommendation == RECOMMEND_RESTRICT_RATE


def test_empty_history_counts_current_request(policy):
    result = assess(policy)

    assert result.prior_requests_in_window == 0
    assert result.projected_requests_in_window == 1


def test_old_event_outside_window_is_ignored(policy):
    result = assess(policy, [event(seconds_ago=120)])

    assert result.projected_requests_in_window == 1


def test_event_exactly_at_window_start_is_excluded(policy):
    result = assess(
        policy,
        [event(seconds_ago=60, correlation_id="boundary-event")],
    )

    assert result.projected_requests_in_window == 1


def test_future_event_is_ignored(policy):
    future = RateLimitEvent(
        agent_id="agent-a",
        capability="storage.read",
        resource="public/report.csv",
        timestamp=NOW + timedelta(seconds=1),
        correlation_id="future",
    )

    result = assess(policy, [future])

    assert result.projected_requests_in_window == 1


def test_different_agent_is_not_counted(policy):
    result = assess(policy, [event(agent_id="agent-b")])

    assert result.projected_requests_in_window == 1


def test_different_capability_is_not_counted(policy):
    result = assess(policy, [event(capability="storage.write")])

    assert result.projected_requests_in_window == 1


def test_different_resource_is_not_counted(policy):
    result = assess(policy, [event(resource="public/other.csv")])

    assert result.projected_requests_in_window == 1


def test_duplicate_correlation_id_is_counted_once(policy):
    first = event(seconds_ago=10, correlation_id="duplicate")
    second = event(seconds_ago=20, correlation_id="duplicate")

    result = assess(policy, [first, second])

    assert result.prior_requests_in_window == 1
    assert result.projected_requests_in_window == 2


def test_policy_rejects_zero_max_requests():
    with pytest.raises(ValueError):
        RateLimitPolicy("invalid", 0, 60)


def test_policy_rejects_zero_window():
    with pytest.raises(ValueError):
        RateLimitPolicy("invalid", 3, 0)


def test_boolean_limit_is_rejected():
    with pytest.raises(TypeError):
        RateLimitPolicy("invalid", True, 60)


def test_naive_now_is_rejected(policy):
    with pytest.raises(ValueError):
        assess(policy, now=datetime(2026, 10, 20, 10, 0))


def test_invalid_event_type_is_rejected(policy):
    with pytest.raises(TypeError):
        assess(policy, ["not-an-event"])


def test_empty_agent_id_is_rejected(policy):
    with pytest.raises(ValueError):
        assess(policy, agent_id=" ")


def test_deterministic_for_identical_inputs(policy):
    events = [event(seconds_ago=10), event(seconds_ago=20)]

    first = assess(policy, events).to_dict()
    second = assess(policy, events).to_dict()

    assert first == second


def test_assessment_does_not_execute_enforcement(policy):
    result = assess(
        policy,
        [event(seconds_ago=10), event(seconds_ago=20),
         event(seconds_ago=30)],
    ).to_dict()

    assert result["executes_throttling"] is False
    assert result["executes_enforcement"] is False
    assert result["is_authorization_decision"] is False


def test_result_has_reason_code(policy):
    result = assess(policy)

    assert result.reason_codes
    assert all(isinstance(code, str) for code in result.reason_codes)


def test_policy_is_immutable(policy):
    with pytest.raises((AttributeError, TypeError)):
        policy.max_requests = 100


def test_input_event_history_is_not_mutated(policy):
    events = [event(seconds_ago=10)]
    before = list(events)

    assess(policy, events)

    assert events == before
