import pytest

from app.security_evidence_correlation import (
    CASE_PARTIAL,
    CASE_RECONSTRUCTED,
    CORRELATION_COMPLETE,
    CORRELATION_PARTIAL,
    RELATIONSHIP_CONNECTED,
    RELATIONSHIP_PARTIAL,
    SOURCE_AUDIT,
    SOURCE_INTEGRITY,
    SOURCE_MONITORING,
    SOURCE_SNAPSHOT,
    STAGE_AUDIT,
    STAGE_BEHAVIORAL,
    STAGE_DECISION,
    STAGE_INTEGRITY,
    STAGE_MONITORING,
    STAGE_PREDICTIVE,
    STAGE_SNAPSHOT,
    STAGE_VALIDATION,
    SecurityEvidenceCorrelation,
    SecurityEvidenceCorrelationEngine,
    SecurityIncidentReconstruction,
    build_correlation_id,
    correlation_has_relationships,
    correlation_is_complete,
    correlation_is_read_only,
    create_evidence_entry,
    decision_is_modified_here,
    enforcement_is_executed_here,
    incident_is_reconstructed,
    malicious_intent_is_inferred_here,
    normalize_event_stage,
)
from app.security_evidence_timeline import (
    SecurityEvidenceTimelineBuilder,
)


def make_entry(
    sequence,
    event_type="DECISION",
    source=SOURCE_AUDIT,
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
        timestamp=timestamp
        or f"2026-09-17T10:0{sequence}:00",
        evidence=evidence
        or {"signal": "observed"},
    )


def make_timeline(entries):
    builder = SecurityEvidenceTimelineBuilder()

    return builder.build_timeline(
        agent_id="agent-1",
        case_id="case-1",
        entries=entries,
    )


def test_normalize_known_event_stage():
    assert normalize_event_stage(
        "BEHAVIORAL"
    ) == STAGE_BEHAVIORAL

    assert normalize_event_stage(
        "DECISION"
    ) == STAGE_DECISION

    assert normalize_event_stage(
        "PREDICTIVE"
    ) == STAGE_PREDICTIVE


def test_normalize_unknown_event_stage():
    assert normalize_event_stage(
        "UNKNOWN_EVENT"
    ) is None


def test_correlation_id_is_deterministic():
    timeline = make_timeline(
        [
            make_entry(1),
            make_entry(2),
        ]
    )

    first = build_correlation_id(
        timeline
    )

    second = build_correlation_id(
        timeline
    )

    assert first == second


