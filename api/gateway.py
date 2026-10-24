"""
Varynx platform API gateway.

Day 79:
Expose structured security decision reason codes through the
existing adaptive explainability module.

This API does not implement a separate security enforcement engine.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.platform.health import health_check, readiness_check
from app.platform.metrics import get_metrics
from app.platform.rate_limit import (
    get_rate_limit_config,
    get_rate_limit_monitor,
)

def gateway_health() -> dict[str, Any]:
    """Return the platform health response."""
    return health_check()


def gateway_readiness() -> dict[str, Any]:
    """Return platform readiness information."""
    return readiness_check()


def gateway_metrics() -> dict[str, Any]:
    result = get_metrics().snapshot()
    result["rate_limit"] = get_rate_limit_monitor().snapshot(
        get_rate_limit_config()
    )
    return result


def gateway_info() -> dict[str, Any]:
    """Return gateway metadata and available endpoints."""
    return {
        "service": "varynx-platform",
        "api_version": "1.0",
        "status": "operational",
        "endpoints": {
            "info": "/",
            "health": "/health",
            "readiness": "/ready",
            "metrics": "/metrics",
            "reason_codes": "/reason-codes",
        },
    }


def gateway_reason_codes(
    payload: dict[str, Any],
    correlation_id_header: str | None = None,
) -> dict[str, Any]:
    """
    Produce an explanation using existing platform explainability.

    The endpoint describes supplied evidence and does not independently
    enforce actions or establish malicious intent.
    """
    from app.adaptive_explainability import explain_adaptive_decision

    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")

    evidence = payload.get("evidence", {})

    if not isinstance(evidence, dict):
        raise ValueError("'evidence' must be a JSON object.")

    response = payload.get("response")

    if response is not None and not isinstance(response, dict):
        raise ValueError("'response' must be a JSON object when supplied.")

    evidence_refs = payload.get("evidence_refs", [])

    if not isinstance(evidence_refs, list):
        raise ValueError("'evidence_refs' must be a JSON array.")

    context = payload.get("context", {})

    if not isinstance(context, dict):
        raise ValueError("'context' must be a JSON object.")

    explanation = explain_adaptive_decision(
        evidence,
        response,
    )

    triggered_signals = explanation.get("triggered_signals", [])

    reason_codes = [
        item["signal"]
        for item in triggered_signals
        if isinstance(item, dict) and item.get("signal")
    ]

    correlation_id = (
        correlation_id_header
        or payload.get("correlation_id")
        or payload.get("event_id")
    )

    result: dict[str, Any] = {
        "service": "varynx-platform",
        "decision": explanation.get("decision", {}),
        "reason_codes": reason_codes,
        "reason_details": triggered_signals,
        "evidence": explanation.get("evidence", {}),
        "reasons": explanation.get("reasons", []),
        "rationale": explanation.get("rationale", ""),
        "recommended_controls": explanation.get(
            "recommended_controls", []
        ),
        "evidence_refs": evidence_refs,
        "correlation_id": correlation_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    for field in ("agent_id", "task_id", "event_id"):
        if field in payload:
            result[field] = payload[field]

    if "context" in payload:
        result["context"] = context

    return result


def create_app():
    """Create the FastAPI application."""
    try:
        from fastapi import FastAPI, Header, HTTPException
        from fastapi.responses import JSONResponse
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
    def ready():
        result = gateway_readiness()

        if result["status"] != "ready":
            return JSONResponse(
                status_code=503,
                content=result,
            )

        return result

    @application.get("/metrics")
    def metrics() -> dict[str, Any]:
        return gateway_metrics()

    @application.post("/reason-codes")
    def reason_codes(
        payload: dict[str, Any],
        x_correlation_id: str | None = Header(default=None),
    ) -> dict[str, Any]:
        try:
            return gateway_reason_codes(
                payload,
                correlation_id_header=x_correlation_id,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail=str(exc),
            ) from exc

    return application


app = create_app()