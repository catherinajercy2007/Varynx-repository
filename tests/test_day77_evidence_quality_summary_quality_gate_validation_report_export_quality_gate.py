from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate import (
    ExportedValidationReportQualityGateResult,
    evaluate_exported_validation_report_quality_gate,
    exported_validation_report_quality_gate_status,
    exported_validation_report_quality_gate_to_dict,
    generate_exported_validation_report_quality_gate,
)


def create_valid_pass_report():
    return {
        "quality_gate": {
            "valid": True,
            "status": "PASS",
            "validation_errors": [],
            "accepted": True,
            "artifact_count": 2,
            "verified_artifact_count": 2,
        },
        "valid": True,
        "status": "PASS",
        "errors": [],
    }


def create_valid_rejected_gate_report():
    return {
        "quality_gate": {
            "valid": False,
            "status": "FAIL",
            "validation_errors": [
                "Evidence artifact integrity verification failed."
            ],
            "accepted": False,
            "artifact_count": 2,
            "verified_artifact_count": 1,
        },
        "valid": True,
        "status": "PASS",
        "errors": [],
    }


def test_valid_report_is_accepted():
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    assert result.valid is True
    assert result.status == "PASS"
    assert result.accepted is True


def test_valid_report_has_no_errors():
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    assert result.validation_errors == []


def test_rejected_underlying_gate_can_be_valid_report():
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_rejected_gate_report()
    )

    assert result.valid is True
    assert result.status == "PASS"
    assert result.accepted is True


def test_invalid_status_is_rejected():
    report = create_valid_pass_report()
    report["status"] = "INVALID"

    result = evaluate_exported_validation_report_quality_gate(
        report
    )

    assert result.valid is False
    assert result.status == "FAIL"
    assert result.accepted is False


def test_missing_quality_gate_is_rejected():
    report = create_valid_pass_report()
    del report["quality_gate"]

    result = evaluate_exported_validation_report_quality_gate(
        report
    )

    assert result.valid is False
    assert result.status == "FAIL"


def test_invalid_valid_type_is_rejected():
    report = create_valid_pass_report()
    report["valid"] = "true"

    result = evaluate_exported_validation_report_quality_gate(
        report
    )

    assert result.valid is False
    assert result.status == "FAIL"


def test_invalid_errors_type_is_rejected():
    report = create_valid_pass_report()
    report["errors"] = "no errors"

    result = evaluate_exported_validation_report_quality_gate(
        report
    )

    assert result.valid is False
    assert result.status == "FAIL"


def test_inconsistent_report_is_rejected():
    report = create_valid_pass_report()
    report["valid"] = False
    report["status"] = "FAIL"
    report["errors"] = []

    result = evaluate_exported_validation_report_quality_gate(
        report
    )

    assert result.valid is False
    assert result.status == "FAIL"


def test_quality_gate_result_is_dataclass():
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    assert isinstance(
        result,
        ExportedValidationReportQualityGateResult,
    )


def test_result_valid_field():
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    assert result.valid is True


def test_result_status_field():
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    assert result.status == "PASS"


def test_result_accepted_field():
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    assert result.accepted is True


def test_failed_result_contains_errors():
    report = create_valid_pass_report()
    report["status"] = "INVALID"

    result = evaluate_exported_validation_report_quality_gate(
        report
    )

    assert result.validation_errors


def test_to_dict_returns_dictionary():
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    data = exported_validation_report_quality_gate_to_dict(
        result
    )

    assert isinstance(data, dict)


def test_to_dict_contains_expected_fields():
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    data = exported_validation_report_quality_gate_to_dict(
        result
    )

    assert set(data.keys()) == {
        "valid",
        "status",
        "validation_errors",
        "accepted",
    }


def test_to_dict_preserves_pass_result():
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    data = exported_validation_report_quality_gate_to_dict(
        result
    )

    assert data["valid"] is True
    assert data["status"] == "PASS"
    assert data["validation_errors"] == []
    assert data["accepted"] is True


def test_status_helper_returns_pass():
    result = evaluate_exported_validation_report_quality_gate(
        create_valid_pass_report()
    )

    assert (
        exported_validation_report_quality_gate_status(
            result
        )
        == "PASS"
    )


def test_status_helper_returns_fail():
    report = create_valid_pass_report()
    report["status"] = "INVALID"

    result = evaluate_exported_validation_report_quality_gate(
        report
    )

    assert (
        exported_validation_report_quality_gate_status(
            result
        )
        == "FAIL"
    )


def test_generate_helper_matches_evaluator():
    report = create_valid_pass_report()

    direct = evaluate_exported_validation_report_quality_gate(
        report
    )

    generated = generate_exported_validation_report_quality_gate(
        report
    )

    assert generated == direct


def test_non_dictionary_input_is_rejected():
    result = evaluate_exported_validation_report_quality_gate(
        ["invalid"]
    )

    assert result.valid is False
    assert result.status == "FAIL"
    assert result.accepted is False