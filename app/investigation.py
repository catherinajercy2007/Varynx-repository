"""
Varynx / AegisGuard Day 42
Security Investigation and Evidence Analysis

Purpose
-------
Provide a deterministic investigation layer over security events.

The module supports:

1. Database-backed event investigation.
2. Agent/task/action/resource/decision/risk/time filtering.
3. Investigation timelines.
4. Agent behavioral profiles.
5. Risk history.
6. Decision history.
7. Suspicious-event identification.
8. Audit-to-event mapping.
9. Evidence aggregation.
10. Structured investigation reports.

Research discipline
-------------------
This module reports observable evidence.

It does NOT claim that correlation proves malicious intent.

It does NOT manufacture risk, anomaly or statistical evidence.

It is intended to provide a traceable evidence layer for the
Varynx behavioral security research pipeline.
"""

from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Iterable, Mapping


# ============================================================
# CONFIGURATION
# ============================================================

DATABASE_PATH = "aegisguard.db"

INVESTIGATION_SCHEMA_NAME = "varynx_investigation"
INVESTIGATION_SCHEMA_VERSION = "1.0"


VALID_DECISIONS = {
    "ALLOW",
    "DENY",
}

VALID_RISK_LEVELS = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
}


# ============================================================
# DATA MODEL
# ============================================================

