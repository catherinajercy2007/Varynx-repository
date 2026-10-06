from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation_report import (
    ExportedQualityGateValidationReport,
    determine_exported_quality_gate_validation_report_status,
    exported_quality_gate_validation_report_status,
    exported_quality_gate_validation_report_to_dict,
    generate_default_exported_quality_gate_validation_report,
    generate_exported_quality_gate_validation_report,
)


def create_valid_pass_quality_gate():
    return {
        "valid": True,
        "status": "PASS",
        "validation_errors": [],
        "accepted": True,
    }


def create_valid_fail_quality_gate():
    return {
        "valid": False,
        "status": "FAIL",
        "validation_errors": [
            "Evidence artifact integrity verification failed."
        ],
        "accepted": False,
    }


def test_valid_pass_record_generates_report():
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    assert report.valid is True
    assert report.status == "PASS"
    assert report.errors == []


def test_valid_fail_record_generates_valid_report():
    report = generate_exported_quality_gate_validation_report(
        create_valid_fail_quality_gate()
    )

    assert report.valid is True
    assert report.status == "PASS"
    assert report.errors == []


def test_report_is_dataclass():
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    assert isinstance(
        report,
        ExportedQualityGateValidationReport,
    )


def test_report_preserves_quality_gate():
    quality_gate = create_valid_pass_quality_gate()

    report = generate_exported_quality_gate_validation_report(
        quality_gate
    )

    assert report.quality_gate == quality_gate


def test_report_valid_field_is_boolean():
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    assert isinstance(report.valid, bool)


def test_report_status_is_pass_for_valid_record():
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    assert report.status == "PASS"


def test_invalid_record_generates_fail_report():
    quality_gate = create_valid_pass_quality_gate()
    quality_gate["status"] = "INVALID"

    report = generate_exported_quality_gate_validation_report(
        quality_gate
    )

    assert report.valid is False
    assert report.status == "FAIL"
    assert report.errors


def test_invalid_record_contains_validation_errors():
    quality_gate = create_valid_pass_quality_gate()
    quality_gate["accepted"] = False

    report = generate_exported_quality_gate_validation_report(
        quality_gate
    )

    assert report.valid is False
    assert report.errors


def test_missing_field_generates_fail_report():
    quality_gate = create_valid_pass_quality_gate()
    del quality_gate["valid"]

    report = generate_exported_quality_gate_validation_report(
        quality_gate
    )

    assert report.valid is False
    assert report.status == "FAIL"


def test_missing_status_generates_fail_report():
    quality_gate = create_valid_pass_quality_gate()
    del quality_gate["status"]

    report = generate_exported_quality_gate_validation_report(
        quality_gate
    )

    assert report.valid is False
    assert report.status == "FAIL"


def test_missing_validation_errors_generates_fail_report():
    quality_gate = create_valid_pass_quality_gate()
    del quality_gate["validation_errors"]

    report = generate_exported_quality_gate_validation_report(
        quality_gate
    )

    assert report.valid is False
    assert report.status == "FAIL"


def test_missing_accepted_generates_fail_report():
    quality_gate = create_valid_pass_quality_gate()
    del quality_gate["accepted"]

    report = generate_exported_quality_gate_validation_report(
        quality_gate
    )

    assert report.valid is False
    assert report.status == "FAIL"


def test_report_errors_are_list():
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    assert isinstance(report.errors, list)


def test_report_to_dict_returns_dictionary():
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    data = exported_quality_gate_validation_report_to_dict(
        report
    )

    assert isinstance(data, dict)


def test_report_to_dict_contains_expected_fields():
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    data = exported_quality_gate_validation_report_to_dict(
        report
    )

    assert set(data.keys()) == {
        "quality_gate",
        "valid",
        "status",
        "errors",
    }


def test_report_to_dict_preserves_pass_values():
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    data = exported_quality_gate_validation_report_to_dict(
        report
    )

    assert data["valid"] is True
    assert data["status"] == "PASS"
    assert data["errors"] == []


def test_report_to_dict_preserves_quality_gate():
    quality_gate = create_valid_pass_quality_gate()

    report = generate_exported_quality_gate_validation_report(
        quality_gate
    )

    data = exported_quality_gate_validation_report_to_dict(
        report
    )

    assert data["quality_gate"] == quality_gate


def test_report_to_dict_preserves_fail_values():
    quality_gate = create_valid_pass_quality_gate()
    quality_gate["status"] = "INVALID"

    report = generate_exported_quality_gate_validation_report(
        quality_gate
    )

    data = exported_quality_gate_validation_report_to_dict(
        report
    )

    assert data["valid"] is False
    assert data["status"] == "FAIL"
    assert data["errors"]


def test_status_helper_returns_pass():
    report = generate_exported_quality_gate_validation_report(
        create_valid_pass_quality_gate()
    )

    assert (
        exported_quality_gate_validation_report_status(
            report
        )
        == "PASS"
    )


def test_status_helper_returns_fail():
    quality_gate = create_valid_pass_quality_gate()
    quality_gate["status"] = "INVALID"

    report = generate_exported_quality_gate_validation_report(
        quality_gate
    )

    assert (
        exported_quality_gate_validation_report_status(
            report
        )
        == "FAIL"
    )


def test_determine_status_returns_pass():
    assert (
        determine_exported_quality_gate_validation_report_status(
            True
        )
        == "PASS"
    )


def test_determine_status_returns_fail():
    assert (
        determine_exported_quality_gate_validation_report_status(
            False
        )
        == "FAIL"
    )


def test_default_helper_matches_generator():
    quality_gate = create_valid_pass_quality_gate()

    direct = generate_exported_quality_gate_validation_report(
        quality_gate
    )

    generated = (
        generate_default_exported_quality_gate_validation_report(
            quality_gate
        )
    )

    assert generated == direct


def test_default_helper_preserves_fail_record():
    quality_gate = create_valid_fail_quality_gate()

    report = (
        generate_default_exported_quality_gate_validation_report(
            quality_gate
        )
    )

    assert report.valid is True
    assert report.status == "PASS"
    assert report.quality_gate == quality_gate


def test_report_contains_no_errors_for_valid_fail_record():
    report = generate_exported_quality_gate_validation_report(
        create_valid_fail_quality_gate()
    )

    assert report.errors == []