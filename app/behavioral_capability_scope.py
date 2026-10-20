
"""Day 81: Behavioral Capability and Scope Assessment for Varynx.

This module evaluates requested capability and resource scope against
an existing Day 80 behavioral capability lease and explicit scope rules.

It produces an assessment only. It does not authorize, execute, or
enforce an operation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Mapping

from app.behavioral_capability_lease import (
    BehavioralCapabilityLease,
    evaluate_capability_lease,
)

VERSION = "DAY81-V1"

STATUS_WITHIN_SCOPE = "WITHIN_SCOPE"
STATUS_OUT_OF_SCOPE = "OUT_OF_SCOPE"
STATUS_LEASE_INELIGIBLE = "LEASE_INELIGIBLE"
STATUS_CAPABILITY_MISMATCH = "CAPABILITY_MISMATCH"
STATUS_EXPLICITLY_RESTRICTED = "EXPLICITLY_RESTRICTED"

RECOMMEND_ALLOW_FOR_POLICY_REVIEW = "ALLOW_FOR_POLICY_REVIEW"
RECOMMEND_RESTRICT_SCOPE = "RESTRICT_SCOPE"
RECOMMEND_DENY_FOR_POLICY_REVIEW = "DENY_FOR_POLICY_REVIEW"


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _scopes(values: tuple[str, ...], field: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field} must be a sequence of scope strings")

    try:
        result = tuple(_text(value, field) for value in values)
    except TypeError as exc:
        raise TypeError(
            f"{field} must be a sequence of scope strings"
        ) from exc

    if len(set(result)) != len(result):
        raise ValueError(f"{field} must not contain duplicate scopes")

    return result


def _matches_scope(resource: str, scope: str) -> bool:
    """Match an exact identifier or a slash-delimited path subtree.

    Wildcards and glob expressions are deliberately unsupported.
    """
    if resource == scope:
        return True

    prefix = scope if scope.endswith("/") else scope + "/"
    return resource.startswith(prefix)


def _matches_any(resource: str, scopes: tuple[str, ...]) -> bool:
    return any(_matches_scope(resource, scope) for scope in scopes)


@dataclass(frozen=True)
class BehavioralScopePolicy:
    """Declarative scope constraints; not an authorization policy engine."""

    policy_id: str
    capability: str
    allowed_scopes: tuple[str, ...]
    restricted_scopes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "policy_id", _text(self.policy_id, "policy_id")
        )
        object.__setattr__(
            self, "capability", _text(self.capability, "capability")
        )

        allowed = _scopes(self.allowed_scopes, "allowed_scopes")
        restricted = _scopes(self.restricted_scopes, "restricted_scopes")

        if not allowed:
            raise ValueError("allowed_scopes must not be empty")

        object.__setattr__(self, "allowed_scopes", allowed)
        object.__setattr__(self, "restricted_scopes", restricted)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": VERSION,
            "policy_id": self.policy_id,
            "capability": self.capability,
            "allowed_scopes": list(self.allowed_scopes),
            "restricted_scopes": list(self.restricted_scopes),
        }


@dataclass(frozen=True)
class BehavioralScopeAssessment:
    """Immutable assessment result; not an authorization decision."""

    policy_id: str
    lease_id: str
    agent_id: str
    task_id: str
    capability: str
    resource: str
    status: str
    eligible_for_policy_review: bool
    recommendation: str
    reason_codes: tuple[str, ...]
    evaluated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["version"] = VERSION
        result["reason_codes"] = list(self.reason_codes)
        result["evaluated_at"] = self.evaluated_at.isoformat()
        result["is_authorization_decision"] = False
        result["executes_enforcement"] = False
        return result


def assess_behavioral_capability_scope(
    *,
    lease: BehavioralCapabilityLease,
    policy: BehavioralScopePolicy,
    agent_id: str,
    task_id: str,
    capability: str,
    resource: str,
    now: datetime,
    behavioral_evidence: Mapping[str, Any] | None = None,
) -> BehavioralScopeAssessment:
    """Assess scope and lease eligibility without enforcing the request.

    Explicitly restricted resources take precedence over allowed scopes.
    A positive result means only that these supplied constraints passed.
    Existing authorization and runtime enforcement remain authoritative.
    """
    if not isinstance(lease, BehavioralCapabilityLease):
        raise TypeError("lease must be a BehavioralCapabilityLease")

    if not isinstance(policy, BehavioralScopePolicy):
        raise TypeError("policy must be a BehavioralScopePolicy")

    agent_id = _text(agent_id, "agent_id")
    task_id = _text(task_id, "task_id")
    capability = _text(capability, "capability")
    resource = _text(resource, "resource")

    if not isinstance(now, datetime):
        raise TypeError("now must be a datetime")
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")

    def assessment(
        status: str,
        eligible: bool,
        recommendation: str,
        *reason_codes: str,
    ) -> BehavioralScopeAssessment:
        return BehavioralScopeAssessment(
            policy_id=policy.policy_id,
            lease_id=lease.lease_id,
            agent_id=agent_id,
            task_id=task_id,
            capability=capability,
            resource=resource,
            status=status,
            eligible_for_policy_review=eligible,
            recommendation=recommendation,
            reason_codes=tuple(reason_codes),
            evaluated_at=now,
        )

    if capability != policy.capability:
        return assessment(
            STATUS_CAPABILITY_MISMATCH,
            False,
            RECOMMEND_DENY_FOR_POLICY_REVIEW,
            "REQUESTED_CAPABILITY_DOES_NOT_MATCH_SCOPE_POLICY",
        )

    # Explicit restrictions always override the policy's allowed scopes.
    if _matches_any(resource, policy.restricted_scopes):
        return assessment(
            STATUS_EXPLICITLY_RESTRICTED,
            False,
            RECOMMEND_RESTRICT_SCOPE,
            "RESOURCE_MATCHES_EXPLICIT_RESTRICTION",
        )

    if not _matches_any(resource, policy.allowed_scopes):
        return assessment(
            STATUS_OUT_OF_SCOPE,
            False,
            RECOMMEND_RESTRICT_SCOPE,
            "RESOURCE_OUTSIDE_CONFIGURED_SCOPE",
        )

    lease_result = evaluate_capability_lease(
        lease,
        agent_id=agent_id,
        task_id=task_id,
        capability=capability,
        resource=resource,
        now=now,
        behavioral_evidence=behavioral_evidence,
    )

    if not lease_result.eligible:
        return assessment(
            STATUS_LEASE_INELIGIBLE,
            False,
            RECOMMEND_DENY_FOR_POLICY_REVIEW,
            "BEHAVIORAL_CAPABILITY_LEASE_INELIGIBLE",
            *lease_result.reason_codes,
        )

    return assessment(
        STATUS_WITHIN_SCOPE,
        True,
        RECOMMEND_ALLOW_FOR_POLICY_REVIEW,
        "RESOURCE_WITHIN_CONFIGURED_SCOPE",
        "BEHAVIORAL_CAPABILITY_LEASE_ELIGIBLE",
    )


__all__ = [
    "VERSION",
    "BehavioralScopePolicy",
    "BehavioralScopeAssessment",
    "assess_behavioral_capability_scope",
    "STATUS_WITHIN_SCOPE",
    "STATUS_OUT_OF_SCOPE",
    "STATUS_LEASE_INELIGIBLE",
    "STATUS_CAPABILITY_MISMATCH",
    "STATUS_EXPLICITLY_RESTRICTED",
    "RECOMMEND_ALLOW_FOR_POLICY_REVIEW",
    "RECOMMEND_RESTRICT_SCOPE",
    "RECOMMEND_DENY_FOR_POLICY_REVIEW",
]
