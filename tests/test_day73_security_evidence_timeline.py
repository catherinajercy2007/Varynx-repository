import pytest

from app.security_evidence_timeline import (
    CASE_COMPLETE,
    CASE_PARTIAL,
    SOURCE_AUDIT,
    SOURCE_INTEGRITY,
    SOURCE_MONITORING,
    SOURCE_SNAPSHOT,
    TIMELINE_COMPLETE,
    TIMELINE_GAPPED,
    TIMELINE_INCONSISTENT,
    TIMELINE_ORDERED,
    SecurityEvidenceTimelineBuilder,
    analyze_sequence,
    case_is_complete,
    create_evidence_entry,
    decision_is_modified_here,
    enforcement_is_executed_here,
    malicious_intent_is_inferred_here,
    timeline_has_gaps,
    timeline_is_complete,
    timeline_is_read_only,
)


def make_entry(
    sequence,
    source=SOURCE_AUDIT,
    event_type="DECISION",
    request_id="req-1",
    decision="MONITOR",
    timestamp=None,
    evidence=None,
):
    return create_evidence_entry(
        agent_id="agent-1",
        case_id="case-1",
        sequence_number=sequence,
        source=source,
        event_type=event_type,
        request_id=request_id,
        decision=decision,
        timestamp=timestamp or f"2026-09-17T10:0{sequence}:00",
        evidence=evidence or {"signal": "observed"},
    )


def test_create_entry():
    entry = make_entry(1)

    assert entry.agent_id == "agent-1"
    assert entry.case_id == "case-1"
    assert entry.sequence_number == 1
    assert entry.source == SOURCE_AUDIT


def test_entry_id_is_deterministic():
    first = make_entry(1)
    second = make_entry(1)

    assert first.entry_id == second.entry_id


def test_different_sequence_changes_entry_id():
    first = make_entry(1)
    second = make_entry(2)

    assert first.entry_id != second.entry_id


def test_evidence_is_defensively_copied():
    evidence = {
        "signals": {
            "deviation": 70,
        }
    }

    entry = make_entry(1, evidence=evidence)

    evidence["signals"]["deviation"] = 10

    assert entry.evidence["signals"]["deviation"] == 70


def test_sequence_ordered():
    entries = [
        make_entry(1),
        make_entry(2),
        make_entry(3),
    ]

    status, gaps = analyze_sequence(entries)

    assert status == TIMELINE_ORDERED
    assert gaps == ()


def test_sequence_detects_gap():
    entries = [
        make_entry(1),
        make_entry(3),
    ]

    status, gaps = analyze_sequence(entries)

    assert status == TIMELINE_GAPPED
    assert gaps == (2,)


def test_sequence_detects_duplicate():
    entries = [
        make_entry(1),
        make_entry(1),
    ]

    status, gaps = analyze_sequence(entries)

    assert status == TIMELINE_INCONSISTENT


def test_sequence_detects_out_of_order():
    entries = [
        make_entry(2),
        make_entry(1),
    ]

    status, gaps = analyze_sequence(entries)

    assert status == TIMELINE_INCONSISTENT


def test_empty_sequence_is_partial():
    status, gaps = analyze_sequence([])

    assert status == TIMELINE_GAPPED
    assert gaps == ()


def test_build_complete_timeline():
    builder = SecurityEvidenceTimelineBuilder()

    timeline = builder.build_timeline(
        agent_id="agent-1",
        case_id="case-1",
        entries=[
            make_entry(1),
            make_entry(2),
            make_entry(3),
        ],
    )

    assert timeline.status == TIMELINE_COMPLETE
    assert timeline.ordering_status == TIMELINE_ORDERED
    assert len(timeline.entries) == 3


def test_complete_timeline_helper():
    builder = SecurityEvidenceTimelineBuilder()

    timeline = builder.build_timeline(
        agent_id="agent-1",
        case_id="case-1",
        entries=[make_entry(1)],
    )

    assert timeline_is_complete(timeline)
    assert timeline_is_read_only()


def test_gap_makes_timeline_partial():
    builder = SecurityEvidenceTimelineBuilder()

    timeline = builder.build_timeline(
        agent_id="agent-1",
        case_id="case-1",
        entries=[
            make_entry(1),
            make_entry(3),
        ],
    )

    assert timeline.status == "TIMELINE_PARTIAL"
    assert timeline_has_gaps(timeline)
    assert timeline.gaps == (2,)


def test_source_counts():
    builder = SecurityEvidenceTimelineBuilder()

    timeline = builder.build_timeline(
        agent_id="agent-1",
        case_id="case-1",
        entries=[
            make_entry(1, SOURCE_AUDIT),
            make_entry(2, SOURCE_AUDIT),
            make_entry(3, SOURCE_INTEGRITY),
            make_entry(4, SOURCE_SNAPSHOT),
        ],
    )

    assert timeline.source_counts[SOURCE_AUDIT] == 2
    assert timeline.source_counts[SOURCE_INTEGRITY] == 1
    assert timeline.source_counts[SOURCE_SNAPSHOT] == 1


