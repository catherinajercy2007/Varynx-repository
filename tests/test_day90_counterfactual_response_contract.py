from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from api.gateway import create_app
from app.platform import CapabilityLeasePlatformAdapter


def make_adapter():
    now = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
    adapter = CapabilityLeasePlatformAdapter(clock=lambda: now)
    adapter.issue_lease(
        agent_id="agent-1",
        capability="read_report",
        scope=["reports/weekly.csv"],
        ttl_seconds=60,
        lease_id="lease-1",
    )
    return adapter


def make_payload(decision="ALLOW", resource="reports/weekly.csv"):
    return {
        "authorization_result": {
            "decision": decision,
            "reason": "Day 90 contract test",
        },
        "lease_id": "lease-1",
        "agent_id": "agent-1",
        "capability": "read_report",
        "resource": resource,
    }


def assert_response_contract(response, *, available, decision, allowed):
    assert response.status_code == 200
    body = response.json()

    assert isinstance(body["available"], bool)
    assert body["available"] is available
    assert body["decision"] == decision
    assert body["allowed"] is allowed
    assert isinstance(body["reason_code"], str)
    assert body["reason_code"]
    assert body["evaluation_type"] == "COUNTERFACTUAL"
    assert body["executed"] is False
    assert body["live_authorization"] is False

    correlation_id = body["correlation_id"]
    assert isinstance(correlation_id, str)
    assert correlation_id
    assert response.headers["X-Correlation-ID"] == correlation_id

    return body


def test_day90_unavailable_response_preserves_contract():
    client = TestClient(create_app())

    response = client.post(
        "/counterfactual-capability",
        json=make_payload(),
    )

    body = assert_response_contract(
        response,
        available=False,
        decision="UNAVAILABLE",
        allowed=False,
    )
    assert body["reason_code"] == "LEASE_REGISTRY_UNAVAILABLE"


@pytest.mark.parametrize(
    ("base_decision", "expected_allowed", "expected_reason"),
    [
        ("ALLOW", True, None),
        ("DENY", False, "BASE_AUTHORIZATION_DENIED"),
    ],
)
def test_day90_configured_registry_preserves_response_contract(
    base_decision, expected_allowed, expected_reason
):
    client = TestClient(create_app(lease_adapter=make_adapter()))

    response = client.post(
        "/counterfactual-capability",
        headers={"X-Correlation-ID": "day90.contract-001"},
        json=make_payload(decision=base_decision),
    )

    body = assert_response_contract(
        response,
        available=True,
        decision=base_decision,
        allowed=expected_allowed,
    )

    assert body["correlation_id"] == "day90.contract-001"
    if expected_reason is not None:
        assert body["reason_code"] == expected_reason


def test_day90_scope_mismatch_preserves_denial_contract():
    client = TestClient(create_app(lease_adapter=make_adapter()))

    response = client.post(
        "/counterfactual-capability",
        json=make_payload(resource="reports/private.csv"),
    )

    body = assert_response_contract(
        response,
        available=True,
        decision="DENY",
        allowed=False,
    )
    assert body["reason_code"] == "SCOPE_MISMATCH"
