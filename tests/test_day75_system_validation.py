"""
Day 75 — Varynx System Validation Tests

These tests validate the Day 75 orchestration layer.

The tests intentionally verify architectural boundaries as well as
functional behavior.

Day 75 must:

- construct deterministic system events
- validate an event sequence
- integrate the existing Day 73 timeline
- integrate the existing Day 74 correlation layer
- reconstruct an incident
- preserve evidence
- expose stage information
- provide deterministic results
- maintain read-only security boundaries

Day 75 must NOT:

- modify decisions
- execute enforcement
- infer malicious intent
- introduce a universal security score
"""

from __future__ import annotations

import pytest

from app.varynx_system import (
    AUDIT_STAGE,
    BEHAVIORAL_STAGE,
    CORRELATION_STAGE,
    DECISION_STAGE,
    ENFORCEMENT_STAGE,
    INCIDENT_STAGE,
    PREDICTIVE_STAGE,
    SNAPSHOT_STAGE,
    SYSTEM_PARTIAL,
    SYSTEM_VALIDATED,
    TIMELINE_STAGE,
    TRUST_STAGE,
    VarynxEvent,
    VarynxSystem,
    creates_universal_security_score,
    decision_is_modified_here,
    enforcement_is_executed_here,
    malicious_intent_is_inferred_here,
    system_is_read_only,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_system() -> VarynxSystem:
    return VarynxSystem()


def build_event(
    *,
    agent_id: str = "agent-1",
    stage: str = BEHAVIORAL_STAGE,
    event_type: str = "BEHAVIORAL_OBSERVATION",
    request_id: str | None = "req-1",
    decision: str | None = None,
    sequence: int = 1,
    evidence: dict | None = None,
) -> VarynxEvent:
    system = build_system()

    return system.create_event(
        agent_id=agent_id,
        stage=stage,
        event_type=event_type,
        request_id=request_id,
        decision=decision,
        timestamp=(
            f"2026-09-17T10:"
            f"{sequence:02d}:00+00:00"
        ),
        evidence=evidence
        or {
            "signal": "observed",
            "sequence": sequence,
        },
    )


def build_complete_events() -> tuple[VarynxEvent, ...]:
    return (
        build_event(
            stage=BEHAVIORAL_STAGE,
            event_type="BEHAVIORAL_OBSERVATION",
            sequence=1,
        ),
        build_event(
            stage=TRUST_STAGE,
            event_type="TRUST_EVALUATION",
            sequence=2,
        ),
        build_event(
            stage=PREDICTIVE_STAGE,
            event_type="PREDICTIVE_EVALUATION",
            sequence=3,
        ),
        build_event(
            stage=DECISION_STAGE,
            event_type="DECISION",
            decision="MONITOR",
            sequence=4,
        ),
    )


# ---------------------------------------------------------------------------
# Event construction
# ---------------------------------------------------------------------------

def test_event_is_created() -> None:
    event = build_event()

    assert isinstance(
        event,
        VarynxEvent,
    )

    assert event.agent_id == "agent-1"
    assert event.stage == BEHAVIORAL_STAGE
    assert event.request_id == "req-1"


def test_event_id_is_deterministic() -> None:
    first = build_event(
        sequence=1
    )

    second = build_event(
        sequence=1
    )

    assert first.event_id == second.event_id


def test_event_evidence_is_preserved() -> None:
    event = build_event(
        evidence={
            "source": "behavior",
            "value": 42,
        }
    )

    assert event.evidence["source"] == "behavior"
    assert event.evidence["value"] == 42


def test_invalid_event_type_is_rejected() -> None:
    system = build_system()

    with pytest.raises(
        (TypeError, ValueError)
    ):
        system.create_event(
            agent_id="agent-1",
            stage=BEHAVIORAL_STAGE,
            event_type="",
        )


# ---------------------------------------------------------------------------
# System initialization
# ---------------------------------------------------------------------------

def test_system_initializes() -> None:
    system = build_system()

    assert isinstance(
        system,
        VarynxSystem,
    )

    assert system.history() == ()


# ---------------------------------------------------------------------------
# Complete validation
# ---------------------------------------------------------------------------

def test_complete_event_sequence_is_validated() -> None:
    system = build_system()

    result = system.validate(
        agent_id="agent-1",
        case_id="case-1",
        events=build_complete_events(),
    )

    assert result.status == SYSTEM_VALIDATED
    assert result.agent_id == "agent-1"

    assert len(result.events) == 4

    assert result.timeline is not None
    assert result.correlation is not None
    assert result.incident is not None


def test_complete_sequence_contains_expected_stages() -> None:
    system = build_system()

    result = system.validate(
        agent_id="agent-1",
        case_id="case-1",
        events=build_complete_events(),
    )

    assert BEHAVIORAL_STAGE in result.stages_present
    assert TRUST_STAGE in result.stages_present
    assert PREDICTIVE_STAGE in result.stages_present
    assert DECISION_STAGE in result.stages_present


def test_missing_stages_are_reported() -> None:
    system = build_system()

    events = (
        build_event(
            stage=BEHAVIORAL_STAGE,
            sequence=1,
        ),
    )

    result = system.validate(
        agent_id="agent-1",
        case_id="case-1",
        events=events,
    )

    assert BEHAVIORAL_STAGE in result.stages_present

    assert TRUST_STAGE in result.stages_missing
    assert PREDICTIVE_STAGE in result.stages_missing


# ---------------------------------------------------------------------------
# Empty / partial validation
# ---------------------------------------------------------------------------

def test_empty_sequence_is_partial() -> None:
    system = build_system()

    result = system.validate(
        agent_id="agent-1",
        case_id="case-1",
        events=(),
    )

    assert result.status == SYSTEM_PARTIAL
    assert result.events == ()

    assert result.timeline is not None
    assert result.correlation is not None
    assert result.incident is not None


# ---------------------------------------------------------------------------
# Request validation
# ---------------------------------------------------------------------------

def test_request_id_is_preserved() -> None:
    system = build_system()

    result = system.validate_request(
        agent_id="agent-1",
        case_id="case-1",
        request_id="req-42",
        stages=(
            BEHAVIORAL_STAGE,
            TRUST_STAGE,
            PREDICTIVE_STAGE,
            DECISION_STAGE,
        ),
        decision="MONITOR",
    )

    assert result.request_id == "req-42"

    assert all(
        event.request_id == "req-42"
        for event in result.events
    )


def test_request_helper_creates_deterministic_result() -> None:
    first_system = build_system()

    first = first_system.validate_request(
        agent_id="agent-1",
        case_id="case-1",
        request_id="req-1",
        stages=(
            BEHAVIORAL_STAGE,
            TRUST_STAGE,
            PREDICTIVE_STAGE,
            DECISION_STAGE,
        ),
        decision="MONITOR",
    )

    second_system = build_system()

    second = second_system.validate_request(
        agent_id="agent-1",
        case_id="case-1",
        request_id="req-1",
        stages=(
            BEHAVIORAL_STAGE,
            TRUST_STAGE,
            PREDICTIVE_STAGE,
            DECISION_STAGE,
        ),
        decision="MONITOR",
    )

    assert first.result_id == second.result_id

    assert (
        first.timeline.timeline_id
        == second.timeline.timeline_id
    )

    assert (
        first.correlation.correlation_id
        == second.correlation.correlation_id
    )

    assert (
        first.incident.incident_id
        == second.incident.incident_id
    )


# ---------------------------------------------------------------------------
# Timeline integration
# ---------------------------------------------------------------------------

def test_day73_timeline_is_integrated() -> None:
    system = build_system()

    result = system.validate(
        agent_id="agent-1",
        case_id="case-1",
        events=build_complete_events(),
    )

    assert result.timeline is not None
    assert result.timeline.agent_id == "agent-1"
    assert result.timeline.case_id == "case-1"

    assert len(
        result.timeline.entries
    ) == 4


def test_timeline_preserves_event_information() -> None:
    system = build_system()

    events = (
        build_event(
            stage=BEHAVIORAL_STAGE,
            event_type="OBSERVATION",
            sequence=1,
            evidence={
                "source": "behavioral",
                "value": "normal",
            },
        ),
    )

    result = system.validate(
        agent_id="agent-1",
        case_id="case-1",
        events=events,
    )

    entry = result.timeline.entries[0]

    assert entry.request_id == "req-1"
    assert entry.event_type == "OBSERVATION"

    assert entry.evidence["source"] == "behavioral"
    assert entry.evidence["value"] == "normal"


# ---------------------------------------------------------------------------
# Correlation integration
# ---------------------------------------------------------------------------

def test_day74_correlation_is_integrated() -> None:
    system = build_system()

    result = system.validate(
        agent_id="agent-1",
        case_id="case-1",
        events=build_complete_events(),
    )

    assert result.correlation is not None

    assert (
        result.correlation.agent_id
        == "agent-1"
    )

    assert (
        result.correlation.case_id
        == "case-1"
    )

    assert len(
        result.correlation.entries
    ) == 4


def test_correlation_contains_relationships() -> None:
    system = build_system()

    result = system.validate(
        agent_id="agent-1",
        case_id="case-1",
        events=build_complete_events(),
    )

    assert result.correlation is not None

    assert len(
        result.correlation.relationships
    ) >= 1


# ---------------------------------------------------------------------------
# Incident reconstruction
# ---------------------------------------------------------------------------

def test_incident_is_reconstructed() -> None:
    system = build_system()

    result = system.validate(
        agent_id="agent-1",
        case_id="case-1",
        events=build_complete_events(),
    )

    assert result.incident is not None

    assert (
        result.incident.case_id
        == "case-1"
    )

    assert (
        result.incident.agent_id
        == "agent-1"
    )

    assert (
        result.incident.entry_count
        == 4
    )


# ---------------------------------------------------------------------------
# Evidence preservation
# ---------------------------------------------------------------------------

def test_system_evidence_is_preserved() -> None:
    system = build_system()

    supplied_evidence = {
        "source": {
            "integrity": "VALID"
        },
        "experiment": "day75",
    }

    result = system.validate(
        agent_id="agent-1",
        case_id="case-1",
        events=build_complete_events(),
        evidence=supplied_evidence,
    )

    assert (
        result.evidence["experiment"]
        == "day75"
    )

    assert (
        result.evidence["source"]["integrity"]
        == "VALID"
    )


def test_event_evidence_is_not_lost() -> None:
    system = build_system()

    event = build_event(
        evidence={
            "origin": "behavioral-engine",
            "integrity": "VALID",
        }
    )

    result = system.validate(
        agent_id="agent-1",
        case_id="case-1",
        events=(event,),
    )

    assert (
        result.events[0].evidence["origin"]
        == "behavioral-engine"
    )

    assert (
        result.timeline.entries[0]
        .evidence["origin"]
        == "behavioral-engine"
    )


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

def test_result_is_recorded_in_history() -> None:
    system = build_system()

    result = system.validate(
        agent_id="agent-1",
        case_id="case-1",
        events=build_complete_events(),
    )

    history = system.history(
        "agent-1"
    )

    assert len(history) == 1
    assert history[0] == result


def test_latest_returns_latest_result() -> None:
    system = build_system()

    first = system.validate_request(
        agent_id="agent-1",
        case_id="case-1",
        request_id="req-1",
        stages=(BEHAVIORAL_STAGE,),
    )

    second = system.validate_request(
        agent_id="agent-1",
        case_id="case-1",
        request_id="req-2",
        stages=(BEHAVIORAL_STAGE,),
    )

    assert system.latest(
        "agent-1"
    ) == second

    assert first != second


def test_result_can_be_retrieved_by_id() -> None:
    system = build_system()

    result = system.validate(
        agent_id="agent-1",
        case_id="case-1",
        events=build_complete_events(),
    )

    assert system.get(
        result.result_id
    ) == result


def test_reset_clears_day75_history() -> None:
    system = build_system()

    system.validate(
        agent_id="agent-1",
        case_id="case-1",
        events=build_complete_events(),
    )

    assert system.history()

    system.reset()

    assert system.history() == ()
    assert system.latest("agent-1") is None


# ---------------------------------------------------------------------------
# Architectural boundaries
# ---------------------------------------------------------------------------

def test_decision_is_not_modified_here() -> None:
    assert decision_is_modified_here() is False


def test_enforcement_is_not_executed_here() -> None:
    assert enforcement_is_executed_here() is False


def test_malicious_intent_is_not_inferred_here() -> None:
    assert malicious_intent_is_inferred_here() is False


def test_no_universal_security_score_is_created() -> None:
    assert (
        creates_universal_security_score()
        is False
    )


def test_system_is_read_only() -> None:
    assert system_is_read_only() is True


# ---------------------------------------------------------------------------
# No score inflation / no duplicate score
# ---------------------------------------------------------------------------

def test_result_does_not_create_security_score() -> None:
    system = build_system()

    result = system.validate(
        agent_id="agent-1",
        case_id="case-1",
        events=build_complete_events(),
    )

    assert not hasattr(
        result,
        "security_score",
    )

    assert not hasattr(
        result,
        "risk_score",
    )


def test_correlation_does_not_create_security_score() -> None:
    system = build_system()

    result = system.validate(
        agent_id="agent-1",
        case_id="case-1",
        events=build_complete_events(),
    )

    assert not hasattr(
        result.correlation,
        "security_score",
    )

    assert not hasattr(
        result.correlation,
        "risk_score",
    )


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def test_invalid_agent_id_is_rejected() -> None:
    system = build_system()

    with pytest.raises(
        (TypeError, ValueError)
    ):
        system.validate(
            agent_id="",
            case_id="case-1",
            events=(),
        )


def test_invalid_case_id_is_rejected() -> None:
    system = build_system()

    with pytest.raises(
        (TypeError, ValueError)
    ):
        system.validate(
            agent_id="agent-1",
            case_id="",
            events=(),
        )


def test_invalid_event_object_is_rejected() -> None:
    system = build_system()

    with pytest.raises(TypeError):
        system.validate(
            agent_id="agent-1",
            case_id="case-1",
            events=("invalid-event",),
        )


def test_mismatched_agent_event_is_rejected() -> None:
    system = build_system()

    event = build_event(
        agent_id="agent-2"
    )

    with pytest.raises(ValueError):
        system.validate(
            agent_id="agent-1",
            case_id="case-1",
            events=(event,),
        )


def test_mismatched_request_event_is_rejected() -> None:
    system = build_system()

    event = build_event(
        request_id="req-2"
    )

    with pytest.raises(ValueError):
        system.validate(
            agent_id="agent-1",
            case_id="case-1",
            request_id="req-1",
            events=(event,),
        )


# ---------------------------------------------------------------------------
# End-to-end scenario
# ---------------------------------------------------------------------------

def test_end_to_end_control_flow() -> None:
    """
    Controlled Day 75 integration scenario.

    The scenario represents:

        behavioral observation
              ↓
        trust evaluation
              ↓
        predictive evaluation
              ↓
        security decision
    """

    system = build_system()

    result = system.validate_request(
        agent_id="agent-1",
        case_id="case-1",
        request_id="req-75",
        stages=(
            BEHAVIORAL_STAGE,
            TRUST_STAGE,
            PREDICTIVE_STAGE,
            DECISION_STAGE,
        ),
        decision="MONITOR",
        evidence={
            "scenario": "day75-end-to-end",
            "integrity": "VALID",
        },
    )

    assert result.status == SYSTEM_VALIDATED

    assert result.request_id == "req-75"

    assert len(result.events) == 4

    assert result.timeline is not None
    assert result.correlation is not None
    assert result.incident is not None

    assert (
        BEHAVIORAL_STAGE
        in result.stages_present
    )

    assert (
        TRUST_STAGE
        in result.stages_present
    )

    assert (
        PREDICTIVE_STAGE
        in result.stages_present
    )

    assert (
        DECISION_STAGE
        in result.stages_present
    )

    assert (
        result.incident.case_id
        == "case-1"
    )


# ---------------------------------------------------------------------------
# Regression-oriented checks
# ---------------------------------------------------------------------------

def test_day75_does_not_execute_an_agent_action() -> None:
    """
    Day 75 only validates supplied evidence/events.

    There is intentionally no agent execution API here.
    """

    system = build_system()

    assert not hasattr(
        system,
        "execute_agent_action",
    )

    assert not hasattr(
        system,
        "execute",
    )


def test_day75_result_is_immutable() -> None:
    system = build_system()

    result = system.validate_request(
        agent_id="agent-1",
        case_id="case-1",
        request_id="req-1",
        stages=(
            BEHAVIORAL_STAGE,
            DECISION_STAGE,
        ),
        decision="MONITOR",
    )

    with pytest.raises(
        Exception
    ):
        result.status = "CHANGED"


# ---------------------------------------------------------------------------
# Final integration contract
# ---------------------------------------------------------------------------

def test_day75_integration_contract() -> None:
    """
    Single contract test covering the main Day 75 objective.
    """

    system = build_system()

    result = system.validate_request(
        agent_id="agent-1",
        case_id="case-75",
        request_id="req-75",
        stages=(
            BEHAVIORAL_STAGE,
            TRUST_STAGE,
            PREDICTIVE_STAGE,
            DECISION_STAGE,
        ),
        decision="MONITOR",
    )

    # System
    assert result.status == SYSTEM_VALIDATED

    # Behavioral stage
    assert (
        BEHAVIORAL_STAGE
        in result.stages_present
    )

    # Trust stage
    assert (
        TRUST_STAGE
        in result.stages_present
    )

    # Predictive stage
    assert (
        PREDICTIVE_STAGE
        in result.stages_present
    )

    # Decision stage
    assert (
        DECISION_STAGE
        in result.stages_present
    )

    # Day 73
    assert result.timeline is not None

    # Day 74
    assert result.correlation is not None

    # Incident reconstruction
    assert result.incident is not None

    # Security boundaries
    assert (
        decision_is_modified_here()
        is False
    )

    assert (
        enforcement_is_executed_here()
        is False
    )

    assert (
        malicious_intent_is_inferred_here()
        is False
    )

    assert (
        creates_universal_security_score()
        is False
    )

    assert system_is_read_only() is True