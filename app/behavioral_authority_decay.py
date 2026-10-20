
"""Day 85: Behavioral Authority Decay and Recovery for Varynx.

This module produces a deterministic authority-state assessment from
explicit evidence, elapsed time, and configured transition parameters.

It does not grant privileges, modify a capability lease, authorize
requests, or execute runtime enforcement.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from math import isfinite
from typing import Any, Mapping


VERSION = "DAY85-V1"

AUTHORITY_NORMAL = "NORMAL"
AUTHORITY_REDUCED = "REDUCED"
AUTHORITY_RESTRICTED = "RESTRICTED"

STATUS_STABLE = "AUTHORITY_STABLE"
STATUS_DECAYED = "AUTHORITY_DECAYED"
STATUS_RECOVERY_QUALIFIED = "RECOVERY_QUALIFIED"
STATUS_RECOVERY_INSUFFICIENT = "RECOVERY_INSUFFICIENT"
STATUS_INVALID_EVIDENCE = "INVALID_EVIDENCE"

RECOMMEND_KEEP_STATE = "KEEP_CURRENT_AUTHORITY_STATE"
RECOMMEND_REDUCE_AUTHORITY = "RECOMMEND_REDUCED_AUTHORITY"
RECOMMEND_RESTRICT_AUTHORITY = "RECOMMEND_RESTRICTED_AUTHORITY"
RECOMMEND_REVIEW_RECOVERY = "RECOMMEND_RECOVERY_REVIEW"

REASON_EVIDENCE_STALE = "BEHAVIORAL_EVIDENCE_STALE"
REASON_ADVERSE_SIGNAL = "ADVERSE_BEHAVIORAL_SIGNAL"
REASON_FRESH_QUALIFYING_EVIDENCE = "FRESH_QUALIFYING_EVIDENCE"
REASON_RECOVERY_REQUIREMENT_UNMET = "RECOVERY_REQUIREMENT_UNMET"


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a finite number") from exc
    if not isfinite(result):
        raise ValueError(f"{field} must be a finite number")
    return result


def _aware_datetime(value: Any, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value


def _state(value: Any) -> str:
    normalized = _text(value, "current_state").upper()
    allowed = {
        AUTHORITY_NORMAL,
        AUTHORITY_REDUCED,
        AUTHORITY_RESTRICTED,
    }
    if normalized not in allowed:
        raise ValueError(f"current_state must be one of {sorted(allowed)}")
    return normalized


@dataclass(frozen=True)
class AuthorityDecayPolicy:
    """Explicit thresholds and transitions for authority assessment."""

    policy_id: str
    evidence_ttl_seconds: int
    recovery_minimum_events: int
    adverse_signal_threshold: float
    recovery_signal_maximum: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "policy_id", _text(self.policy_id, "policy_id")
        )

        for field in ("evidence_ttl_seconds", "recovery_minimum_events"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field} must be an integer")
            if value < 1:
                raise ValueError(f"{field} must be at least 1")

        adverse = _number(
            self.adverse_signal_threshold, "adverse_signal_threshold"
        )
        recovery = _number(
            self.recovery_signal_maximum, "recovery_signal_maximum"
        )
        if not 0 <= adverse <= 100:
            raise ValueError("adverse_signal_threshold must be in [0, 100]")
        if not 0 <= recovery <= 100:
            raise ValueError("recovery_signal_maximum must be in [0, 100]")

        object.__setattr__(self, "adverse_signal_threshold", adverse)
        object.__setattr__(self, "recovery_signal_maximum", recovery)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["version"] = VERSION
        return result


@dataclass(frozen=True)
class AuthorityAssessment:
    """Immutable recommendation; not a granted authority or lease update."""

    agent_id: str
    policy_id: str
    current_state: str
    recommended_state: str
    status: str
    evidence_age_seconds: float
    recovery_qualifying_events: int
    reason_codes: tuple[str, ...]
    recommendation: str
    evaluated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["version"] = VERSION
        result["evaluated_at"] = self.evaluated_at.isoformat()
        result["reason_codes"] = list(self.reason_codes)
        result["changes_authority_directly"] = False
        result["executes_enforcement"] = False
        result["is_authorization_decision"] = False
        return result


def assess_behavioral_authority(
    *,
    agent_id: str,
    current_state: str,
    policy: AuthorityDecayPolicy,
    now: datetime,
    last_qualifying_evidence_at: datetime | None,
    adverse_signal_score: float | None,
    recovery_signal_score: float | None = None,
    recovery_qualifying_events: int = 0,
) -> AuthorityAssessment:
    """Recommend an authority state from explicit behavioral evidence.

    Rules:
    - A sufficiently strong adverse signal reduces authority by one level.
    - Stale or missing qualifying evidence reduces NORMAL to REDUCED.
    - REDUCED authority can be recommended for recovery only when evidence
      is fresh, the recovery signal is below threshold, and enough
      qualifying events have been recorded.
    - RESTRICTED authority is never automatically restored by this module.
    - Invalid or missing evidence never increases authority.

    Thresholds are configuration choices and require empirical validation.
    """
    agent_id = _text(agent_id, "agent_id")
    if not isinstance(policy, AuthorityDecayPolicy):
        raise TypeError("policy must be an AuthorityDecayPolicy")

    current_state = _state(current_state)
    now = _aware_datetime(now, "now")

    if isinstance(recovery_qualifying_events, bool) or not isinstance(
        recovery_qualifying_events, int
    ):
        raise TypeError("recovery_qualifying_events must be an integer")
    if recovery_qualifying_events < 0:
        raise ValueError("recovery_qualifying_events must be >= 0")

    last_evidence = None
    age_seconds = float("inf")
    if last_qualifying_evidence_at is not None:
        last_evidence = _aware_datetime(
            last_qualifying_evidence_at, "last_qualifying_evidence_at"
        )
        age_seconds = (now - last_evidence).total_seconds()

    if age_seconds < 0:
        raise ValueError("qualifying evidence timestamp cannot be in the future")

    reasons: list[str] = []

    def result(
        recommended_state: str,
        status: str,
        recommendation: str,
        *codes: str,
    ) -> AuthorityAssessment:
        return AuthorityAssessment(
            agent_id=agent_id,
            policy_id=policy.policy_id,
            current_state=current_state,
            recommended_state=recommended_state,
            status=status,
            evidence_age_seconds=age_seconds,
            recovery_qualifying_events=recovery_qualifying_events,
            reason_codes=tuple(codes),
            recommendation=recommendation,
            evaluated_at=now,
        )

    if last_evidence is None or age_seconds > policy.evidence_ttl_seconds:
        reasons.append(REASON_EVIDENCE_STALE)

    if adverse_signal_score is not None:
        try:
            adverse = _number(adverse_signal_score, "adverse_signal_score")
        except ValueError:
            return result(
                current_state,
                STATUS_INVALID_EVIDENCE,
                RECOMMEND_KEEP_STATE,
                "INVALID_ADVERSE_SIGNAL",
            )
        if not 0 <= adverse <= 100:
            return result(
                current_state,
                STATUS_INVALID_EVIDENCE,
                RECOMMEND_KEEP_STATE,
                "ADVERSE_SIGNAL_OUT_OF_RANGE",
            )
        if adverse >= policy.adverse_signal_threshold:
            reasons.append(REASON_ADVERSE_SIGNAL)
            target = {
                AUTHORITY_NORMAL: AUTHORITY_REDUCED,
                AUTHORITY_REDUCED: AUTHORITY_RESTRICTED,
                AUTHORITY_RESTRICTED: AUTHORITY_RESTRICTED,
            }[current_state]
            recommendation = (
                RECOMMEND_REDUCE_AUTHORITY
                if target == AUTHORITY_REDUCED
                else RECOMMEND_RESTRICT_AUTHORITY
            )
            return result(
                target,
                STATUS_DECAYED,
                recommendation,
                *reasons,
            )

    stale = REASON_EVIDENCE_STALE in reasons
    if stale:
        if current_state == AUTHORITY_NORMAL:
            return result(
                AUTHORITY_REDUCED,
                STATUS_DECAYED,
                RECOMMEND_REDUCE_AUTHORITY,
                *reasons,
            )
        return result(
            current_state,
            STATUS_STABLE,
            RECOMMEND_KEEP_STATE,
            *reasons,
        )

    # A restricted state needs an explicit, separate recovery review.
    if current_state == AUTHORITY_RESTRICTED:
        return result(
            AUTHORITY_RESTRICTED,
            STATUS_RECOVERY_INSUFFICIENT,
            RECOMMEND_KEEP_STATE,
            REASON_RECOVERY_REQUIREMENT_UNMET,
        )

    if current_state == AUTHORITY_REDUCED:
        if recovery_signal_score is None:
            return result(
                AUTHORITY_REDUCED,
                STATUS_RECOVERY_INSUFFICIENT,
                RECOMMEND_KEEP_STATE,
                REASON_RECOVERY_REQUIREMENT_UNMET,
            )

        try:
            recovery = _number(recovery_signal_score, "recovery_signal_score")
        except ValueError:
            return result(
                AUTHORITY_REDUCED,
                STATUS_INVALID_EVIDENCE,
                RECOMMEND_KEEP_STATE,
                "INVALID_RECOVERY_SIGNAL",
            )

        if not 0 <= recovery <= 100:
            return result(
                AUTHORITY_REDUCED,
                STATUS_INVALID_EVIDENCE,
                RECOMMEND_KEEP_STATE,
                "RECOVERY_SIGNAL_OUT_OF_RANGE",
            )

        if (
            recovery <= policy.recovery_signal_maximum
            and recovery_qualifying_events >= policy.recovery_minimum_events
        ):
            return result(
                AUTHORITY_NORMAL,
                STATUS_RECOVERY_QUALIFIED,
                RECOMMEND_REVIEW_RECOVERY,
                REASON_FRESH_QUALIFYING_EVIDENCE,
            )

        return result(
            AUTHORITY_REDUCED,
            STATUS_RECOVERY_INSUFFICIENT,
            RECOMMEND_KEEP_STATE,
            REASON_RECOVERY_REQUIREMENT_UNMET,
        )

    return result(
        AUTHORITY_NORMAL,
        STATUS_STABLE,
        RECOMMEND_KEEP_STATE,
        "FRESH_EVIDENCE_NO_ADVERSE_TRANSITION",
    )


__all__ = [
    "VERSION",
    "AuthorityDecayPolicy",
    "AuthorityAssessment",
    "assess_behavioral_authority",
    "AUTHORITY_NORMAL",
    "AUTHORITY_REDUCED",
    "AUTHORITY_RESTRICTED",
    "STATUS_STABLE",
    "STATUS_DECAYED",
    "STATUS_RECOVERY_QUALIFIED",
    "STATUS_RECOVERY_INSUFFICIENT",
    "STATUS_INVALID_EVIDENCE",
]
