"""
Varynx Day 40
Canonical Security Event Schema

Defines the canonical event contract used by Varynx security-analysis
components.

Engineering principles:
1. Security events have a predictable structure.
2. Validation occurs at the system boundary.
3. Invalid data fails explicitly.
4. Optional evidence remains optional.
5. Schema versioning is explicit.
6. Serialization is deterministic.
7. The schema does not itself make security decisions.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


# ============================================================
# CONSTANTS
# ============================================================

SCHEMA_NAME = "varnyx.security_event"
SCHEMA_VERSION = "1.0"

MAX_TEXT_LENGTH = 512
MAX_AGENT_ID_LENGTH = 128
MAX_RESOURCE_LENGTH = 512
MAX_CONTEXT_LENGTH = 256
MAX_ACTION_LENGTH = 128


# ============================================================
# VALIDATION HELPERS
# ============================================================


def _require_text(
    value: Any,
    field_name: str,
    *,
    max_length: int,
) -> str:
    """Validate and normalize a required text field."""

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


def _optional_text(
    value: Any,
    field_name: str,
    *,
    max_length: int,
) -> str | None:
    """Validate an optional text field."""

    if value is None:
        return None

    return _require_text(
        value,
        field_name,
        max_length=max_length,
    )


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
    """
    Validate an ISO-8601 timestamp.

    Naive timestamps are rejected because security events
    require an unambiguous timezone.
    """

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
    Validate and normalize an optional mapping.

    IMPORTANT:
    Validation happens before dict(value) conversion.

    This prevents malformed values such as:
        ["invalid"]

    from producing confusing Python ValueErrors such as:
        dictionary update sequence element #0 ...
    """

    if value is None:
        return {}

    if not isinstance(value, Mapping):
        raise TypeError(
            f"{field_name} must be a mapping"
        )

    return dict(value)


# ============================================================
# SECURITY EVENT
# ============================================================


