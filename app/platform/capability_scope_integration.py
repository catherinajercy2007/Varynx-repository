"""Fail-closed integration of capability leases with authorization results."""

from __future__ import annotations

from typing import Any

from .capability_lease import CapabilityLeasePlatformAdapter


class CapabilityScopeIntegration:
    """Require both existing authorization and a valid capability lease.

    This adapter does not issue authorization decisions on behalf of the
    central authorization service and does not execute or enforce runtime
    actions. It combines an already-computed authorization result with a
    lease validation result.
    """

    def __init__(self, lease_adapter: CapabilityLeasePlatformAdapter) -> None:
        if not isinstance(lease_adapter, CapabilityLeasePlatformAdapter):
            raise TypeError("lease_adapter must be a CapabilityLeasePlatformAdapter")
        self._lease_adapter = lease_adapter

    def evaluate(
        self,
        authorization_result: dict[str, Any],
        *,
        lease_id: str,
        agent_id: str,
        capability: str,
        resource: str,
    ) -> dict[str, Any]:
        """Combine an existing authorization result and lease validation.

        Existing authorization must explicitly return ``ALLOW``. Missing,
        malformed, or non-ALLOW results are denied. A lease can never
        override an existing authorization denial.
        """
        if not isinstance(authorization_result, dict):
            return self._result(
                False,
                "AUTHORIZATION_RESULT_INVALID",
                "Existing authorization result is invalid",
            )

        decision = authorization_result.get("decision")
        if decision != "ALLOW":
            return self._result(
                False,
                "BASE_AUTHORIZATION_DENIED",
                "Existing authorization did not allow this request",
                authorization_decision=decision,
                authorization_reason=authorization_result.get("reason"),
            )

        try:
            lease_result = self._lease_adapter.validate_lease(
                lease_id=lease_id,
                agent_id=agent_id,
                capability=capability,
                resource=resource,
            )
        except (TypeError, ValueError) as exc:
            return self._result(
                False,
                "LEASE_REQUEST_INVALID",
                "Capability lease validation request is invalid",
                detail=str(exc),
                authorization_decision=decision,
            )

        if not lease_result.get("allowed") or lease_result.get("decision") != "ALLOW":
            return self._result(
                False,
                lease_result.get("reason_code", "LEASE_VALIDATION_FAILED"),
                lease_result.get("reason", "Capability lease validation failed"),
                authorization_decision=decision,
                lease_decision=lease_result.get("decision", "DENY"),
            )

        return self._result(
            True,
            "AUTHORIZATION_AND_LEASE_VALID",
            "Existing authorization and capability lease both allow this request",
            authorization_decision=decision,
            lease_decision="ALLOW",
            lease_id=lease_id,
            agent_id=agent_id,
            capability=capability,
            resource=resource,
        )

    @staticmethod
    def _result(
        allowed: bool,
        reason_code: str,
        reason: str,
        **details: Any,
    ) -> dict[str, Any]:
        return {
            "allowed": allowed,
            "decision": "ALLOW" if allowed else "DENY",
            "reason_code": reason_code,
            "reason": reason,
            **details,
        }


__all__ = ["CapabilityScopeIntegration"]
