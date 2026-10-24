"""Platform-level capability leases for time-bounded, scoped grants."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable


def _require_text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _aware_utc(value: datetime, field: str = "datetime") -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must include timezone information")
    return value.astimezone(timezone.utc)


@dataclass
class CapabilityLease:
    """A scoped capability grant with a fixed expiration time."""

    lease_id: str
    agent_id: str
    capability: str
    scope: tuple[str, ...]
    issued_at: datetime
    expires_at: datetime
    status: str = "active"
    revoked_at: datetime | None = None
    revocation_reason: str = ""

    def status_at(self, now: datetime) -> str:
        """Return the effective status at the supplied aware time."""
        if self.status == "revoked":
            return "revoked"
        if _aware_utc(now) >= self.expires_at:
            return "expired"
        return "active"

    def to_dict(self, now: datetime | None = None) -> dict:
        """Return a JSON-friendly representation of this lease."""
        current = now or datetime.now(timezone.utc)
        return {
            "lease_id": self.lease_id,
            "agent_id": self.agent_id,
            "capability": self.capability,
            "scope": list(self.scope),
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "status": self.status_at(current),
            "revoked_at": (
                self.revoked_at.isoformat() if self.revoked_at else None
            ),
            "revocation_reason": self.revocation_reason,
        }


class CapabilityLeasePlatformAdapter:
    """Issue, inspect, revoke, and validate capability leases.

    This adapter maintains an in-memory registry. It describes grants but
    does not execute tools or replace the existing authorization pipeline.
    Resource scope matching is exact; wildcard matching is not supported.
    """

    def __init__(
        self,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._leases: dict[str, CapabilityLease] = {}

    def _now(self) -> datetime:
        return _aware_utc(self._clock(), "clock result")

    def issue_lease(
        self,
        agent_id: str,
        capability: str,
        scope: Iterable[str],
        ttl_seconds: int = 300,
        lease_id: str | None = None,
    ) -> CapabilityLease:
        """Create a lease for one agent, capability, and exact resource set."""
        agent_id = _require_text(agent_id, "agent_id")
        capability = _require_text(capability, "capability")

        if isinstance(scope, (str, bytes)):
            raise ValueError("scope must be an iterable of resource strings")

        try:
            resources = tuple(
                dict.fromkeys(_require_text(item, "scope item") for item in scope)
            )
        except TypeError as exc:
            raise ValueError("scope must be an iterable of resource strings") from exc

        if not resources:
            raise ValueError("scope must contain at least one resource")

        if (
            isinstance(ttl_seconds, bool)
            or not isinstance(ttl_seconds, int)
            or ttl_seconds <= 0
        ):
            raise ValueError("ttl_seconds must be a positive integer")

        now = self._now()
        identifier = (
            _require_text(lease_id, "lease_id")
            if lease_id is not None
            else secrets.token_urlsafe(12)
        )

        if identifier in self._leases:
            raise ValueError(f"lease_id already exists: {identifier}")

        lease = CapabilityLease(
            lease_id=identifier,
            agent_id=agent_id,
            capability=capability,
            scope=resources,
            issued_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )
        self._leases[identifier] = lease
        return lease

    def get_lease(self, lease_id: str) -> CapabilityLease | None:
        """Return a lease by ID, or None if it does not exist."""
        return self._leases.get(lease_id)

    def list_leases(self) -> list[dict]:
        """Return JSON-friendly lease records with current effective status."""
        now = self._now()
        return [
            lease.to_dict(now)
            for lease in self._leases.values()
        ]

    def revoke_lease(
        self,
        lease_id: str,
        reason: str = "revoked",
    ) -> CapabilityLease:
        """Revoke a lease. Repeated revocation is idempotent."""
        lease = self._leases.get(lease_id)
        if lease is None:
            raise KeyError(f"Unknown lease_id: {lease_id}")

        if lease.status != "revoked":
            lease.status = "revoked"
            lease.revoked_at = self._now()
            lease.revocation_reason = _require_text(reason, "reason")

        return lease

    def validate_lease(
        self,
        lease_id: str,
        agent_id: str,
        capability: str,
        resource: str,
    ) -> dict:
        """Check lease identity, status, capability, and exact resource scope."""
        lease = self._leases.get(lease_id)

        if lease is None:
            return self._result(False, "LEASE_NOT_FOUND", "Lease does not exist")

        if agent_id != lease.agent_id:
            return self._result(False, "AGENT_MISMATCH", "Lease belongs to another agent")

        status = lease.status_at(self._now())
        if status == "revoked":
            return self._result(False, "LEASE_REVOKED", "Lease has been revoked")

        if status == "expired":
            return self._result(False, "LEASE_EXPIRED", "Lease has expired")

        if capability != lease.capability:
            return self._result(
                False, "CAPABILITY_MISMATCH", "Capability is not granted by this lease"
            )

        if resource not in lease.scope:
            return self._result(False, "SCOPE_MISMATCH", "Resource is outside lease scope")

        return self._result(True, "LEASE_VALID", "Lease is valid for this request")

    @staticmethod
    def _result(allowed: bool, reason_code: str, reason: str) -> dict:
        return {
            "allowed": allowed,
            "decision": "ALLOW" if allowed else "DENY",
            "reason_code": reason_code,
            "reason": reason,
        }

    def reset(self) -> None:
        """Clear this adapter's in-memory registry, useful for isolated tests."""
        self._leases.clear()


__all__ = [
    "CapabilityLease",
    "CapabilityLeasePlatformAdapter",
]
