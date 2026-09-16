from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.security_provenance import (
    PROVENANCE_COMPLETE,
    PROVENANCE_PARTIAL,
    STAGE_BEHAVIORAL,
    STAGE_DECISION,
    STAGE_ENFORCEMENT,
    STAGE_PREDICTIVE,
    STAGE_RECONCILIATION,
    STAGE_RUNTIME,
    STAGE_VALIDATION,
    SecurityProvenanceBuilder,
    ProvenanceEvent,
    build_provenance_id,
    create_provenance_event,
    decision_is_modified_here,
    enforcement_is_executed_here,
    get_provenance_stage_names,
    has_stage,
    provenance_is_complete,
)


def make_builder() -> SecurityProvenanceBuilder:
    return SecurityProvenanceBuilder()


def make_events():
    return (
        create_provenance_event(
            stage=STAGE_BEHAVIORAL,
            event_type="behavioral_observation",
            evidence={
                "deviation_score": 72,
            },
        ),
        create_provenance_event(
            stage=STAGE_PREDICTIVE,
            event_type="predictive_signal",
            evidence={
                "projected_score": 78,
                "confidence": "HIGH",
            },
        ),
        create_provenance_event(
            stage=STAGE_DECISION,
            event_type="security_decision",
            evidence={
                "decision": "REDUCE_SCOPE",
            },
        ),
        create_provenance_event(
            stage=STAGE_RECONCILIATION,
            event_type="reconciliation",
            evidence={
                "status": "ESCALATED",
            },
        ),
        create_provenance_event(
            stage=STAGE_RUNTIME,
            event_type="runtime_envelope",
        ),
        create_provenance_event(
            stage=STAGE_ENFORCEMENT,
            event_type="enforcement_request",
        ),
        create_provenance_event(
            stage=STAGE_VALIDATION,
            event_type="validation",
            evidence={
                "safe_to_forward": True,
            },
        ),
    )


# ---------------------------------------------------------------------------
# ID
# ---------------------------------------------------------------------------


def test_build_provenance_id():
    result = build_provenance_id(
        "agent-1",
        "request-1",
    )

    assert result == "agent-1-provenance-request-1"


def test_build_provenance_id_rejects_empty_agent():
    with pytest.raises(ValueError):
        build_provenance_id(
            "",
            "request-1",
        )


def test_build_provenance_id_rejects_empty_request():
    with pytest.raises(ValueError):
        build_provenance_id(
            "agent-1",
            "",
        )


# ---------------------------------------------------------------------------
# Event construction
# ---------------------------------------------------------------------------


def test_create_event():
    event = create_provenance_event(
        stage=STAGE_BEHAVIORAL,
        event_type="observation",
        evidence={
            "signal": "deviation",
        },
    )

    assert isinstance(
        event,
        ProvenanceEvent,
    )

    assert event.stage == STAGE_BEHAVIORAL
    assert event.event_type == "observation"
    assert event.evidence["signal"] == "deviation"


def test_event_evidence_is_defensively_copied():
    source = {
        "signals": ["deviation"],
    }

    event = create_provenance_event(
        stage=STAGE_BEHAVIORAL,
        event_type="observation",
        evidence=source,
    )

    source["signals"].append("modified")

    assert event.evidence["signals"] == [
        "deviation"
    ]


def test_invalid_stage_is_rejected():
    with pytest.raises(ValueError):
        create_provenance_event(
            stage="INVALID_STAGE",
            event_type="observation",
        )


def test_empty_event_type_is_rejected():
    with pytest.raises(ValueError):
        create_provenance_event(
            stage=STAGE_BEHAVIORAL,
            event_type="",
        )


# ---------------------------------------------------------------------------
# Record construction
# ---------------------------------------------------------------------------


