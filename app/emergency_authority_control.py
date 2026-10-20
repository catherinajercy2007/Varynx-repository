
"""Varynx Day 87: Runtime Kill Switch and Emergency Authority Revocation.

Defines emergency control state and enforcement handoff signals.
This module does not itself stop an agent or enforce a capability denial.

IMPORTANT:
- State is in-memory only.
- A production deployment needs durable storage, authenticated operator
  actions, concurrency control, and integration with Member 2's enforcer.
- Releasing a control requires an explicit operator action and reason.
- Emergency controls never auto-release based on elapsed time.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


VERSION = "DAY87-V1"


class ControlTarget(str, Enum):
    GLOBAL = "GLOBAL"
    AGENT = "AGENT"
    CAPABILITY = "CAPABILITY"


class ControlState(str, Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"


class EmergencyEventType(str, Enum):
    KILL_SWITCH_ACTIVATED = "KILL_SWITCH_ACTIVATED"
    AGENT_AUTHORITY_REVOKED = "AGENT_AUTHORITY_REVOKED"
    CAPABILITY_AUTHORITY_REVOKED = "CAPABILITY_AUTHORITY_REVOKED"
    CONTROL_RELEASED = "CONTROL_RELEASED"


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value


@dataclass(frozen=True)
class EmergencyControl:
    """One active or released emergency control record."""

    control_id: str
    target_type: ControlTarget
    target_id: str
    state: ControlState
    reason: str
    activated_by: str
    activated_at: datetime
    released_by: str | None = None
    released_at: datetime | None = None
    release_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["version"] = VERSION
        result["target_type"] = self.target_type.value
        result["state"] = self.state.value
        result["activated_at"] = self.activated_at.isoformat()
        result["released_at"] = (
            self.released_at.isoformat() if self.released_at else None
        )
        result["is_authorization_decision"] = False
        result["executes_enforcement"] = False
        return result


@dataclass(frozen=True)
class EmergencyControlEvent:
    """Audit-friendly event describing a control-state transition."""

    event_id: str
    event_type: EmergencyEventType
    control_id: str
    target_type: ControlTarget
    target_id: str
    actor_id: str
    reason: str
    occurred_at: datetime

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["version"] = VERSION
        result["event_type"] = self.event_type.value
        result["target_type"] = self.target_type.value
        result["occurred_at"] = self.occurred_at.isoformat()
        return result


@dataclass(frozen=True)
class EmergencyControlAssessment:
    """Assessment for the enforcement layer to consume."""

    blocked_by_emergency_control: bool
    matching_control_ids: tuple[str, ...]
    target_type: ControlTarget
    target_id: str
    assessed_at: datetime
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["version"] = VERSION
        result["target_type"] = self.target_type.value
        result["assessed_at"] = self.assessed_at.isoformat()
        result["matching_control_ids"] = list(self.matching_control_ids)
        result["reason_codes"] = list(self.reason_codes)
        result["is_authorization_decision"] = False
        result["executes_enforcement"] = False
        return result


class EmergencyAuthorityControl:
    """In-memory emergency-control registry with explicit release.

    The registry is a signal source, not a security boundary by itself.
    Runtime enforcement must query this state or consume its events.
    """

    def __init__(self) -> None:
        self._controls: dict[str, EmergencyControl] = {}
        self._events: list[EmergencyControlEvent] = []

    @property
    def controls(self) -> tuple[EmergencyControl, ...]:
        return tuple(self._controls.values())

    @property
    def events(self) -> tuple[EmergencyControlEvent, ...]:
        return tuple(self._events)

    def _record_event(
        self,
        *,
        event_type: EmergencyEventType,
        control: EmergencyControl,
        actor_id: str,
        reason: str,
        occurred_at: datetime,
    ) -> EmergencyControlEvent:
        event = EmergencyControlEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            control_id=control.control_id,
            target_type=control.target_type,
            target_id=control.target_id,
            actor_id=actor_id,
            reason=reason,
            occurred_at=occurred_at,
        )
        self._events.append(event)
        return event

    def activate(
        self,
        *,
        target_type: ControlTarget,
        target_id: str,
        reason: str,
        actor_id: str,
        now: datetime,
    ) -> EmergencyControl:
        """Activate a global, agent, or capability emergency control."""
        if not isinstance(target_type, ControlTarget):
            raise TypeError("target_type must be a ControlTarget")

        target_id = _text(target_id, "target_id")
        reason = _text(reason, "reason")
        actor_id = _text(actor_id, "actor_id")
        now = _timestamp(now, "now")

        if target_type == ControlTarget.GLOBAL and target_id != "*":
            raise ValueError("GLOBAL target_id must be '*'")
        if target_type != ControlTarget.GLOBAL and target_id == "*":
            raise ValueError("Only GLOBAL controls may use target_id '*'")

        # Idempotency: do not create duplicate active controls for the
        # same target. Preserve the original event/reason for traceability.
        for existing in self._controls.values():
            if (
                existing.state == ControlState.ACTIVE
                and existing.target_type == target_type
                and existing.target_id == target_id
            ):
                return existing

        control = EmergencyControl(
            control_id=str(uuid4()),
            target_type=target_type,
            target_id=target_id,
            state=ControlState.ACTIVE,
            reason=reason,
            activated_by=actor_id,
            activated_at=now,
        )
        self._controls[control.control_id] = control

        event_type = {
            ControlTarget.GLOBAL: EmergencyEventType.KILL_SWITCH_ACTIVATED,
            ControlTarget.AGENT: EmergencyEventType.AGENT_AUTHORITY_REVOKED,
            ControlTarget.CAPABILITY:
                EmergencyEventType.CAPABILITY_AUTHORITY_REVOKED,
        }[target_type]

        self._record_event(
            event_type=event_type,
            control=control,
            actor_id=actor_id,
            reason=reason,
            occurred_at=now,
        )
        return control

    def release(
        self,
        *,
        control_id: str,
        actor_id: str,
        reason: str,
        now: datetime,
    ) -> EmergencyControl:
        """Release a control only through an explicit operator action."""
        control_id = _text(control_id, "control_id")
        actor_id = _text(actor_id, "actor_id")
        reason = _text(reason, "reason")
        now = _timestamp(now, "now")

        if control_id not in self._controls:
            raise KeyError(f"Unknown control_id: {control_id}")

        existing = self._controls[control_id]
        if existing.state == ControlState.RELEASED:
            raise ValueError("Control has already been released")
        if now < existing.activated_at:
            raise ValueError("release time cannot precede activation time")

        released = EmergencyControl(
            control_id=existing.control_id,
            target_type=existing.target_type,
            target_id=existing.target_id,
            state=ControlState.RELEASED,
            reason=existing.reason,
            activated_by=existing.activated_by,
            activated_at=existing.activated_at,
            released_by=actor_id,
            released_at=now,
            release_reason=reason,
        )
        self._controls[control_id] = released
        self._record_event(
            event_type=EmergencyEventType.CONTROL_RELEASED,
            control=released,
            actor_id=actor_id,
            reason=reason,
            occurred_at=now,
        )
        return released

    def assess(
        self,
        *,
        agent_id: str,
        capability: str,
        now: datetime,
    ) -> EmergencyControlAssessment:
        """Return active controls matching the agent/capability request."""
        agent_id = _text(agent_id, "agent_id")
        capability = _text(capability, "capability")
        now = _timestamp(now, "now")

        matching: list[EmergencyControl] = []
        for control in self._controls.values():
            if control.state != ControlState.ACTIVE:
                continue
            if control.activated_at > now:
                continue

            if control.target_type == ControlTarget.GLOBAL:
                matching.append(control)
            elif (
                control.target_type == ControlTarget.AGENT
                and control.target_id == agent_id
            ):
                matching.append(control)
            elif (
                control.target_type == ControlTarget.CAPABILITY
                and control.target_id == capability
            ):
                matching.append(control)

        matching.sort(key=lambda item: item.control_id)
        reason_codes = tuple(
            {
                ControlTarget.GLOBAL: "GLOBAL_KILL_SWITCH_ACTIVE",
                ControlTarget.AGENT: "AGENT_AUTHORITY_REVOKED",
                ControlTarget.CAPABILITY: "CAPABILITY_AUTHORITY_REVOKED",
            }[control.target_type]
            for control in matching
        )

        return EmergencyControlAssessment(
            blocked_by_emergency_control=bool(matching),
            matching_control_ids=tuple(
                control.control_id for control in matching
            ),
            target_type=ControlTarget.AGENT,
            target_id=agent_id,
            assessed_at=now,
            reason_codes=reason_codes,
        )

    def enforcement_signal(
        self,
        *,
        agent_id: str,
        capability: str,
        now: datetime,
    ) -> dict[str, Any]:
        """Build a handoff payload; this does not execute enforcement."""
        assessment = self.assess(
            agent_id=agent_id,
            capability=capability,
            now=now,
        )
        return {
            "version": VERSION,
            "signal_type": "EMERGENCY_CONTROL_ASSESSMENT",
            "agent_id": agent_id,
            "capability": capability,
            "blocked_by_emergency_control":
                assessment.blocked_by_emergency_control,
            "matching_control_ids": list(assessment.matching_control_ids),
            "reason_codes": list(assessment.reason_codes),
            "assessed_at": assessment.assessed_at.isoformat(),
            "enforcement_executed": False,
            "authorization_decision_made": False,
        }


__all__ = [
    "VERSION",
    "ControlTarget",
    "ControlState",
    "EmergencyEventType",
    "EmergencyControl",
    "EmergencyControlEvent",
    "EmergencyControlAssessment",
    "EmergencyAuthorityControl",
]
