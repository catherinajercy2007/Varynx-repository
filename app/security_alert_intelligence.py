
"""Varynx Day 88: Security Alert and Escalation Intelligence.

Transforms supplied security evidence into explainable alert records.
This is an intelligence and handoff layer, not a notification service,
authorization engine, or runtime enforcement mechanism.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Mapping


VERSION = "DAY88-V1"

SEVERITY_INFO = "INFO"
SEVERITY_LOW = "LOW"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_HIGH = "HIGH"
SEVERITY_CRITICAL = "CRITICAL"

ESCALATION_NONE = "NO_ESCALATION"
ESCALATION_REVIEW = "SECURITY_REVIEW"
ESCALATION_PRIORITY = "PRIORITY_SECURITY_REVIEW"
ESCALATION_URGENT = "URGENT_SECURITY_REVIEW"
ESCALATION_EMERGENCY = "EMERGENCY_RESPONSE_REVIEW"

REASON_RISK_ELEVATED = "ALERT_RISK_ELEVATED"
REASON_RISK_HIGH = "ALERT_RISK_HIGH"
REASON_RISK_CRITICAL = "ALERT_RISK_CRITICAL"
REASON_EMERGENCY_CONTROL = "EMERGENCY_CONTROL_ACTIVE"
REASON_SECURITY_REASON_CODES = "SECURITY_REASON_CODES_PRESENT"
REASON_EVIDENCE_INCOMPLETE = "ALERT_EVIDENCE_INCOMPLETE"


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _score(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a finite score")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a finite score") from exc
    if not isfinite(result) or not 0 <= result <= 100:
        raise ValueError(f"{field} must be between 0 and 100")
    return result


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value


def _stable_digest(payload: Mapping[str, Any]) -> str:
    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return sha256(serialized.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AlertPolicy:
    """Thresholds and escalation mapping for alert classification."""

    policy_id: str
    medium_threshold: float = 40.0
    high_threshold: float = 60.0
    critical_threshold: float = 80.0
    require_evidence_for_escalation: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "policy_id", _text(self.policy_id, "policy_id")
        )
        medium = _score(self.medium_threshold, "medium_threshold")
        high = _score(self.high_threshold, "high_threshold")
        critical = _score(self.critical_threshold, "critical_threshold")
        if not medium < high < critical:
            raise ValueError(
                "Thresholds must satisfy medium < high < critical"
            )
        if not isinstance(self.require_evidence_for_escalation, bool):
            raise TypeError("require_evidence_for_escalation must be bool")
        object.__setattr__(self, "medium_threshold", medium)
        object.__setattr__(self, "high_threshold", high)
        object.__setattr__(self, "critical_threshold", critical)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["version"] = VERSION
        return result


@dataclass(frozen=True)
class SecurityAlert:
    """Immutable alert record derived from supplied evidence."""

    alert_id: str
    deduplication_key: str
    agent_id: str
    alert_type: str
    correlation_id: str | None
    severity: str
    risk_score: float
    reason_codes: tuple[str, ...]
    evidence_references: tuple[str, ...]
    evidence_complete: bool
    emergency_control_active: bool
    escalation_recommendation: str
    summary: str
    observed_at: datetime
    policy_id: str

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["version"] = VERSION
        result["observed_at"] = self.observed_at.isoformat()
        result["reason_codes"] = list(self.reason_codes)
        result["evidence_references"] = list(self.evidence_references)
        result["is_authorization_decision"] = False
        result["executes_enforcement"] = False
        result["sends_notification"] = False
        return result


def classify_alert_severity(
    *,
    risk_score: float,
    policy: AlertPolicy,
    emergency_control_active: bool = False,
) -> str:
    """Classify supplied risk evidence using explicit thresholds.

    An active emergency control raises alert severity to at least HIGH.
    It does not create or enforce the emergency control.
    """
    risk = _score(risk_score, "risk_score")
    if not isinstance(policy, AlertPolicy):
        raise TypeError("policy must be an AlertPolicy")
    if not isinstance(emergency_control_active, bool):
        raise TypeError("emergency_control_active must be bool")

    if emergency_control_active:
        return (
            SEVERITY_CRITICAL
            if risk >= policy.critical_threshold
            else SEVERITY_HIGH
        )
    if risk >= policy.critical_threshold:
        return SEVERITY_CRITICAL
    if risk >= policy.high_threshold:
        return SEVERITY_HIGH
    if risk >= policy.medium_threshold:
        return SEVERITY_MEDIUM
    if risk > 0:
        return SEVERITY_LOW
    return SEVERITY_INFO


def _escalation_for(
    severity: str,
    *,
    evidence_complete: bool,
    policy: AlertPolicy,
) -> str:
    if (
        policy.require_evidence_for_escalation
        and not evidence_complete
        and severity not in {SEVERITY_CRITICAL}
    ):
        return ESCALATION_REVIEW

    return {
        SEVERITY_INFO: ESCALATION_NONE,
        SEVERITY_LOW: ESCALATION_NONE,
        SEVERITY_MEDIUM: ESCALATION_REVIEW,
        SEVERITY_HIGH: ESCALATION_PRIORITY,
        SEVERITY_CRITICAL: ESCALATION_EMERGENCY,
    }[severity]


def build_security_alert(
    *,
    agent_id: str,
    alert_type: str,
    risk_score: float,
    observed_at: datetime,
    policy: AlertPolicy,
    reason_codes: tuple[str, ...] | list[str] = (),
    evidence_references: tuple[str, ...] | list[str] = (),
    correlation_id: str | None = None,
    emergency_control_active: bool = False,
    evidence_complete: bool = True,
) -> SecurityAlert:
    """Create a deterministic alert from already-produced evidence.

    Alert identity is stable for the same agent, alert type, correlation
    ID, and policy version. Occurrence time and score are deliberately
    excluded from the identity so repeated observations can be grouped.
    """
    agent_id = _text(agent_id, "agent_id")
    alert_type = _text(alert_type, "alert_type").upper()
    observed_at = _timestamp(observed_at, "observed_at")
    risk = _score(risk_score, "risk_score")

    if not isinstance(policy, AlertPolicy):
        raise TypeError("policy must be an AlertPolicy")
    if correlation_id is not None:
        correlation_id = _text(correlation_id, "correlation_id")
    if not isinstance(emergency_control_active, bool):
        raise TypeError("emergency_control_active must be bool")
    if not isinstance(evidence_complete, bool):
        raise TypeError("evidence_complete must be bool")
    if isinstance(reason_codes, (str, bytes)):
        raise TypeError("reason_codes must be an iterable of strings")
    if isinstance(evidence_references, (str, bytes)):
        raise TypeError("evidence_references must be an iterable of strings")

    reasons = tuple(sorted({
        _text(code, "reason_code").upper() for code in reason_codes
    }))
    references = tuple(sorted({
        _text(reference, "evidence_reference")
        for reference in evidence_references
    }))

    if emergency_control_active:
        reasons = tuple(sorted(set(reasons) | {REASON_EMERGENCY_CONTROL}))
    if reasons:
        reasons = tuple(sorted(set(reasons) | {REASON_SECURITY_REASON_CODES}))
    if not evidence_complete:
        reasons = tuple(sorted(set(reasons) | {REASON_EVIDENCE_INCOMPLETE}))

    if risk >= policy.critical_threshold:
        reasons = tuple(sorted(set(reasons) | {REASON_RISK_CRITICAL}))
    elif risk >= policy.high_threshold:
        reasons = tuple(sorted(set(reasons) | {REASON_RISK_HIGH}))
    elif risk >= policy.medium_threshold:
        reasons = tuple(sorted(set(reasons) | {REASON_RISK_ELEVATED}))

    severity = classify_alert_severity(
        risk_score=risk,
        policy=policy,
        emergency_control_active=emergency_control_active,
    )
    escalation = _escalation_for(
        severity,
        evidence_complete=evidence_complete,
        policy=policy,
    )

    identity = {
        "agent_id": agent_id,
        "alert_type": alert_type,
        "correlation_id": correlation_id,
        "policy_id": policy.policy_id,
        "version": VERSION,
    }
    deduplication_key = _stable_digest(identity)
    alert_id = f"alert-{deduplication_key[:20]}"

    summary = (
        f"{severity} {alert_type} alert for agent {agent_id}; "
        f"risk score {risk:.2f}/100. "
        f"Escalation recommendation: {escalation}."
    )
    if not evidence_complete:
        summary += " Supporting evidence is marked incomplete."
    if emergency_control_active:
        summary += " An emergency control is reported active."

    return SecurityAlert(
        alert_id=alert_id,
        deduplication_key=deduplication_key,
        agent_id=agent_id,
        alert_type=alert_type,
        correlation_id=correlation_id,
        severity=severity,
        risk_score=risk,
        reason_codes=reasons,
        evidence_references=references,
        evidence_complete=evidence_complete,
        emergency_control_active=emergency_control_active,
        escalation_recommendation=escalation,
        summary=summary,
        observed_at=observed_at,
        policy_id=policy.policy_id,
    )


__all__ = [
    "VERSION",
    "AlertPolicy",
    "SecurityAlert",
    "classify_alert_severity",
    "build_security_alert",
    "SEVERITY_INFO",
    "SEVERITY_LOW",
    "SEVERITY_MEDIUM",
    "SEVERITY_HIGH",
    "SEVERITY_CRITICAL",
    "ESCALATION_NONE",
    "ESCALATION_REVIEW",
    "ESCALATION_PRIORITY",
    "ESCALATION_URGENT",
    "ESCALATION_EMERGENCY",
]