def test_build_complete_provenance_record():
    builder = make_builder()

    events = make_events()

    record = builder.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="REDUCE_SCOPE",
        stages=[
            STAGE_BEHAVIORAL,
            STAGE_PREDICTIVE,
            STAGE_DECISION,
            STAGE_RECONCILIATION,
            STAGE_RUNTIME,
            STAGE_ENFORCEMENT,
            STAGE_VALIDATION,
        ],
        events=events,
        decision_evidence={
            "decision": "REDUCE_SCOPE",
            "projected_score": 78,
        },
        source_evidence={
            "reason": "behavioral deterioration",
        },
    )

    assert record.agent_id == "agent-1"
    assert record.request_id == "request-1"
    assert record.decision == "REDUCE_SCOPE"

    assert (
        record.provenance_status
        == PROVENANCE_COMPLETE
    )

    assert len(record.events) == 7
    assert record.execution_performed_here is False


def test_partial_record_is_classified_correctly():
    builder = make_builder()

    record = builder.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="MONITOR",
        stages=[
            STAGE_DECISION,
        ],
    )

    assert (
        record.provenance_status
        == PROVENANCE_PARTIAL
    )

    assert provenance_is_complete(record) is False


def test_complete_record_is_detected():
    builder = make_builder()

    record = builder.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="BLOCK",
        stages=[
            STAGE_DECISION,
        ],
        events=[
            create_provenance_event(
                stage=STAGE_DECISION,
                event_type="decision",
            )
        ],
        decision_evidence={
            "decision": "BLOCK",
        },
    )

    assert provenance_is_complete(record) is True


# ---------------------------------------------------------------------------
# Stage traceability
# ---------------------------------------------------------------------------


def test_stage_names_are_preserved():
    builder = make_builder()

    stages = [
        STAGE_BEHAVIORAL,
        STAGE_PREDICTIVE,
        STAGE_DECISION,
    ]

    record = builder.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="MONITOR",
        stages=stages,
    )

    assert get_provenance_stage_names(record) == tuple(
        stages
    )


@pytest.mark.parametrize(
    "stage",
    [
        STAGE_BEHAVIORAL,
        STAGE_PREDICTIVE,
        STAGE_DECISION,
        STAGE_RECONCILIATION,
        STAGE_RUNTIME,
        STAGE_ENFORCEMENT,
        STAGE_VALIDATION,
    ],
)
def test_has_stage(stage):
    builder = make_builder()

    record = builder.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="MONITOR",
        stages=[
            STAGE_BEHAVIORAL,
            STAGE_PREDICTIVE,
            STAGE_DECISION,
            STAGE_RECONCILIATION,
            STAGE_RUNTIME,
            STAGE_ENFORCEMENT,
            STAGE_VALIDATION,
        ],
    )

    assert has_stage(record, stage) is True


def test_missing_stage_returns_false():
    builder = make_builder()

    record = builder.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="MONITOR",
        stages=[
            STAGE_DECISION,
        ],
    )

    assert has_stage(
        record,
        STAGE_BEHAVIORAL,
    ) is False


# ---------------------------------------------------------------------------
# Evidence preservation
# ---------------------------------------------------------------------------


def test_decision_evidence_is_preserved():
    builder = make_builder()

    evidence = {
        "decision": "REDUCE_SCOPE",
        "projected_score": 72,
        "confidence": "HIGH",
    }

    record = builder.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="REDUCE_SCOPE",
        stages=[
            STAGE_DECISION,
        ],
        decision_evidence=evidence,
    )

    assert record.decision_evidence == evidence


def test_source_evidence_is_preserved():
    builder = make_builder()

    evidence = {
        "reason": "behavioral deviation",
        "signals": [
            "trajectory",
            "consequence",
        ],
    }

    record = builder.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="BLOCK",
        stages=[
            STAGE_DECISION,
        ],
        source_evidence=evidence,
    )

    assert record.source_evidence == evidence


def test_source_evidence_is_defensively_copied():
    builder = make_builder()

    evidence = {
        "signals": ["deviation"],
    }

    record = builder.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="MONITOR",
        stages=[
            STAGE_DECISION,
        ],
        source_evidence=evidence,
    )

    evidence["signals"].append(
        "modified"
    )

    assert record.source_evidence["signals"] == [
        "deviation"
    ]


