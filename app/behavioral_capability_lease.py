"""Day 80: Behavioral Capability Lease for Varynx.

A lease represents bounded, time-limited behavioral authority.
Evaluation is deterministic and explanatory: it does not authorize,
execute, or enforce an operation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from math import isfinite
from typing import Any, Mapping


VERSION = "DAY80-V1"

AUTHORITY_ACTIVE = "ACTIVE"
AUTHORITY_SUSPENDED = "SUSPENDED"
AUTHORITY_REVOKED = "REVOKED"

STATUS_ELIGIBLE = "ELIGIBLE"
STATUS_REVOKED = "REVOKED"
STATUS_SUSPENDED = "SUSPENDED"
STATUS_NOT_YET_VALID = "NOT_YET_VALID"
STATUS_EXPIRED = "EXPIRED"
STATUS_CONTEXT_MISMATCH = "CONTEXT_MISMATCH"
STATUS_OUT_OF_SCOPE = "OUT_OF_SCOPE"
STATUS_BEHAVIORAL_CONDITION_FAILED = "BEHAVIORAL_CONDITION_FAILED"

SUPPORTED_OPERATORS = {"lt", "lte", "gt", "gte", "eq"}


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _aware_datetime(value: Any, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a finite number") from exc
    if not isfinite(result):
        raise ValueError(f"{field} must be a finite number")
    return result


@dataclass(frozen=True)
class BehavioralCondition:
    """A simple numeric condition over an existing evidence signal."""

    signal: str
    operator: str
    threshold: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "signal", _required_text(self.signal, "signal")
        )
        operator = _required_text(self.operator, "operator").lower()
        if operator not in SUPPORTED_OPERATORS:
            raise ValueError(
                f"operator must be one of {sorted(SUPPORTED_OPERATORS)}"
            )
        object.__setattr__(self, "operator", operator)
        object.__setattr__(
            self, "threshold", _finite_number(self.threshold, "threshold")
        )

    def evaluate(self, evidence: Mapping[str, Any]) -> tuple[bool, str]:
        """Return whether the signal satisfies this condition."""
        if self.signal not in evidence:
            return False, f"MISSING_BEHAVIOR_SIGNAL:{self.signal}"

        try:
            observed = _finite_number(evidence[self.signal], self.signal)
        except (TypeError, ValueError):
            return False, f"INVALID_BEHAVIOR_SIGNAL:{self.signal}"

        checks = {
            "lt": observed < self.threshold,
            "lte": observed <= self.threshold,
            "gt": observed > self.threshold,
            "gte": observed >= self.threshold,
            "eq": observed == self.threshold,
        }
        passed = checks[self.operator]
        if passed:
            return True, f"BEHAVIOR_CONDITION_MET:{self.signal}"

        return False, f"BEHAVIOR_CONDITION_FAILED:{self.signal}"


@dataclass(frozen=True)
class BehavioralCapabilityLease:
    """Immutable declaration of bounded behavioral authority.

    Resource scopes are exact resource identifiers or path-like prefixes.
    Prefix matching observes a path boundary, so ``public/`` does not
    match ``publicity/``. Wildcards and glob patterns are not supported.
    """

    lease_id: str
    agent_id: str
    task_id: str
    capability: str
    resource_scopes: tuple[str, ...]
    issued_at: datetime
    not_before: datetime
    expires_at: datetime
    conditions: tuple[BehavioralCondition, ...] = ()
    authority_state: str = AUTHORITY_ACTIVE

    def __post_init__(self) -> None:
        for field in ("lease_id", "agent_id", "task_id", "capability"):
            object.__setattr__(
                self, field, _required_text(getattr(self, field), field)
            )

        scopes = tuple(
            _required_text(scope, "resource_scope")
            for scope in self.resource_scopes
        )
        if not scopes:
            raise ValueError("resource_scopes must contain at least one scope")
        object.__setattr__(self, "resource_scopes", scopes)

        issued = _aware_datetime(self.issued_at, "issued_at")
        start = _aware_datetime(self.not_before, "not_before")
        expiry = _aware_datetime(self.expires_at, "expires_at")

        if expiry <= start:
            raise ValueError("expires_at must be later than not_before")
        if issued > expiry:
            raise ValueError("issued_at cannot be later than expires_at")

        state = _required_text(self.authority_state, "authority_state").upper()
        if state not in {
            AUTHORITY_ACTIVE,
            AUTHORITY_SUSPENDED,
            AUTHORITY_REVOKED,
        }:
            raise ValueError("Unsupported authority_state")
        object.__setattr__(self, "authority_state", state)

        conditions = tuple(self.conditions)
        if any(not isinstance(c, BehavioralCondition) for c in conditions):
            raise TypeError(
                "conditions must contain BehavioralCondition records"
            )
        object.__setattr__(self, "conditions", conditions)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the lease into JSON-friendly values."""
        return {
            "version": VERSION,
            "lease_id": self.lease_id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "capability": self.capability,
            "resource_scopes": list(self.resource_scopes),
            "issued_at": self.issued_at.isoformat(),
            "not_before": self.not_before.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "conditions": [asdict(c) for c in self.conditions],
            "authority_state": self.authority_state,
        }


