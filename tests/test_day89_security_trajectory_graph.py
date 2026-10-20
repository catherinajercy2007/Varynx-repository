
from datetime import datetime, timezone

import pytest

from app.security_evidence_timeline import create_evidence_entry
from app.security_trajectory_graph import (
    EDGE_CHRONOLOGICAL,
    EDGE_CONTEXT_CHANGE,
    EDGE_REPEATED_DENIAL,
    EDGE_RESOURCE_EXPANSION,
    EDGE_RISK_ESCALATION,
    FINDING_CONTEXT_CHANGE,
    FINDING_DECISION_CHANGE,
    FINDING_REPEATED_DENIALS,
    FINDING_RESOURCE_EXPANSION,
    FINDING_RISK_ESCALATION,
    VERSION,
    build_security_trajectory,
)


def entry(
    sequence,
    *,
    event_type="AGENT_ACTION",
    action="read",
    resource="reports/a.csv",
    context="task-a",
    decision="ALLOW",
    risk=10,
    entry_id=None,
):
    evidence = {}
    if action is not None:
        evidence["action"] = action
    if resource is not None:
        evidence["resource"] = resource
    if context is not None:
        evidence["context"] = context
    if risk is not None:
        evidence["risk_score"] = risk

    return create_evidence_entry(
        agent_id="agent-1",
        case_id="case-1",
        sequence_number=sequence,
        source="AUDIT",
        event_type=event_type,
        decision=decision,
        timestamp=f"2026-10-20T10:{sequence:02d}:00+00:00",
        evidence=evidence,
    )


def build(entries, **kwargs):
    return build_security_trajectory(
        agent_id="agent-1",
        case_id="case-1",
        entries=entries,
        **kwargs,
    )


def test_empty_input_creates_empty_graph():
    graph = build([])
    assert graph.nodes == ()
    assert graph.edges == ()
    assert graph.findings == ()
    assert graph.input_entry_count == 0


def test_version_and_boundary_flags_are_serialized():
    payload = build([entry(1)]).to_dict()
    assert payload["version"] == VERSION
    assert payload["is_authorization_decision"] is False
    assert payload["executes_enforcement"] is False
    assert payload["infers_malicious_intent"] is False
    assert payload["calculates_universal_risk_score"] is False


def test_entries_are_sorted_by_sequence_number():
    graph = build([entry(3), entry(1), entry(2)])
    assert [node.sequence_number for node in graph.nodes] == [1, 2, 3]


def test_adjacent_events_get_chronological_edges():
    graph = build([entry(1), entry(2), entry(3)])
    assert sum(e.edge_type == EDGE_CHRONOLOGICAL for e in graph.edges) == 2


def test_graph_is_deterministic_for_same_evidence():
    records = [entry(1), entry(2, resource="reports/b.csv")]
    first = build(records).to_dict()
    second = build(records).to_dict()
    assert first == second


def test_reordered_input_does_not_change_graph():
    records = [entry(1), entry(2), entry(3)]
    assert build(records).to_dict() == build(list(reversed(records))).to_dict()


def test_repeated_consecutive_denials_create_finding_and_edges():
    records = [
        entry(1, decision="DENY"),
        entry(2, decision="DENY"),
        entry(3, decision="BLOCK"),
    ]
    graph = build(records)
    assert any(e.edge_type == EDGE_REPEATED_DENIAL for e in graph.edges)
    assert any(f.finding_type == FINDING_REPEATED_DENIALS for f in graph.findings)


def test_single_denial_does_not_trigger_repeated_denial_finding():
    graph = build([entry(1, decision="DENY"), entry(2, decision="ALLOW")])
    assert not any(
        f.finding_type == FINDING_REPEATED_DENIALS for f in graph.findings
    )


def test_nonconsecutive_denials_do_not_count_as_consecutive_run():
    graph = build([
        entry(1, decision="DENY"),
        entry(2, decision="ALLOW"),
        entry(3, decision="DENY"),
    ])
    assert not any(
        f.finding_type == FINDING_REPEATED_DENIALS for f in graph.findings
    )


def test_resource_expansion_is_reported_without_intent_claim():
    graph = build([
        entry(1, resource="reports/a.csv"),
        entry(2, resource="reports/b.csv"),
    ])
    assert any(e.edge_type == EDGE_RESOURCE_EXPANSION for e in graph.edges)
    finding = next(
        f for f in graph.findings
        if f.finding_type == FINDING_RESOURCE_EXPANSION
    )
    assert "expected depends on policy" in finding.explanation


def test_same_resource_does_not_trigger_resource_expansion():
    graph = build([entry(1), entry(2), entry(3)])
    assert not any(
        f.finding_type == FINDING_RESOURCE_EXPANSION for f in graph.findings
    )


