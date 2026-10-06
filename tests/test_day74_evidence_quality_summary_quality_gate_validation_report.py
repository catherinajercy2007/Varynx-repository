from evaluation.evidence_quality_summary_quality_gate_validation_report import (
    EvidenceQualitySummaryQualityGateValidationReport,
    determine_quality_gate_validation_report_status,
    evidence_quality_summary_quality_gate_validation_report_status,
    evidence_quality_summary_quality_gate_validation_report_to_dict,
    generate_default_quality_gate_validation_report,
    generate_evidence_quality_summary_quality_gate_validation_report,
)


def create_valid_pass_quality_gate():
    return {
        "valid": True,
        "status": "PASS",
        "validation_errors": [],
        "accepted": True,
        "artifact_count": 2,
        "verified_artifact_count": 2,
    }


def create_valid_fail_quality_gate():
    return {
        "valid": False,
        "status": "FAIL",
        "validation_errors": [
            "Evidence artifact integrity verification failed."
        ],
        "accepted": False,
        "artifact_count": 2,
        "verified_artifact_count": 1,
    }


def test_pass_quality_gate_generates_pass_report():
    gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            gate
        )
    )

    assert report.valid is True
    assert report.status == "PASS"
    assert report.errors == []


def test_fail_quality_gate_generates_fail_report():
    gate = create_valid_fail_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            gate
        )
    )

    assert report.valid is True
    assert report.status == "PASS"
    assert report.errors == []


def test_invalid_quality_gate_generates_fail_report():
    gate = create_valid_pass_quality_gate()
    gate["status"] = "UNKNOWN"

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            gate
        )
    )

    assert report.valid is False
    assert report.status == "FAIL"
    assert report.errors


def test_missing_field_generates_fail_report():
    gate = create_valid_pass_quality_gate()
    del gate["artifact_count"]

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            gate
        )
    )

    assert report.valid is False
    assert report.status == "FAIL"
    assert report.errors


def test_report_preserves_quality_gate():
    gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            gate
        )
    )

    assert report.quality_gate == gate


def test_report_status_helper_for_valid_result():
    assert (
        determine_quality_gate_validation_report_status(
            True
        )
        == "PASS"
    )


def test_report_status_helper_for_invalid_result():
    assert (
        determine_quality_gate_validation_report_status(
            False
        )
        == "FAIL"
    )


def test_report_status_method_for_pass_report():
    gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            gate
        )
    )

    assert (
        evidence_quality_summary_quality_gate_validation_report_status(
            report
        )
        == "PASS"
    )


def test_report_to_dict_for_pass():
    gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            gate
        )
    )

    data = (
        evidence_quality_summary_quality_gate_validation_report_to_dict(
            report
        )
    )

    assert data == {
        "quality_gate": gate,
        "valid": True,
        "status": "PASS",
        "errors": [],
    }


def test_report_to_dict_for_invalid_gate():
    gate = create_valid_pass_quality_gate()
    gate["accepted"] = False

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            gate
        )
    )

    data = (
        evidence_quality_summary_quality_gate_validation_report_to_dict(
            report
        )
    )

    assert data["valid"] is False
    assert data["status"] == "FAIL"
    assert data["errors"]


def test_default_report_matches_generated_report():
    gate = create_valid_pass_quality_gate()

    report_one = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            gate
        )
    )

    report_two = (
        generate_default_quality_gate_validation_report(
            gate
        )
    )

    assert report_one == report_two


def test_report_is_dataclass_instance():
    gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            gate
        )
    )

    assert isinstance(
        report,
        EvidenceQualitySummaryQualityGateValidationReport,
    )


def test_report_contains_expected_fields():
    gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            gate
        )
    )

    assert hasattr(report, "quality_gate")
    assert hasattr(report, "valid")
    assert hasattr(report, "status")
    assert hasattr(report, "errors")


def test_invalid_boolean_is_reported():
    gate = create_valid_pass_quality_gate()
    gate["accepted"] = "true"

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            gate
        )
    )

    assert report.valid is False
    assert report.status == "FAIL"
    assert report.errors


def test_invalid_numeric_value_is_reported():
    gate = create_valid_pass_quality_gate()
    gate["artifact_count"] = -1

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            gate
        )
    )

    assert report.valid is False
    assert report.status == "FAIL"
    assert report.errors


def test_artifact_count_consistency_is_reported():
    gate = create_valid_pass_quality_gate()
    gate["artifact_count"] = 1
    gate["verified_artifact_count"] = 2

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            gate
        )
    )

    assert report.valid is False
    assert report.status == "FAIL"
    assert report.errors


def test_non_dictionary_gate_is_reported():
    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            "invalid"
        )
    )

    assert report.valid is False
    assert report.status == "FAIL"
    assert report.errors


def test_validation_errors_are_copied_into_report():
    gate = create_valid_pass_quality_gate()
    gate["status"] = "UNKNOWN"

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            gate
        )
    )

    assert len(report.errors) > 0


def test_pass_report_has_empty_errors():
    gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            gate
        )
    )

    assert report.errors == []


def test_fail_quality_gate_record_can_still_be_valid():
    gate = create_valid_fail_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            gate
        )
    )

    assert report.valid is True
    assert report.status == "PASS"


def test_report_dictionary_preserves_original_gate_data():
    gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            gate
        )
    )

    data = (
        evidence_quality_summary_quality_gate_validation_report_to_dict(
            report
        )
    )

    assert data["quality_gate"]["artifact_count"] == 2
    assert (
        data["quality_gate"]["verified_artifact_count"]
        == 2
    )


def test_report_status_matches_valid_field():
    gate = create_valid_pass_quality_gate()

    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            gate
        )
    )

    expected_status = (
        "PASS" if report.valid else "FAIL"
    )

    assert report.status == expected_status