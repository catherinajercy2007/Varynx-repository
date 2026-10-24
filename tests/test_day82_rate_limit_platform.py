from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from api.gateway import create_app, gateway_metrics
from app.platform.rate_limit import (
    RateLimitConfig,
    RateLimitMonitor,
    get_rate_limit_config,
)


def test_rate_limit_config_defaults_are_disabled():
    config = RateLimitConfig()

    assert config.enabled is False
    assert config.max_requests == 60
    assert config.window_seconds == 60


def test_rate_limit_config_serializes():
    config = RateLimitConfig(
        enabled=True,
        max_requests=25,
        window_seconds=30,
    )

    assert config.to_dict() == {
        "enabled": True,
        "max_requests": 25,
        "window_seconds": 30,
    }


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_requests": 0},
        {"max_requests": -1},
        {"window_seconds": 0},
        {"window_seconds": -5},
        {"max_requests": True},
        {"window_seconds": False},
        {"enabled": 1},
    ],
)
def test_invalid_rate_limit_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):
        RateLimitConfig(**kwargs)


def test_rate_limit_config_reads_environment(monkeypatch):
    monkeypatch.setenv("VARYNX_RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("VARYNX_RATE_LIMIT_MAX_REQUESTS", "15")
    monkeypatch.setenv("VARYNX_RATE_LIMIT_WINDOW_SECONDS", "45")

    config = get_rate_limit_config()

    assert config.enabled is True
    assert config.max_requests == 15
    assert config.window_seconds == 45


def test_invalid_rate_limit_boolean_is_rejected(monkeypatch):
    monkeypatch.setenv("VARYNX_RATE_LIMIT_ENABLED", "sometimes")

    with pytest.raises(ValueError):
        get_rate_limit_config()


def test_invalid_rate_limit_integer_is_rejected(monkeypatch):
    monkeypatch.setenv("VARYNX_RATE_LIMIT_MAX_REQUESTS", "many")

    with pytest.raises(ValueError):
        get_rate_limit_config()


def test_monitor_records_allowed_and_limited_outcomes():
    monitor = RateLimitMonitor()

    monitor.record_request(allowed=True)
    monitor.record_request(allowed=True)
    monitor.record_request(allowed=False)

    result = monitor.snapshot(RateLimitConfig())

    assert result["requests_allowed"] == 2
    assert result["requests_limited"] == 1
    assert result["requests_observed"] == 3
    assert result["enforcement_integrated"] is False


def test_monitor_rejects_non_boolean_outcome():
    monitor = RateLimitMonitor()

    with pytest.raises(ValueError):
        monitor.record_request(allowed=1)


def test_monitor_is_thread_safe():
    monitor = RateLimitMonitor()
    count = 500

    def record(index: int) -> None:
        monitor.record_request(allowed=(index % 2 == 0))

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(record, range(count)))

    result = monitor.snapshot(RateLimitConfig())

    assert result["requests_allowed"] == 250
    assert result["requests_limited"] == 250
    assert result["requests_observed"] == count


def test_gateway_metrics_preserves_existing_keys():
    result = gateway_metrics()

    assert "requests_total" in result
    assert "requests_successful" in result
    assert "requests_failed" in result
    assert "average_latency_seconds" in result
    assert "rate_limit" in result


def test_metrics_endpoint_exposes_rate_limit_configuration():
    client = TestClient(create_app())

    response = client.get("/metrics")

    assert response.status_code == 200
    result = response.json()
    assert result["rate_limit"]["configuration"]["enabled"] is False
    assert result["rate_limit"]["enforcement_integrated"] is False
    assert "requests_allowed" in result["rate_limit"]
    assert "requests_limited" in result["rate_limit"]
