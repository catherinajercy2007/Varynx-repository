"""
Day 74 - Security Evidence Correlation

Correlates the Day 73 security evidence timeline into a deterministic,
explainable evidence chain.

Design principles:
- deterministic identifiers
- chronological evidence correlation
- request and event grouping
- lifecycle-stage discovery
- descriptive relationships only
- evidence preservation
- read-only correlation semantics
- incident/case reconstruction
- no new risk score
- no attacker-intent inference
- no enforcement action
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping, Sequence

from app.security_evidence_timeline import (
    SecurityEvidenceEntry,
    SecurityEvidenceTimeline,
)

# Day 73 already defines the authoritative security boundary predicates.
# Day 74 re-exports them instead of redefining a second source of truth,
# so the correlation layer asserts exactly the same boundaries.
from app.security_evidence_timeline import (  # noqa: F401
    decision_is_modified_here,
    enforcement_is_executed_here,
    malicious_intent_is_inferred_here,
)


# ============================================================================
# STATUS CONSTANTS
# ============================================================================

CORRELATION_COMPLETE = "CORRELATION_COMPLETE"
CORRELATION_PARTIAL = "CORRELATION_PARTIAL"

RELATIONSHIP_CONNECTED = "RELATIONSHIP_CONNECTED"
RELATIONSHIP_PARTIAL = "RELATIONSHIP_PARTIAL"

CASE_RECONSTRUCTED = "CASE_RECONSTRUCTED"
CASE_PARTIAL = "CASE_PARTIAL"


# ============================================================================
# RELATIONSHIP TYPES
# ============================================================================

SAME_REQUEST_SEQUENCE = "SAME_REQUEST_SEQUENCE"
CHRONOLOGICAL_LIFECYCLE_SEQUENCE = (
    "CHRONOLOGICAL_LIFECYCLE_SEQUENCE"
)
CHRONOLOGICAL_EVIDENCE_SEQUENCE = (
    "CHRONOLOGICAL_EVIDENCE_SEQUENCE"
)

# Compatibility aliases.
RELATIONSHIP_SAME_REQUEST = SAME_REQUEST_SEQUENCE
RELATIONSHIP_CHRONOLOGICAL_LIFECYCLE = (
    CHRONOLOGICAL_LIFECYCLE_SEQUENCE
)
RELATIONSHIP_CHRONOLOGICAL_EVIDENCE = (
    CHRONOLOGICAL_EVIDENCE_SEQUENCE
)


# ============================================================================
# SOURCE / STAGE CONSTANTS
# ============================================================================

SOURCE_AUDIT = "AUDIT"
SOURCE_INTEGRITY = "INTEGRITY"
SOURCE_MONITORING = "MONITORING"
SOURCE_SNAPSHOT = "SNAPSHOT"

STAGE_AUDIT = SOURCE_AUDIT
STAGE_INTEGRITY = SOURCE_INTEGRITY
STAGE_MONITORING = SOURCE_MONITORING
STAGE_SNAPSHOT = SOURCE_SNAPSHOT


# ============================================================================
# SECURITY LIFECYCLE STAGES
# ============================================================================

STAGE_BEHAVIORAL = "BEHAVIORAL"
STAGE_PREDICTIVE = "PREDICTIVE"
STAGE_DECISION = "DECISION"
STAGE_RECONCILIATION = "RECONCILIATION"
STAGE_RUNTIME = "RUNTIME"
STAGE_ENFORCEMENT = "ENFORCEMENT"
STAGE_VALIDATION = "VALIDATION"
STAGE_PROVENANCE = "PROVENANCE"


CORE_LIFECYCLE_STAGES = (
    STAGE_BEHAVIORAL,
    STAGE_PREDICTIVE,
    STAGE_DECISION,
)

KNOWN_STAGES = (
    STAGE_BEHAVIORAL,
    STAGE_PREDICTIVE,
    STAGE_DECISION,
    STAGE_RECONCILIATION,
    STAGE_RUNTIME,
    STAGE_ENFORCEMENT,
    STAGE_VALIDATION,
    STAGE_PROVENANCE,
)


# ============================================================================
# BASIC VALIDATION HELPERS
# ============================================================================

def _validate_text(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")

    if not value.strip():
        raise ValueError(f"{name} must not be empty")

    return value


def _validate_optional_text(
    value: Any,
    name: str,
) -> str | None:
    if value is None:
        return None

    return _validate_text(value, name)


def _validate_sequence_number(value: Any) -> int:
    if isinstance(value, bool):
        raise TypeError(
            "sequence_number must be an integer"
        )

    if not isinstance(value, int):
        raise TypeError(
            "sequence_number must be an integer"
        )

    if value < 0:
        raise ValueError(
            "sequence_number must be greater than or equal to zero"
        )

    return value


def _copy_mapping(
    value: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if value is None:
        return {}

    if not isinstance(value, Mapping):
        raise TypeError(
            "evidence must be a mapping"
        )

    return deepcopy(dict(value))


def _stable_hash(value: Any) -> str:
    return sha256(
        repr(value).encode("utf-8")
    ).hexdigest()[:16]


# ============================================================================
# ENTRY ACCESSORS
# ============================================================================

def _event_type(
    entry: SecurityEvidenceEntry,
) -> str:
    return str(
        getattr(
            entry,
            "event_type",
            "",
        )
    ).upper()


def _request_id(
    entry: SecurityEvidenceEntry,
) -> str | None:
    value = getattr(
        entry,
        "request_id",
        None,
    )

    if value is None:
        return None

    return str(value)


def _entry_sort_key(
    entry: SecurityEvidenceEntry,
) -> tuple[Any, ...]:
    return (
        str(
            getattr(
                entry,
                "timestamp",
                "",
            )
        ),
        int(
            getattr(
                entry,
                "sequence_number",
                0,
            )
        ),
        str(
            getattr(
                entry,
                "entry_id",
                "",
            )
        ),
    )


# ============================================================================
# STAGE NORMALIZATION
# ============================================================================

def _normalize_stage(
    event_type: str,
) -> str | None:
    normalized = _validate_text(
        event_type,
        "event_type",
    ).upper()

    if normalized in KNOWN_STAGES:
        return normalized

    return None


def normalize_event_stage(
    event_type: str,
) -> str | None:
    """
    Return the known lifecycle stage represented by an event type.

    Unknown/custom events return None rather than being assigned a
    fabricated lifecycle meaning.
    """

    return _normalize_stage(event_type)


# ============================================================================
# ENTRY CREATION
# ============================================================================

def create_evidence_entry(
    *,
    agent_id: str,
    case_id: str,
    sequence_number: int,
    source: str,
    event_type: str,
    request_id: str | None = None,
    decision: str | None = None,
    timestamp: str = "",
    evidence: Mapping[str, Any] | None = None,
) -> SecurityEvidenceEntry:
    """
    Construct a deterministic Day 73 evidence entry.

    The entry_id is generated from the complete stable evidence payload.
    """

    agent_id = _validate_text(
        agent_id,
        "agent_id",
    )

    case_id = _validate_text(
        case_id,
        "case_id",
    )

    source = _validate_text(
        source,
        "source",
    )

    event_type = _validate_text(
        event_type,
        "event_type",
    )

    request_id = _validate_optional_text(
        request_id,
        "request_id",
    )

    decision = _validate_optional_text(
        decision,
        "decision",
    )

    if not isinstance(timestamp, str):
        raise TypeError(
            "timestamp must be a string"
        )

    sequence_number = _validate_sequence_number(
        sequence_number
    )

    safe_evidence = _copy_mapping(
        evidence
    )

    payload = (
        agent_id,
        case_id,
        sequence_number,
        source,
        event_type,
        request_id,
        decision,
        timestamp,
        repr(safe_evidence),
    )

    entry_id = (
        "entry-"
        + _stable_hash(payload)
    )

    return SecurityEvidenceEntry(
        entry_id=entry_id,
        agent_id=agent_id,
        case_id=case_id,
        sequence_number=sequence_number,
        source=source,
        event_type=event_type,
        request_id=request_id,
        decision=decision,
        timestamp=timestamp,
        evidence=safe_evidence,
    )


# ============================================================================
# RELATIONSHIP MODEL
# ============================================================================

@dataclass(frozen=True)
class EvidenceRelationship:
    relationship_id: str
    case_id: str | None
    request_id: str | None
    left_event_id: str
    right_event_id: str
    relationship_type: str
    reason: str


# ============================================================================
# CORRELATION MODEL
# ============================================================================

@dataclass(frozen=True)
class SecurityEvidenceCorrelation:
    correlation_id: str
    agent_id: str | None
    case_id: str | None
    request_id: str | None

    status: str
    relationship_status: str

    entries: tuple[SecurityEvidenceEntry, ...]
    relationships: tuple[EvidenceRelationship, ...]

    request_groups: Mapping[
        str,
        tuple[SecurityEvidenceEntry, ...],
    ]

    event_groups: Mapping[
        str,
        tuple[SecurityEvidenceEntry, ...],
    ]

    # Explicit public field required by Day 74.
    stages_present: tuple[str, ...]

    # Compatibility field.
    stages: tuple[str, ...]

    # Core lifecycle stages that are absent from this evidence chain.
    #
    # Both names refer to the same value: the Day 74 specification names
    # this `missing_stages`, while the Day 74 test suite reads
    # `stages_missing`. Neither name is dropped.
    missing_stages: tuple[str, ...]
    stages_missing: tuple[str, ...]

    evidence: Mapping[str, Any]

    summary: Mapping[str, Any]


# ============================================================================
# INCIDENT RECONSTRUCTION MODEL
# ============================================================================

@dataclass(frozen=True)
class SecurityIncidentReconstruction:
    incident_id: str

    agent_id: str | None
    case_id: str | None

    status: str

    entry_count: int
    relationship_count: int

    entries: tuple[SecurityEvidenceEntry, ...]
    relationships: tuple[EvidenceRelationship, ...]

    stages: tuple[str, ...]
    decisions: tuple[str, ...]

    evidence: Mapping[str, Any]

    summary: Mapping[str, Any]


# ============================================================================
# TIMELINE VALIDATION / EXTRACTION
# ============================================================================

def _extract_entries(
    timeline: SecurityEvidenceTimeline,
) -> tuple[SecurityEvidenceEntry, ...]:
    """
    Accept only a real Day 73 SecurityEvidenceTimeline.

    This deliberately rejects strings, lists, dictionaries and arbitrary
    iterables so invalid timeline input cannot silently become evidence.
    """

    if not isinstance(
        timeline,
        SecurityEvidenceTimeline,
    ):
        raise TypeError(
            "timeline must be SecurityEvidenceTimeline"
        )

    raw_entries = getattr(
        timeline,
        "entries",
        (),
    )

    if raw_entries is None:
        raw_entries = ()

    if not isinstance(
        raw_entries,
        (list, tuple),
    ):
        raise TypeError(
            "timeline.entries must be a sequence"
        )

    entries: list[
        SecurityEvidenceEntry
    ] = []

    for entry in raw_entries:
        if not isinstance(
            entry,
            SecurityEvidenceEntry,
        ):
            raise TypeError(
                "timeline contains an invalid evidence entry"
            )

        entries.append(entry)

    entries.sort(
        key=_entry_sort_key
    )

    return tuple(entries)


# ============================================================================
# CORRELATION ID
# ============================================================================

def build_correlation_id(
    timeline: SecurityEvidenceTimeline,
    evidence: Mapping[str, Any] | None = None,
) -> str:
    """
    Generate a deterministic correlation identifier.

    Supports:
        build_correlation_id(timeline)

    and:
        build_correlation_id(timeline, evidence)
    """

    entries = _extract_entries(
        timeline
    )

    entry_payload = tuple(
        (
            getattr(
                entry,
                "entry_id",
                None,
            ),
            getattr(
                entry,
                "agent_id",
                None,
            ),
            getattr(
                entry,
                "case_id",
                None,
            ),
            getattr(
                entry,
                "sequence_number",
                None,
            ),
            getattr(
                entry,
                "source",
                None,
            ),
            getattr(
                entry,
                "event_type",
                None,
            ),
            getattr(
                entry,
                "request_id",
                None,
            ),
            getattr(
                entry,
                "decision",
                None,
            ),
            getattr(
                entry,
                "timestamp",
                None,
            ),
            repr(
                getattr(
                    entry,
                    "evidence",
                    {},
                )
            ),
        )
        for entry in entries
    )

    payload = (
        entry_payload,
        repr(dict(evidence or {})),
    )

    return (
        "corr-"
        + _stable_hash(payload)
    )


# ============================================================================
# RELATIONSHIP ID
# ============================================================================

def _build_relationship_id(
    *,
    case_id: str | None,
    request_id: str | None,
    left_event_id: str,
    right_event_id: str,
    relationship_type: str,
) -> str:
    return (
        "rel-"
        + _stable_hash(
            (
                case_id,
                request_id,
                left_event_id,
                right_event_id,
                relationship_type,
            )
        )
    )


# ============================================================================
# GROUPING
# ============================================================================

def _build_request_groups(
    entries: Sequence[SecurityEvidenceEntry],
) -> dict[
    str,
    tuple[SecurityEvidenceEntry, ...],
]:
    groups: dict[
        str,
        list[SecurityEvidenceEntry],
    ] = {}

    for entry in entries:
        request_id = _request_id(entry)

        if request_id is None:
            continue

        groups.setdefault(
            request_id,
            [],
        ).append(entry)

    return {
        key: tuple(value)
        for key, value in groups.items()
    }


def _build_event_groups(
    entries: Sequence[SecurityEvidenceEntry],
) -> dict[
    str,
    tuple[SecurityEvidenceEntry, ...],
]:
    groups: dict[
        str,
        list[SecurityEvidenceEntry],
    ] = {}

    for entry in entries:
        event_type = _event_type(entry)

        groups.setdefault(
            event_type,
            [],
        ).append(entry)

    return {
        key: tuple(value)
        for key, value in groups.items()
    }


# ============================================================================
# DECISION EXTRACTION
# ============================================================================

def _extract_decisions(
    entries: Sequence[SecurityEvidenceEntry],
) -> tuple[str, ...]:
    """
    Collect the security decisions recorded by this evidence chain.

    Only DECISION-stage evidence carries an actual security decision.
    Behavioral, predictive, validation and custom evidence may carry a
    decision field describing the decision context they were captured
    under; treating that as a decision of the case would over-report
    what the evidence actually establishes.
    """

    return tuple(
        sorted(
            {
                str(entry.decision)
                for entry in entries
                if getattr(entry, "decision", None) is not None
                and _normalize_stage(
                    _event_type(entry)
                )
                == STAGE_DECISION
            }
        )
    )


# ============================================================================
# LIFECYCLE RELATIONSHIP LOGIC
# ============================================================================

def _is_known_lifecycle_event(
    entry: SecurityEvidenceEntry,
) -> bool:
    event_type = _event_type(entry)

    return event_type in CORE_LIFECYCLE_STAGES


def _relationship_type(
    left: SecurityEvidenceEntry,
    right: SecurityEvidenceEntry,
) -> str:
    """
    Determine a descriptive relationship between adjacent entries.

    Known lifecycle + same request:
        SAME_REQUEST_SEQUENCE

    Known lifecycle + different/missing request:
        CHRONOLOGICAL_LIFECYCLE_SEQUENCE

    Any unknown/custom event:
        CHRONOLOGICAL_EVIDENCE_SEQUENCE
    """

    left_known = _is_known_lifecycle_event(
        left
    )

    right_known = _is_known_lifecycle_event(
        right
    )

    if left_known and right_known:
        left_request = _request_id(left)
        right_request = _request_id(right)

        if (
            left_request is not None
            and right_request is not None
            and left_request == right_request
        ):
            return SAME_REQUEST_SEQUENCE

        return CHRONOLOGICAL_LIFECYCLE_SEQUENCE

    return CHRONOLOGICAL_EVIDENCE_SEQUENCE


def _relationship_reason(
    relationship_type: str,
) -> str:
    if (
        relationship_type
        == SAME_REQUEST_SEQUENCE
    ):
        return (
            "Recognized lifecycle evidence entries "
            "belong to the same security request."
        )

    if (
        relationship_type
        == CHRONOLOGICAL_LIFECYCLE_SEQUENCE
    ):
        return (
            "Recognized lifecycle evidence entries "
            "form a chronological security lifecycle sequence."
        )

    return (
        "Evidence entries form a chronological evidence "
        "sequence without asserting lifecycle meaning."
    )


# ============================================================================
# RELATIONSHIP CONSTRUCTION
# ============================================================================

def _build_relationships(
    entries: Sequence[SecurityEvidenceEntry],
) -> tuple[EvidenceRelationship, ...]:
    """
    Connect adjacent chronological evidence entries.

    The engine deliberately avoids all-to-all correlation because that
    would create unsupported relationships.
    """

    if len(entries) < 2:
        return ()

    relationships: list[
        EvidenceRelationship
    ] = []

    for left, right in zip(
        entries,
        entries[1:],
    ):
        relationship_type = _relationship_type(
            left,
            right,
        )

        left_request = _request_id(left)
        right_request = _request_id(right)

        relationship_request_id = (
            left_request
            if (
                left_request is not None
                and left_request == right_request
            )
            else None
        )

        relationship = EvidenceRelationship(
            relationship_id=_build_relationship_id(
                case_id=getattr(
                    left,
                    "case_id",
                    None,
                ),
                request_id=relationship_request_id,
                left_event_id=str(
                    getattr(
                        left,
                        "entry_id",
                        "",
                    )
                ),
                right_event_id=str(
                    getattr(
                        right,
                        "entry_id",
                        "",
                    )
                ),
                relationship_type=relationship_type,
            ),
            case_id=getattr(
                left,
                "case_id",
                None,
            ),
            request_id=relationship_request_id,
            left_event_id=str(
                getattr(
                    left,
                    "entry_id",
                    "",
                )
            ),
            right_event_id=str(
                getattr(
                    right,
                    "entry_id",
                    "",
                )
            ),
            relationship_type=relationship_type,
            reason=_relationship_reason(
                relationship_type
            ),
        )

        relationships.append(
            relationship
        )

    return tuple(relationships)


# ============================================================================
# ENGINE
# ============================================================================

class SecurityEvidenceCorrelationEngine:
    """
    Day 74 security evidence correlation engine.

    Correlations are retained in memory for deterministic history,
    latest-result and case-based inspection.
    """

    def __init__(self) -> None:
        self._history: list[
            SecurityEvidenceCorrelation
        ] = []

    # ------------------------------------------------------------------
    # CORRELATE
    # ------------------------------------------------------------------

    def correlate(
        self,
        timeline: SecurityEvidenceTimeline,
        *,
        agent_id: str | None = None,
        case_id: str | None = None,
        request_id: str | None = None,
        evidence: Mapping[str, Any] | None = None,
    ) -> SecurityEvidenceCorrelation:

        entries = _extract_entries(
            timeline
        )

        safe_evidence = _copy_mapping(
            evidence
        )

        # Infer identity only from actual evidence.
        if agent_id is None and entries:
            agent_id = getattr(
                entries[0],
                "agent_id",
                None,
            )

        if case_id is None and entries:
            case_id = getattr(
                entries[0],
                "case_id",
                None,
            )

        request_ids = {
            _request_id(entry)
            for entry in entries
            if _request_id(entry) is not None
        }

        if (
            request_id is None
            and len(request_ids) == 1
        ):
            request_id = next(
                iter(request_ids)
            )

        correlation_id = build_correlation_id(
            timeline,
            safe_evidence,
        )

        request_groups = _build_request_groups(
            entries
        )

        event_groups = _build_event_groups(
            entries
        )

        relationships = _build_relationships(
            entries
        )

        normalized_stages = {
            _normalize_stage(
                _event_type(entry)
            )
            for entry in entries
        }

        normalized_stages.discard(
            None
        )

        stages_present = tuple(
            stage
            for stage in KNOWN_STAGES
            if stage in normalized_stages
        )

        missing_stages = tuple(
            stage
            for stage in CORE_LIFECYCLE_STAGES
            if stage not in stages_present
        )

        # Strict lifecycle completeness.
        status = (
            CORRELATION_COMPLETE
            if all(
                stage in stages_present
                for stage in CORE_LIFECYCLE_STAGES
            )
            else CORRELATION_PARTIAL
        )

        relationship_status = (
            RELATIONSHIP_CONNECTED
            if relationships
            else RELATIONSHIP_PARTIAL
        )

        summary = {
            "entry_count": len(entries),
            "relationship_count": len(
                relationships
            ),
            "request_group_count": len(
                request_groups
            ),
            "event_group_count": len(
                event_groups
            ),
            "stages_present": stages_present,
            "missing_stages": missing_stages,
            "event_types": tuple(
                sorted(
                    {
                        _event_type(entry)
                        for entry in entries
                    }
                )
            ),
            "unknown_event_types": tuple(
                sorted(
                    {
                        _event_type(entry)
                        for entry in entries
                        if _normalize_stage(
                            _event_type(entry)
                        )
                        is None
                    }
                )
            ),
        }

        correlation = SecurityEvidenceCorrelation(
            correlation_id=correlation_id,
            agent_id=agent_id,
            case_id=case_id,
            request_id=request_id,
            status=status,
            relationship_status=relationship_status,
            entries=tuple(entries),
            relationships=relationships,
            request_groups=deepcopy(
                request_groups
            ),
            event_groups=deepcopy(
                event_groups
            ),
            stages_present=stages_present,
            stages=stages_present,
            missing_stages=missing_stages,
            stages_missing=missing_stages,
            evidence=deepcopy(
                safe_evidence
            ),
            summary=deepcopy(
                summary
            ),
        )

        self._history.append(
            correlation
        )

        return correlation

    # ------------------------------------------------------------------
    # INCIDENT RECONSTRUCTION
    # ------------------------------------------------------------------

    def reconstruct_incident(
        self,
        correlation: SecurityEvidenceCorrelation,
    ) -> SecurityIncidentReconstruction:

        if not isinstance(
            correlation,
            SecurityEvidenceCorrelation,
        ):
            raise TypeError(
                "correlation must be SecurityEvidenceCorrelation"
            )

        entries = tuple(
            correlation.entries
        )

        relationships = tuple(
            correlation.relationships
        )

        decisions = _extract_decisions(
            entries
        )

        # An empty timeline cannot reconstruct an incident.
        #
        # A non-empty correlated chain with relationships can be
        # reconstructed even when lifecycle completeness is partial.
        reconstructed = (
            len(entries) > 0
            and len(relationships) > 0
        )

        status = (
            CASE_RECONSTRUCTED
            if reconstructed
            else CASE_PARTIAL
        )

        incident_id = (
            "incident-"
            + _stable_hash(
                (
                    correlation.correlation_id,
                    correlation.agent_id,
                    correlation.case_id,
                    tuple(
                        entry.entry_id
                        for entry in entries
                    ),
                    tuple(
                        relationship.relationship_id
                        for relationship
                        in relationships
                    ),
                )
            )
        )

        # IMPORTANT:
        # Preserve supplied correlation evidence at the same top level.
        #
        # Example:
        # {"source": {"integrity": "VALID"}}
        #
        # must remain:
        # incident.evidence["source"]["integrity"]
        reconstruction_evidence = deepcopy(
            dict(
                correlation.evidence
            )
        )

        # Add entry evidence without replacing existing caller evidence.
        reconstruction_evidence.setdefault(
            "entries",
            [
                deepcopy(
                    getattr(
                        entry,
                        "evidence",
                        {},
                    )
                )
                for entry in entries
            ],
        )

        summary = {
            "entry_count": len(entries),
            "relationship_count": len(
                relationships
            ),
            "stage_count": len(
                correlation.stages_present
            ),
            "decision_count": len(
                decisions
            ),
        }

        return SecurityIncidentReconstruction(
            incident_id=incident_id,
            agent_id=correlation.agent_id,
            case_id=correlation.case_id,
            status=status,
            entry_count=len(entries),
            relationship_count=len(
                relationships
            ),
            entries=entries,
            relationships=relationships,
            stages=tuple(
                correlation.stages_present
            ),
            decisions=decisions,
            evidence=deepcopy(
                reconstruction_evidence
            ),
            summary=deepcopy(
                summary
            ),
        )

    # ------------------------------------------------------------------
    # HISTORY
    # ------------------------------------------------------------------

    def latest(
        self,
        agent_id: str | None = None,
    ) -> SecurityEvidenceCorrelation | None:

        if agent_id is None:
            if not self._history:
                return None

            return self._history[-1]

        for correlation in reversed(
            self._history
        ):
            if correlation.agent_id == agent_id:
                return correlation

        return None

    def history(
        self,
        agent_id: str | None = None,
    ) -> tuple[
        SecurityEvidenceCorrelation,
        ...,
    ]:

        if agent_id is None:
            return tuple(
                self._history
            )

        return tuple(
            correlation
            for correlation in self._history
            if correlation.agent_id == agent_id
        )

    def by_case(
        self,
        case_id: str,
    ) -> tuple[
        SecurityEvidenceCorrelation,
        ...,
    ]:

        case_id = _validate_text(
            case_id,
            "case_id",
        )

        return tuple(
            correlation
            for correlation in self._history
            if correlation.case_id == case_id
        )

    # ------------------------------------------------------------------
    # SNAPSHOT
    # ------------------------------------------------------------------

    def snapshot_all(
        self,
    ) -> tuple[
        SecurityEvidenceCorrelation,
        ...,
    ]:
        return tuple(
            self._history
        )

    # ------------------------------------------------------------------
    # RESET
    # ------------------------------------------------------------------

    def reset(self) -> None:
        self._history.clear()


# ============================================================================
# PUBLIC VALIDATION HELPERS
# ============================================================================

def correlation_is_complete(
    correlation: SecurityEvidenceCorrelation,
) -> bool:
    """
    Day 74 helper for a usable correlated evidence chain.

    This helper checks whether evidence has actually been connected.
    It intentionally differs from correlation.status, which represents
    strict behavioral -> predictive -> decision lifecycle completeness.
    """

    if not isinstance(
        correlation,
        SecurityEvidenceCorrelation,
    ):
        raise TypeError(
            "correlation must be SecurityEvidenceCorrelation"
        )

    return (
        len(correlation.entries) > 0
        and len(correlation.relationships) > 0
    )


# Fields that Day 74 correlation must never introduce.
FORBIDDEN_CORRELATION_FIELDS = (
    "risk_score",
    "security_score",
    "enforcement_action",
    "response_action",
)


def correlation_is_read_only(
    correlation: SecurityEvidenceCorrelation | None = None,
) -> bool:
    """
    Verify that correlation represents evidence only.

    Called with a correlation, this checks that specific object.
    Called with no argument, this asserts the layer-level guarantee:
    the correlation model itself declares no scoring or enforcement
    field, so no correlation this module produces can carry one.

    Correlation must not introduce:
    - risk scores
    - security scores
    - enforcement actions
    - response actions
    """

    if correlation is None:
        return not any(
            field in SecurityEvidenceCorrelation.__annotations__
            for field in FORBIDDEN_CORRELATION_FIELDS
        )

    if not isinstance(
        correlation,
        SecurityEvidenceCorrelation,
    ):
        raise TypeError(
            "correlation must be SecurityEvidenceCorrelation"
        )

    return not any(
        hasattr(
            correlation,
            field,
        )
        for field in FORBIDDEN_CORRELATION_FIELDS
    )


def incident_is_reconstructed(
    incident: SecurityIncidentReconstruction,
) -> bool:
    """
    Return True when an incident contains a non-empty connected
    evidence chain.
    """

    if not isinstance(
        incident,
        SecurityIncidentReconstruction,
    ):
        raise TypeError(
            "incident must be SecurityIncidentReconstruction"
        )

    return (
        incident.entry_count > 0
        and incident.relationship_count > 0
    )


def correlation_has_relationships(
    correlation: SecurityEvidenceCorrelation,
) -> bool:
    if not isinstance(
        correlation,
        SecurityEvidenceCorrelation,
    ):
        raise TypeError(
            "correlation must be SecurityEvidenceCorrelation"
        )

    return bool(
        correlation.relationships
    )


def incident_has_relationships(
    incident: SecurityIncidentReconstruction,
) -> bool:
    if not isinstance(
        incident,
        SecurityIncidentReconstruction,
    ):
        raise TypeError(
            "incident must be SecurityIncidentReconstruction"
        )

    return (
        incident.relationship_count > 0
    )


def correlation_is_evidence_only() -> bool:
    """
    Day 74 layer-level guarantee: correlation is descriptive only.
    """

    return correlation_is_read_only()


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # statuses
    "CORRELATION_COMPLETE",
    "CORRELATION_PARTIAL",
    "RELATIONSHIP_CONNECTED",
    "RELATIONSHIP_PARTIAL",
    "CASE_RECONSTRUCTED",
    "CASE_PARTIAL",

    # relationship types
    "SAME_REQUEST_SEQUENCE",
    "CHRONOLOGICAL_LIFECYCLE_SEQUENCE",
    "CHRONOLOGICAL_EVIDENCE_SEQUENCE",
    "RELATIONSHIP_SAME_REQUEST",
    "RELATIONSHIP_CHRONOLOGICAL_LIFECYCLE",
    "RELATIONSHIP_CHRONOLOGICAL_EVIDENCE",

    # sources
    "SOURCE_AUDIT",
    "SOURCE_INTEGRITY",
    "SOURCE_MONITORING",
    "SOURCE_SNAPSHOT",

    # source/stage aliases
    "STAGE_AUDIT",
    "STAGE_INTEGRITY",
    "STAGE_MONITORING",
    "STAGE_SNAPSHOT",

    # lifecycle stages
    "STAGE_BEHAVIORAL",
    "STAGE_PREDICTIVE",
    "STAGE_DECISION",
    "STAGE_RECONCILIATION",
    "STAGE_RUNTIME",
    "STAGE_ENFORCEMENT",
    "STAGE_VALIDATION",
    "STAGE_PROVENANCE",
    "CORE_LIFECYCLE_STAGES",
    "KNOWN_STAGES",

    # models
    "EvidenceRelationship",
    "SecurityEvidenceCorrelation",
    "SecurityIncidentReconstruction",

    # creation / normalization
    "create_evidence_entry",
    "build_correlation_id",
    "normalize_event_stage",

    # validation helpers
    "correlation_is_complete",
    "correlation_is_read_only",
    "correlation_is_evidence_only",
    "incident_is_reconstructed",
    "correlation_has_relationships",
    "incident_has_relationships",

    # security boundaries (re-exported from Day 73)
    "decision_is_modified_here",
    "enforcement_is_executed_here",
    "malicious_intent_is_inferred_here",

    # engine
    "SecurityEvidenceCorrelationEngine",
]
