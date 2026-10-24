from datetime import datetime, timezone

import pytest

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


def test_day86_hypothetical_allow_is_not_live_authorization():
    result = evaluate_counterfactual_capability(
        make_payload(), lease_adapter=make_adapter()
    )

    assert result["available"] is True
    assert result["decision"] == "ALLOW"
    assert result["allowed"] is True
    assert result["evaluation_type"] == "COUNTERFACTUAL"
    assert result["executed"] is False
    assert result["live_authorization"] is False


def test_day86_base_denial_cannot_be_overridden():
    payload = make_payload()
    payload["authorization_result"] = {
        "decision": "DENY",
        "reason": "Hypothetical policy denial",
    }

    result = evaluate_counterfactual_capability(
        payload, lease_adapter=make_adapter()
    )

    assert result["decision"] == "DENY"
    assert result["reason_code"] == "BASE_AUTHORIZATION_DENIED"
    assert result["executed"] is False


def test_day86_missing_registry_is_explicitly_unavailable():
    result = evaluate_counterfactual_capability(
        make_payload(), lease_adapter=None
    )

    assert result["available"] is False
    assert result["decision"] == "UNAVAILABLE"
    assert result["reason_code"] == "LEASE_REGISTRY_UNAVAILABLE"
    assert result["live_authorization"] is False


def test_day86_unknown_lease_is_denied():
    payload = make_payload()
    payload["lease_id"] = "missing-lease"

    result = evaluate_counterfactual_capability(
        payload, lease_adapter=make_adapter()
    )

    assert result["decision"] == "DENY"
    assert result["reason_code"] == "LEASE_NOT_FOUND"


@pytest.mark.parametrize(
    "field",
    ["lease_id", "agent_id", "capability", "resource"],
)
def test_day86_required_fields_are_validated(field):
    payload = make_payload()
    payload[field] = " "

    with pytest.raises(ValueError, match=field):
        evaluate_counterfactual_capability(
            payload, lease_adapter=make_adapter()
        )


def test_day86_authorization_result_must_be_an_object():
    payload = make_payload()
    payload["authorization_result"] = "ALLOW"

    with pytest.raises(ValueError, match="authorization_result"):
        evaluate_counterfactual_capability(
            payload, lease_adapter=make_adapter()
        )


def test_day86_payload_must_be_an_object():
    with pytest.raises(ValueError, match="payload"):
        evaluate_counterfactual_capability(
            ["not", "an", "object"],  # type: ignore[arg-type]
            lease_adapter=make_adapter(),
        )
