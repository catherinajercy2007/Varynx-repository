from __future__ import annotations

import ast
from pathlib import Path

from fastapi.testclient import TestClient

from api.gateway import create_app
from app.adaptive_explainability import (
    evaluate_explainable_decision,
    explain_adaptive_decision,
)


ROOT = Path(__file__).resolve().parents[1]


def test_day79_explainability_identifies_existing_signals():
    explanation = evaluate_explainable_decision(
        {
            "risk_score": 95,
            "anomaly_score": 85,
        }
    )

    reason_codes = {
        item["signal"]
        for item in explanation["triggered_signals"]
    }

    assert "risk_score" in reason_codes
    assert "anomaly_score" in reason_codes
    assert explanation["decision"]["action"]


def test_day79_supplied_decision_is_preserved():
    explanation = explain_adaptive_decision(
        {
            "risk_score": 95,
        },
        {
            "action": "BLOCK",
            "severity": "CRITICAL",
            "score": 95,
            "reasons": [
                "Existing runtime reason",
            ],
            "recommended_controls": [
                "Reject requested action",
            ],
        },
    )

    assert explanation["decision"]["action"] == "BLOCK"
    assert explanation["decision"]["severity"] == "CRITICAL"
    assert explanation["decision"]["score"] == 95
    assert explanation["reasons"] == [
        "Existing runtime reason"
    ]


def test_day79_api_returns_reason_codes_and_trace_context():
    client = TestClient(create_app())

    response = client.post(
        "/reason-codes",
        headers={
            "X-Correlation-ID": "day79-correlation",
        },
        json={
            "evidence": {
                "risk_score": 95,
                "anomaly_score": 85,
            },
            "agent_id": "agent-day79",
            "task_id": "task-day79",
            "event_id": "event-day79",
            "context": {
                "resource": "reports/private.csv",
            },
            "evidence_refs": [
                "audit:event-day79",
            ],
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["decision"]["action"]
    assert result["reason_codes"]
    assert result["evidence"]["risk_score"] == 95

    assert result["correlation_id"] == "day79-correlation"
    assert result["timestamp"]

    assert result["agent_id"] == "agent-day79"
    assert result["task_id"] == "task-day79"
    assert result["event_id"] == "event-day79"

    assert result["context"]["resource"] == "reports/private.csv"
    assert result["evidence_refs"] == ["audit:event-day79"]


def test_day79_api_rejects_invalid_evidence():
    client = TestClient(create_app())

    response = client.post(
        "/reason-codes",
        json={
            "evidence": "not-an-object",
        },
    )

    assert response.status_code == 422


def test_day79_dashboard_contains_navigation_and_view():
    dashboard_path = ROOT / "dashboard.py"
    source = dashboard_path.read_text(encoding="utf-8-sig")

    # This checks Python syntax without executing Streamlit.
    ast.parse(source)

    assert "Day 79 Security Decision Reason Codes" in source
    assert "day79_reason_code_result" in source