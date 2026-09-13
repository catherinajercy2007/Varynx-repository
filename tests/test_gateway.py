from __future__ import annotations

from api.gateway import (
    create_app,
    gateway_health,
    gateway_info,
    gateway_metrics,
    gateway_readiness,
)


def test_gateway_health():
    result = gateway_health()

    assert result["status"] == "healthy"
    assert result["service"] == "varynx-platform"


def test_gateway_info():
    result = gateway_info()

    assert result["service"] == "varynx-platform"
    assert result["api_version"] == "1.0"
    assert result["status"] == "operational"

    assert result["endpoints"]["health"] == "/health"
    assert result["endpoints"]["readiness"] == "/ready"
    assert result["endpoints"]["metrics"] == "/metrics"


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


def test_fastapi_application_can_be_created():
    application = create_app()

    assert application is not None

    routes = {
        route.path
        for route in application.routes
    }

    assert "/" in routes
    assert "/health" in routes
    assert "/ready" in routes
    assert "/metrics" in routes