"""Day 86 service wrapper for counterfactual capability-gate evaluation."""
from __future__ import annotations

from typing import Any

from .capability_lease import CapabilityLeasePlatformAdapter
from .counterfactual_capability_gate import CounterfactualCapabilityGate


def evaluate_counterfactual_capability(
    payload: dict[str, Any],
    *,
    lease_adapter: CapabilityLeasePlatformAdapter | None,
) -> dict[str, Any]:
    """Evaluate a hypothetical scenario when a registry is explicitly supplied."""
    if lease_adapter is None:
        return {
            "evaluation_type": "COUNTERFACTUAL",
            "executed": False,
            "live_authorization": False,
            "available": False,
            "decision": "UNAVAILABLE",
            "allowed": False,
            "reason_code": "LEASE_REGISTRY_UNAVAILABLE",
            "reason": (
                "No shared capability lease registry is configured. "
                "No authorization conclusion was reached."
            ),
        }

    result = CounterfactualCapabilityGate(lease_adapter).evaluate(payload)
    return {"available": True, **result}


__all__ = ["evaluate_counterfactual_capability"]