def test_event_type_counts():
    builder = SecurityEvidenceTimelineBuilder()

    timeline = builder.build_timeline(
        agent_id="agent-1",
        case_id="case-1",
        entries=[
            make_entry(1, event_type="DECISION"),
            make_entry(2, event_type="DECISION"),
            make_entry(3, event_type="VALIDATION"),
        ],
    )

    assert timeline.event_type_counts["DECISION"] == 2
    assert timeline.event_type_counts["VALIDATION"] == 1


def test_request_ids_are_unique():
    builder = SecurityEvidenceTimelineBuilder()

    entry1 = make_entry(1, request_id="req-1")
    entry2 = make_entry(2, request_id="req-1")
    entry3 = make_entry(3, request_id="req-2")

    timeline = builder.build_timeline(
        agent_id="agent-1",
        case_id="case-1",
        entries=[entry1, entry2, entry3],
    )

    assert timeline.request_ids == ("req-1", "req-2")


def test_build_timeline_is_deterministic():
    builder = SecurityEvidenceTimelineBuilder()

    entries = [
        make_entry(1),
        make_entry(2),
    ]

    first = builder.build_timeline(
        agent_id="agent-1",
        case_id="case-1",
        entries=entries,
    )

    second = builder.build_timeline(
        agent_id="agent-1",
        case_id="case-1",
        entries=entries,
    )

    assert first.timeline_id == second.timeline_id


def test_agent_mismatch_rejected():
    builder = SecurityEvidenceTimelineBuilder()

    foreign = create_evidence_entry(
        agent_id="agent-2",
        case_id="case-1",
        sequence_number=1,
        source=SOURCE_AUDIT,
        event_type="DECISION",
    )

    with pytest.raises(ValueError):
        builder.build_timeline(
            agent_id="agent-1",
            case_id="case-1",
            entries=[foreign],
        )


def test_case_mismatch_rejected():
    builder = SecurityEvidenceTimelineBuilder()

    foreign = create_evidence_entry(
        agent_id="agent-1",
        case_id="case-2",
        sequence_number=1,
        source=SOURCE_AUDIT,
        event_type="DECISION",
    )

    with pytest.raises(ValueError):
        builder.build_timeline(
            agent_id="agent-1",
            case_id="case-1",
            entries=[foreign],
        )


def test_latest_history():
    builder = SecurityEvidenceTimelineBuilder()

    first = builder.build_timeline(
        agent_id="agent-1",
        case_id="case-1",
        entries=[make_entry(1)],
    )

    second = builder.build_timeline(
        agent_id="agent-1",
        case_id="case-1",
        entries=[make_entry(1), make_entry(2)],
    )

    assert builder.latest("agent-1") == second
    assert len(builder.history("agent-1")) == 2
    assert first != second


def test_by_case():
    builder = SecurityEvidenceTimelineBuilder()

    builder.build_timeline(
        agent_id="agent-1",
        case_id="case-1",
        entries=[make_entry(1)],
    )

    other_entry = create_evidence_entry(
        agent_id="agent-1",
        case_id="case-2",
        sequence_number=1,
        source=SOURCE_AUDIT,
        event_type="DECISION",
    )

    builder.build_timeline(
        agent_id="agent-1",
        case_id="case-2",
        entries=[other_entry],
    )

    matches = builder.by_case("case-1")

    assert len(matches) == 1
    assert matches[0].case_id == "case-1"


def test_reconstruct_complete_case():
    builder = SecurityEvidenceTimelineBuilder()

    timeline = builder.build_timeline(
        agent_id="agent-1",
        case_id="case-1",
        entries=[
            make_entry(
                1,
                event_type="BEHAVIORAL",
                decision=None,
            ),
            make_entry(
                2,
                event_type="PREDICTIVE",
                decision="MONITOR",
            ),
            make_entry(
                3,
                event_type="RECONCILIATION",
                decision="REDUCE_SCOPE",
            ),
        ],
    )

    case = builder.reconstruct_case(timeline)

    assert case.status == CASE_COMPLETE
    assert case.entry_count == 3
    assert case.decisions == ("MONITOR", "REDUCE_SCOPE")


def test_reconstruct_partial_case():
    builder = SecurityEvidenceTimelineBuilder()

    timeline = builder.build_timeline(
        agent_id="agent-1",
        case_id="case-1",
        entries=[
            make_entry(1),
            make_entry(3),
        ],
    )

    case = builder.reconstruct_case(timeline)

    assert case.status == CASE_PARTIAL
    assert case.gaps == (2,)
    assert not case_is_complete(case)


