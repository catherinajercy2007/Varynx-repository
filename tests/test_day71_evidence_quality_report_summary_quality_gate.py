from evaluation.evidence_quality_report_summary_quality_gate import (
    EvidenceQualitySummaryQualityGateResult,
    evaluate_evidence_quality_summary_quality_gate,
    evidence_quality_summary_quality_gate_status,
    evidence_quality_summary_quality_gate_to_dict,
    generate_evidence_quality_summary_quality_gate,
)


def create_valid_accepted_summary():
    return {
        "overall_status": "ACCEPTED",
        "accepted": True,
        "quality_gate_status": "PASS",
        "integrity_verified": True,
        "artifact_count": 2,
        "verified_artifact_count": 2,
        "validation_error_count": 0,
    }


def create_valid_rejected_summary():
    return {
        "overall_status": "REJECTED",
        "accepted": False,
        "quality_gate_status": "FAIL",
        "integrity_verified": False,
        "artifact_count": 0,
        "verified_artifact_count": 0,
        "validation_error_count": 1,
    }


def test_accepted_summary_passes_quality_gate():
    summary = create_valid_accepted_summary()

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    assert result.valid is True
    assert result.status == "PASS"
    assert result.accepted is True
    assert result.validation_errors == []


def test_rejected_summary_fails_quality_gate():
    summary = create_valid_rejected_summary()

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    assert result.valid is True
    assert result.status == "FAIL"
    assert result.accepted is False
    assert result.validation_errors == []


def test_accepted_summary_artifact_counts_are_preserved():
    summary = create_valid_accepted_summary()

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    assert result.artifact_count == 2
    assert result.verified_artifact_count == 2


def test_rejected_summary_artifact_counts_are_preserved():
    summary = create_valid_rejected_summary()

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    assert result.artifact_count == 0
    assert result.verified_artifact_count == 0


def test_invalid_overall_status_fails_quality_gate():
    summary = create_valid_accepted_summary()
    summary["overall_status"] = "UNKNOWN"

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    assert result.valid is False
    assert result.status == "FAIL"
    assert result.accepted is False
    assert result.validation_errors


def test_invalid_quality_gate_status_fails_quality_gate():
    summary = create_valid_accepted_summary()
    summary["quality_gate_status"] = "UNKNOWN"

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    assert result.valid is False
    assert result.status == "FAIL"
    assert result.validation_errors


def test_acceptance_mismatch_fails_quality_gate():
    summary = create_valid_accepted_summary()
    summary["accepted"] = False

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    assert result.valid is False
    assert result.status == "FAIL"
    assert result.accepted is False
    assert result.validation_errors


def test_quality_gate_acceptance_mismatch_fails():
    summary = create_valid_accepted_summary()
    summary["quality_gate_status"] = "FAIL"

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    assert result.valid is False
    assert result.status == "FAIL"
    assert result.validation_errors


def test_verified_artifacts_exceeding_total_fails():
    summary = create_valid_accepted_summary()
    summary["artifact_count"] = 1
    summary["verified_artifact_count"] = 2

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    assert result.valid is False
    assert result.status == "FAIL"
    assert result.validation_errors


def test_missing_field_fails_quality_gate():
    summary = create_valid_accepted_summary()
    del summary["artifact_count"]

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    assert result.valid is False
    assert result.status == "FAIL"
    assert result.validation_errors


def test_invalid_numeric_value_fails_quality_gate():
    summary = create_valid_accepted_summary()
    summary["artifact_count"] = -1

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    assert result.valid is False
    assert result.status == "FAIL"
    assert result.validation_errors


def test_non_dictionary_summary_fails_quality_gate():
    result = evaluate_evidence_quality_summary_quality_gate(
        "invalid"
    )

    assert result.valid is False
    assert result.status == "FAIL"
    assert result.accepted is False
    assert result.validation_errors


def test_generate_quality_gate_matches_evaluation():
    summary = create_valid_accepted_summary()

    result = generate_evidence_quality_summary_quality_gate(
        summary
    )

    assert isinstance(
        result,
        EvidenceQualitySummaryQualityGateResult,
    )

    assert result.valid is True
    assert result.status == "PASS"


def test_quality_gate_to_dict():
    summary = create_valid_accepted_summary()

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    data = evidence_quality_summary_quality_gate_to_dict(
        result
    )

    assert data == {
        "valid": True,
        "status": "PASS",
        "validation_errors": [],
        "accepted": True,
        "artifact_count": 2,
        "verified_artifact_count": 2,
    }


def test_quality_gate_status_helper():
    summary = create_valid_accepted_summary()

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    assert (
        evidence_quality_summary_quality_gate_status(result)
        == "PASS"
    )


def test_rejected_quality_gate_status_helper():
    summary = create_valid_rejected_summary()

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    assert (
        evidence_quality_summary_quality_gate_status(result)
        == "FAIL"
    )


def test_invalid_summary_contains_validation_errors():
    summary = create_valid_accepted_summary()
    summary["accepted"] = "true"

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    assert result.valid is False
    assert result.validation_errors


def test_valid_accepted_summary_has_no_validation_errors():
    summary = create_valid_accepted_summary()

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    assert result.validation_errors == []


def test_quality_gate_result_fields_are_correct():
    summary = create_valid_accepted_summary()

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    assert hasattr(result, "valid")
    assert hasattr(result, "status")
    assert hasattr(result, "validation_errors")
    assert hasattr(result, "accepted")
    assert hasattr(result, "artifact_count")
    assert hasattr(result, "verified_artifact_count")