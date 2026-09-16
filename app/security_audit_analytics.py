"""
Day 69 - Security Audit Analytics & Evidence Correlation.

This module provides deterministic, read-only analytics over the
Security Decision Audit Trail.

Security boundaries:
- Does not create security decisions.
- Does not modify existing decisions.
- Does not execute enforcement.
- Does not infer malicious intent.
- Does not calculate a universal Varynx security score.
- Does not modify adaptive response or authorization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ANALYTICS_COMPLETE = "ANALYTICS_COMPLETE"
ANALYTICS_PARTIAL = "ANALYTICS_PARTIAL"

DIRECTIONS = (
    "ALLOW",
    "MONITOR",
    "STEP_UP_VERIFICATION",
    "REDUCE_SCOPE",
    "HUMAN_REVIEW",
    "BLOCK",
)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _validate_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    value = value.strip()

    if not value:
        raise ValueError(f"{field_name} must not be empty")

    return value


def _validate_mapping(
    value: Mapping[str, Any],
    field_name: str,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")

    return dict(value)


def _validate_events(
    events: Iterable[Any],
) -> tuple[Any, ...]:
    if isinstance(events, (str, bytes)):
        raise TypeError("events must be an iterable of audit events")

    materialized = tuple(events)

    if not materialized:
        raise ValueError("events must not be empty")

    return materialized


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AuditAnalyticsSummary:
    """
    Deterministic aggregate summary of audit events.
    """

    agent_id: str
    status: str
    total_events: int
    unique_requests: int
    event_type_counts: dict[str, int]
    decision_counts: dict[str, int]
    request_event_counts: dict[str, int]
    execution_events: int
    non_execution_events: int
    evidence_event_count: int
    event_types: tuple[str, ...]
    decisions: tuple[str, ...]


@dataclass(frozen=True)
class AuditRequestAnalysis:
    """
    Request-level reconstruction of recorded audit activity.
    """

    agent_id: str
    request_id: str
    event_count: int
    event_types: tuple[str, ...]
    decisions: tuple[str, ...]
    sequence_numbers: tuple[int, ...]
    evidence: tuple[dict[str, Any], ...]
    execution_performed_here: bool


@dataclass(frozen=True)
class AuditEvidenceCorrelation:
    """
    Read-only correlation of evidence attached to audit events.
    """

    agent_id: str
    request_id: str | None
    event_count: int
    evidence_keys: tuple[str, ...]
    evidence_fragments: tuple[dict[str, Any], ...]
    consistent_execution_boundary: bool


# ---------------------------------------------------------------------------
# Event extraction helpers
# ---------------------------------------------------------------------------

def _event_value(event: Any, field_name: str) -> Any:
    """
    Read an event attribute without assuming a concrete implementation.

    This keeps analytics compatible with frozen dataclasses and simple
    test doubles.
    """
    if not hasattr(event, field_name):
        raise AttributeError(
            f"audit event is missing required field: {field_name}"
        )

    return getattr(event, field_name)


def _event_evidence(event: Any) -> dict[str, Any]:
    evidence = _event_value(event, "evidence")

    return _validate_mapping(evidence, "event.evidence")


# ---------------------------------------------------------------------------
# Core analytics
# ---------------------------------------------------------------------------

class SecurityAuditAnalytics:
    """
    Read-only analytics engine for SecurityDecisionAuditTrail events.

    Events are supplied by the caller. The analytics engine never mutates
    those events.
    """

    def __init__(self) -> None:
        self._summaries: dict[str, AuditAnalyticsSummary] = {}
        self._request_analyses: dict[
            tuple[str, str],
            AuditRequestAnalysis,
        ] = {}

    def summarize(
        self,
        agent_id: str,
        events: Iterable[Any],
    ) -> AuditAnalyticsSummary:
        agent_id = _validate_text(agent_id, "agent_id")
        materialized = _validate_events(events)

        event_type_counts: dict[str, int] = {}
        decision_counts: dict[str, int] = {}
        request_event_counts: dict[str, int] = {}

        request_ids: set[str] = set()
        event_types: list[str] = []
        decisions: list[str] = []

        execution_events = 0
        non_execution_events = 0
        evidence_event_count = 0

        for event in materialized:
            event_agent = _validate_text(
                _event_value(event, "agent_id"),
                "event.agent_id",
            )

            if event_agent != agent_id:
                raise ValueError(
                    "all events must belong to the requested agent"
                )

            event_type = _validate_text(
                _event_value(event, "event_type"),
                "event.event_type",
            )

            request_id = _validate_text(
                _event_value(event, "request_id"),
                "event.request_id",
            )

            decision = getattr(event, "decision", None)

            request_ids.add(request_id)

            event_type_counts[event_type] = (
                event_type_counts.get(event_type, 0) + 1
            )

            request_event_counts[request_id] = (
                request_event_counts.get(request_id, 0) + 1
            )

            if event_type not in event_types:
                event_types.append(event_type)

            if decision is not None:
                decision = _validate_text(
                    decision,
                    "event.decision",
                )

                decision_counts[decision] = (
                    decision_counts.get(decision, 0) + 1
                )

                if decision not in decisions:
                    decisions.append(decision)

            execution_performed = bool(
                _event_value(
                    event,
                    "execution_performed_here",
                )
            )

            if execution_performed:
                execution_events += 1
            else:
                non_execution_events += 1

            evidence = _event_evidence(event)

            if evidence:
                evidence_event_count += 1

        status = (
            ANALYTICS_COMPLETE
            if non_execution_events == len(materialized)
            else ANALYTICS_PARTIAL
        )

        summary = AuditAnalyticsSummary(
            agent_id=agent_id,
            status=status,
            total_events=len(materialized),
            unique_requests=len(request_ids),
            event_type_counts=dict(event_type_counts),
            decision_counts=dict(decision_counts),
            request_event_counts=dict(request_event_counts),
            execution_events=execution_events,
            non_execution_events=non_execution_events,
            evidence_event_count=evidence_event_count,
            event_types=tuple(event_types),
            decisions=tuple(decisions),
        )

        self._summaries[agent_id] = summary

        return summary

    def analyze_request(
        self,
        agent_id: str,
        request_id: str,
        events: Iterable[Any],
    ) -> AuditRequestAnalysis:
        agent_id = _validate_text(agent_id, "agent_id")
        request_id = _validate_text(request_id, "request_id")

        materialized = _validate_events(events)

        matching_events = []

        for event in materialized:
            event_agent = _validate_text(
                _event_value(event, "agent_id"),
                "event.agent_id",
            )

            event_request = _validate_text(
                _event_value(event, "request_id"),
                "event.request_id",
            )

            if event_agent == agent_id and event_request == request_id:
                matching_events.append(event)

        if not matching_events:
            raise ValueError(
                "no audit events found for the requested agent and request"
            )

        event_types: list[str] = []
        decisions: list[str] = []
        sequence_numbers: list[int] = []
        evidence: list[dict[str, Any]] = []

        execution_flags: list[bool] = []

        for event in matching_events:
            event_type = _validate_text(
                _event_value(event, "event_type"),
                "event.event_type",
            )

            if event_type not in event_types:
                event_types.append(event_type)

            decision = getattr(event, "decision", None)

            if decision is not None:
                decision = _validate_text(
                    decision,
                    "event.decision",
                )

                if decision not in decisions:
                    decisions.append(decision)

            sequence_number = _event_value(
                event,
                "sequence_number",
            )

            if not isinstance(sequence_number, int):
                raise TypeError(
                    "event.sequence_number must be an integer"
                )

            sequence_numbers.append(sequence_number)

            evidence.append(dict(_event_evidence(event)))

            execution_flags.append(
                bool(
                    _event_value(
                        event,
                        "execution_performed_here",
                    )
                )
            )

        analysis = AuditRequestAnalysis(
            agent_id=agent_id,
            request_id=request_id,
            event_count=len(matching_events),
            event_types=tuple(event_types),
            decisions=tuple(decisions),
            sequence_numbers=tuple(sequence_numbers),
            evidence=tuple(evidence),
            execution_performed_here=any(execution_flags),
        )

        self._request_analyses[(agent_id, request_id)] = analysis

        return analysis

    def correlate_evidence(
        self,
        agent_id: str,
        events: Iterable[Any],
        request_id: str | None = None,
    ) -> AuditEvidenceCorrelation:
        agent_id = _validate_text(agent_id, "agent_id")
        materialized = _validate_events(events)

        if request_id is not None:
            request_id = _validate_text(
                request_id,
                "request_id",
            )

        fragments: list[dict[str, Any]] = []
        evidence_keys: list[str] = []
        execution_flags: list[bool] = []

        selected_count = 0

        for event in materialized:
            event_agent = _validate_text(
                _event_value(event, "agent_id"),
                "event.agent_id",
            )

            if event_agent != agent_id:
                continue

            event_request = _validate_text(
                _event_value(event, "request_id"),
                "event.request_id",
            )

            if request_id is not None and event_request != request_id:
                continue

            selected_count += 1

            event_evidence = _event_evidence(event)

            copied_evidence = dict(event_evidence)

            fragments.append(copied_evidence)

            for key in copied_evidence:
                if key not in evidence_keys:
                    evidence_keys.append(key)

            execution_flags.append(
                bool(
                    _event_value(
                        event,
                        "execution_performed_here",
                    )
                )
            )

        if selected_count == 0:
            raise ValueError("no matching audit events found")

        # Day 69 itself must never execute enforcement.
        # A true execution flag therefore makes the analytics boundary
        # incomplete rather than being silently rewritten.
        consistent_execution_boundary = not any(execution_flags)

        return AuditEvidenceCorrelation(
            agent_id=agent_id,
            request_id=request_id,
            event_count=selected_count,
            evidence_keys=tuple(evidence_keys),
            evidence_fragments=tuple(fragments),
            consistent_execution_boundary=consistent_execution_boundary,
        )

    # ------------------------------------------------------------------
    # Stored results
    # ------------------------------------------------------------------

    def latest_summary(
        self,
        agent_id: str,
    ) -> AuditAnalyticsSummary | None:
        agent_id = _validate_text(agent_id, "agent_id")
        return self._summaries.get(agent_id)

    def latest_request_analysis(
        self,
        agent_id: str,
        request_id: str,
    ) -> AuditRequestAnalysis | None:
        agent_id = _validate_text(agent_id, "agent_id")
        request_id = _validate_text(request_id, "request_id")

        return self._request_analyses.get(
            (agent_id, request_id)
        )

    def snapshot_summaries(
        self,
    ) -> dict[str, AuditAnalyticsSummary]:
        return dict(self._summaries)

    def snapshot_request_analyses(
        self,
    ) -> dict[tuple[str, str], AuditRequestAnalysis]:
        return dict(self._request_analyses)

    def reset(self) -> None:
        self._summaries.clear()
        self._request_analyses.clear()


# ---------------------------------------------------------------------------
# Standalone analytics helpers
# ---------------------------------------------------------------------------

def count_event_types(
    events: Iterable[Any],
) -> dict[str, int]:
    materialized = _validate_events(events)

    counts: dict[str, int] = {}

    for event in materialized:
        event_type = _validate_text(
            _event_value(event, "event_type"),
            "event.event_type",
        )

        counts[event_type] = counts.get(event_type, 0) + 1

    return counts


def count_decisions(
    events: Iterable[Any],
) -> dict[str, int]:
    materialized = _validate_events(events)

    counts: dict[str, int] = {}

    for event in materialized:
        decision = getattr(event, "decision", None)

        if decision is None:
            continue

        decision = _validate_text(
            decision,
            "event.decision",
        )

        counts[decision] = counts.get(decision, 0) + 1

    return counts


def verify_non_execution_boundary(
    events: Iterable[Any],
) -> bool:
    materialized = _validate_events(events)

    return all(
        not bool(
            _event_value(
                event,
                "execution_performed_here",
            )
        )
        for event in materialized
    )


def analytics_is_read_only() -> bool:
    return True


def decision_is_modified_here() -> bool:
    return False


def enforcement_is_executed_here() -> bool:
    return False


__all__ = [
    "ANALYTICS_COMPLETE",
    "ANALYTICS_PARTIAL",
    "AuditAnalyticsSummary",
    "AuditRequestAnalysis",
    "AuditEvidenceCorrelation",
    "SecurityAuditAnalytics",
    "count_event_types",
    "count_decisions",
    "verify_non_execution_boundary",
    "analytics_is_read_only",
    "decision_is_modified_here",
    "enforcement_is_executed_here",
]