@dataclass(frozen=True)
class LeaseEvaluation:
    """Read-only assessment of whether a request meets lease constraints."""

    lease_id: str
    status: str
    eligible: bool
    reason_codes: tuple[str, ...]
    evaluated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": VERSION,
            "lease_id": self.lease_id,
            "status": self.status,
            "eligible": self.eligible,
            "reason_codes": list(self.reason_codes),
            "evaluated_at": self.evaluated_at.isoformat(),
            "is_authorization_decision": False,
            "executes_enforcement": False,
        }


def _resource_in_scope(resource: str, scope: str) -> bool:
    """Match an exact resource or a slash-boundary path prefix."""
    if resource == scope:
        return True
    prefix = scope if scope.endswith("/") else scope + "/"
    return resource.startswith(prefix)


def evaluate_capability_lease(
    lease: BehavioralCapabilityLease,
    *,
    agent_id: str,
    task_id: str,
    capability: str,
    resource: str,
    now: datetime,
    behavioral_evidence: Mapping[str, Any] | None = None,
) -> LeaseEvaluation:
    """Evaluate identity, scope, time, authority, and behavioral conditions.

    ``now`` is explicit so experiments and tests are reproducible.
    Missing behavioral evidence never counts as satisfying a condition.
    This function returns lease eligibility only, not an authorization
    decision and not a runtime enforcement action.
    """
    if not isinstance(lease, BehavioralCapabilityLease):
        raise TypeError("lease must be a BehavioralCapabilityLease")

    now = _aware_datetime(now, "now")
    request = {
        "agent_id": _required_text(agent_id, "agent_id"),
        "task_id": _required_text(task_id, "task_id"),
        "capability": _required_text(capability, "capability"),
        "resource": _required_text(resource, "resource"),
    }

    if behavioral_evidence is None:
        evidence: Mapping[str, Any] = {}
    elif isinstance(behavioral_evidence, Mapping):
        evidence = behavioral_evidence
    else:
        raise TypeError("behavioral_evidence must be a mapping or None")

    def result(status: str, *codes: str) -> LeaseEvaluation:
        return LeaseEvaluation(
            lease_id=lease.lease_id,
            status=status,
            eligible=(status == STATUS_ELIGIBLE),
            reason_codes=tuple(codes),
            evaluated_at=now,
        )

    if lease.authority_state == AUTHORITY_REVOKED:
        return result(STATUS_REVOKED, "LEASE_AUTHORITY_REVOKED")

    if lease.authority_state == AUTHORITY_SUSPENDED:
        return result(STATUS_SUSPENDED, "LEASE_AUTHORITY_SUSPENDED")

    if now < lease.not_before:
        return result(STATUS_NOT_YET_VALID, "LEASE_NOT_YET_VALID")

    if now >= lease.expires_at:
        return result(STATUS_EXPIRED, "LEASE_EXPIRED")

    identity_fields = ("agent_id", "task_id", "capability")
    mismatches = [
        f"LEASE_{field.upper()}_MISMATCH"
        for field in identity_fields
        if request[field] != getattr(lease, field)
    ]
    if mismatches:
        return result(STATUS_CONTEXT_MISMATCH, *mismatches)

    if not any(
        _resource_in_scope(request["resource"], scope)
        for scope in lease.resource_scopes
    ):
        return result(STATUS_OUT_OF_SCOPE, "RESOURCE_OUTSIDE_LEASE_SCOPE")

    failed = []
    for condition in lease.conditions:
        passed, reason = condition.evaluate(evidence)
        if not passed:
            failed.append(reason)

    if failed:
        return result(STATUS_BEHAVIORAL_CONDITION_FAILED, *failed)

    return result(
        STATUS_ELIGIBLE,
        "LEASE_ACTIVE",
        "IDENTITY_AND_TASK_MATCH",
        "CAPABILITY_MATCH",
        "RESOURCE_WITHIN_SCOPE",
        "LEASE_WITHIN_VALIDITY_WINDOW",
        "BEHAVIORAL_CONDITIONS_SATISFIED",
    )


def lease_evaluation_is_authorization(evaluation: LeaseEvaluation) -> bool:
    """Lease eligibility is not itself an authorization decision."""
    if not isinstance(evaluation, LeaseEvaluation):
        raise TypeError("evaluation must be a LeaseEvaluation")
    return False


def lease_evaluation_executes_enforcement(
    evaluation: LeaseEvaluation,
) -> bool:
    """This module never executes runtime enforcement."""
    if not isinstance(evaluation, LeaseEvaluation):
        raise TypeError("evaluation must be a LeaseEvaluation")
    return False


__all__ = [
    "VERSION",
    "AUTHORITY_ACTIVE",
    "AUTHORITY_SUSPENDED",
    "AUTHORITY_REVOKED",
    "STATUS_ELIGIBLE",
    "STATUS_REVOKED",
    "STATUS_SUSPENDED",
    "STATUS_NOT_YET_VALID",
    "STATUS_EXPIRED",
    "STATUS_CONTEXT_MISMATCH",
    "STATUS_OUT_OF_SCOPE",
    "STATUS_BEHAVIORAL_CONDITION_FAILED",
    "BehavioralCondition",
    "BehavioralCapabilityLease",
    "LeaseEvaluation",
    "evaluate_capability_lease",
    "lease_evaluation_is_authorization",
    "lease_evaluation_executes_enforcement",
]