@dataclass(frozen=True)
class SecurityEvent:
    """
    Canonical Varynx security event.

    Required fields:
        event_id
        timestamp
        agent_id
        action
        resource
        context
        risk_score
        anomaly_score

    Optional evidence:
        capability
        decision
        reason
        source
        behavioral_evidence
        cross_context_evidence
        metadata
    """

    event_id: str
    timestamp: datetime

    agent_id: str
    action: str
    resource: str
    context: str

    risk_score: float
    anomaly_score: float

    capability: str | None = None
    decision: str | None = None
    reason: str | None = None
    source: str | None = None

    behavioral_evidence: dict[str, Any] = field(
        default_factory=dict
    )

    cross_context_evidence: dict[str, Any] = field(
        default_factory=dict
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Validate the event immediately after construction."""

        object.__setattr__(
            self,
            "event_id",
            _require_text(
                self.event_id,
                "event_id",
                max_length=128,
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
                max_length=MAX_AGENT_ID_LENGTH,
            ),
        )

        object.__setattr__(
            self,
            "action",
            _require_text(
                self.action,
                "action",
                max_length=MAX_ACTION_LENGTH,
            ),
        )

        object.__setattr__(
            self,
            "resource",
            _require_text(
                self.resource,
                "resource",
                max_length=MAX_RESOURCE_LENGTH,
            ),
        )

        object.__setattr__(
            self,
            "context",
            _require_text(
                self.context,
                "context",
                max_length=MAX_CONTEXT_LENGTH,
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
            "capability",
            _optional_text(
                self.capability,
                "capability",
                max_length=MAX_TEXT_LENGTH,
            ),
        )

        object.__setattr__(
            self,
            "decision",
            _optional_text(
                self.decision,
                "decision",
                max_length=MAX_TEXT_LENGTH,
            ),
        )

        object.__setattr__(
            self,
            "reason",
            _optional_text(
                self.reason,
                "reason",
                max_length=MAX_TEXT_LENGTH,
            ),
        )

        object.__setattr__(
            self,
            "source",
            _optional_text(
                self.source,
                "source",
                max_length=MAX_TEXT_LENGTH,
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
            "metadata",
            _normalize_mapping(
                self.metadata,
                "metadata",
            ),
        )

        if self.schema_name != SCHEMA_NAME:
            raise ValueError(
                "Unsupported schema name"
            )

        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                "Unsupported schema version"
            )

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(self) -> dict[str, Any]:
        """Convert the event to a JSON-compatible dictionary."""

        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "action": self.action,
            "resource": self.resource,
            "context": self.context,
            "capability": self.capability,
            "decision": self.decision,
            "reason": self.reason,
            "source": self.source,
            "risk_score": self.risk_score,
            "anomaly_score": self.anomaly_score,
            "behavioral_evidence": dict(
                self.behavioral_evidence
            ),
            "cross_context_evidence": dict(
                self.cross_context_evidence
            ),
            "metadata": dict(
                self.metadata
            ),
        }

    def to_json(self) -> str:
        """Produce deterministic JSON."""

        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )

    # ========================================================
    # DESERIALIZATION
    # ========================================================

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
    ) -> "SecurityEvent":
        """Construct a SecurityEvent from a mapping."""

        if not isinstance(data, Mapping):
            raise TypeError(
                "data must be a mapping"
            )

        required = {
            "event_id",
            "timestamp",
            "agent_id",
            "action",
            "resource",
            "context",
            "risk_score",
            "anomaly_score",
        }

        missing = (
            required
            - set(data.keys())
        )

        if missing:
            raise ValueError(
                "Missing required event fields: "
                + ", ".join(
                    sorted(missing)
                )
            )

        schema_name = data.get(
            "schema_name",
            SCHEMA_NAME,
        )

        schema_version = data.get(
            "schema_version",
            SCHEMA_VERSION,
        )

        return cls(
            event_id=data["event_id"],
            timestamp=data["timestamp"],
            agent_id=data["agent_id"],
            action=data["action"],
            resource=data["resource"],
            context=data["context"],
            risk_score=data["risk_score"],
            anomaly_score=data["anomaly_score"],
            capability=data.get(
                "capability"
            ),
            decision=data.get(
                "decision"
            ),
            reason=data.get(
                "reason"
            ),
            source=data.get(
                "source"
            ),
            behavioral_evidence=data.get(
                "behavioral_evidence"
            ),
            cross_context_evidence=data.get(
                "cross_context_evidence"
            ),
            metadata=data.get(
                "metadata"
            ),
            schema_name=schema_name,
            schema_version=schema_version,
        )

    @classmethod
    def from_json(
        cls,
        value: str,
    ) -> "SecurityEvent":
        """Construct an event from JSON."""

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

        return cls.from_dict(data)


# ============================================================
# EVENT ID
# ============================================================


def generate_event_id(
    *,
    timestamp: datetime,
    agent_id: str,
    action: str,
    resource: str,
    context: str,
) -> str:
    """
    Generate a deterministic event identifier.

    Useful for reproducible experimental datasets.
    """

    normalized_timestamp = _validate_timestamp(
        timestamp
    ).isoformat()

    canonical = "|".join(
        [
            normalized_timestamp,
            str(agent_id).strip(),
            str(action).strip(),
            str(resource).strip(),
            str(context).strip(),
        ]
    )

    digest = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()

    return f"evt_{digest[:32]}"


# ============================================================
# FACTORY
# ============================================================


def create_security_event(
    *,
    timestamp: datetime | str,
    agent_id: str,
    action: str,
    resource: str,
    context: str,
    risk_score: float,
    anomaly_score: float,
    event_id: str | None = None,
    capability: str | None = None,
    decision: str | None = None,
    reason: str | None = None,
    source: str | None = None,
    behavioral_evidence: Mapping[str, Any] | None = None,
    cross_context_evidence: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> SecurityEvent:
    """
    Construct a canonical SecurityEvent.

    Invalid mappings are rejected before conversion.
    """

    parsed_timestamp = _validate_timestamp(
        timestamp
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Validate evidence BEFORE constructing SecurityEvent.
    # This guarantees predictable TypeError behaviour.
    # --------------------------------------------------------

    normalized_behavioral_evidence = _normalize_mapping(
        behavioral_evidence,
        "behavioral_evidence",
    )

    normalized_cross_context_evidence = _normalize_mapping(
        cross_context_evidence,
        "cross_context_evidence",
    )

    normalized_metadata = _normalize_mapping(
        metadata,
        "metadata",
    )

    if event_id is None:
        event_id = generate_event_id(
            timestamp=parsed_timestamp,
            agent_id=agent_id,
            action=action,
            resource=resource,
            context=context,
        )

    return SecurityEvent(
        event_id=event_id,
        timestamp=parsed_timestamp,
        agent_id=agent_id,
        action=action,
        resource=resource,
        context=context,
        risk_score=risk_score,
        anomaly_score=anomaly_score,
        capability=capability,
        decision=decision,
        reason=reason,
        source=source,
        behavioral_evidence=normalized_behavioral_evidence,
        cross_context_evidence=normalized_cross_context_evidence,
        metadata=normalized_metadata,
    )


# ============================================================
# SCHEMA UTILITIES
# ============================================================


def validate_event(
    event: SecurityEvent,
) -> bool:
    """
    Validate an already constructed event.
    """

    if not isinstance(
        event,
        SecurityEvent,
    ):
        raise TypeError(
            "event must be a SecurityEvent"
        )

    event.__post_init__()

    return True


def canonicalize_event(
    data: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Convert input into canonical event representation.
    """

    event = SecurityEvent.from_dict(
        data
    )

    return event.to_dict()


def get_schema_metadata() -> dict[str, str]:
    """Return schema identification metadata."""

    return {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
    }


__all__ = [
    "SCHEMA_NAME",
    "SCHEMA_VERSION",
    "SecurityEvent",
    "create_security_event",
    "generate_event_id",
    "validate_event",
    "canonicalize_event",
    "get_schema_metadata",
]