# ---------------------------------------------------------------------------
# Event preservation
# ---------------------------------------------------------------------------


def test_events_are_preserved_in_order():
    builder = make_builder()

    events = make_events()

    record = builder.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="REDUCE_SCOPE",
        stages=[
            STAGE_BEHAVIORAL,
            STAGE_PREDICTIVE,
            STAGE_DECISION,
        ],
        events=events,
    )

    assert record.events == events


def test_events_are_immutable():
    builder = make_builder()

    record = builder.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="MONITOR",
        stages=[
            STAGE_DECISION,
        ],
        events=[
            create_provenance_event(
                stage=STAGE_DECISION,
                event_type="decision",
            )
        ],
    )

    with pytest.raises(FrozenInstanceError):
        record.decision = "BLOCK"


def test_event_is_immutable():
    event = create_provenance_event(
        stage=STAGE_DECISION,
        event_type="decision",
    )

    with pytest.raises(FrozenInstanceError):
        event.event_type = "modified"


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


def test_latest_returns_latest_record():
    builder = make_builder()

    first = builder.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="MONITOR",
        stages=[STAGE_DECISION],
    )

    second = builder.build(
        agent_id="agent-1",
        request_id="request-2",
        decision="BLOCK",
        stages=[STAGE_DECISION],
    )

    assert builder.latest("agent-1") == second
    assert builder.latest("agent-1") != first


def test_latest_unknown_agent_returns_none():
    builder = make_builder()

    assert builder.latest("unknown") is None


def test_history_preserves_order():
    builder = make_builder()

    first = builder.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="ALLOW",
        stages=[STAGE_DECISION],
    )

    second = builder.build(
        agent_id="agent-1",
        request_id="request-2",
        decision="MONITOR",
        stages=[STAGE_DECISION],
    )

    assert builder.history("agent-1") == (
        first,
        second,
    )


def test_history_isolated_between_agents():
    builder = make_builder()

    builder.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="ALLOW",
        stages=[STAGE_DECISION],
    )

    builder.build(
        agent_id="agent-2",
        request_id="request-1",
        decision="BLOCK",
        stages=[STAGE_DECISION],
    )

    assert len(
        builder.history("agent-1")
    ) == 1

    assert len(
        builder.history("agent-2")
    ) == 1


# ---------------------------------------------------------------------------
# Snapshot
# ---------------------------------------------------------------------------


def test_snapshot_all_contains_all_agents():
    builder = make_builder()

    builder.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="ALLOW",
        stages=[STAGE_DECISION],
    )

    builder.build(
        agent_id="agent-2",
        request_id="request-1",
        decision="BLOCK",
        stages=[STAGE_DECISION],
    )

    snapshot = builder.snapshot_all()

    assert set(snapshot.keys()) == {
        "agent-1",
        "agent-2",
    }

    assert len(snapshot["agent-1"]) == 1
    assert len(snapshot["agent-2"]) == 1


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


def test_reset_one_agent():
    builder = make_builder()

    builder.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="MONITOR",
        stages=[STAGE_DECISION],
    )

    builder.build(
        agent_id="agent-2",
        request_id="request-1",
        decision="BLOCK",
        stages=[STAGE_DECISION],
    )

    builder.reset("agent-1")

    assert builder.latest("agent-1") is None
    assert builder.latest("agent-2") is not None


def test_reset_all_agents():
    builder = make_builder()

    builder.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="MONITOR",
        stages=[STAGE_DECISION],
    )

    builder.build(
        agent_id="agent-2",
        request_id="request-1",
        decision="BLOCK",
        stages=[STAGE_DECISION],
    )

    builder.reset()

    assert builder.snapshot_all() == {}


