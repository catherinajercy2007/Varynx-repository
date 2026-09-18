"""
Varynx System
=============

Day 75 — Functional System Validation

This module provides a thin orchestration and validation boundary for
the existing Varynx security pipeline.

Architectural purpose
---------------------
Day 75 does NOT replace existing security components.

It provides a common system-level representation of:

    behavioral evidence
            ↓
    behavioral intelligence
            ↓
    dynamic behavioral trust
            ↓
    predictive / counterfactual analysis
            ↓
    security response
            ↓
    evidence preservation
            ↓
    timeline
            ↓
    correlation
            ↓
    incident reconstruction

Security boundaries
-------------------
This module does NOT:

- create a new universal risk score
- modify authorization decisions
- execute enforcement
- infer malicious intent
- claim exact attacker behavior
- replace adaptive_response.py
- replace security_evidence_timeline.py
- replace security_evidence_correlation.py

It is intentionally deterministic and evidence-oriented.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Mapping, Optional, Sequence

from app.security_evidence_correlation import (
    SecurityEvidenceCorrelation,
    SecurityEvidenceCorrelationEngine,
    SecurityIncidentReconstruction,
    create_evidence_entry,
)
from app.security_evidence_timeline import (
    SecurityEvidenceTimeline,
    SecurityEvidenceTimelineBuilder,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SYSTEM_VALIDATED = "VALIDATED"
SYSTEM_PARTIAL = "PARTIAL"

BEHAVIORAL_STAGE = "BEHAVIORAL"
TRUST_STAGE = "TRUST"
PREDICTIVE_STAGE = "PREDICTIVE"
DECISION_STAGE = "DECISION"
ENFORCEMENT_STAGE = "ENFORCEMENT"
AUDIT_STAGE = "AUDIT"
SNAPSHOT_STAGE = "SNAPSHOT"
TIMELINE_STAGE = "TIMELINE"
CORRELATION_STAGE = "CORRELATION"
INCIDENT_STAGE = "INCIDENT"

SUPPORTED_STAGES = (
    BEHAVIORAL_STAGE,
    TRUST_STAGE,
    PREDICTIVE_STAGE,
    DECISION_STAGE,
    ENFORCEMENT_STAGE,
    AUDIT_STAGE,
    SNAPSHOT_STAGE,
    TIMELINE_STAGE,
    CORRELATION_STAGE,
    INCIDENT_STAGE,
)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _validate_text(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")

    value = value.strip()

    if not value:
        raise ValueError(f"{name} must not be empty")

    return value


def _copy_mapping(
    value: Optional[Mapping[str, Any]],
) -> dict[str, Any]:
    if value is None:
        return {}

    if not isinstance(value, Mapping):
        raise TypeError("context/evidence must be a mapping")

    return dict(value)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _deterministic_id(
    prefix: str,
    *parts: Any,
) -> str:
    payload = "|".join(str(part) for part in parts)

    digest = sha256(
        payload.encode("utf-8")
    ).hexdigest()[:16]

    return f"{prefix}-{digest}"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VarynxEvent:
    """
    Immutable representation of one system-level Varynx observation.
    """

    event_id: str
    agent_id: str
    stage: str
    event_type: str
    request_id: Optional[str]
    decision: Optional[str]
    timestamp: str
    evidence: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        _validate_text(self.event_id, "event_id")
        _validate_text(self.agent_id, "agent_id")
        _validate_text(self.stage, "stage")
        _validate_text(self.event_type, "event_type")
        _validate_text(self.timestamp, "timestamp")

        if self.request_id is not None:
            _validate_text(
                self.request_id,
                "request_id",
            )

        if self.decision is not None:
            _validate_text(
                self.decision,
                "decision",
            )

        if not isinstance(self.evidence, Mapping):
            raise TypeError(
                "evidence must be a mapping"
            )


@dataclass(frozen=True)
class VarynxSystemResult:
    """
    Immutable system-level result.

    This object intentionally contains evidence and stage information
    rather than introducing a new universal security score.
    """

    result_id: str
    agent_id: str
    request_id: Optional[str]
    status: str

    stages_present: tuple[str, ...]
    stages_missing: tuple[str, ...]

    events: tuple[VarynxEvent, ...]

    timeline: Optional[SecurityEvidenceTimeline]
    correlation: Optional[SecurityEvidenceCorrelation]
    incident: Optional[SecurityIncidentReconstruction]

    evidence: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if self.status not in (
            SYSTEM_VALIDATED,
            SYSTEM_PARTIAL,
        ):
            raise ValueError(
                "invalid system result status"
            )


# ---------------------------------------------------------------------------
# Main system
# ---------------------------------------------------------------------------

class VarynxSystem:
    """
    Day 75 Varynx orchestration boundary.

    The class coordinates existing evidence-oriented components without
    replacing their responsibilities.
    """

    def __init__(
        self,
        *,
        timeline_builder: Optional[
            SecurityEvidenceTimelineBuilder
        ] = None,
        correlation_engine: Optional[
            SecurityEvidenceCorrelationEngine
        ] = None,
    ) -> None:
        self._timeline_builder = (
            timeline_builder
            if timeline_builder is not None
            else SecurityEvidenceTimelineBuilder()
        )

        self._correlation_engine = (
            correlation_engine
            if correlation_engine is not None
            else SecurityEvidenceCorrelationEngine()
        )

        self._history: dict[
            str,
            VarynxSystemResult,
        ] = {}

    # ------------------------------------------------------------------
    # Basic properties
    # ------------------------------------------------------------------

    @property
    def timeline_builder(
        self,
    ) -> SecurityEvidenceTimelineBuilder:
        return self._timeline_builder

    @property
    def correlation_engine(
        self,
    ) -> SecurityEvidenceCorrelationEngine:
        return self._correlation_engine

    # ------------------------------------------------------------------
    # Event construction
    # ------------------------------------------------------------------

    def create_event(
        self,
        *,
        agent_id: str,
        stage: str,
        event_type: str,
        request_id: Optional[str] = None,
        decision: Optional[str] = None,
        timestamp: Optional[str] = None,
        evidence: Optional[Mapping[str, Any]] = None,
    ) -> VarynxEvent:
        """
        Create a deterministic Varynx event.

        No security decision is made here.
        """

        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        stage = _validate_text(
            stage,
            "stage",
        ).upper()

        event_type = _validate_text(
            event_type,
            "event_type",
        ).upper()

        if request_id is not None:
            request_id = _validate_text(
                request_id,
                "request_id",
            )

        if decision is not None:
            decision = _validate_text(
                decision,
                "decision",
            ).upper()

        timestamp = (
            timestamp
            if timestamp is not None
            else _utc_timestamp()
        )

        evidence_copy = _copy_mapping(
            evidence
        )

        event_id = _deterministic_id(
            "event",
            agent_id,
            stage,
            event_type,
            request_id,
            decision,
            timestamp,
            repr(sorted(evidence_copy.items())),
        )

        return VarynxEvent(
            event_id=event_id,
            agent_id=agent_id,
            stage=stage,
            event_type=event_type,
            request_id=request_id,
            decision=decision,
            timestamp=timestamp,
            evidence=evidence_copy,
        )

    # ------------------------------------------------------------------
    # Event → Day 73 evidence entry
    # ------------------------------------------------------------------

    def _event_to_evidence_entry(
        self,
        *,
        event: VarynxEvent,
        case_id: str,
        sequence_number: int,
    ):
        """
        Convert a Day 75 event into the existing Day 73 evidence-entry
        representation.
        """

        # Day 73 has a restricted source vocabulary. AUDIT is used as
        # the neutral system-observation source here. The original
        # stage is preserved inside evidence.
        evidence = dict(event.evidence)

        evidence["varynx_stage"] = event.stage
        evidence["varynx_event_id"] = event.event_id

        return create_evidence_entry(
            agent_id=event.agent_id,
            case_id=case_id,
            sequence_number=sequence_number,
            source="AUDIT",
            event_type=event.event_type,
            request_id=event.request_id,
            decision=event.decision,
            timestamp=event.timestamp,
            evidence=evidence,
        )

    # ------------------------------------------------------------------
    # Stage analysis
    # ------------------------------------------------------------------

    @staticmethod
    def _stage_summary(
        events: Sequence[VarynxEvent],
    ) -> tuple[
        tuple[str, ...],
        tuple[str, ...],
    ]:
        present = tuple(
            stage
            for stage in SUPPORTED_STAGES
            if any(
                event.stage == stage
                for event in events
            )
        )

        missing = tuple(
            stage
            for stage in SUPPORTED_STAGES
            if stage not in present
        )

        return present, missing

    # ------------------------------------------------------------------
    # System validation
    # ------------------------------------------------------------------

    def validate(
        self,
        *,
        agent_id: str,
        case_id: str,
        events: Sequence[VarynxEvent],
        request_id: Optional[str] = None,
        evidence: Optional[Mapping[str, Any]] = None,
    ) -> VarynxSystemResult:
        """
        Validate an existing sequence of Varynx events.

        The method performs:

        1. event validation
        2. evidence-entry conversion
        3. timeline construction
        4. evidence correlation
        5. incident reconstruction
        6. immutable system-result construction

        It does not execute an agent action.
        """

        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        case_id = _validate_text(
            case_id,
            "case_id",
        )

        if request_id is not None:
            request_id = _validate_text(
                request_id,
                "request_id",
            )

        if not isinstance(events, Sequence):
            raise TypeError(
                "events must be a sequence"
            )

        validated_events: list[VarynxEvent] = []

        for event in events:
            if not isinstance(
                event,
                VarynxEvent,
            ):
                raise TypeError(
                    "events must contain VarynxEvent objects"
                )

            if event.agent_id != agent_id:
                raise ValueError(
                    "event agent_id does not match system agent_id"
                )

            if (
                request_id is not None
                and event.request_id != request_id
            ):
                raise ValueError(
                    "event request_id does not match requested request_id"
                )

            validated_events.append(event)

        validated_events_tuple = tuple(
            validated_events
        )

        # --------------------------------------------------------------
        # Day 73 timeline
        # --------------------------------------------------------------

        evidence_entries = tuple(
            self._event_to_evidence_entry(
                event=event,
                case_id=case_id,
                sequence_number=index,
            )
            for index, event
            in enumerate(
                validated_events_tuple,
                start=1,
            )
        )

        timeline = self._timeline_builder.build_timeline(
            agent_id=agent_id,
            case_id=case_id,
            entries=evidence_entries,
            evidence=_copy_mapping(evidence),
        )

        # --------------------------------------------------------------
        # Day 74 correlation
        # --------------------------------------------------------------

        correlation = (
            self._correlation_engine.correlate(
                timeline
            )
        )

        # --------------------------------------------------------------
        # Incident reconstruction
        # --------------------------------------------------------------

        incident = (
            self._correlation_engine.reconstruct_incident(
                correlation
            )
        )

        # --------------------------------------------------------------
        # Stage summary
        # --------------------------------------------------------------

        stages_present, stages_missing = (
            self._stage_summary(
                validated_events_tuple
            )
        )

        # --------------------------------------------------------------
        # Evidence
        # --------------------------------------------------------------

        result_evidence = _copy_mapping(
            evidence
        )

        result_evidence.update(
            {
                "event_count": len(
                    validated_events_tuple
                ),
                "timeline_id": timeline.timeline_id,
                "correlation_id": correlation.correlation_id,
                "incident_id": incident.incident_id,
            }
        )

        status = (
            SYSTEM_VALIDATED
            if validated_events_tuple
            else SYSTEM_PARTIAL
        )

        result_id = _deterministic_id(
            "varynx-result",
            agent_id,
            case_id,
            request_id,
            tuple(
                event.event_id
                for event in validated_events_tuple
            ),
        )

        result = VarynxSystemResult(
            result_id=result_id,
            agent_id=agent_id,
            request_id=request_id,
            status=status,
            stages_present=stages_present,
            stages_missing=stages_missing,
            events=validated_events_tuple,
            timeline=timeline,
            correlation=correlation,
            incident=incident,
            evidence=result_evidence,
        )

        self._history[result_id] = result

        return result

    # ------------------------------------------------------------------
    # Convenience API
    # ------------------------------------------------------------------

    def validate_request(
        self,
        *,
        agent_id: str,
        case_id: str,
        request_id: str,
        stages: Sequence[str],
        decision: Optional[str] = None,
        evidence: Optional[Mapping[str, Any]] = None,
    ) -> VarynxSystemResult:
        """
        Construct a deterministic validation sequence for one request.

        This helper is intended for controlled testing and demonstrations.
        It does not execute the actual agent request.
        """

        request_id = _validate_text(
            request_id,
            "request_id",
        )

        if not isinstance(stages, Sequence):
            raise TypeError(
                "stages must be a sequence"
            )

        events: list[VarynxEvent] = []

        for index, stage in enumerate(
            stages,
            start=1,
        ):
            normalized_stage = _validate_text(
                stage,
                "stage",
            ).upper()

            event_decision = (
                decision
                if normalized_stage
                == DECISION_STAGE
                else None
            )

            event = self.create_event(
                agent_id=agent_id,
                stage=normalized_stage,
                event_type=normalized_stage,
                request_id=request_id,
                decision=event_decision,
                timestamp=(
                    f"2026-09-17T10:"
                    f"{index:02d}:00+00:00"
                ),
                evidence={
                    **_copy_mapping(evidence),
                    "stage": normalized_stage,
                    "sequence": index,
                },
            )

            events.append(event)

        return self.validate(
            agent_id=agent_id,
            case_id=case_id,
            request_id=request_id,
            events=events,
            evidence=evidence,
        )

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def latest(
        self,
        agent_id: str,
    ) -> Optional[VarynxSystemResult]:
        """
        Return the most recent result for an agent.
        """

        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        matching = [
            result
            for result in self._history.values()
            if result.agent_id == agent_id
        ]

        if not matching:
            return None

        return matching[-1]

    def history(
        self,
        agent_id: Optional[str] = None,
    ) -> tuple[VarynxSystemResult, ...]:
        """
        Return immutable system validation history.
        """

        if agent_id is None:
            return tuple(
                self._history.values()
            )

        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        return tuple(
            result
            for result in self._history.values()
            if result.agent_id == agent_id
        )

    def get(
        self,
        result_id: str,
    ) -> Optional[VarynxSystemResult]:
        result_id = _validate_text(
            result_id,
            "result_id",
        )

        return self._history.get(
            result_id
        )

    def reset(self) -> None:
        """
        Clear Day 75 in-memory validation history.

        This does not modify the underlying Varynx audit database.
        """

        self._history.clear()


# ---------------------------------------------------------------------------
# Architectural boundary helpers
# ---------------------------------------------------------------------------

def decision_is_modified_here() -> bool:
    """
    Day 75 does not modify security decisions.
    """

    return False


def enforcement_is_executed_here() -> bool:
    """
    Day 75 does not execute enforcement.
    """

    return False


def malicious_intent_is_inferred_here() -> bool:
    """
    Day 75 does not infer malicious intent.
    """

    return False


def creates_universal_security_score() -> bool:
    """
    Day 75 does not introduce a new universal security score.
    """

    return False


def system_is_read_only() -> bool:
    """
    Day 75 operates as an orchestration/validation layer.
    """

    return True


__all__ = [
    "SYSTEM_VALIDATED",
    "SYSTEM_PARTIAL",
    "BEHAVIORAL_STAGE",
    "TRUST_STAGE",
    "PREDICTIVE_STAGE",
    "DECISION_STAGE",
    "ENFORCEMENT_STAGE",
    "AUDIT_STAGE",
    "SNAPSHOT_STAGE",
    "TIMELINE_STAGE",
    "CORRELATION_STAGE",
    "INCIDENT_STAGE",
    "SUPPORTED_STAGES",
    "VarynxEvent",
    "VarynxSystemResult",
    "VarynxSystem",
    "decision_is_modified_here",
    "enforcement_is_executed_here",
    "malicious_intent_is_inferred_here",
    "creates_universal_security_score",
    "system_is_read_only",
]