@dataclass(frozen=True)
class InvestigationTimelineEntry:
    """
    Normalized representation of one investigation timeline event.
    """

    event_id: int
    timestamp: str
    agent_id: str
    task_id: str
    action: str
    resource: str
    decision: str
    risk: float
    reason: str

    @classmethod
    def from_mapping(
        cls,
        event: Mapping[str, Any],
    ) -> "InvestigationTimelineEntry":
        """
        Build a timeline entry from a mapping.
        """

        return cls(
            event_id=int(
                event.get("id", event.get("event_id", 0))
                or 0
            ),
            timestamp=str(
                event.get("timestamp", "")
            ),
            agent_id=str(
                event.get("agent_id", "")
            ),
            task_id=str(
                event.get("task_id", "")
            ),
            action=str(
                event.get("action", "")
            ),
            resource=str(
                event.get("resource", "")
            ),
            decision=str(
                event.get("decision", "")
            ),
            risk=float(
                event.get("risk", 0)
                or 0
            ),
            reason=str(
                event.get("reason", "")
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Return a JSON/DataFrame-friendly dictionary.
        """

        return asdict(self)


# ============================================================
# DATABASE
# ============================================================

def _connect() -> sqlite3.Connection:
    """
    Create a SQLite connection.

    DATABASE_PATH intentionally remains a mutable module-level
    variable because tests replace it with a temporary database.
    """

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# VALIDATION HELPERS
# ============================================================

def _validate_limit(
    limit: int,
) -> None:

    if not isinstance(limit, int):
        raise ValueError(
            "limit must be an integer"
        )

    if limit <= 0:
        raise ValueError(
            "limit must be greater than zero"
        )

    if limit > 5000:
        raise ValueError(
            "limit cannot exceed 5000"
        )


def _validate_risk_value(
    value: int | float | None,
    name: str,
) -> None:

    if value is None:
        return

    if isinstance(value, bool):
        raise ValueError(
            f"{name} must be between 0 and 100"
        )

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"{name} must be between 0 and 100"
        )

    if not 0 <= numeric <= 100:
        raise ValueError(
            f"{name} must be between 0 and 100"
        )


def _risk_condition(
    risk_level: str,
) -> tuple[str, list[int]]:
    """
    Convert risk-level labels into SQL conditions.

    LOW       = 0-20
    MEDIUM    = 21-50
    HIGH      = 51-79
    CRITICAL  = 80-100
    """

    normalized = str(
        risk_level
    ).upper()

    if normalized == "LOW":
        return (
            "risk BETWEEN ? AND ?",
            [0, 20],
        )

    if normalized == "MEDIUM":
        return (
            "risk BETWEEN ? AND ?",
            [21, 50],
        )

    if normalized == "HIGH":
        return (
            "risk BETWEEN ? AND ?",
            [51, 79],
        )

    if normalized == "CRITICAL":
        return (
            "risk >= ?",
            [80],
        )

    raise ValueError(
        f"Unsupported risk level: {risk_level}"
    )


def _normalize_event(
    event: Any,
) -> dict[str, Any]:
    """
    Normalize a mapping or dataclass-like event.

    Invalid non-mapping objects are rejected rather than silently
    converted into misleading investigation records.
    """

    if isinstance(event, Mapping):
        return dict(event)

    if hasattr(event, "to_dict"):
        value = event.to_dict()

        if isinstance(value, Mapping):
            return dict(value)

    if hasattr(event, "model_dump"):
        value = event.model_dump()

        if isinstance(value, Mapping):
            return dict(value)

    if hasattr(event, "dict"):
        value = event.dict()

        if isinstance(value, Mapping):
            return dict(value)

    if hasattr(event, "__dict__"):
        value = vars(event)

        if isinstance(value, Mapping):
            return dict(value)

    raise TypeError(
        "Investigation events must be mappings "
        "or mapping-compatible objects."
    )


def _normalize_events(
    events: Iterable[Any] | None,
) -> list[dict[str, Any]]:

    if events is None:
        return []

    return [
        _normalize_event(event)
        for event in events
    ]


def _event_value(
    event: Mapping[str, Any],
    key: str,
    default: Any = None,
) -> Any:

    if key in event:
        return event[key]

    aliases = {
        "id": ["event_id"],
        "risk": [
            "risk_score",
            "risk_level_score",
        ],
        "timestamp": [
            "time",
            "created_at",
        ],
    }

    for alias in aliases.get(key, []):
        if alias in event:
            return event[alias]

    return default


def _risk_number(
    event: Mapping[str, Any],
) -> float:

    value = _event_value(
        event,
        "risk",
        0,
    )

    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


# ============================================================
# DATABASE INVESTIGATION
# ============================================================

def get_investigation_events(
    agent_id: str | None = None,
    task_id: str | None = None,
    action: str | None = None,
    resource: str | None = None,
    decision: str | None = None,
    risk_level: str | None = None,
    minimum_risk: int | None = None,
    maximum_risk: int | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """
    Retrieve security events using investigation filters.

    All filters are optional.

    SQL values are parameterized.
    """

    _validate_limit(limit)

    if decision is not None:

        normalized_decision = str(
            decision
        ).upper()

        if normalized_decision not in VALID_DECISIONS:
            raise ValueError(
                f"Unsupported decision: {decision}"
            )

        decision = normalized_decision

    if risk_level is not None:

        normalized_risk = str(
            risk_level
        ).upper()

        if normalized_risk not in VALID_RISK_LEVELS:
            raise ValueError(
                f"Unsupported risk level: {risk_level}"
            )

        risk_level = normalized_risk

    _validate_risk_value(
        minimum_risk,
        "minimum_risk",
    )

    _validate_risk_value(
        maximum_risk,
        "maximum_risk",
    )

    if (
        minimum_risk is not None
        and maximum_risk is not None
        and minimum_risk > maximum_risk
    ):
        raise ValueError(
            "minimum_risk cannot exceed maximum_risk"
        )

    conditions: list[str] = []
    parameters: list[Any] = []

    if agent_id:
        conditions.append(
            "agent_id = ?"
        )
        parameters.append(agent_id)

    if task_id:
        conditions.append(
            "task_id = ?"
        )
        parameters.append(task_id)

    if action:
        conditions.append(
            "action = ?"
        )
        parameters.append(action)

    if resource:
        conditions.append(
            "resource = ?"
        )
        parameters.append(resource)

    if decision:
        conditions.append(
            "decision = ?"
        )
        parameters.append(decision)

    if risk_level:

        condition, values = _risk_condition(
            risk_level
        )

        conditions.append(condition)
        parameters.extend(values)

    if minimum_risk is not None:
        conditions.append(
            "risk >= ?"
        )
        parameters.append(minimum_risk)

    if maximum_risk is not None:
        conditions.append(
            "risk <= ?"
        )
        parameters.append(maximum_risk)

    if start_time:
        conditions.append(
            "timestamp >= ?"
        )
        parameters.append(start_time)

    if end_time:
        conditions.append(
            "timestamp <= ?"
        )
        parameters.append(end_time)

    query = """
        SELECT
            id,
            timestamp,
            agent_id,
            task_id,
            action,
            resource,
            decision,
            risk,
            reason
        FROM audit_events
    """

    if conditions:

        query += (
            "\nWHERE "
            + "\nAND ".join(
                conditions
            )
        )

    query += """
        ORDER BY id DESC
        LIMIT ?
    """

    parameters.append(limit)

    connection = _connect()

    try:

        rows = connection.execute(
            query,
            parameters,
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


def get_investigation_event(
    event_id: int,
) -> dict[str, Any] | None:
    """
    Retrieve one event by database ID.
    """

    if not isinstance(
        event_id,
        int,
    ) or event_id <= 0:

        raise ValueError(
            "event_id must be greater than zero"
        )

    connection = _connect()

    try:

        row = connection.execute(
            """
            SELECT
                id,
                timestamp,
                agent_id,
                task_id,
                action,
                resource,
                decision,
                risk,
                reason
            FROM audit_events
            WHERE id = ?
            """,
            (event_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:

        connection.close()


def get_investigation_filter_options() -> dict[str, list[str]]:
    """
    Return distinct values available for investigation filters.
    """

    connection = _connect()

    try:

        agents = connection.execute(
            """
            SELECT DISTINCT agent_id
            FROM audit_events
            WHERE agent_id IS NOT NULL
            ORDER BY agent_id
            """
        ).fetchall()

        tasks = connection.execute(
            """
            SELECT DISTINCT task_id
            FROM audit_events
            WHERE task_id IS NOT NULL
            ORDER BY task_id
            """
        ).fetchall()

        actions = connection.execute(
            """
            SELECT DISTINCT action
            FROM audit_events
            WHERE action IS NOT NULL
            ORDER BY action
            """
        ).fetchall()

        resources = connection.execute(
            """
            SELECT DISTINCT resource
            FROM audit_events
            WHERE resource IS NOT NULL
            ORDER BY resource
            """
        ).fetchall()

        return {
            "agents": [
                row[0]
                for row in agents
            ],
            "tasks": [
                row[0]
                for row in tasks
            ],
            "actions": [
                row[0]
                for row in actions
            ],
            "resources": [
                row[0]
                for row in resources
            ],
        }

    finally:

        connection.close()


def count_investigation_events(
    **filters: Any,
) -> int:
    """
    Count events matching investigation filters.

    This preserves the existing filtering semantics.
    """

    return len(
        get_investigation_events(
            **filters,
            limit=5000,
        )
    )


# ============================================================
# TIMELINE
# ============================================================

def build_event_timeline(
    events: Iterable[Any] | None,
    *,
    agent_id: str | None = None,
) -> list[InvestigationTimelineEntry]:
    """
    Build a chronological investigation timeline.

    Events are ordered by timestamp and then event ID.
    """

    normalized = _normalize_events(
        events
    )

    if agent_id is not None:

        normalized = [
            event
            for event in normalized
            if str(
                _event_value(
                    event,
                    "agent_id",
                    "",
                )
            )
            == str(agent_id)
        ]

    normalized.sort(
        key=lambda event: (
            str(
                _event_value(
                    event,
                    "timestamp",
                    "",
                )
            ),
            int(
                _event_value(
                    event,
                    "id",
                    _event_value(
                        event,
                        "event_id",
                        0,
                    ),
                )
                or 0
            ),
        )
    )

    return [
        InvestigationTimelineEntry.from_mapping(
            event
        )
        for event in normalized
    ]


# ============================================================
# AGENT PROFILE
# ============================================================

def build_agent_profile(
    events: Iterable[Any] | None,
    *,
    agent_id: str | None = None,
) -> dict[str, Any]:
    """
    Build an evidence-based profile for an agent.
    """

    normalized = _normalize_events(
        events
    )

    if agent_id is not None:

        normalized = [
            event
            for event in normalized
            if str(
                _event_value(
                    event,
                    "agent_id",
                    "",
                )
            )
            == str(agent_id)
        ]

    if not normalized:

        return {
            "agent_id": agent_id,
            "event_count": 0,
            "allow_count": 0,
            "deny_count": 0,
            "average_risk": 0.0,
            "maximum_risk": 0.0,
            "unique_tasks": 0,
            "unique_actions": 0,
            "unique_resources": 0,
        }

    risks = [
        _risk_number(event)
        for event in normalized
    ]

    allow_count = sum(
        str(
            _event_value(
                event,
                "decision",
                "",
            )
        ).upper()
        == "ALLOW"
        for event in normalized
    )

    deny_count = sum(
        str(
            _event_value(
                event,
                "decision",
                "",
            )
        ).upper()
        == "DENY"
        for event in normalized
    )

    tasks = {
        str(
            _event_value(
                event,
                "task_id",
                "",
            )
        )
        for event in normalized
        if _event_value(
            event,
            "task_id",
            None,
        ) is not None
    }

    actions = {
        str(
            _event_value(
                event,
                "action",
                "",
            )
        )
        for event in normalized
        if _event_value(
            event,
            "action",
            None,
        ) is not None
    }

    resources = {
        str(
            _event_value(
                event,
                "resource",
                "",
            )
        )
        for event in normalized
        if _event_value(
            event,
            "resource",
            None,
        ) is not None
    }

    resolved_agent_id = agent_id

    if resolved_agent_id is None:

        resolved_agent_id = str(
            _event_value(
                normalized[0],
                "agent_id",
                "",
            )
        )

    return {
        "agent_id": resolved_agent_id,
        "event_count": len(normalized),
        "allow_count": int(allow_count),
        "deny_count": int(deny_count),
        "deny_rate": round(
            deny_count / len(normalized),
            6,
        ),
        "average_risk": round(
            sum(risks) / len(risks),
            4,
        ),
        "maximum_risk": max(risks),
        "unique_tasks": len(tasks),
        "unique_actions": len(actions),
        "unique_resources": len(resources),
    }


# ============================================================
# RISK HISTORY
# ============================================================

def build_risk_history(
    events: Iterable[Any] | None,
    *,
    agent_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Return chronological risk observations.
    """

    timeline = build_event_timeline(
        events,
        agent_id=agent_id,
    )

    return [
        {
            "event_id":
                entry.event_id,

            "timestamp":
                entry.timestamp,

            "agent_id":
                entry.agent_id,

            "risk":
                entry.risk,

            "decision":
                entry.decision,
        }
        for entry in timeline
    ]


# ============================================================
# DECISION HISTORY
# ============================================================

def build_decision_history(
    events: Iterable[Any] | None,
    *,
    agent_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Return chronological authorization decisions.
    """

    timeline = build_event_timeline(
        events,
        agent_id=agent_id,
    )

    return [
        {
            "event_id":
                entry.event_id,

            "timestamp":
                entry.timestamp,

            "agent_id":
                entry.agent_id,

            "decision":
                entry.decision,

            "risk":
                entry.risk,

            "action":
                entry.action,

            "resource":
                entry.resource,
        }
        for entry in timeline
    ]


# ============================================================
# SUSPICIOUS EVENTS
# ============================================================

def find_suspicious_events(
    events: Iterable[Any] | None,
    *,
    minimum_risk: float = 80,
    include_denied: bool = True,
) -> list[dict[str, Any]]:
    """
    Identify events requiring investigation attention.

    Default criterion:
        risk >= 80

    Optionally includes all denied events even if their risk is below
    the threshold.

    This function identifies evidence requiring attention; it does
    not establish malicious intent.
    """

    _validate_risk_value(
        minimum_risk,
        "minimum_risk",
    )

    normalized = _normalize_events(
        events
    )

    suspicious: list[dict[str, Any]] = []

    for event in normalized:

        decision = str(
            _event_value(
                event,
                "decision",
                "",
            )
        ).upper()

        risk = _risk_number(
            event
        )

        if (
            risk >= minimum_risk
            or (
                include_denied
                and decision == "DENY"
            )
        ):

            suspicious.append(
                dict(event)
            )

    suspicious.sort(
        key=lambda event: (
            -_risk_number(event),
            str(
                _event_value(
                    event,
                    "timestamp",
                    "",
                )
            ),
        )
    )

    return suspicious


# ============================================================
# AUDIT MAPPING
# ============================================================

def map_audits_to_events(
    audits: Iterable[Any] | None,
    events: Iterable[Any] | None,
) -> list[dict[str, Any]]:
    """
    Map audit records to corresponding security events.

    Matching priority:

    1. event ID
    2. timestamp + agent ID
    3. agent ID + action + resource

    Unmatched audits are retained with event=None.
    """

    normalized_audits = _normalize_events(
        audits
    )

    normalized_events = _normalize_events(
        events
    )

    by_id: dict[str, dict[str, Any]] = {}
    by_timestamp_agent: dict[
        tuple[str, str],
        dict[str, Any],
    ] = {}
    by_signature: dict[
        tuple[str, str, str],
        dict[str, Any],
    ] = {}

    for event in normalized_events:

        event_id = _event_value(
            event,
            "id",
            _event_value(
                event,
                "event_id",
                None,
            ),
        )

        if event_id is not None:
            by_id[str(event_id)] = event

        timestamp = str(
            _event_value(
                event,
                "timestamp",
                "",
            )
        )

        agent_id = str(
            _event_value(
                event,
                "agent_id",
                "",
            )
        )

        action = str(
            _event_value(
                event,
                "action",
                "",
            )
        )

        resource = str(
            _event_value(
                event,
                "resource",
                "",
            )
        )

        by_timestamp_agent[
            (
                timestamp,
                agent_id,
            )
        ] = event

        by_signature[
            (
                agent_id,
                action,
                resource,
            )
        ] = event

    results: list[dict[str, Any]] = []

    for audit in normalized_audits:

        audit_id = _event_value(
            audit,
            "id",
            _event_value(
                audit,
                "event_id",
                None,
            ),
        )

        event = None

        if audit_id is not None:
            event = by_id.get(
                str(audit_id)
            )

        if event is None:

            timestamp = str(
                _event_value(
                    audit,
                    "timestamp",
                    "",
                )
            )

            agent_id = str(
                _event_value(
                    audit,
                    "agent_id",
                    "",
                )
            )

            event = by_timestamp_agent.get(
                (
                    timestamp,
                    agent_id,
                )
            )

        if event is None:

            agent_id = str(
                _event_value(
                    audit,
                    "agent_id",
                    "",
                )
            )

            action = str(
                _event_value(
                    audit,
                    "action",
                    "",
                )
            )

            resource = str(
                _event_value(
                    audit,
                    "resource",
                    "",
                )
            )

            event = by_signature.get(
                (
                    agent_id,
                    action,
                    resource,
                )
            )

        results.append(
            {
                "audit":
                    dict(audit),

                "event":
                    dict(event)
                    if event is not None
                    else None,

                "matched":
                    event is not None,
            }
        )

    return results


# ============================================================
# EVIDENCE AGGREGATION
# ============================================================

def aggregate_investigation_evidence(
    events: Iterable[Any] | None,
    *,
    agent_id: str | None = None,
) -> dict[str, Any]:
    """
    Aggregate observable evidence for an investigation scope.
    """

    normalized = _normalize_events(
        events
    )

    if agent_id is not None:

        normalized = [
            event
            for event in normalized
            if str(
                _event_value(
                    event,
                    "agent_id",
                    "",
                )
            )
            == str(agent_id)
        ]

    risks = [
        _risk_number(event)
        for event in normalized
    ]

    decisions = [
        str(
            _event_value(
                event,
                "decision",
                "",
            )
        ).upper()
        for event in normalized
    ]

    actions = {
        str(
            _event_value(
                event,
                "action",
                "",
            )
        )
        for event in normalized
    }

    resources = {
        str(
            _event_value(
                event,
                "resource",
                "",
            )
        )
        for event in normalized
    }

    tasks = {
        str(
            _event_value(
                event,
                "task_id",
                "",
            )
        )
        for event in normalized
    }

    denied_events = sum(
        decision == "DENY"
        for decision in decisions
    )

    critical_events = sum(
        risk >= 80
        for risk in risks
    )

    high_risk_events = sum(
        risk >= 51
        for risk in risks
    )

    return {
        "event_count":
            len(normalized),

        "allow_count":
            decisions.count("ALLOW"),

        "deny_count":
            denied_events,

        "deny_rate":
            round(
                denied_events / len(normalized),
                6,
            )
            if normalized
            else 0.0,

        "average_risk":
            round(
                sum(risks) / len(risks),
                4,
            )
            if risks
            else 0.0,

        "maximum_risk":
            max(risks)
            if risks
            else 0.0,

        "high_risk_events":
            high_risk_events,

        "critical_events":
            critical_events,

        "unique_tasks":
            len(tasks - {""}),

        "unique_actions":
            len(actions - {""}),

        "unique_resources":
            len(resources - {""}),
    }


# ============================================================
# INVESTIGATION REPORT
# ============================================================

def build_investigation_report(
    events: Iterable[Any] | None,
    *,
    agent_id: str | None = None,
    minimum_suspicious_risk: float = 80,
) -> dict[str, Any]:
    """
    Build a complete structured investigation report.

    The report contains evidence, not an assertion of malicious intent.
    """

    normalized = _normalize_events(
        events
    )

    if agent_id is not None:

        normalized = [
            event
            for event in normalized
            if str(
                _event_value(
                    event,
                    "agent_id",
                    "",
                )
            )
            == str(agent_id)
        ]

    timeline = build_event_timeline(
        normalized
    )

    profile = build_agent_profile(
        normalized,
        agent_id=agent_id,
    )

    risk_history = build_risk_history(
        normalized
    )

    decision_history = build_decision_history(
        normalized
    )

    suspicious_events = find_suspicious_events(
        normalized,
        minimum_risk=minimum_suspicious_risk,
    )

    evidence = aggregate_investigation_evidence(
        normalized,
        agent_id=agent_id,
    )

    return {
        "schema": {
            "name":
                INVESTIGATION_SCHEMA_NAME,

            "version":
                INVESTIGATION_SCHEMA_VERSION,
        },

        "investigation": {
            "agent_id":
                agent_id,

            "generated_at":
                datetime.utcnow().isoformat()
                + "Z",

            "evidence_only":
                True,
        },

        "summary":
            evidence,

        "agent_profile":
            profile,

        "timeline": [
            entry.to_dict()
            for entry in timeline
        ],

        "risk_history":
            risk_history,

        "decision_history":
            decision_history,

        "suspicious_events":
            suspicious_events,

        "interpretation": {
            "statement":
                (
                    "The report summarizes observable security "
                    "evidence. Correlation or suspicious activity "
                    "does not by itself establish malicious intent."
                )
        },
    }


# ============================================================
# INVESTIGATION COLLECTION HELPERS
# ============================================================

def get_investigation_agents(
    events: Iterable[Any] | None,
) -> list[str]:
    """
    Return sorted unique agent IDs.
    """

    normalized = _normalize_events(
        events
    )

    return sorted(
        {
            str(
                _event_value(
                    event,
                    "agent_id",
                    "",
                )
            )
            for event in normalized
            if _event_value(
                event,
                "agent_id",
                None,
            ) is not None
        }
    )


def get_investigation_event_count(
    events: Iterable[Any] | None,
    *,
    agent_id: str | None = None,
) -> int:
    """
    Return event count for an investigation scope.
    """

    normalized = _normalize_events(
        events
    )

    if agent_id is None:
        return len(normalized)

    return sum(
        str(
            _event_value(
                event,
                "agent_id",
                "",
            )
        )
        == str(agent_id)
        for event in normalized
    )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "DATABASE_PATH",
    "VALID_DECISIONS",
    "VALID_RISK_LEVELS",
    "INVESTIGATION_SCHEMA_NAME",
    "INVESTIGATION_SCHEMA_VERSION",
    "InvestigationTimelineEntry",
    "get_investigation_events",
    "get_investigation_event",
    "get_investigation_filter_options",
    "count_investigation_events",
    "build_event_timeline",
    "build_agent_profile",
    "build_risk_history",
    "build_decision_history",
    "find_suspicious_events",
    "map_audits_to_events",
    "aggregate_investigation_evidence",
    "build_investigation_report",
    "get_investigation_agents",
    "get_investigation_event_count",
]