def test_reset_restarts_counter():
    builder = make_builder()

    first = builder.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="MONITOR",
        stages=[STAGE_DECISION],
    )

    builder.reset("agent-1")

    second = builder.build(
        agent_id="agent-1",
        request_id="request-2",
        decision="BLOCK",
        stages=[STAGE_DECISION],
    )

    assert first.provenance_id.endswith(
        "-provenance-1"
    )

    assert second.provenance_id.endswith(
        "-provenance-1"
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_invalid_agent_id_is_rejected():
    builder = make_builder()

    with pytest.raises(ValueError):
        builder.build(
            agent_id="",
            request_id="request-1",
            decision="ALLOW",
            stages=[STAGE_DECISION],
        )


def test_invalid_request_id_is_rejected():
    builder = make_builder()

    with pytest.raises(ValueError):
        builder.build(
            agent_id="agent-1",
            request_id="",
            decision="ALLOW",
            stages=[STAGE_DECISION],
        )


def test_invalid_decision_is_rejected_when_empty():
    builder = make_builder()

    with pytest.raises(ValueError):
        builder.build(
            agent_id="agent-1",
            request_id="request-1",
            decision="",
            stages=[STAGE_DECISION],
        )


def test_invalid_stage_is_rejected():
    builder = make_builder()

    with pytest.raises(ValueError):
        builder.build(
            agent_id="agent-1",
            request_id="request-1",
            decision="ALLOW",
            stages=["INVALID"],
        )


def test_invalid_events_type_is_rejected():
    builder = make_builder()

    with pytest.raises(TypeError):
        builder.build(
            agent_id="agent-1",
            request_id="request-1",
            decision="ALLOW",
            stages=[STAGE_DECISION],
            events=["not-an-event"],
        )


def test_invalid_event_object_is_rejected():
    builder = make_builder()

    with pytest.raises(TypeError):
        builder.build(
            agent_id="agent-1",
            request_id="request-1",
            decision="ALLOW",
            stages=[STAGE_DECISION],
            events=[object()],
        )


# ---------------------------------------------------------------------------
# Security boundaries
# ---------------------------------------------------------------------------


def test_decision_is_not_modified_here():
    assert decision_is_modified_here() is False


def test_enforcement_is_not_executed_here():
    assert enforcement_is_executed_here() is False


def test_record_explicitly_states_no_execution():
    builder = make_builder()

    record = builder.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="BLOCK",
        stages=[STAGE_DECISION],
    )

    assert record.execution_performed_here is False


def test_no_universal_security_score():
    builder = make_builder()

    record = builder.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="BLOCK",
        stages=[STAGE_DECISION],
        decision_evidence={
            "projected_score": 80,
        },
    )

    assert not hasattr(
        record,
        "overall_risk_score",
    )

    assert not hasattr(
        record,
        "security_score",
    )


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_same_inputs_have_same_provenance_fields():
    builder1 = make_builder()
    builder2 = make_builder()

    record1 = builder1.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="REDUCE_SCOPE",
        stages=[
            STAGE_BEHAVIORAL,
            STAGE_PREDICTIVE,
            STAGE_DECISION,
        ],
        events=[
            create_provenance_event(
                stage=STAGE_DECISION,
                event_type="decision",
                evidence={
                    "projected_score": 70,
                },
            )
        ],
        decision_evidence={
            "decision": "REDUCE_SCOPE",
        },
        source_evidence={
            "reason": "deterioration",
        },
    )

    record2 = builder2.build(
        agent_id="agent-1",
        request_id="request-1",
        decision="REDUCE_SCOPE",
        stages=[
            STAGE_BEHAVIORAL,
            STAGE_PREDICTIVE,
            STAGE_DECISION,
        ],
        events=[
            create_provenance_event(
                stage=STAGE_DECISION,
                event_type="decision",
                evidence={
                    "projected_score": 70,
                },
            )
        ],
        decision_evidence={
            "decision": "REDUCE_SCOPE",
        },
        source_evidence={
            "reason": "deterioration",
        },
    )

    assert record1.agent_id == record2.agent_id
    assert record1.request_id == record2.request_id
    assert record1.decision == record2.decision
    assert record1.stages == record2.stages
    assert record1.events == record2.events
    assert (
        record1.decision_evidence
        == record2.decision_evidence
    )
    assert (
        record1.source_evidence
        == record2.source_evidence
    )
    assert (
        record1.provenance_status
        == record2.provenance_status
    )