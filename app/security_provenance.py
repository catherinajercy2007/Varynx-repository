"""
Varynx Day 67 - Security Decision Provenance & Traceability.

Creates an immutable provenance record describing the evidence and
decision stages associated with a validated enforcement request.

This module is descriptive and trace-oriented.

It does NOT:
- make security decisions
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
# Provenance stages
# ---------------------------------------------------------------------------

STAGE_BEHAVIORAL = "BEHAVIORAL_INTELLIGENCE"
STAGE_PREDICTIVE = "PREDICTIVE_SECURITY"
STAGE_DECISION = "SECURITY_DECISION"
STAGE_RECONCILIATION = "DECISION_RECONCILIATION"
STAGE_RUNTIME = "RUNTIME_SECURITY"
STAGE_ENFORCEMENT = "ENFORCEMENT_BOUNDARY"
STAGE_VALIDATION = "ENFORCEMENT_VALIDATION"

VALID_STAGES = frozenset(
    {
        STAGE_BEHAVIORAL,
        STAGE_PREDICTIVE,
        STAGE_DECISION,
        STAGE_RECONCILIATION,
        STAGE_RUNTIME,
        STAGE_ENFORCEMENT,
        STAGE_VALIDATION,
    }
)


# ---------------------------------------------------------------------------
# Provenance status
# ---------------------------------------------------------------------------

PROVENANCE_COMPLETE = "PROVENANCE_COMPLETE"
PROVENANCE_PARTIAL = "PROVENANCE_PARTIAL"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validate_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")

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


def _validate_stages(
    stages: list[str] | tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(stages, (list, tuple)):
        raise TypeError("stages must be a list or tuple")

    validated: list[str] = []

    for stage in stages:
        stage = _validate_text(stage, "stage")

        if stage not in VALID_STAGES:
            raise ValueError(
                f"Unsupported provenance stage: {stage}"
            )

        validated.append(stage)

    return tuple(validated)


# ---------------------------------------------------------------------------
# Provenance event
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProvenanceEvent:
    """
    Immutable record of one stage contributing information to the
    security decision path.
    """

    stage: str
    event_type: str
    evidence: dict[str, Any]


# ---------------------------------------------------------------------------
# Provenance record
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SecurityProvenanceRecord:
    """
    Immutable end-to-end traceability record.

    The record describes the security decision path without re-evaluating
    or changing any decision.
    """

    provenance_id: str
    agent_id: str
    request_id: str

    decision: str
    provenance_status: str

    stages: tuple[str, ...]
    events: tuple[ProvenanceEvent, ...]

    decision_evidence: dict[str, Any]
    source_evidence: dict[str, Any]

    execution_performed_here: bool


# ---------------------------------------------------------------------------
# Provenance ID
# ---------------------------------------------------------------------------


def build_provenance_id(
    agent_id: str,
    request_id: str,
) -> str:
    agent_id = _validate_text(agent_id, "agent_id")
    request_id = _validate_text(request_id, "request_id")

    return f"{agent_id}-provenance-{request_id}"


# ---------------------------------------------------------------------------
# Event construction
# ---------------------------------------------------------------------------


def create_provenance_event(
    *,
    stage: str,
    event_type: str,
    evidence: Optional[Mapping[str, Any]] = None,
) -> ProvenanceEvent:
    stage = _validate_text(stage, "stage")
    event_type = _validate_text(
        event_type,
        "event_type",
    )

    if stage not in VALID_STAGES:
        raise ValueError(
            f"Unsupported provenance stage: {stage}"
        )

    return ProvenanceEvent(
        stage=stage,
        event_type=event_type,
        evidence=_validate_mapping(
            evidence,
            "evidence",
        ),
    )


# ---------------------------------------------------------------------------
# Main provenance builder
# ---------------------------------------------------------------------------


class SecurityProvenanceBuilder:
    """
    Builds provenance records from already-existing Varynx evidence.

    The builder never recomputes a security decision.
    """

    def __init__(self) -> None:
        self._history: dict[
            str,
            list[SecurityProvenanceRecord],
        ] = {}

        self._counters: dict[str, int] = {}

    def _next_id(
        self,
        agent_id: str,
    ) -> str:
        count = self._counters.get(agent_id, 0) + 1
        self._counters[agent_id] = count

        return f"{agent_id}-provenance-{count}"

    def build(
        self,
        *,
        agent_id: str,
        request_id: str,
        decision: str,
        stages: list[str] | tuple[str, ...],
        events: Optional[
            list[ProvenanceEvent] | tuple[ProvenanceEvent, ...]
        ] = None,
        decision_evidence: Optional[
            Mapping[str, Any]
        ] = None,
        source_evidence: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> SecurityProvenanceRecord:
        """
        Build a provenance record.

        No decision is calculated here.
        """

        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        request_id = _validate_text(
            request_id,
            "request_id",
        )

        decision = _validate_text(
            decision,
            "decision",
        )

        validated_stages = _validate_stages(stages)

        if events is None:
            validated_events: tuple[
                ProvenanceEvent,
                ...
            ] = ()
        else:
            if not isinstance(events, (list, tuple)):
                raise TypeError(
                    "events must be a list, tuple, or None"
                )

            for event in events:
                if not isinstance(
                    event,
                    ProvenanceEvent,
                ):
                    raise TypeError(
                        "events must contain ProvenanceEvent objects"
                    )

            validated_events = tuple(events)

        provenance_id = self._next_id(agent_id)

        complete = bool(
            validated_stages
            and validated_events
            and decision_evidence is not None
        )

        provenance_status = (
            PROVENANCE_COMPLETE
            if complete
            else PROVENANCE_PARTIAL
        )

        record = SecurityProvenanceRecord(
            provenance_id=provenance_id,
            agent_id=agent_id,
            request_id=request_id,
            decision=decision,
            provenance_status=provenance_status,
            stages=validated_stages,
            events=tuple(
                deepcopy(validated_events)
            ),
            decision_evidence=_validate_mapping(
                decision_evidence,
                "decision_evidence",
            ),
            source_evidence=_validate_mapping(
                source_evidence,
                "source_evidence",
            ),
            execution_performed_here=False,
        )

        self._history.setdefault(
            agent_id,
            [],
        ).append(record)

        return record

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def latest(
        self,
        agent_id: str,
    ) -> Optional[SecurityProvenanceRecord]:
        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        records = self._history.get(agent_id)

        if not records:
            return None

        return records[-1]

    def history(
        self,
        agent_id: str,
    ) -> tuple[SecurityProvenanceRecord, ...]:
        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        return tuple(
            self._history.get(agent_id, ())
        )

    def snapshot_all(
        self,
    ) -> dict[
        str,
        tuple[SecurityProvenanceRecord, ...],
    ]:
        return {
            agent_id: tuple(records)
            for agent_id, records in self._history.items()
        }

    def reset(
        self,
        agent_id: Optional[str] = None,
    ) -> None:
        if agent_id is None:
            self._history.clear()
            self._counters.clear()
            return

        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        self._history.pop(
            agent_id,
            None,
        )

        self._counters.pop(
            agent_id,
            None,
        )


# ---------------------------------------------------------------------------
# Traceability helpers
# ---------------------------------------------------------------------------


def get_provenance_stage_names(
    record: SecurityProvenanceRecord,
) -> tuple[str, ...]:
    if not isinstance(
        record,
        SecurityProvenanceRecord,
    ):
        raise TypeError(
            "record must be a SecurityProvenanceRecord"
        )

    return tuple(record.stages)


def has_stage(
    record: SecurityProvenanceRecord,
    stage: str,
) -> bool:
    if not isinstance(
        record,
        SecurityProvenanceRecord,
    ):
        raise TypeError(
            "record must be a SecurityProvenanceRecord"
        )

    stage = _validate_text(
        stage,
        "stage",
    )

    if stage not in VALID_STAGES:
        raise ValueError(
            f"Unsupported provenance stage: {stage}"
        )

    return stage in record.stages


def provenance_is_complete(
    record: SecurityProvenanceRecord,
) -> bool:
    if not isinstance(
        record,
        SecurityProvenanceRecord,
    ):
        raise TypeError(
            "record must be a SecurityProvenanceRecord"
        )

    return (
        record.provenance_status
        == PROVENANCE_COMPLETE
    )


# ---------------------------------------------------------------------------
# Architectural invariant
# ---------------------------------------------------------------------------


def decision_is_modified_here() -> bool:
    """
    Day 67 is a traceability layer only.
    """

    return False


def enforcement_is_executed_here() -> bool:
    """
    Day 67 never performs enforcement.
    """

    return False