def test_correlate_complete_timeline():
    timeline = make_timeline(
        [
            make_entry(
                1,
                event_type="BEHAVIORAL",
            ),
            make_entry(
                2,
                event_type="PREDICTIVE",
            ),
            make_entry(
                3,
                event_type="DECISION",
            ),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    result = engine.correlate(timeline)

    assert result.status == CORRELATION_COMPLETE
    assert result.relationship_status == (
        RELATIONSHIP_CONNECTED
    )
    assert len(result.entries) == 3
    assert len(result.relationships) == 2


def test_partial_empty_timeline():
    timeline = make_timeline([])

    engine = SecurityEvidenceCorrelationEngine()

    result = engine.correlate(timeline)

    assert result.status == CORRELATION_PARTIAL
    assert result.relationship_status == (
        RELATIONSHIP_PARTIAL
    )


def test_stages_present():
    timeline = make_timeline(
        [
            make_entry(
                1,
                event_type="BEHAVIORAL",
            ),
            make_entry(
                2,
                event_type="PREDICTIVE",
            ),
            make_entry(
                3,
                event_type="DECISION",
            ),
            make_entry(
                4,
                event_type="VALIDATION",
            ),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    result = engine.correlate(timeline)

    assert STAGE_BEHAVIORAL in result.stages_present
    assert STAGE_PREDICTIVE in result.stages_present
    assert STAGE_DECISION in result.stages_present
    assert STAGE_VALIDATION in result.stages_present


def test_missing_stages_are_reported():
    timeline = make_timeline(
        [
            make_entry(
                1,
                event_type="BEHAVIORAL",
            ),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    result = engine.correlate(timeline)

    assert STAGE_BEHAVIORAL in result.stages_present
    assert STAGE_PREDICTIVE in result.stages_missing
    assert STAGE_DECISION in result.stages_missing


def test_request_grouping():
    timeline = make_timeline(
        [
            make_entry(
                1,
                request_id="req-1",
            ),
            make_entry(
                2,
                request_id="req-1",
            ),
            make_entry(
                3,
                request_id="req-2",
            ),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    result = engine.correlate(timeline)

    assert len(
        result.request_groups["req-1"]
    ) == 2

    assert len(
        result.request_groups["req-2"]
    ) == 1


def test_event_grouping():
    timeline = make_timeline(
        [
            make_entry(
                1,
                event_type="DECISION",
            ),
            make_entry(
                2,
                event_type="DECISION",
            ),
            make_entry(
                3,
                event_type="VALIDATION",
            ),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    result = engine.correlate(timeline)

    assert len(
        result.event_groups["DECISION"]
    ) == 2

    assert len(
        result.event_groups["VALIDATION"]
    ) == 1


def test_same_request_relationship():
    timeline = make_timeline(
        [
            make_entry(
                1,
                event_type="BEHAVIORAL",
                request_id="req-1",
            ),
            make_entry(
                2,
                event_type="DECISION",
                request_id="req-1",
            ),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    result = engine.correlate(timeline)

    assert len(result.relationships) == 1

    relationship = result.relationships[0]

    assert (
        relationship.relationship_type
        == "SAME_REQUEST_SEQUENCE"
    )


def test_chronological_lifecycle_relationship():
    timeline = make_timeline(
        [
            make_entry(
                1,
                event_type="BEHAVIORAL",
                request_id="req-1",
            ),
            make_entry(
                2,
                event_type="PREDICTIVE",
                request_id=None,
            ),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    result = engine.correlate(timeline)

    relationship = result.relationships[0]

    assert (
        relationship.relationship_type
        == "CHRONOLOGICAL_LIFECYCLE_SEQUENCE"
    )


def test_unknown_event_relationship_remains_descriptive():
    timeline = make_timeline(
        [
            make_entry(
                1,
                event_type="CUSTOM_EVENT",
            ),
            make_entry(
                2,
                event_type="DECISION",
            ),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    result = engine.correlate(timeline)

    relationship = result.relationships[0]

    assert (
        relationship.relationship_type
        == "CHRONOLOGICAL_EVIDENCE_SEQUENCE"
    )


def test_relationship_ids_are_deterministic():
    timeline = make_timeline(
        [
            make_entry(1),
            make_entry(2),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    first = engine.correlate(timeline)
    second = engine.correlate(timeline)

    assert (
        first.relationships[0].relationship_id
        == second.relationships[0].relationship_id
    )


def test_evidence_is_defensively_copied():
    external = {
        "signals": {
            "deviation": 70,
        }
    }

    timeline = make_timeline(
        [
            make_entry(
                1,
                evidence=external,
            )
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    result = engine.correlate(
        timeline,
        evidence={
            "summary": {
                "status": "valid",
            }
        },
    )

    external["signals"]["deviation"] = 10

    assert (
        timeline.entries[0]
        .evidence["signals"]["deviation"]
        == 70
    )

    assert (
        result.evidence["summary"]["status"]
        == "valid"
    )


def test_incident_reconstruction():
    timeline = make_timeline(
        [
            make_entry(
                1,
                event_type="BEHAVIORAL",
            ),
            make_entry(
                2,
                event_type="PREDICTIVE",
            ),
            make_entry(
                3,
                event_type="DECISION",
                decision="REDUCE_SCOPE",
            ),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    correlation = engine.correlate(
        timeline
    )

    incident = engine.reconstruct_incident(
        correlation
    )

    assert incident.status == (
        CASE_RECONSTRUCTED
    )

    assert incident.entry_count == 3
    assert incident.relationship_count == 2
    assert incident.decisions == (
        "REDUCE_SCOPE",
    )


def test_partial_incident_reconstruction():
    timeline = make_timeline([])

    engine = SecurityEvidenceCorrelationEngine()

    correlation = engine.correlate(
        timeline
    )

    incident = engine.reconstruct_incident(
        correlation
    )

    assert incident.status == CASE_PARTIAL
    assert incident.entry_count == 0


def test_incident_id_is_deterministic():
    timeline = make_timeline(
        [
            make_entry(1),
            make_entry(2),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    correlation = engine.correlate(
        timeline
    )

    first = engine.reconstruct_incident(
        correlation
    )

    second = engine.reconstruct_incident(
        correlation
    )

    assert first.incident_id == second.incident_id


def test_latest_history():
    timeline = make_timeline(
        [
            make_entry(1),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    first = engine.correlate(timeline)
    second = engine.correlate(timeline)

    assert engine.latest(
        "agent-1"
    ) == second

    assert len(
        engine.history("agent-1")
    ) == 2

    assert first == second


def test_by_case():
    timeline = make_timeline(
        [
            make_entry(1),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    engine.correlate(timeline)

    matches = engine.by_case(
        "case-1"
    )

    assert len(matches) == 1


def test_snapshot_all():
    timeline = make_timeline(
        [
            make_entry(1),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    engine.correlate(timeline)
    engine.correlate(timeline)

    assert len(
        engine.snapshot_all()
    ) == 2


def test_reset():
    timeline = make_timeline(
        [
            make_entry(1),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    engine.correlate(timeline)

    assert engine.latest(
        "agent-1"
    ) is not None

    engine.reset()

    assert engine.latest(
        "agent-1"
    ) is None

    assert engine.snapshot_all() == ()


def test_correlation_helpers():
    timeline = make_timeline(
        [
            make_entry(1),
            make_entry(2),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    correlation = engine.correlate(
        timeline
    )

    assert correlation_is_complete(
        correlation
    )

    assert correlation_has_relationships(
        correlation
    )

    assert correlation_is_read_only()


def test_incident_helper():
    timeline = make_timeline(
        [
            make_entry(1),
            make_entry(2),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    correlation = engine.correlate(
        timeline
    )

    incident = engine.reconstruct_incident(
        correlation
    )

    assert incident_is_reconstructed(
        incident
    )


def test_security_boundaries():
    assert decision_is_modified_here() is False
    assert enforcement_is_executed_here() is False
    assert malicious_intent_is_inferred_here() is False


def test_invalid_timeline_type_rejected():
    engine = SecurityEvidenceCorrelationEngine()

    with pytest.raises(TypeError):
        engine.correlate(
            "not-a-timeline"
        )


def test_invalid_correlation_type_rejected():
    engine = SecurityEvidenceCorrelationEngine()

    with pytest.raises(TypeError):
        engine.reconstruct_incident(
            "not-a-correlation"
        )


def test_relationship_contains_case_id():
    timeline = make_timeline(
        [
            make_entry(1),
            make_entry(2),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    correlation = engine.correlate(
        timeline
    )

    relationship = correlation.relationships[0]

    assert relationship.case_id == "case-1"


def test_relationship_tracks_request():
    timeline = make_timeline(
        [
            make_entry(
                1,
                request_id="req-42",
            ),
            make_entry(
                2,
                request_id="req-42",
            ),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    correlation = engine.correlate(
        timeline
    )

    assert (
        correlation.relationships[0]
        .request_id
        == "req-42"
    )


def test_multiple_sources_are_preserved():
    timeline = make_timeline(
        [
            make_entry(
                1,
                source=SOURCE_AUDIT,
            ),
            make_entry(
                2,
                source=SOURCE_INTEGRITY,
            ),
            make_entry(
                3,
                source=SOURCE_MONITORING,
            ),
            make_entry(
                4,
                source=SOURCE_SNAPSHOT,
            ),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    result = engine.correlate(timeline)

    sources = {
        entry.source
        for entry in result.entries
    }

    assert sources == {
        SOURCE_AUDIT,
        SOURCE_INTEGRITY,
        SOURCE_MONITORING,
        SOURCE_SNAPSHOT,
    }


def test_no_new_security_score_is_created():
    timeline = make_timeline(
        [
            make_entry(1),
            make_entry(2),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    result = engine.correlate(timeline)

    assert not hasattr(
        result,
        "security_score",
    )

    assert not hasattr(
        result,
        "risk_score",
    )


def test_reconstruction_preserves_evidence():
    timeline = make_timeline(
        [
            make_entry(1),
        ]
    )

    engine = SecurityEvidenceCorrelationEngine()

    correlation = engine.correlate(
        timeline,
        evidence={
            "source": {
                "integrity": "VALID",
            }
        },
    )

    incident = engine.reconstruct_incident(
        correlation
    )

    assert (
        incident.evidence["source"]["integrity"]
        == "VALID"
    )