def test_context_change_creates_edge_and_finding():
    graph = build([entry(1, context="task-a"), entry(2, context="task-b")])
    assert any(e.edge_type == EDGE_CONTEXT_CHANGE for e in graph.edges)
    assert any(f.finding_type == FINDING_CONTEXT_CHANGE for f in graph.findings)


def test_missing_context_is_not_invented():
    graph = build([entry(1, context=None), entry(2, context="task-b")])
    assert not any(e.edge_type == EDGE_CONTEXT_CHANGE for e in graph.edges)


def test_risk_escalation_uses_supplied_signal_only():
    graph = build([entry(1, risk=20), entry(2, risk=40)])
    assert any(e.edge_type == EDGE_RISK_ESCALATION for e in graph.edges)
    assert any(f.finding_type == FINDING_RISK_ESCALATION for f in graph.findings)


def test_small_risk_change_does_not_trigger_escalation():
    graph = build([entry(1, risk=20), entry(2, risk=30)])
    assert not any(
        f.finding_type == FINDING_RISK_ESCALATION for f in graph.findings
    )


def test_missing_risk_signal_is_not_imputed():
    graph = build([entry(1, risk=None), entry(2, risk=90)])
    assert not any(
        f.finding_type == FINDING_RISK_ESCALATION for f in graph.findings
    )


def test_decision_change_is_reported_as_observation():
    graph = build([entry(1, decision="ALLOW"), entry(2, decision="DENY")])
    assert any(
        f.finding_type == FINDING_DECISION_CHANGE for f in graph.findings
    )


def test_agent_mismatch_is_rejected():
    other = create_evidence_entry(
        agent_id="agent-2",
        case_id="case-1",
        sequence_number=1,
        source="AUDIT",
        event_type="AGENT_ACTION",
        evidence={"action": "read"},
    )
    with pytest.raises(ValueError, match="match agent_id and case_id"):
        build([other])


def test_case_mismatch_is_rejected():
    other = create_evidence_entry(
        agent_id="agent-1",
        case_id="case-2",
        sequence_number=1,
        source="AUDIT",
        event_type="AGENT_ACTION",
    )
    with pytest.raises(ValueError, match="match agent_id and case_id"):
        build([other])


def test_duplicate_entry_ids_are_rejected():
    first = entry(1)
    duplicate = {
        "entry_id": first.entry_id,
        "agent_id": "agent-1",
        "case_id": "case-1",
        "sequence_number": 2,
        "event_type": "AGENT_ACTION",
        "timestamp": None,
        "decision": "ALLOW",
        "evidence": {},
    }
    with pytest.raises(ValueError, match="duplicate entry_id"):
        build([first, duplicate])


def test_duplicate_sequence_numbers_are_rejected():
    with pytest.raises(ValueError, match="unique"):
        build([entry(1), entry(1, resource="reports/b.csv")])


@pytest.mark.parametrize("bad_score", [-1, 101, float("nan"), float("inf"), True])
def test_invalid_risk_scores_are_rejected(bad_score):
    with pytest.raises(ValueError):
        build([entry(1, risk=bad_score)])


@pytest.mark.parametrize("bad_threshold", [True, 1, 0, -2, 2.5])
def test_invalid_denial_threshold_is_rejected(bad_threshold):
    with pytest.raises(ValueError):
        build([entry(1)], repeated_denial_threshold=bad_threshold)


def test_invalid_evidence_mapping_is_rejected():
    malformed = {
        "entry_id": "entry-x",
        "agent_id": "agent-1",
        "case_id": "case-1",
        "sequence_number": 1,
        "event_type": "AGENT_ACTION",
        "evidence": ["not", "a", "mapping"],
    }
    with pytest.raises(TypeError, match="evidence must be a mapping"):
        build([malformed])


def test_evidence_completeness_is_preserved():
    graph = build([entry(1)], evidence_complete=False)
    assert graph.evidence_complete is False
    assert graph.to_dict()["evidence_complete"] is False


def test_finding_ids_are_stable():
    records = [entry(1, decision="DENY"), entry(2, decision="DENY")]
    first = build(records)
    second = build(records)
    assert [f.finding_id for f in first.findings] == [
        f.finding_id for f in second.findings
    ]


def test_findings_retain_source_entry_ids():
    graph = build([entry(1, decision="DENY"), entry(2, decision="DENY")])
    finding = next(
        f for f in graph.findings
        if f.finding_type == FINDING_REPEATED_DENIALS
    )
    assert finding.evidence_entry_ids == (
        graph.nodes[0].entry_id,
        graph.nodes[1].entry_id,
    )
