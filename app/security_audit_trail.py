"""
Varynx Day 68 - Security Decision Audit Trail.

Provides an append-oriented, immutable audit trail for security decision
and enforcement-boundary events.

This module records existing evidence.

It does NOT:
- create security decisions
- modify security decisions
- execute enforcement
- modify authorization
- modify adaptive response
- modify policy
- infer malicious intent
- create a universal security score
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping, Optional


# ---------------------------------------------------------------------------
# Audit event types
# ---------------------------------------------------------------------------

AUDIT_BEHAVIORAL = "BEHAVIORAL_EVIDENCE"
AUDIT_PREDICTIVE = "PREDICTIVE_SIGNAL"
AUDIT_DECISION = "SECURITY_DECISION"
AUDIT_RECONCILIATION = "DECISION_RECONCILIATION"
AUDIT_RUNTIME = "RUNTIME_SECURITY"
AUDIT_ENFORCEMENT = "ENFORCEMENT_REQUEST"
AUDIT_VALIDATION = "ENFORCEMENT_VALIDATION"
AUDIT_PROVENANCE = "SECURITY_PROVENANCE"

VALID_AUDIT_EVENT_TYPES = frozenset(
    {
        AUDIT_BEHAVIORAL,
        AUDIT_PREDICTIVE,
        AUDIT_DECISION,
        AUDIT_RECONCILIATION,
        AUDIT_RUNTIME,
        AUDIT_ENFORCEMENT,
        AUDIT_VALIDATION,
        AUDIT_PROVENANCE,
    }
)


# ---------------------------------------------------------------------------
# Audit statuses
# ---------------------------------------------------------------------------

AUDIT_RECORDED = "AUDIT_RECORDED"
AUDIT_PARTIAL = "AUDIT_PARTIAL"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validate_text(
    value: str,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string"
        )

    if not value.strip():
        raise ValueError(
            f"{field_name} must not be empty"
        )

    return value.strip()


def _validate_mapping(
    value: Optional[Mapping[str, Any]],
    field_name: str,
) -> dict[str, Any]:
    if value is None:
        return {}

    if not isinstance(value, Mapping):
        raise TypeError(
            f"{field_name} must be a mapping or None"
        )

    return deepcopy(dict(value))


def _validate_event_type(
    event_type: str,
) -> str:
    event_type = _validate_text(
        event_type,
        "event_type",
    )

    if event_type not in VALID_AUDIT_EVENT_TYPES:
        raise ValueError(
            f"Unsupported audit event type: {event_type}"
        )

    return event_type


def _validate_sequence(
    sequence_number: int,
) -> int:
    if isinstance(sequence_number, bool):
        raise TypeError(
            "sequence_number must be an integer"
        )

    if not isinstance(sequence_number, int):
        raise TypeError(
            "sequence_number must be an integer"
        )

    if sequence_number < 1:
        raise ValueError(
            "sequence_number must be greater than zero"
        )

    return sequence_number


# ---------------------------------------------------------------------------
# Audit event
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SecurityAuditEvent:
    """
    Immutable audit event.

    The event records what was observed or produced by an existing Varynx
    stage. It does not execute or reinterpret that stage.
    """

    audit_id: str
    agent_id: str
    request_id: str

    sequence_number: int
    event_type: str

    decision: Optional[str]
    status: str

    evidence: dict[str, Any]

    execution_performed_here: bool


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------


class SecurityDecisionAuditTrail:
    """
    Append-oriented audit trail for Varynx security events.

    The trail:
    - preserves insertion order
    - assigns per-agent sequence numbers
    - creates immutable events
    - keeps agent histories isolated
    - supports latest/history/snapshot
    - supports filtering by request and event type

    It does not perform enforcement.
    """

    def __init__(self) -> None:
        self._events: dict[
            str,
            list[SecurityAuditEvent],
        ] = {}

        self._counters: dict[str, int] = {}

    # ------------------------------------------------------------------
    # Audit ID
    # ------------------------------------------------------------------

    def _next_sequence(
        self,
        agent_id: str,
    ) -> int:
        sequence = (
            self._counters.get(agent_id, 0)
            + 1
        )

        self._counters[agent_id] = sequence

        return sequence

    def _build_audit_id(
        self,
        agent_id: str,
        sequence_number: int,
    ) -> str:
        return (
            f"{agent_id}-audit-{sequence_number}"
        )

    # ------------------------------------------------------------------
    # Record event
    # ------------------------------------------------------------------

    def record(
        self,
        *,
        agent_id: str,
        request_id: str,
        event_type: str,
        decision: Optional[str] = None,
        status: str = AUDIT_RECORDED,
        evidence: Optional[Mapping[str, Any]] = None,
    ) -> SecurityAuditEvent:
        """
        Record an existing security event.

        No security decision is generated here.
        No enforcement is performed here.
        """

        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        request_id = _validate_text(
            request_id,
            "request_id",
        )

        event_type = _validate_event_type(
            event_type
        )

        status = _validate_text(
            status,
            "status",
        )

        if decision is not None:
            decision = _validate_text(
                decision,
                "decision",
            )

        sequence_number = self._next_sequence(
            agent_id
        )

        event = SecurityAuditEvent(
            audit_id=self._build_audit_id(
                agent_id,
                sequence_number,
            ),
            agent_id=agent_id,
            request_id=request_id,
            sequence_number=sequence_number,
            event_type=event_type,
            decision=decision,
            status=status,
            evidence=_validate_mapping(
                evidence,
                "evidence",
            ),
            execution_performed_here=False,
        )

        self._events.setdefault(
            agent_id,
            [],
        ).append(event)

        return event

    # ------------------------------------------------------------------
    # Query operations
    # ------------------------------------------------------------------

    def latest(
        self,
        agent_id: str,
    ) -> Optional[SecurityAuditEvent]:
        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        events = self._events.get(
            agent_id
        )

        if not events:
            return None

        return events[-1]

    def history(
        self,
        agent_id: str,
    ) -> tuple[SecurityAuditEvent, ...]:
        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        return tuple(
            self._events.get(
                agent_id,
                (),
            )
        )

    def snapshot_all(
        self,
    ) -> dict[
        str,
        tuple[SecurityAuditEvent, ...],
    ]:
        return {
            agent_id: tuple(events)
            for agent_id, events
            in self._events.items()
        }

    def by_request(
        self,
        request_id: str,
    ) -> tuple[SecurityAuditEvent, ...]:
        request_id = _validate_text(
            request_id,
            "request_id",
        )

        matches: list[
            SecurityAuditEvent
        ] = []

        for events in self._events.values():
            for event in events:
                if event.request_id == request_id:
                    matches.append(event)

        return tuple(matches)

    def by_event_type(
        self,
        agent_id: str,
        event_type: str,
    ) -> tuple[SecurityAuditEvent, ...]:
        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        event_type = _validate_event_type(
            event_type
        )

        return tuple(
            event
            for event in self._events.get(
                agent_id,
                (),
            )
            if event.event_type == event_type
        )

    def count(
        self,
        agent_id: str,
    ) -> int:
        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        return len(
            self._events.get(
                agent_id,
                (),
            )
        )

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(
        self,
        agent_id: Optional[str] = None,
    ) -> None:
        if agent_id is None:
            self._events.clear()
            self._counters.clear()
            return

        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        self._events.pop(
            agent_id,
            None,
        )

        self._counters.pop(
            agent_id,
            None,
        )


# ---------------------------------------------------------------------------
# Audit summary
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuditTrailSummary:
    """
    Immutable summary of an agent's audit history.
    """

    agent_id: str
    event_count: int
    event_types: tuple[str, ...]
    request_ids: tuple[str, ...]
    decisions: tuple[str, ...]


def summarize_audit_history(
    events: tuple[
        SecurityAuditEvent,
        ...
    ],
) -> AuditTrailSummary:
    if not isinstance(events, tuple):
        raise TypeError(
            "events must be a tuple of SecurityAuditEvent"
        )

    for event in events:
        if not isinstance(
            event,
            SecurityAuditEvent,
        ):
            raise TypeError(
                "events must contain SecurityAuditEvent objects"
            )

    if not events:
        raise ValueError(
            "events must not be empty"
        )

    event_types = tuple(
        dict.fromkeys(
            event.event_type
            for event in events
        )
    )

    request_ids = tuple(
        dict.fromkeys(
            event.request_id
            for event in events
        )
    )

    decisions = tuple(
        dict.fromkeys(
            event.decision
            for event in events
            if event.decision is not None
        )
    )

    return AuditTrailSummary(
        agent_id=events[0].agent_id,
        event_count=len(events),
        event_types=event_types,
        request_ids=request_ids,
        decisions=decisions,
    )


# ---------------------------------------------------------------------------
# Architectural invariants
# ---------------------------------------------------------------------------


def decision_is_modified_here() -> bool:
    """
    Day 68 records decisions but never modifies them.
    """

    return False


def enforcement_is_executed_here() -> bool:
    """
    Day 68 never performs enforcement.
    """

    return False