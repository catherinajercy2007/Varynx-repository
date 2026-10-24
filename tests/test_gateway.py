from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient

from api.gateway import (
    create_app,
    gateway_health,
    gateway_info,
    gateway_metrics,
    gateway_readiness,
    gateway_reason_codes,
)


def test_gateway_health():
    result = gateway_health()

    assert result["status"] == "healthy"
    assert result["service"] == "varynx-platform"


def test_gateway_info_includes_all_endpoints():
    result = gateway_info()

    assert result["service"] == "varynx-platform"
    assert result["api_version"] == "1.0"
    assert result["status"] == "operational"

    assert result["endpoints"]["health"] == "/health"
    assert result["endpoints"]["readiness"] == "/ready"
    assert result["endpoints"]["metrics"] == "/metrics"
    assert result["endpoints"]["reason_codes"] == "/reason-codes"


def test_gateway_metrics():
    result = gateway_metrics()

    assert "requests_total" in result
    assert "requests_successful" in result
    assert "requests_failed" in result
    assert "average_latency_seconds" in result


def test_gateway_readiness():
    result = gateway_readiness()

    assert "status" in result
    assert result["service"] == "varynx-platform"


def test_fastapi_application_registers_all_routes():
    application = create_app()

    routes = {
        route.path
        for route in application.routes
    }

    assert "/" in routes
    assert "/health" in routes
    assert "/ready" in routes
    assert "/metrics" in routes
    assert "/reason-codes" in routes


def test_gateway_reason_codes_returns_existing_explanation():
    result = gateway_reason_codes(
        {
            "evidence": {
                "risk_score": 95,
                "anomaly_score": 85,
            },
            "agent_id": "agent-test",
            "task_id": "task-test",
            "event_id": "event-test",
            "context": {
                "resource": "reports/private.csv",
            },
            "evidence_refs": [
                "audit:event-test",
            ],
            "correlation_id": "correlation-test",
        }
    )

    assert result["decision"]["action"]
    assert "risk_score" in result["reason_codes"]
    assert "anomaly_score" in result["reason_codes"]

    assert result["agent_id"] == "agent-test"
    assert result["task_id"] == "task-test"
    assert result["event_id"] == "event-test"

    assert result["context"]["resource"] == "reports/private.csv"
    assert result["evidence_refs"] == ["audit:event-test"]
    assert result["correlation_id"] == "correlation-test"

    parsed_timestamp = datetime.fromisoformat(result["timestamp"])
    assert parsed_timestamp.tzinfo is not None


def test_gateway_reason_codes_prefers_correlation_header():
    result = gateway_reason_codes(
        {
            "evidence": {},
            "correlation_id": "body-correlation",
        },
        correlation_id_header="header-correlation",
    )

    assert result["correlation_id"] == "header-correlation"


def test_gateway_reason_codes_preserves_supplied_decision():
    supplied_response = {
        "action": "BLOCK",
        "severity": "CRITICAL",
        "score": 95.0,
        "reasons": [
            "Existing runtime reason",
        ],
        "recommended_controls": [
            "Reject requested action",
        ],
    }

    result = gateway_reason_codes(
        {
            "evidence": {
                "risk_score": 95,
            },
            "response": supplied_response,
        }
    )

    assert result["decision"]["action"] == "BLOCK"
    assert result["decision"]["severity"] == "CRITICAL"
    assert result["decision"]["score"] == 95.0

    assert result["reasons"] == ["Existing runtime reason"]
    assert result["recommended_controls"] == [
        "Reject requested action"
    ]


def test_reason_codes_http_endpoint_returns_context():
    client = TestClient(create_app())

    response = client.post(
        "/reason-codes",
        headers={
            "X-Correlation-ID": "http-correlation-123",
        },
        json={
            "evidence": {
                "risk_score": 95,
                "anomaly_score": 85,
            },
            "agent_id": "agent-http",
            "task_id": "task-http",
            "event_id": "event-http",
            "context": {
                "resource": "reports/private.csv",
            },
            "evidence_refs": [
                "audit:event-http",
            ],
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["correlation_id"] == "http-correlation-123"
    assert result["agent_id"] == "agent-http"
    assert result["task_id"] == "task-http"
    assert result["event_id"] == "event-http"

    assert result["context"]["resource"] == "reports/private.csv"
    assert result["evidence_refs"] == ["audit:event-http"]
    assert "risk_score" in result["reason_codes"]
    assert result["timestamp"]


def test_reason_codes_endpoint_rejects_invalid_evidence():
    client = TestClient(create_app())

    response = client.post(
        "/reason-codes",
        json={
            "evidence": [
                "invalid",
                "evidence",
            ],
        },
    )

    assert response.status_code == 422


def test_reason_codes_endpoint_rejects_invalid_context():
    client = TestClient(create_app())

    response = client.post(
        "/reason-codes",
        json={
            "evidence": {},
            "context": "not-an-object",
        },
    )

    assert response.status_code == 422