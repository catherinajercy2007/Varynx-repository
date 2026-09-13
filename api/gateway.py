"""
Varynx platform API gateway.

The gateway exposes a small, stable HTTP boundary around the existing
security platform. Core security logic remains inside app.* modules.
"""

from __future__ import annotations

from typing import Any

from app.platform.health import health_check, readiness_check
from app.platform.metrics import get_metrics


def gateway_health() -> dict[str, Any]:
    """Return the platform liveness response."""
    return health_check()


def gateway_readiness() -> dict[str, Any]:
    """Return the platform readiness response."""
    return readiness_check()


def gateway_metrics() -> dict[str, Any]:
    """Return current platform metrics."""
    return get_metrics().snapshot()


def gateway_info() -> dict[str, Any]:
    """Return basic gateway metadata."""

    return {
        "service": "varynx-platform",
        "api_version": "1.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "readiness": "/ready",
            "metrics": "/metrics",
            "info": "/",
        },
    }


def create_app():
    """
    Create the HTTP application when FastAPI is available.

    FastAPI is imported lazily so importing the gateway module itself does
    not force the entire platform to depend on FastAPI.
    """

    try:
        from fastapi import FastAPI
    except ImportError as exc:
        raise RuntimeError(
            "FastAPI is required to create the HTTP gateway. "
            "Install requirements-platform.txt first."
        ) from exc

    application = FastAPI(
        title="Varynx Security Platform API",
        version="1.0.0",
        description=(
            "Platform gateway for the Varynx autonomous-agent "
            "security architecture."
        ),
    )

    @application.get("/")
    def info() -> dict[str, Any]:
        return gateway_info()

    @application.get("/health")
    def health() -> dict[str, Any]:
        return gateway_health()

    @application.get("/ready")
    def ready() -> dict[str, Any]:
        result = gateway_readiness()

        if result["status"] != "ready":
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=503,
                content=result,
            )

        return result

    @application.get("/metrics")
    def metrics() -> dict[str, Any]:
        return gateway_metrics()

    return application


app = create_app()