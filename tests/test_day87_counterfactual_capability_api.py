from datetime import datetime, timezone

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


def make_payload():
    return {
        "authorization_result": {
            "decision": "ALLOW",
            "reason": "Hypothetical policy allow",
        },
        "lease_id": "lease-1",
        "agent_id": "agent-1",
        "capability": "read_report",
        "resource": "reports/weekly.csv",
    }


def test_day87_counterfactual_route_is_registered():
    routes = {route.path for route in create_app().routes}
    assert "/counterfactual-capability" in routes


def test_day87_missing_registry_returns_unavailable():
    client = TestClient(create_app())
    response = client.post(
        "/counterfactual-capability",
        headers={"X-Correlation-ID": "day87-test-1"},
        json=make_payload(),
    )

    assert response.status_code == 200
    result = response.json()
    assert result["available"] is False
    assert result["decision"] == "UNAVAILABLE"
    assert result["allowed"] is False
    assert result["reason_code"] == "LEASE_REGISTRY_UNAVAILABLE"
    assert result["evaluation_type"] == "COUNTERFACTUAL"
    assert result["executed"] is False
    assert result["live_authorization"] is False
    assert result["correlation_id"] == "day87-test-1"
    assert response.headers["X-Correlation-ID"] == "day87-test-1"


def test_day87_configured_registry_evaluates_hypothetical_allow():
    client = TestClient(create_app(lease_adapter=make_adapter()))
    response = client.post(
        "/counterfactual-capability",
        json=make_payload(),
    )

    assert response.status_code == 200
    result = response.json()
    assert result["available"] is True
    assert result["decision"] == "ALLOW"
    assert result["allowed"] is True
    assert result["evaluation_type"] == "COUNTERFACTUAL"
    assert result["executed"] is False
    assert result["live_authorization"] is False
    assert response.headers["X-Correlation-ID"]


def test_day87_base_denial_remains_denied():
    payload = make_payload()
    payload["authorization_result"] = {
        "decision": "DENY",
        "reason": "Hypothetical policy denial",
    }
    client = TestClient(create_app(lease_adapter=make_adapter()))

    response = client.post("/counterfactual-capability", json=payload)

    assert response.status_code == 200
    result = response.json()
    assert result["decision"] == "DENY"
    assert result["allowed"] is False
    assert result["reason_code"] == "BASE_AUTHORIZATION_DENIED"
    assert result["executed"] is False


def test_day87_invalid_payload_returns_422():
    client = TestClient(create_app(lease_adapter=make_adapter()))
    response = client.post(
        "/counterfactual-capability",
        json={
            "authorization_result": {"decision": "ALLOW"},
            "lease_id": "",
            "agent_id": "agent-1",
            "capability": "read_report",
            "resource": "reports/weekly.csv",
        },
    )

    assert response.status_code == 422


def test_day87_invalid_correlation_header_is_rejected():
    client = TestClient(create_app())
    response = client.post(
        "/counterfactual-capability",
        headers={"X-Correlation-ID": "invalid correlation id"},
        json=make_payload(),
    )

    assert response.status_code == 400
