"""Day 86: counterfactual capability-gate evaluation.

Evaluates hypothetical inputs only. Does not execute actions, issue leases,
or replace central authorization.
"""
from __future__ import annotations

from typing import Any

from .capability_lease import CapabilityLeasePlatformAdapter
from .capability_scope_integration import CapabilityScopeIntegration


class CounterfactualCapabilityGate:
    """Evaluate hypothetical authorization and capability-lease inputs."""

    def __init__(self, lease_adapter: CapabilityLeasePlatformAdapter) -> None:
        if not isinstance(lease_adapter, CapabilityLeasePlatformAdapter):
            raise TypeError(
                "lease_adapter must be a CapabilityLeasePlatformAdapter"
            )
        self._integration = CapabilityScopeIntegration(lease_adapter)

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Evaluate a supplied scenario without executing any action."""
        if not isinstance(payload, dict):
            raise ValueError("payload must be a JSON object")

        authorization_result = payload.get("authorization_result")
        if not isinstance(authorization_result, dict):
            raise ValueError("authorization_result must be a JSON object")

        values: dict[str, str] = {}
        for field in ("lease_id", "agent_id", "capability", "resource"):
            value = payload.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty string")
            values[field] = value.strip()

        result = self._integration.evaluate(
            authorization_result,
            lease_id=values["lease_id"],
            agent_id=values["agent_id"],
            capability=values["capability"],
            resource=values["resource"],
        )
        return {
            **result,
            "evaluation_type": "COUNTERFACTUAL",
            "executed": False,
            "live_authorization": False,
        }


__all__ = ["CounterfactualCapabilityGate"]
