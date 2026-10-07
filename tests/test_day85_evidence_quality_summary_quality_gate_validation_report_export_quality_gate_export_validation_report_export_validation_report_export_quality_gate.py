from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation_report_export_validation_report_export_quality_gate import (
    ExportedValidationReportExportQualityGateResult,
    evaluate_exported_validation_report_export_quality_gate,
    exported_validation_report_export_quality_gate_status,
    exported_validation_report_export_quality_gate_to_dict,
    generate_exported_validation_report_export_quality_gate,
)


def create_valid_pass_report():
    return {
        "quality_gate": {
            "valid": True,
            "status": "PASS",
            "validation_errors": [],
            "accepted": True,
        },
        "valid": True,
        "status": "PASS",
        "errors": [],
    }


def create_valid_fail_underlying_gate_report():
    return {
        "quality_gate": {
            "valid": False,
            "status": "FAIL",
            "validation_errors": [
                "Evidence artifact integrity verification failed."
            ],
            "accepted": False,
        },
        "valid": True,
        "status": "PASS",
        "errors": [],
    }


def create_invalid_report():
    return {
        "quality_gate": {
            "valid": True,
            "status": "PASS",
            "validation_errors": [],
            "accepted": True,
        },
        "valid": True,
        "status": "INVALID",
        "errors": [],
    }


def test_valid_report_returns_dataclass():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    assert isinstance(
        result,
        ExportedValidationReportExportQualityGateResult,
    )


def test_valid_report_is_valid():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    assert result.valid is True


def test_valid_report_status_is_pass():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    assert result.status == "PASS"


def test_valid_report_is_accepted():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    assert result.accepted is True


def test_valid_report_has_no_validation_errors():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    assert result.validation_errors == []


def test_invalid_report_is_rejected():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_invalid_report()
        )
    )

    assert result.valid is False
    assert result.status == "FAIL"
    assert result.accepted is False
    assert result.validation_errors


def test_invalid_report_contains_validation_errors():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_invalid_report()
        )
    )

    assert len(result.validation_errors) > 0


def test_failed_underlying_gate_can_produce_pass_export_quality_gate():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_fail_underlying_gate_report()
        )
    )

    assert result.valid is True
    assert result.status == "PASS"
    assert result.accepted is True


def test_failed_underlying_gate_is_not_same_as_invalid_export():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_fail_underlying_gate_report()
        )
    )

    assert result.validation_errors == []


def test_dict_conversion_returns_dictionary():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    converted = (
        exported_validation_report_export_quality_gate_to_dict(
            result
        )
    )

    assert isinstance(converted, dict)


def test_dict_conversion_contains_expected_fields():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    converted = (
        exported_validation_report_export_quality_gate_to_dict(
            result
        )
    )

    assert set(converted.keys()) == {
        "valid",
        "status",
        "validation_errors",
        "accepted",
    }


def test_dict_conversion_preserves_valid():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    converted = (
        exported_validation_report_export_quality_gate_to_dict(
            result
        )
    )

    assert converted["valid"] is True


def test_dict_conversion_preserves_status():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    converted = (
        exported_validation_report_export_quality_gate_to_dict(
            result
        )
    )

    assert converted["status"] == "PASS"


def test_dict_conversion_preserves_accepted():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    converted = (
        exported_validation_report_export_quality_gate_to_dict(
            result
        )
    )

    assert converted["accepted"] is True


def test_dict_conversion_preserves_errors():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_invalid_report()
        )
    )

    converted = (
        exported_validation_report_export_quality_gate_to_dict(
            result
        )
    )

    assert converted["validation_errors"] == (
        result.validation_errors
    )


def test_status_helper_returns_pass():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    assert (
        exported_validation_report_export_quality_gate_status(
            result
        )
        == "PASS"
    )


def test_status_helper_returns_fail():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_invalid_report()
        )
    )

    assert (
        exported_validation_report_export_quality_gate_status(
            result
        )
        == "FAIL"
    )


def test_generate_helper_returns_dataclass():
    result = (
        generate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    assert isinstance(
        result,
        ExportedValidationReportExportQualityGateResult,
    )


def test_generate_helper_returns_pass():
    result = (
        generate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    assert result.status == "PASS"
    assert result.accepted is True


def test_generate_helper_returns_fail():
    result = (
        generate_exported_validation_report_export_quality_gate(
            create_invalid_report()
        )
    )

    assert result.status == "FAIL"
    assert result.accepted is False


def test_generate_helper_preserves_validation_errors():
    result = (
        generate_exported_validation_report_export_quality_gate(
            create_invalid_report()
        )
    )

    assert result.validation_errors


def test_result_fields_are_accessible():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    assert hasattr(result, "valid")
    assert hasattr(result, "status")
    assert hasattr(result, "validation_errors")
    assert hasattr(result, "accepted")


def test_valid_report_dict_has_expected_values():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_pass_report()
        )
    )

    converted = (
        exported_validation_report_export_quality_gate_to_dict(
            result
        )
    )

    assert converted == {
        "valid": True,
        "status": "PASS",
        "validation_errors": [],
        "accepted": True,
    }


def test_invalid_report_dict_has_expected_values():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_invalid_report()
        )
    )

    converted = (
        exported_validation_report_export_quality_gate_to_dict(
            result
        )
    )

    assert converted["valid"] is False
    assert converted["status"] == "FAIL"
    assert converted["accepted"] is False
    assert converted["validation_errors"]


def test_failed_underlying_gate_dict_is_accepted_export():
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            create_valid_fail_underlying_gate_report()
        )
    )

    converted = (
        exported_validation_report_export_quality_gate_to_dict(
            result
        )
    )

    assert converted["valid"] is True
    assert converted["status"] == "PASS"
    assert converted["accepted"] is True