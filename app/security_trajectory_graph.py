
"""Varynx Day 89: Security Trajectory and Action-Sequence Risk Graph.

Builds a deterministic, read-only graph from existing security evidence.
Findings describe observed sequences; they do not prove intent or authorize
or enforce actions. No universal risk score is calculated.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Iterable, Mapping


VERSION = "DAY89-V1"

EDGE_CHRONOLOGICAL = "CHRONOLOGICAL_SUCCESSION"
EDGE_REPEATED_DENIAL = "REPEATED_DENIAL_SEQUENCE"
EDGE_RESOURCE_EXPANSION = "RESOURCE_EXPANSION"
EDGE_CONTEXT_CHANGE = "CONTEXT_CHANGE"
EDGE_RISK_ESCALATION = "RISK_ESCALATION"

FINDING_REPEATED_DENIALS = "REPEATED_DENIALS"
FINDING_RESOURCE_EXPANSION = "RESOURCE_EXPANSION"
FINDING_CONTEXT_CHANGE = "CONTEXT_CHANGE"
FINDING_RISK_ESCALATION = "RISK_ESCALATION"
FINDING_DECISION_CHANGE = "DECISION_CHANGE"

SEVERITY_INFO = "INFO"
SEVERITY_LOW = "LOW"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_HIGH = "HIGH"


def _text(value: Any, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _score(value: Any) -> float | None:
    """Read a risk signal only when it is explicitly present and valid."""
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("risk_score must be a finite number from 0 to 100")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "risk_score must be a finite number from 0 to 100"
        ) from exc
    if not isfinite(result) or not 0 <= result <= 100:
        raise ValueError("risk_score must be a finite number from 0 to 100")
    return result


def _digest(payload: Mapping[str, Any]) -> str:
    serialized = json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    )
    return sha256(serialized.encode("utf-8")).hexdigest()


def _read(entry: Any, name: str, default: Any = None) -> Any:
    if isinstance(entry, Mapping):
        return entry.get(name, default)
    return getattr(entry, name, default)


def _resource_prefix(resource: str) -> tuple[str, ...]:
    """Return path prefixes without treating arbitrary text as a path."""
    normalized = resource.strip("/")
    if not normalized:
        return ()
    parts = normalized.split("/")
    return tuple("/".join(parts[:i]) for i in range(1, len(parts) + 1))


@dataclass(frozen=True)
class TrajectoryNode:
    node_id: str
    agent_id: str
    case_id: str
    sequence_number: int
    entry_id: str
    timestamp: str | None
    event_type: str
    action: str | None
    resource: str | None
    context: str | None
    decision: str | None
    risk_score: float | None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["version"] = VERSION
        return result


@dataclass(frozen=True)
class TrajectoryEdge:
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_type: str
    explanation: str
    evidence_entry_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["version"] = VERSION
        result["evidence_entry_ids"] = list(self.evidence_entry_ids)
        return result


@dataclass(frozen=True)
class TrajectoryFinding:
    finding_id: str
    finding_type: str
    severity: str
    explanation: str
    node_ids: tuple[str, ...]
    evidence_entry_ids: tuple[str, ...]
    observed_values: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["version"] = VERSION
        result["node_ids"] = list(self.node_ids)
        result["evidence_entry_ids"] = list(self.evidence_entry_ids)
        result["observed_values"] = list(self.observed_values)
        return result


@dataclass(frozen=True)
class SecurityTrajectoryGraph:
    graph_id: str
    agent_id: str
    case_id: str
    nodes: tuple[TrajectoryNode, ...]
    edges: tuple[TrajectoryEdge, ...]
    findings: tuple[TrajectoryFinding, ...]
    input_entry_count: int
    omitted_entries: int
    evidence_complete: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": VERSION,
            "graph_id": self.graph_id,
            "agent_id": self.agent_id,
            "case_id": self.case_id,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "findings": [finding.to_dict() for finding in self.findings],
            "input_entry_count": self.input_entry_count,
            "omitted_entries": self.omitted_entries,
            "evidence_complete": self.evidence_complete,
            "is_authorization_decision": False,
            "executes_enforcement": False,
            "infers_malicious_intent": False,
            "calculates_universal_risk_score": False,
        }


def _make_edge(
    source: TrajectoryNode,
    target: TrajectoryNode,
    edge_type: str,
    explanation: str,
) -> TrajectoryEdge:
    payload = {
        "source": source.node_id,
        "target": target.node_id,
        "type": edge_type,
        "explanation": explanation,
    }
    return TrajectoryEdge(
        edge_id="edge-" + _digest(payload)[:20],
        source_node_id=source.node_id,
        target_node_id=target.node_id,
        edge_type=edge_type,
        explanation=explanation,
        evidence_entry_ids=(source.entry_id, target.entry_id),
    )


def _make_finding(
    finding_type: str,
    severity: str,
    explanation: str,
    nodes: tuple[TrajectoryNode, ...],
    observed_values: tuple[str, ...] = (),
) -> TrajectoryFinding:
    entry_ids = tuple(node.entry_id for node in nodes)
    payload = {
        "type": finding_type,
        "entries": entry_ids,
        "observed_values": observed_values,
    }
    return TrajectoryFinding(
        finding_id="finding-" + _digest(payload)[:20],
        finding_type=finding_type,
        severity=severity,
        explanation=explanation,
        node_ids=tuple(node.node_id for node in nodes),
        evidence_entry_ids=entry_ids,
        observed_values=observed_values,
    )


def build_security_trajectory(
    *,
    agent_id: str,
    case_id: str,
    entries: Iterable[Any],
    repeated_denial_threshold: int = 2,
    resource_expansion_threshold: int = 2,
    risk_increase_threshold: float = 15.0,
    evidence_complete: bool = True,
) -> SecurityTrajectoryGraph:
    """Build a deterministic action-sequence graph from supplied evidence.

    Accepted entries are Day 73 SecurityEvidenceEntry objects or mappings
    with equivalent fields: entry_id, agent_id, case_id, sequence_number,
    event_type, timestamp, request_id (optional), decision (optional),
    and evidence (optional mapping).

    The function does not query a database, infer missing events, or execute
    security controls. The caller is responsible for selecting one case.
    """
    agent_id = _text(agent_id, "agent_id")
    case_id = _text(case_id, "case_id")

    for name, value in (
        ("repeated_denial_threshold", repeated_denial_threshold),
        ("resource_expansion_threshold", resource_expansion_threshold),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 2:
            raise ValueError(f"{name} must be an integer >= 2")

    risk_increase_threshold = _score(risk_increase_threshold)
    if risk_increase_threshold is None or risk_increase_threshold <= 0:
        raise ValueError("risk_increase_threshold must be greater than zero")
    if not isinstance(evidence_complete, bool):
        raise TypeError("evidence_complete must be bool")

    if isinstance(entries, (str, bytes, Mapping)):
        raise TypeError("entries must be an iterable of evidence entries")

    raw_entries = list(entries)
    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for entry in raw_entries:
        entry_agent = _text(_read(entry, "agent_id"), "entry.agent_id")
        entry_case = _text(_read(entry, "case_id"), "entry.case_id")
        if entry_agent != agent_id or entry_case != case_id:
            raise ValueError("all entries must match agent_id and case_id")

        entry_id = _text(_read(entry, "entry_id"), "entry.entry_id")
        if entry_id in seen_ids:
            raise ValueError(f"duplicate entry_id: {entry_id}")
        seen_ids.add(entry_id)

        sequence = _read(entry, "sequence_number")
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
            raise ValueError("sequence_number must be an integer >= 1")

        event_type = _text(_read(entry, "event_type"), "entry.event_type")
        timestamp = _read(entry, "timestamp")
        if timestamp is not None and not isinstance(timestamp, str):
            raise TypeError("timestamp must be a string or None")

        evidence = _read(entry, "evidence", {})
        if evidence is None:
            evidence = {}
        if not isinstance(evidence, Mapping):
            raise TypeError("entry.evidence must be a mapping")

        action = _text(evidence.get("action"), "action", optional=True)
        resource = _text(evidence.get("resource"), "resource", optional=True)
        context = _text(
            evidence.get("context", evidence.get("context_id")),
            "context", optional=True,
        )
        risk = _score(evidence.get("risk_score", evidence.get("risk")))
        decision = _text(_read(entry, "decision"), "decision", optional=True)
        if decision is not None:
            decision = decision.upper()

        normalized.append({
            "entry_id": entry_id,
            "sequence_number": sequence,
            "timestamp": timestamp,
            "event_type": event_type,
            "action": action,
            "resource": resource,
            "context": context,
            "decision": decision,
            "risk_score": risk,
        })

    normalized.sort(key=lambda item: (
        item["sequence_number"],
        item["timestamp"] or "",
        item["entry_id"],
    ))

    if len({item["sequence_number"] for item in normalized}) != len(normalized):
        raise ValueError("sequence_number values must be unique within a case")

    nodes: list[TrajectoryNode] = []
    for item in normalized:
        identity = {
            "agent_id": agent_id,
            "case_id": case_id,
            "entry_id": item["entry_id"],
            "sequence_number": item["sequence_number"],
        }
        nodes.append(TrajectoryNode(
            node_id="node-" + _digest(identity)[:20],
            agent_id=agent_id,
            case_id=case_id,
            **item,
        ))

    edges: list[TrajectoryEdge] = []
    findings: list[TrajectoryFinding] = []

    # Every adjacent observed event receives a chronological edge.
    for previous, current in zip(nodes, nodes[1:]):
        edges.append(_make_edge(
            previous, current, EDGE_CHRONOLOGICAL,
            "The events are adjacent in the supplied sequence ordering.",
        ))

        if previous.context and current.context and previous.context != current.context:
            edges.append(_make_edge(
                previous, current, EDGE_CONTEXT_CHANGE,
                "The supplied context identifier changed between events.",
            ))
            findings.append(_make_finding(
                FINDING_CONTEXT_CHANGE, SEVERITY_MEDIUM,
                "A context change was observed; this is not proof of misuse.",
                (previous, current),
                (previous.context, current.context),
            ))

        if previous.decision and current.decision and previous.decision != current.decision:
            findings.append(_make_finding(
                FINDING_DECISION_CHANGE, SEVERITY_INFO,
                "The recorded security decision changed between adjacent events.",
                (previous, current),
                (previous.decision, current.decision),
            ))

        if (
            previous.risk_score is not None
            and current.risk_score is not None
            and current.risk_score - previous.risk_score >= risk_increase_threshold
        ):
            edges.append(_make_edge(
                previous, current, EDGE_RISK_ESCALATION,
                "The supplied risk signal increased beyond the configured threshold.",
            ))
            findings.append(_make_finding(
                FINDING_RISK_ESCALATION, SEVERITY_HIGH,
                "The supplied risk signal increased materially; no new score was calculated.",
                (previous, current),
                (str(previous.risk_score), str(current.risk_score)),
            ))

    # Consecutive denied actions for the same agent/case form a pattern.
    denial_run: list[TrajectoryNode] = []
    for node in nodes:
        if node.decision in {"DENY", "BLOCK", "RESTRICT"}:
            denial_run.append(node)
        else:
            if len(denial_run) >= repeated_denial_threshold:
                for left, right in zip(denial_run, denial_run[1:]):
                    edges.append(_make_edge(
                        left, right, EDGE_REPEATED_DENIAL,
                        "Consecutive restricted/denied decisions were observed.",
                    ))
                findings.append(_make_finding(
                    FINDING_REPEATED_DENIALS, SEVERITY_MEDIUM,
                    "A consecutive sequence of denied or restricted decisions was observed.",
                    tuple(denial_run),
                    (f"count={len(denial_run)}",),
                ))
            denial_run = []
    if len(denial_run) >= repeated_denial_threshold:
        for left, right in zip(denial_run, denial_run[1:]):
            edges.append(_make_edge(
                left, right, EDGE_REPEATED_DENIAL,
                "Consecutive restricted/denied decisions were observed.",
            ))
        findings.append(_make_finding(
            FINDING_REPEATED_DENIALS, SEVERITY_MEDIUM,
            "A consecutive sequence of denied or restricted decisions was observed.",
            tuple(denial_run),
            (f"count={len(denial_run)}",),
        ))

    # Detect a growing set of distinct resources; no maliciousness inferred.
    known_resources: set[str] = set()
    expansion_nodes: list[TrajectoryNode] = []
    for node in nodes:
        if node.resource and node.resource not in known_resources:
            known_resources.add(node.resource)
            expansion_nodes.append(node)
            if len(known_resources) == resource_expansion_threshold:
                first = expansion_nodes[-2]
                edges.append(_make_edge(
                    first, node, EDGE_RESOURCE_EXPANSION,
                    "A new distinct resource appeared in the observed sequence.",
                ))
            elif len(known_resources) > resource_expansion_threshold:
                edges.append(_make_edge(
                    expansion_nodes[-2], node, EDGE_RESOURCE_EXPANSION,
                    "A further distinct resource appeared in the observed sequence.",
                ))

    if len(known_resources) >= resource_expansion_threshold:
        findings.append(_make_finding(
            FINDING_RESOURCE_EXPANSION, SEVERITY_LOW,
            "Multiple distinct resources were observed; whether this is expected depends on policy and task context.",
            tuple(expansion_nodes),
            (f"distinct_resources={len(known_resources)}",),
        ))

    # Stable deduplication preserves graph output when inputs are unchanged.
    edge_map = {edge.edge_id: edge for edge in edges}
    finding_map = {finding.finding_id: finding for finding in findings}
    ordered_edges = tuple(sorted(
        edge_map.values(),
        key=lambda item: (
            item.source_node_id, item.target_node_id, item.edge_type, item.edge_id
        ),
    ))
    ordered_findings = tuple(sorted(
        finding_map.values(),
        key=lambda item: (item.finding_type, item.finding_id),
    ))

    graph_payload = {
        "version": VERSION,
        "agent_id": agent_id,
        "case_id": case_id,
        "nodes": [node.node_id for node in nodes],
        "edges": [edge.edge_id for edge in ordered_edges],
        "findings": [finding.finding_id for finding in ordered_findings],
        "evidence_complete": evidence_complete,
    }

    return SecurityTrajectoryGraph(
        graph_id="trajectory-" + _digest(graph_payload)[:20],
        agent_id=agent_id,
        case_id=case_id,
        nodes=tuple(nodes),
        edges=ordered_edges,
        findings=ordered_findings,
        input_entry_count=len(raw_entries),
        omitted_entries=0,
        evidence_complete=evidence_complete,
    )
