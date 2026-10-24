from datetime import datetime, timedelta, timezone

import pytest

from app.platform import CapabilityLeasePlatformAdapter
from app.platform.capability_scope_integration import CapabilityScopeIntegration


def make_fixture():
    state = {"now": datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)}
    leases = CapabilityLeasePlatformAdapter(clock=lambda: state["now"])
    leases.issue_lease(
        agent_id="agent-1",
        capability="read_report",
        scope=["reports/weekly.csv"],
        ttl_seconds=60,
        lease_id="lease-1",
    )
    integration = CapabilityScopeIntegration(leases)
    return state, leases, integration


_DEFAULT_AUTHORIZATION = object()


def evaluate(integration, authorization_result=_DEFAULT_AUTHORIZATION, **overrides):
    values = {
        "lease_id": "lease-1",
        "agent_id": "agent-1",
        "capability": "read_report",
        "resource": "reports/weekly.csv",
    }
    values.update(overrides)

    if authorization_result is _DEFAULT_AUTHORIZATION:
        authorization_result = {
            "decision": "ALLOW",
            "risk": 10,
            "reason": "Policy allowed",
        }

    return integration.evaluate(authorization_result, **values)


def test_day81_allows_when_base_authorization_and_lease_allow():
    _, _, integration = make_fixture()

    result = evaluate(integration)

    assert result["decision"] == "ALLOW"
    assert result["allowed"] is True
    assert result["reason_code"] == "AUTHORIZATION_AND_LEASE_VALID"
    assert result["authorization_decision"] == "ALLOW"
    assert result["lease_decision"] == "ALLOW"


def test_day81_existing_authorization_deny_cannot_be_overridden():
    _, _, integration = make_fixture()

    result = evaluate(
        integration,
        {"decision": "DENY", "reason": "Policy denied"},
    )

    assert result["decision"] == "DENY"
    assert result["reason_code"] == "BASE_AUTHORIZATION_DENIED"


@pytest.mark.parametrize(
    "authorization_result",
    [
        None,
        {},
        {"decision": "UNKNOWN"},
        {"decision": "ALLOW "},
    ],
)
def test_day81_missing_or_non_allow_base_decision_fails_closed(authorization_result):
    _, _, integration = make_fixture()

    result = evaluate(integration, authorization_result)

    assert result["decision"] == "DENY"
    expected_reason = (
        "AUTHORIZATION_RESULT_INVALID"
        if authorization_result is None
        else "BASE_AUTHORIZATION_DENIED"
    )
    assert result["reason_code"] == expected_reason


def test_day81_invalid_authorization_result_type_fails_closed():
    _, _, integration = make_fixture()

    result = integration.evaluate(
        ["ALLOW"],
        lease_id="lease-1",
        agent_id="agent-1",
        capability="read_report",
        resource="reports/weekly.csv",
    )

    assert result["decision"] == "DENY"
    assert result["reason_code"] == "AUTHORIZATION_RESULT_INVALID"


def test_day81_unknown_lease_is_denied():
    _, _, integration = make_fixture()

    result = evaluate(integration, lease_id="missing")

    assert result["decision"] == "DENY"
    assert result["reason_code"] == "LEASE_NOT_FOUND"


def test_day81_expired_lease_is_denied():
    state, _, integration = make_fixture()
    state["now"] += timedelta(seconds=60)

    result = evaluate(integration)

    assert result["decision"] == "DENY"
    assert result["reason_code"] == "LEASE_EXPIRED"


def test_day81_revoked_lease_is_denied():
    _, leases, integration = make_fixture()
    leases.revoke_lease("lease-1", "operator request")

    result = evaluate(integration)

    assert result["decision"] == "DENY"
    assert result["reason_code"] == "LEASE_REVOKED"


def test_day81_capability_mismatch_is_denied():
    _, _, integration = make_fixture()

    result = evaluate(integration, capability="delete_report")

    assert result["decision"] == "DENY"
    assert result["reason_code"] == "CAPABILITY_MISMATCH"


def test_day81_scope_mismatch_is_denied():
    _, _, integration = make_fixture()

    result = evaluate(integration, resource="reports/private.csv")

    assert result["decision"] == "DENY"
    assert result["reason_code"] == "SCOPE_MISMATCH"


def test_day81_agent_mismatch_is_denied():
    _, _, integration = make_fixture()

    result = evaluate(integration, agent_id="agent-2")

    assert result["decision"] == "DENY"
    assert result["reason_code"] == "AGENT_MISMATCH"


def test_day81_missing_adapter_is_rejected():
    with pytest.raises(TypeError):
        CapabilityScopeIntegration(None)


def test_day81_result_does_not_mutate_base_authorization():
    _, _, integration = make_fixture()
    base = {"decision": "ALLOW", "risk": 10, "reason": "Policy allowed"}

    evaluate(integration, base)

    assert base == {
        "decision": "ALLOW",
        "risk": 10,
        "reason": "Policy allowed",
    }
