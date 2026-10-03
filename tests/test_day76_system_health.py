"""Day 76 tests for the Varynx system health/readiness gate."""

from app.varynx_system import (
    SYSTEM_VALIDATED,
    VarynxSystemResult,
)

from app.system_health import (
    CHECK_FAIL,
    READINESS_NOT_READY,
    READINESS_PARTIAL,
    READINESS_READY,
    SystemHealthGate,
    decision_is_modified_here,
    enforcement_is_executed_here,
    malicious_intent_is_inferred_here,
    system_health_is_read_only,
)


def make_result(
    *,
    stages_present,
    stages_missing=(),
    events=("event-1",),
    timeline=object(),
    correlation=object(),
    incident=object(),
    status=SYSTEM_VALIDATED,
):
    """Create a valid Day75 VarynxSystemResult for Day76 tests."""

    return VarynxSystemResult(
        result_id="result-001",
        agent_id="agent-001",
        request_id="request-001",
        status=status,
        stages_present=tuple(stages_present),
        stages_missing=tuple(stages_missing),
        events=tuple(events),
        timeline=timeline,
        correlation=correlation,
        incident=incident,
        evidence={"source": "test"},
    )


def test_full_result_is_ready():
    result = make_result(
        stages_present=(
            "BEHAVIORAL",
            "TRUST",
            "PREDICTIVE",
            "DECISION",
            "TIMELINE",
            "CORRELATION",
            "INCIDENT",
        )
    )

    report = SystemHealthGate().evaluate(result)

    assert report.readiness == READINESS_READY
    assert report.failed_checks == 0
    assert report.passed_checks >= 6
    assert report.missing_stages == ()


def test_missing_evidence_stage_is_partial_when_core_is_intact():
    result = make_result(
        stages_present=(
            "BEHAVIORAL",
            "TRUST",
            "PREDICTIVE",
            "DECISION",
            "TIMELINE",
        ),
        stages_missing=(
            "CORRELATION",
            "INCIDENT",
        ),
    )

    report = SystemHealthGate().evaluate(result)

    assert report.readiness == READINESS_PARTIAL
    assert report.failed_checks == 0
    assert "CORRELATION" in report.missing_stages
    assert "INCIDENT" in report.missing_stages


def test_missing_core_stage_is_not_ready():
    result = make_result(
        stages_present=(
            "BEHAVIORAL",
            "PREDICTIVE",
            "DECISION",
            "TIMELINE",
            "CORRELATION",
            "INCIDENT",
        ),
        stages_missing=("TRUST",),
    )

    report = SystemHealthGate().evaluate(result)

    assert report.readiness == READINESS_NOT_READY
    assert report.failed_checks >= 1
    assert "TRUST" in report.missing_stages


def test_no_events_is_not_ready():
    result = make_result(
        stages_present=(
            "BEHAVIORAL",
            "TRUST",
            "PREDICTIVE",
            "DECISION",
            "TIMELINE",
            "CORRELATION",
            "INCIDENT",
        ),
        events=(),
    )

    report = SystemHealthGate().evaluate(result)

    assert report.readiness == READINESS_NOT_READY

    event_check = next(
        check
        for check in report.checks
        if check.name == "event_presence"
    )

    assert event_check.status == CHECK_FAIL


def test_missing_artifact_fails_even_if_stage_name_is_present():
    result = make_result(
        stages_present=(
            "BEHAVIORAL",
            "TRUST",
            "PREDICTIVE",
            "DECISION",
            "TIMELINE",
            "CORRELATION",
            "INCIDENT",
        ),
        timeline=None,
    )

    report = SystemHealthGate().evaluate(result)

    assert report.readiness == READINESS_NOT_READY

    assert any(
        check.name == "timeline_artifact"
        and check.status == CHECK_FAIL
        for check in report.checks
    )


def test_report_is_deterministic_for_same_result():
    result = make_result(
        stages_present=(
            "BEHAVIORAL",
            "TRUST",
            "PREDICTIVE",
            "DECISION",
            "TIMELINE",
            "CORRELATION",
            "INCIDENT",
        )
    )

    gate = SystemHealthGate()

    first = gate.evaluate(result)
    second = gate.evaluate(result)

    assert first.report_id == second.report_id
    assert first.evidence == second.evidence


def test_supplied_evidence_is_preserved_without_changing_core_fields():
    result = make_result(
        stages_present=(
            "BEHAVIORAL",
            "TRUST",
            "PREDICTIVE",
            "DECISION",
            "TIMELINE",
            "CORRELATION",
            "INCIDENT",
        )
    )

    report = SystemHealthGate().evaluate(
        result,
        evidence={
            "experiment_id": "day76-smoke",
        },
    )

    assert report.evidence["experiment_id"] == "day76-smoke"
    assert report.evidence["read_only"] is True
    assert report.evidence["decision_modified"] is False
    assert report.evidence["enforcement_executed"] is False
    assert report.evidence["malicious_intent_inferred"] is False


def test_architectural_boundaries_are_explicit():
    assert system_health_is_read_only() is True
    assert decision_is_modified_here() is False
    assert enforcement_is_executed_here() is False
    assert malicious_intent_is_inferred_here() is False


def test_invalid_result_type_is_rejected():
    try:
        SystemHealthGate().evaluate(object())
    except TypeError as exc:
        assert "VarynxSystemResult" in str(exc)
    else:
        raise AssertionError(
            "invalid result type was accepted"
        )