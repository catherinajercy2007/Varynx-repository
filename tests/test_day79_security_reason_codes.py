from copy import deepcopy

import pytest

from app.security_reason_codes import (
    VERSION,
    SecurityReasonCode,
    generate_security_reason_codes,
    reason_code_generation_is_read_only,
    reason_codes_execute_enforcement,
    reason_codes_infer_malicious_intent,
    reason_codes_modify_decision,
    reason_codes_to_dicts,
)


def test_version_and_existing_decision_are_preserved():
    evidence = {"risk_score": 0.2}
    before = deepcopy(evidence)

    result = generate_security_reason_codes(
        decision="ALLOW",
        evidence=evidence,
    )

    assert VERSION == "DAY79-V1"
    assert result[0].code == "EXISTING_DECISION_RECORDED"
    assert result[0].decision == "ALLOW"
    assert evidence == before


def test_emits_deterministic_codes_from_supplied_evidence():
    evidence = {
        "risk_score": 85,
        "anomaly_score": 0.75,
        "denial_score": 59,
    }

    first = generate_security_reason_codes(
        decision="BLOCK",
        evidence=evidence,
    )
    second = generate_security_reason_codes(
        decision="BLOCK",
        evidence=evidence,
    )

    assert first == second

    assert [item.code for item in first] == [
        "EXISTING_DECISION_RECORDED",
        "PRIMARY_RISK_CRITICAL",
        "BEHAVIORAL_DEVIATION_ELEVATED",
    ]

    assert first[1].observed_value == 85
    assert first[1].threshold == 80


def test_missing_or_low_evidence_is_not_invented():
    result = generate_security_reason_codes(
        decision="ALLOW",
        evidence={"risk_score": 20},
    )

    assert [item.code for item in result] == [
        "EXISTING_DECISION_RECORDED"
    ]


def test_aliases_are_supported_without_changing_source_mapping():
    evidence = {
        "behavioral_risk_index": 65,
    }

    result = generate_security_reason_codes(
        decision="MONITOR",
        evidence=evidence,
    )

    assert result[1].code == "PRIMARY_RISK_ELEVATED"
    assert result[1].source_key == "behavioral_risk_index"


def test_unknown_decision_is_explained_without_reclassification():
    result = generate_security_reason_codes(
        decision="CUSTOM_REVIEW",
        evidence={},
    )

    assert result[0].decision == "CUSTOM_REVIEW"
    assert "CUSTOM_REVIEW" in result[0].message


def test_serialization_returns_fresh_dicts():
    result = generate_security_reason_codes(
        decision="BLOCK",
        evidence={"risk_score": 90},
    )

    serialized = reason_codes_to_dicts(result)
    serialized[0]["code"] = "CHANGED"

    assert result[0].code == "EXISTING_DECISION_RECORDED"


@pytest.mark.parametrize(
    "decision",
    ["", "  ", None, 4],
)
def test_rejects_invalid_decision(decision):
    with pytest.raises(ValueError):
        generate_security_reason_codes(
            decision=decision,
            evidence={},
        )


@pytest.mark.parametrize(
    "evidence",
    [None, [], "bad", 4],
)
def test_rejects_non_mapping_evidence(evidence):
    with pytest.raises(TypeError):
        generate_security_reason_codes(
            decision="ALLOW",
            evidence=evidence,
        )


@pytest.mark.parametrize(
    "value",
    [-1, 101, float("nan"), float("inf"), True, "bad"],
)
def test_rejects_invalid_scores(value):
    with pytest.raises(ValueError):
        generate_security_reason_codes(
            decision="ALLOW",
            evidence={"risk_score": value},
        )


def test_boundary_helpers_document_non_interference():
    assert reason_code_generation_is_read_only() is True
    assert reason_codes_modify_decision() is False
    assert reason_codes_execute_enforcement() is False
    assert reason_codes_infer_malicious_intent() is False


def test_serialization_rejects_wrong_container():
    with pytest.raises(TypeError):
        reason_codes_to_dicts([])


def test_context_entropy_alias_is_explained_when_supplied():
    result = generate_security_reason_codes(
        decision="ALLOW_WITH_MONITORING",
        evidence={"context_entropy": 0.72},
    )

    assert result[-1].code == "CONTEXT_ENTROPY_CONCERN"
    assert result[-1].source_key == "context_entropy"
    assert result[-1].observed_value == 72.0


def test_records_are_immutable():
    result = generate_security_reason_codes(
        decision="BLOCK",
        evidence={"risk_score": 90},
    )

    assert isinstance(result[0], SecurityReasonCode)

    with pytest.raises((AttributeError, TypeError)):
        result[0].code = "MODIFIED"