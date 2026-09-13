from __future__ import annotations

import os

import pytest

from app.platform.config import PlatformConfig
from app.platform.health import health_check, readiness_check


def test_health_check_returns_healthy():
    result = health_check()

    assert result["status"] == "healthy"
    assert result["service"] == "varynx-platform"
    assert "timestamp" in result


def test_platform_config_defaults():
    config = PlatformConfig()

    assert config.service_name == "varynx-platform"
    assert config.environment == "development"
    assert config.host == "0.0.0.0"
    assert config.port == 8000
    assert config.metrics_enabled is True


def test_platform_config_from_environment(monkeypatch):
    monkeypatch.setenv(
        "VARYNX_SERVICE_NAME",
        "test-service",
    )
    monkeypatch.setenv(
        "VARYNX_ENVIRONMENT",
        "test",
    )
    monkeypatch.setenv(
        "VARYNX_PORT",
        "9000",
    )
    monkeypatch.setenv(
        "VARYNX_METRICS_ENABLED",
        "false",
    )

    config = PlatformConfig.from_environment()

    assert config.service_name == "test-service"
    assert config.environment == "test"
    assert config.port == 9000
    assert config.metrics_enabled is False


def test_invalid_port_configuration(monkeypatch):
    monkeypatch.setenv(
        "VARYNX_PORT",
        "not-an-integer",
    )

    with pytest.raises(ValueError):
        PlatformConfig.from_environment()


def test_health_does_not_require_database():
    result = health_check()

    assert result["status"] == "healthy"


def test_readiness_has_structured_response():
    result = readiness_check()

    assert "status" in result
    assert "service" in result
    assert "environment" in result
    assert "database" in result
    assert "timestamp" in result


def test_readiness_database_status_is_structured():
    result = readiness_check()

    assert result["database"]["status"] in {
        "healthy",
        "unavailable",
    }