def test_case_contains_sources():
    builder = SecurityEvidenceTimelineBuilder()

    timeline = builder.build_timeline(
        agent_id="agent-1",
        case_id="case-1",
        entries=[
            make_entry(1, SOURCE_AUDIT),
            make_entry(2, SOURCE_INTEGRITY),
            make_entry(3, SOURCE_SNAPSHOT),
        ],
    )

    case = builder.reconstruct_case(timeline)

    assert case.sources == (
        SOURCE_AUDIT,
        SOURCE_INTEGRITY,
        SOURCE_SNAPSHOT,
    )


def test_case_timestamps():
    builder = SecurityEvidenceTimelineBuilder()

    timeline = builder.build_timeline(
        agent_id="agent-1",
        case_id="case-1",
        entries=[
            make_entry(
                1,
                timestamp="2026-09-17T10:00:00",
            ),
            make_entry(
                2,
                timestamp="2026-09-17T10:05:00",
            ),
        ],
    )

    case = builder.reconstruct_case(timeline)

    assert case.first_timestamp == "2026-09-17T10:00:00"
    assert case.last_timestamp == "2026-09-17T10:05:00"


def test_snapshot_all():
    builder = SecurityEvidenceTimelineBuilder()

    builder.build_timeline(
        agent_id="agent-1",
        case_id="case-1",
        entries=[make_entry(1)],
    )

    builder.build_timeline(
        agent_id="agent-2",
        case_id="case-2",
        entries=[
            create_evidence_entry(
                agent_id="agent-2",
                case_id="case-2",
                sequence_number=1,
                source=SOURCE_AUDIT,
                event_type="DECISION",
            )
        ],
    )

    assert len(builder.snapshot_all()) == 2


def test_reset():
    builder = SecurityEvidenceTimelineBuilder()

    builder.build_timeline(
        agent_id="agent-1",
        case_id="case-1",
        entries=[make_entry(1)],
    )

    assert builder.latest("agent-1") is not None

    builder.reset()

    assert builder.latest("agent-1") is None
    assert builder.snapshot_all() == ()


def test_execution_boundary():
    builder = SecurityEvidenceTimelineBuilder()

    timeline = builder.build_timeline(
        agent_id="agent-1",
        case_id="case-1",
        entries=[make_entry(1)],
    )

    case = builder.reconstruct_case(timeline)

    assert timeline.execution_performed_here is False
    assert case.execution_performed_here is False
    assert enforcement_is_executed_here() is False


def test_decision_boundary():
    assert decision_is_modified_here() is False


def test_intent_boundary():
    assert malicious_intent_is_inferred_here() is False


def test_invalid_source_rejected():
    with pytest.raises(ValueError):
        create_evidence_entry(
            agent_id="agent-1",
            case_id="case-1",
            sequence_number=1,
            source="UNKNOWN",
            event_type="DECISION",
        )


def test_invalid_sequence_rejected():
    with pytest.raises(ValueError):
        create_evidence_entry(
            agent_id="agent-1",
            case_id="case-1",
            sequence_number=0,
            source=SOURCE_AUDIT,
            event_type="DECISION",
        )


def test_invalid_event_type_rejected():
    with pytest.raises(ValueError):
        create_evidence_entry(
            agent_id="agent-1",
            case_id="case-1",
            sequence_number=1,
            source=SOURCE_AUDIT,
            event_type="",
        )


def test_empty_agent_rejected():
    with pytest.raises(ValueError):
        create_evidence_entry(
            agent_id="",
            case_id="case-1",
            sequence_number=1,
            source=SOURCE_AUDIT,
            event_type="DECISION",
        )


def test_empty_case_rejected():
    with pytest.raises(ValueError):
        create_evidence_entry(
            agent_id="agent-1",
            case_id="",
            sequence_number=1,
            source=SOURCE_AUDIT,
            event_type="DECISION",
        )


def test_custom_entry_id_preserved():
    entry = create_evidence_entry(
        agent_id="agent-1",
        case_id="case-1",
        sequence_number=1,
        source=SOURCE_AUDIT,
        event_type="DECISION",
        entry_id="custom-entry-1",
    )

    assert entry.entry_id == "custom-entry-1"


def test_nested_evidence_preserved():
    entry = make_entry(
        1,
        evidence={
            "decision": {
                "projected_score": 65,
                "confidence": "HIGH",
            }
        },
    )

    assert entry.evidence["decision"]["projected_score"] == 65
    assert entry.evidence["decision"]["confidence"] == "HIGH"


def test_timeline_evidence_preserved():
    builder = SecurityEvidenceTimelineBuilder()

    timeline = builder.build_timeline(
        agent_id="agent-1",
        case_id="case-1",
        entries=[make_entry(1)],
        evidence={
            "integrity_status": "VALID",
            "snapshot_reference": "snapshot-001",
        },
    )

    assert timeline.evidence["integrity_status"] == "VALID"


def test_read_only_helper():
    assert timeline_is_read_only() is True