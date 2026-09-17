"""
Varynx Day 73 - Security Evidence Timeline & Case Reconstruction.

This module provides a deterministic, read-only layer for reconstructing
chronological security evidence from previously generated Varynx artifacts.

The module does not:
- authorize actions
- execute enforcement
- modify security decisions
- calculate a new universal risk score
- infer malicious intent
- predict exact attacker behavior
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Iterable, Mapping


TIMELINE_COMPLETE = "TIMELINE_COMPLETE"
TIMELINE_PARTIAL = "TIMELINE_PARTIAL"

TIMELINE_ORDERED = "TIMELINE_ORDERED"
TIMELINE_GAPPED = "TIMELINE_GAPPED"
TIMELINE_INCONSISTENT = "TIMELINE_INCONSISTENT"

CASE_COMPLETE = "CASE_COMPLETE"
CASE_PARTIAL = "CASE_PARTIAL"

SOURCE_AUDIT = "AUDIT"
SOURCE_INTEGRITY = "INTEGRITY"
SOURCE_MONITORING = "MONITORING"
SOURCE_SNAPSHOT = "SNAPSHOT"
SOURCE_EXTERNAL = "EXTERNAL"

VALID_SOURCES = frozenset(
    {
        SOURCE_AUDIT,
        SOURCE_INTEGRITY,
        SOURCE_MONITORING,
        SOURCE_SNAPSHOT,
        SOURCE_EXTERNAL,
    }
)


def _validate_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()
from copy import deepcopy

def _validate_mapping(
    value: Mapping[str, Any] | None,
    field_name: str,
) -> dict[str, Any]:
    if value is None:
        return {}

    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")

    return deepcopy(dict(value))


def _validate_sequence(value: int, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{field_name} must be an integer")

    if value < 1:
        raise ValueError(f"{field_name} must be >= 1")

    return value


def _validate_source(source: str) -> str:
    source = _validate_text(source, "source")

    if source not in VALID_SOURCES:
        raise ValueError(
            f"Unsupported source '{source}'. "
            f"Expected one of {sorted(VALID_SOURCES)}"
        )

    return source


def _canonicalize(value: Any) -> Any:
    """
    Convert supported nested structures into deterministic representations.
    """

    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }

    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]

    if isinstance(value, set):
        return sorted(
            (_canonicalize(item) for item in value),
            key=lambda item: repr(item),
        )

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    return repr(value)


def _canonical_payload(payload: Mapping[str, Any]) -> str:
    canonical = _canonicalize(payload)
    return repr(canonical)


def build_timeline_id(
    agent_id: str,
    case_id: str,
    entries: Iterable["SecurityEvidenceEntry"],
) -> str:
    """
    Build a deterministic timeline identifier.
    """

    agent_id = _validate_text(agent_id, "agent_id")
    case_id = _validate_text(case_id, "case_id")

    entry_payload = [
        {
            "entry_id": entry.entry_id,
            "sequence_number": entry.sequence_number,
            "source": entry.source,
            "event_type": entry.event_type,
            "request_id": entry.request_id,
            "decision": entry.decision,
            "timestamp": entry.timestamp,
        }
        for entry in entries
    ]

    payload = {
        "agent_id": agent_id,
        "case_id": case_id,
        "entries": entry_payload,
    }

    digest = sha256(_canonical_payload(payload).encode("utf-8")).hexdigest()

    return f"timeline-{digest[:16]}"


@dataclass(frozen=True)
class SecurityEvidenceEntry:
    """
    Immutable normalized evidence entry.

    An entry references previously produced evidence. It does not create
    a new security decision.
    """

    entry_id: str
    agent_id: str
    case_id: str
    sequence_number: int
    source: str
    event_type: str
    request_id: str | None
    decision: str | None
    timestamp: str | None
    evidence: Mapping[str, Any]

    def __post_init__(self) -> None:
        _validate_text(self.entry_id, "entry_id")
        _validate_text(self.agent_id, "agent_id")
        _validate_text(self.case_id, "case_id")
        _validate_sequence(self.sequence_number, "sequence_number")
        _validate_source(self.source)
        _validate_text(self.event_type, "event_type")

        if self.request_id is not None:
            _validate_text(self.request_id, "request_id")

        if self.decision is not None:
            _validate_text(self.decision, "decision")

        if self.timestamp is not None:
            _validate_text(self.timestamp, "timestamp")

        _validate_mapping(self.evidence, "evidence")


@dataclass(frozen=True)
class SecurityEvidenceTimeline:
    """
    Immutable chronological timeline for one security case.
    """

    timeline_id: str
    agent_id: str
    case_id: str
    status: str
    ordering_status: str
    entries: tuple[SecurityEvidenceEntry, ...]
    source_counts: Mapping[str, int]
    event_type_counts: Mapping[str, int]
    request_ids: tuple[str, ...]
    gaps: tuple[int, ...]
    evidence: Mapping[str, Any]
    execution_performed_here: bool = False


@dataclass(frozen=True)
class SecurityCaseReconstruction:
    """
    Immutable reconstructed security case.
    """

    case_id: str
    agent_id: str
    status: str
    timeline_id: str
    entry_count: int
    first_timestamp: str | None
    last_timestamp: str | None
    decisions: tuple[str, ...]
    sources: tuple[str, ...]
    requests: tuple[str, ...]
    gaps: tuple[int, ...]
    evidence: Mapping[str, Any]
    execution_performed_here: bool = False


def create_evidence_entry(
    *,
    agent_id: str,
    case_id: str,
    sequence_number: int,
    source: str,
    event_type: str,
    request_id: str | None = None,
    decision: str | None = None,
    timestamp: str | None = None,
    evidence: Mapping[str, Any] | None = None,
    entry_id: str | None = None,
) -> SecurityEvidenceEntry:
    """
    Create a normalized immutable evidence entry.

    If entry_id is omitted, a deterministic identifier is generated.
    """

    agent_id = _validate_text(agent_id, "agent_id")
    case_id = _validate_text(case_id, "case_id")
    source = _validate_source(source)
    event_type = _validate_text(event_type, "event_type")

    sequence_number = _validate_sequence(
        sequence_number,
        "sequence_number",
    )

    normalized_evidence = _validate_mapping(evidence, "evidence")

    if entry_id is None:
        payload = {
            "agent_id": agent_id,
            "case_id": case_id,
            "sequence_number": sequence_number,
            "source": source,
            "event_type": event_type,
            "request_id": request_id,
            "decision": decision,
            "timestamp": timestamp,
            "evidence": normalized_evidence,
        }

        digest = sha256(
            _canonical_payload(payload).encode("utf-8")
        ).hexdigest()

        entry_id = f"entry-{digest[:16]}"

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
        evidence=normalized_evidence,
    )


def analyze_sequence(
    entries: Iterable[SecurityEvidenceEntry],
) -> tuple[str, tuple[int, ...]]:
    """
    Analyze sequence ordering and missing sequence numbers.
    """

    entries = tuple(entries)

    if not entries:
        return TIMELINE_GAPPED, ()

    sequence_numbers = [
        entry.sequence_number
        for entry in entries
    ]

    expected = set(range(1, max(sequence_numbers) + 1))
    actual = set(sequence_numbers)

    gaps = tuple(sorted(expected - actual))

    if len(sequence_numbers) != len(set(sequence_numbers)):
        return TIMELINE_INCONSISTENT, gaps

    if sequence_numbers != sorted(sequence_numbers):
        return TIMELINE_INCONSISTENT, gaps

    if gaps:
        return TIMELINE_GAPPED, gaps

    return TIMELINE_ORDERED, ()


def _build_source_counts(
    entries: Iterable[SecurityEvidenceEntry],
) -> dict[str, int]:
    counts: dict[str, int] = {}

    for entry in entries:
        counts[entry.source] = counts.get(entry.source, 0) + 1

    return dict(sorted(counts.items()))


def _build_event_type_counts(
    entries: Iterable[SecurityEvidenceEntry],
) -> dict[str, int]:
    counts: dict[str, int] = {}

    for entry in entries:
        counts[entry.event_type] = counts.get(entry.event_type, 0) + 1

    return dict(sorted(counts.items()))


class SecurityEvidenceTimelineBuilder:
    """
    Read-only builder and historical store for security evidence timelines.
    """

    def __init__(self) -> None:
        self._history: dict[str, list[SecurityEvidenceTimeline]] = {}

    def build_timeline(
        self,
        *,
        agent_id: str,
        case_id: str,
        entries: Iterable[SecurityEvidenceEntry],
        evidence: Mapping[str, Any] | None = None,
    ) -> SecurityEvidenceTimeline:
        agent_id = _validate_text(agent_id, "agent_id")
        case_id = _validate_text(case_id, "case_id")

        normalized_entries = tuple(entries)

        for entry in normalized_entries:
            if entry.agent_id != agent_id:
                raise ValueError(
                    "All entries must belong to the supplied agent_id"
                )

            if entry.case_id != case_id:
                raise ValueError(
                    "All entries must belong to the supplied case_id"
                )

        ordering_status, gaps = analyze_sequence(normalized_entries)

        if not normalized_entries:
            status = TIMELINE_PARTIAL
        elif ordering_status == TIMELINE_ORDERED:
            status = TIMELINE_COMPLETE
        else:
            status = TIMELINE_PARTIAL

        timeline_id = build_timeline_id(
            agent_id,
            case_id,
            normalized_entries,
        )

        source_counts = _build_source_counts(normalized_entries)
        event_type_counts = _build_event_type_counts(normalized_entries)

        request_ids = tuple(
            sorted(
                {
                    entry.request_id
                    for entry in normalized_entries
                    if entry.request_id is not None
                }
            )
        )

        normalized_evidence = _validate_mapping(
            evidence,
            "evidence",
        )

        timeline = SecurityEvidenceTimeline(
            timeline_id=timeline_id,
            agent_id=agent_id,
            case_id=case_id,
            status=status,
            ordering_status=ordering_status,
            entries=normalized_entries,
            source_counts=source_counts,
            event_type_counts=event_type_counts,
            request_ids=request_ids,
            gaps=gaps,
            evidence=normalized_evidence,
            execution_performed_here=False,
        )

        self._history.setdefault(agent_id, []).append(timeline)

        return timeline

    def latest(
        self,
        agent_id: str,
    ) -> SecurityEvidenceTimeline | None:
        agent_id = _validate_text(agent_id, "agent_id")

        history = self._history.get(agent_id, [])

        if not history:
            return None

        return history[-1]

    def history(
        self,
        agent_id: str,
    ) -> tuple[SecurityEvidenceTimeline, ...]:
        agent_id = _validate_text(agent_id, "agent_id")

        return tuple(self._history.get(agent_id, []))

    def by_case(
        self,
        case_id: str,
    ) -> tuple[SecurityEvidenceTimeline, ...]:
        case_id = _validate_text(case_id, "case_id")

        matches: list[SecurityEvidenceTimeline] = []

        for timelines in self._history.values():
            matches.extend(
                timeline
                for timeline in timelines
                if timeline.case_id == case_id
            )

        return tuple(matches)

    def reconstruct_case(
        self,
        timeline: SecurityEvidenceTimeline,
    ) -> SecurityCaseReconstruction:
        decisions = tuple(
            dict.fromkeys(
                entry.decision
                for entry in timeline.entries
                if entry.decision is not None
            )
        )

        sources = tuple(
            sorted(
                {
                    entry.source
                    for entry in timeline.entries
                }
            )
        )

        requests = tuple(
            sorted(
                {
                    entry.request_id
                    for entry in timeline.entries
                    if entry.request_id is not None
                }
            )
        )

        timestamps = [
            entry.timestamp
            for entry in timeline.entries
            if entry.timestamp is not None
        ]

        first_timestamp = (
            min(timestamps)
            if timestamps
            else None
        )

        last_timestamp = (
            max(timestamps)
            if timestamps
            else None
        )

        status = (
            CASE_COMPLETE
            if timeline.status == TIMELINE_COMPLETE
            and timeline.ordering_status == TIMELINE_ORDERED
            else CASE_PARTIAL
        )

        return SecurityCaseReconstruction(
            case_id=timeline.case_id,
            agent_id=timeline.agent_id,
            status=status,
            timeline_id=timeline.timeline_id,
            entry_count=len(timeline.entries),
            first_timestamp=first_timestamp,
            last_timestamp=last_timestamp,
            decisions=decisions,
            sources=sources,
            requests=requests,
            gaps=timeline.gaps,
            evidence=dict(timeline.evidence),
            execution_performed_here=False,
        )

    def snapshot_all(
        self,
    ) -> tuple[SecurityEvidenceTimeline, ...]:
        timelines: list[SecurityEvidenceTimeline] = []

        for agent_timelines in self._history.values():
            timelines.extend(agent_timelines)

        return tuple(timelines)

    def reset(self) -> None:
        self._history.clear()


def timeline_is_complete(
    timeline: SecurityEvidenceTimeline,
) -> bool:
    return (
        timeline.status == TIMELINE_COMPLETE
        and timeline.ordering_status == TIMELINE_ORDERED
    )


def timeline_has_gaps(
    timeline: SecurityEvidenceTimeline,
) -> bool:
    return bool(timeline.gaps)


def case_is_complete(
    case: SecurityCaseReconstruction,
) -> bool:
    return case.status == CASE_COMPLETE


def timeline_is_read_only() -> bool:
    return True


def decision_is_modified_here() -> bool:
    return False


def enforcement_is_executed_here() -> bool:
    return False


def malicious_intent_is_inferred_here() -> bool:
    return False