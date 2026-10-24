import re
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from api.gateway import create_app
from app.platform import CapabilityLeasePlatformAdapter
from app.platform.counterfactual_capability_gate_service import (
    evaluate_counterfactual_capability,
)


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


@pytest.mark.parametrize(
    "authorization_result",
    [
        {},
        {"decision": "UNKNOWN"},
        {"decision": "ALLOW "},
        {"decision": None},
        {"decision": ["ALLOW"]},
    ],
)
def test_day88_malformed_or_unsupported_decisions_fail_closed(
    authorization_result,
):
    payload = make_payload()
    payload["authorization_result"] = authorization_result

    result = evaluate_counterfactual_capability(
        payload,
        lease_adapter=make_adapter(),
    )

    assert result["decision"] == "DENY"
    assert result["allowed"] is False
    assert result["reason_code"] == "BASE_AUTHORIZATION_DENIED"
    assert result["evaluation_type"] == "COUNTERFACTUAL"
    assert result["executed"] is False
    assert result["live_authorization"] is False


def test_day88_scope_mismatch_preserves_counterfactual_invariants():
    payload = make_payload()
    payload["resource"] = "reports/private.csv"

    result = evaluate_counterfactual_capability(
        payload,
        lease_adapter=make_adapter(),
    )

    assert result["decision"] == "DENY"
    assert result["allowed"] is False
    assert result["reason_code"] == "SCOPE_MISMATCH"
    assert result["evaluation_type"] == "COUNTERFACTUAL"
    assert result["executed"] is False
    assert result["live_authorization"] is False


def test_day88_whitespace_correlation_header_gets_generated_id():
    client = TestClient(create_app())
    response = client.post(
        "/counterfactual-capability",
        headers={"X-Correlation-ID": "   "},
        json=make_payload(),
    )

    assert response.status_code == 200
    body_id = response.json()["correlation_id"]
    header_id = response.headers["X-Correlation-ID"]

    assert re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", body_id)
    assert header_id == body_id
