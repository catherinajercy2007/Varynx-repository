"""
Varynx Day 41
Audit and Evidence Architecture

Provides a structured, immutable evidence record for security
decisions made by the Varynx behavioral risk-control pipeline.

Architecture:

Security Event
      |
      v
Evidence Collection
      |
      +--> risk evidence
      +--> behavioral evidence
      +--> cross-context evidence
      +--> policy evidence
      |
      v
Security Decision
      |
      v
Audit Evidence Record

This module does not make security decisions.
It records the evidence and decision produced by other components.

Important principles:
- evidence must be traceable to an event
- decisions must be explainable
- evidence must not be silently fabricated
- timestamps are timezone-aware
- scores are validated
- records are serializable
- schema versions are explicit
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from app.event_schema import (
    SCHEMA_VERSION as EVENT_SCHEMA_VERSION,
    SecurityEvent,
)


# ============================================================
# CONSTANTS
# ============================================================

AUDIT_SCHEMA_NAME = "varnyx.audit_evidence"
AUDIT_SCHEMA_VERSION = "1.0"

MAX_DECISION_LENGTH = 128
MAX_REASON_LENGTH = 1024


# ============================================================
# VALIDATION HELPERS
# ============================================================


def _require_text(
    value: Any,
    field_name: str,
    max_length: int,
) -> str:
    """Validate a required text value."""

    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string"
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f"{field_name} cannot be empty"
        )

    if len(value) > max_length:
        raise ValueError(
            f"{field_name} exceeds maximum length "
            f"of {max_length}"
        )

    return value


def _validate_score(
    value: Any,
    field_name: str,
) -> float:
    """Validate a security score in the range 0-100."""

    if isinstance(value, bool):
        raise TypeError(
            f"{field_name} must be numeric"
        )

    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(
            f"{field_name} must be numeric"
        ) from exc

    if not math.isfinite(numeric):
        raise ValueError(
            f"{field_name} must be finite"
        )

    if not 0.0 <= numeric <= 100.0:
        raise ValueError(
            f"{field_name} must be between 0 and 100"
        )

    return numeric


def _validate_timestamp(
    value: Any,
) -> datetime:
    """Validate and normalize a timezone-aware timestamp."""

    if isinstance(value, datetime):
        timestamp = value

    elif isinstance(value, str):

        normalized = value.strip()

        if normalized.endswith("Z"):
            normalized = (
                normalized[:-1]
                + "+00:00"
            )

        try:
            timestamp = datetime.fromisoformat(
                normalized
            )
        except ValueError as exc:
            raise ValueError(
                "timestamp must be valid ISO-8601"
            ) from exc

    else:
        raise TypeError(
            "timestamp must be datetime or ISO-8601 string"
        )

    if timestamp.tzinfo is None:
        raise ValueError(
            "timestamp must include timezone information"
        )

    return timestamp.astimezone(
        timezone.utc
    )


def _normalize_mapping(
    value: Mapping[str, Any] | None,
    field_name: str,
) -> dict[str, Any]:
    """
    Validate a mapping before converting it.

    This intentionally follows the Day 40 validation pattern.
    """

    if value is None:
        return {}

    if not isinstance(value, Mapping):
        raise TypeError(
            f"{field_name} must be a mapping"
        )

    return dict(value)


def _normalize_list(
    value: list[Any] | tuple[Any, ...] | None,
    field_name: str,
) -> list[Any]:
    """Validate an optional list/tuple."""

    if value is None:
        return []

    if not isinstance(
        value,
        (list, tuple),
    ):
        raise TypeError(
            f"{field_name} must be a list or tuple"
        )

    return list(value)


# ============================================================
# AUDIT EVIDENCE RECORD
# ============================================================


@dataclass(frozen=True)
class AuditEvidenceRecord:
    """
    Immutable evidence record representing one security decision.

    The record links:

    event
      -> evidence
      -> decision
      -> reason
      -> audit record
    """

    audit_id: str
    event_id: str
    timestamp: datetime

    agent_id: str

    decision: str
    reason: str

    risk_score: float
    anomaly_score: float

    behavioral_evidence: dict[str, Any] = field(
        default_factory=dict
    )

    cross_context_evidence: dict[str, Any] = field(
        default_factory=dict
    )

    policy_evidence: dict[str, Any] = field(
        default_factory=dict
    )

    triggered_rules: list[Any] = field(
        default_factory=list
    )

    source: str | None = None

    event_schema_version: str = (
        EVENT_SCHEMA_VERSION
    )

    schema_name: str = (
        AUDIT_SCHEMA_NAME
    )

    schema_version: str = (
        AUDIT_SCHEMA_VERSION
    )

    def __post_init__(self) -> None:
        """Validate the audit record."""

        object.__setattr__(
            self,
            "audit_id",
            _require_text(
                self.audit_id,
                "audit_id",
                128,
            ),
        )

        object.__setattr__(
            self,
            "event_id",
            _require_text(
                self.event_id,
                "event_id",
                128,
            ),
        )

        object.__setattr__(
            self,
            "timestamp",
            _validate_timestamp(
                self.timestamp
            ),
        )

        object.__setattr__(
            self,
            "agent_id",
            _require_text(
                self.agent_id,
                "agent_id",
                128,
            ),
        )

        object.__setattr__(
            self,
            "decision",
            _require_text(
                self.decision,
                "decision",
                MAX_DECISION_LENGTH,
            ),
        )

        object.__setattr__(
            self,
            "reason",
            _require_text(
                self.reason,
                "reason",
                MAX_REASON_LENGTH,
            ),
        )

        object.__setattr__(
            self,
            "risk_score",
            _validate_score(
                self.risk_score,
                "risk_score",
            ),
        )

        object.__setattr__(
            self,
            "anomaly_score",
            _validate_score(
                self.anomaly_score,
                "anomaly_score",
            ),
        )

        object.__setattr__(
            self,
            "behavioral_evidence",
            _normalize_mapping(
                self.behavioral_evidence,
                "behavioral_evidence",
            ),
        )

        object.__setattr__(
            self,
            "cross_context_evidence",
            _normalize_mapping(
                self.cross_context_evidence,
                "cross_context_evidence",
            ),
        )

        object.__setattr__(
            self,
            "policy_evidence",
            _normalize_mapping(
                self.policy_evidence,
                "policy_evidence",
            ),
        )

        object.__setattr__(
            self,
            "triggered_rules",
            _normalize_list(
                self.triggered_rules,
                "triggered_rules",
            ),
        )

        if self.source is not None:
            object.__setattr__(
                self,
                "source",
                _require_text(
                    self.source,
                    "source",
                    256,
                ),
            )

        if self.schema_name != AUDIT_SCHEMA_NAME:
            raise ValueError(
                "Unsupported audit schema name"
            )

        if self.schema_version != AUDIT_SCHEMA_VERSION:
            raise ValueError(
                "Unsupported audit schema version"
            )

        if (
            self.event_schema_version
            != EVENT_SCHEMA_VERSION
        ):
            raise ValueError(
                "Unsupported event schema version"
            )

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """Return a JSON-compatible dictionary."""

        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "event_schema_version": (
                self.event_schema_version
            ),
            "audit_id": self.audit_id,
            "event_id": self.event_id,
            "timestamp": (
                self.timestamp.isoformat()
            ),
            "agent_id": self.agent_id,
            "decision": self.decision,
            "reason": self.reason,
            "risk_score": self.risk_score,
            "anomaly_score": (
                self.anomaly_score
            ),
            "behavioral_evidence": dict(
                self.behavioral_evidence
            ),
            "cross_context_evidence": dict(
                self.cross_context_evidence
            ),
            "policy_evidence": dict(
                self.policy_evidence
            ),
            "triggered_rules": list(
                self.triggered_rules
            ),
            "source": self.source,
        }

    def to_json(
        self,
    ) -> str:
        """Return deterministic JSON."""

        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
        )


# ============================================================
# AUDIT ID
# ============================================================


def generate_audit_id(
    *,
    event_id: str,
    decision: str,
    timestamp: datetime,
) -> str:
    """
    Generate a deterministic audit identifier.

    This is useful for reproducible experiments and
    deterministic testing.

    Persistence systems should still enforce uniqueness.
    """

    normalized_timestamp = (
        _validate_timestamp(
            timestamp
        ).isoformat()
    )

    canonical = "|".join(
        [
            str(event_id).strip(),
            str(decision).strip(),
            normalized_timestamp,
        ]
    )

    digest = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()

    return f"audit_{digest[:32]}"


# ============================================================
# BUILD FROM SECURITY EVENT
# ============================================================


def create_audit_evidence(
    *,
    event: SecurityEvent,
    decision: str,
    reason: str,
    audit_id: str | None = None,
    behavioral_evidence: Mapping[str, Any] | None = None,
    cross_context_evidence: Mapping[str, Any] | None = None,
    policy_evidence: Mapping[str, Any] | None = None,
    triggered_rules: list[Any]
    | tuple[Any, ...]
    | None = None,
    source: str | None = None,
) -> AuditEvidenceRecord:
    """
    Create an audit evidence record from a canonical
    SecurityEvent.

    The event is the source of truth for:

    - event ID
    - timestamp
    - agent ID
    - risk score
    - anomaly score

    Additional evidence is explicitly supplied by the
    analysis/decision pipeline.
    """

    if not isinstance(
        event,
        SecurityEvent,
    ):
        raise TypeError(
            "event must be a SecurityEvent"
        )

    normalized_behavioral_evidence = (
        _normalize_mapping(
            behavioral_evidence,
            "behavioral_evidence",
        )
    )

    normalized_cross_context_evidence = (
        _normalize_mapping(
            cross_context_evidence,
            "cross_context_evidence",
        )
    )

    normalized_policy_evidence = (
        _normalize_mapping(
            policy_evidence,
            "policy_evidence",
        )
    )

    normalized_triggered_rules = _normalize_list(
        triggered_rules,
        "triggered_rules",
    )

    if audit_id is None:
        audit_id = generate_audit_id(
            event_id=event.event_id,
            decision=decision,
            timestamp=event.timestamp,
        )

    return AuditEvidenceRecord(
        audit_id=audit_id,
        event_id=event.event_id,
        timestamp=event.timestamp,
        agent_id=event.agent_id,
        decision=decision,
        reason=reason,
        risk_score=event.risk_score,
        anomaly_score=event.anomaly_score,
        behavioral_evidence=(
            normalized_behavioral_evidence
        ),
        cross_context_evidence=(
            normalized_cross_context_evidence
        ),
        policy_evidence=(
            normalized_policy_evidence
        ),
        triggered_rules=(
            normalized_triggered_rules
        ),
        source=source,
    )


# ============================================================
# DESERIALIZATION
# ============================================================


def audit_evidence_from_dict(
    data: Mapping[str, Any],
) -> AuditEvidenceRecord:
    """Construct an audit record from a dictionary."""

    if not isinstance(data, Mapping):
        raise TypeError(
            "data must be a mapping"
        )

    required = {
        "audit_id",
        "event_id",
        "timestamp",
        "agent_id",
        "decision",
        "reason",
        "risk_score",
        "anomaly_score",
    }

    missing = (
        required
        - set(data.keys())
    )

    if missing:
        raise ValueError(
            "Missing required audit fields: "
            + ", ".join(
                sorted(missing)
            )
        )

    return AuditEvidenceRecord(
        audit_id=data["audit_id"],
        event_id=data["event_id"],
        timestamp=data["timestamp"],
        agent_id=data["agent_id"],
        decision=data["decision"],
        reason=data["reason"],
        risk_score=data["risk_score"],
        anomaly_score=data[
            "anomaly_score"
        ],
        behavioral_evidence=data.get(
            "behavioral_evidence"
        ),
        cross_context_evidence=data.get(
            "cross_context_evidence"
        ),
        policy_evidence=data.get(
            "policy_evidence"
        ),
        triggered_rules=data.get(
            "triggered_rules"
        ),
        source=data.get(
            "source"
        ),
        event_schema_version=data.get(
            "event_schema_version",
            EVENT_SCHEMA_VERSION,
        ),
        schema_name=data.get(
            "schema_name",
            AUDIT_SCHEMA_NAME,
        ),
        schema_version=data.get(
            "schema_version",
            AUDIT_SCHEMA_VERSION,
        ),
    )


def audit_evidence_from_json(
    value: str,
) -> AuditEvidenceRecord:
    """Construct an audit record from JSON."""

    if not isinstance(value, str):
        raise TypeError(
            "JSON input must be a string"
        )

    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Invalid JSON"
        ) from exc

    return audit_evidence_from_dict(
        data
    )


# ============================================================
# EVENT -> AUDIT CONVERSION
# ============================================================


def create_audit_from_event(
    event: SecurityEvent,
    *,
    decision: str,
    reason: str,
    triggered_rules: list[Any]
    | tuple[Any, ...]
    | None = None,
) -> AuditEvidenceRecord:
    """
    Convenience wrapper for creating an audit record directly
    from a SecurityEvent.
    """

    return create_audit_evidence(
        event=event,
        decision=decision,
        reason=reason,
        triggered_rules=triggered_rules,
    )


# ============================================================
# EVIDENCE SUMMARY
# ============================================================


def build_evidence_summary(
    record: AuditEvidenceRecord,
) -> dict[str, Any]:
    """
    Produce a compact evidence summary suitable for dashboards,
    investigation views, and research reports.
    """

    if not isinstance(
        record,
        AuditEvidenceRecord,
    ):
        raise TypeError(
            "record must be an AuditEvidenceRecord"
        )

    return {
        "audit_id": record.audit_id,
        "event_id": record.event_id,
        "agent_id": record.agent_id,
        "decision": record.decision,
        "risk_score": record.risk_score,
        "anomaly_score": record.anomaly_score,
        "behavioral_evidence_count": len(
            record.behavioral_evidence
        ),
        "cross_context_evidence_count": len(
            record.cross_context_evidence
        ),
        "policy_evidence_count": len(
            record.policy_evidence
        ),
        "triggered_rule_count": len(
            record.triggered_rules
        ),
        "source": record.source,
    }


# ============================================================
# EVIDENCE INTEGRITY
# ============================================================


def calculate_evidence_fingerprint(
    record: AuditEvidenceRecord,
) -> str:
    """
    Calculate a SHA-256 fingerprint of the canonical audit
    record.

    This provides integrity evidence for the serialized
    representation.

    It is NOT a digital signature and does not prove who
    created the record.
    """

    if not isinstance(
        record,
        AuditEvidenceRecord,
    ):
        raise TypeError(
            "record must be an AuditEvidenceRecord"
        )

    payload = record.to_json()

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


# ============================================================
# VALIDATION
# ============================================================


def validate_audit_evidence(
    record: AuditEvidenceRecord,
) -> bool:
    """
    Validate an AuditEvidenceRecord.
    """

    if not isinstance(
        record,
        AuditEvidenceRecord,
    ):
        raise TypeError(
            "record must be an AuditEvidenceRecord"
        )

    record.__post_init__()

    return True


# ============================================================
# PUBLIC API
# ============================================================


__all__ = [
    "AUDIT_SCHEMA_NAME",
    "AUDIT_SCHEMA_VERSION",
    "AuditEvidenceRecord",
    "generate_audit_id",
    "create_audit_evidence",
    "create_audit_from_event",
    "audit_evidence_from_dict",
    "audit_evidence_from_json",
    "build_evidence_summary",
    "calculate_evidence_fingerprint",
    "validate_audit_evidence",
]