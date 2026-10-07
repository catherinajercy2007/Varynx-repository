from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation_report_export_validation_report import (
    ExportedValidationReportExportValidationReport,
    determine_exported_validation_report_export_validation_report_status,
    exported_validation_report_export_validation_report_status,
    exported_validation_report_export_validation_report_to_dict,
    generate_default_exported_validation_report_export_validation_report,
    generate_exported_validation_report_export_validation_report,
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


def test_generate_returns_dataclass():
    result = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    assert isinstance(
        result,
        ExportedValidationReportExportValidationReport,
    )


def test_generated_report_contains_original_report():
    report = create_valid_pass_report()

    result = (
        generate_exported_validation_report_export_validation_report(
            report
        )
    )

    assert result.report == report


def test_valid_report_generates_valid_result():
    result = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    assert result.valid is True


def test_valid_report_generates_pass_status():
    result = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    assert result.status == "PASS"


def test_valid_report_generates_empty_errors():
    result = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    assert result.errors == []


def test_invalid_report_generates_invalid_result():
    result = (
        generate_exported_validation_report_export_validation_report(
            create_invalid_report()
        )
    )

    assert result.valid is False


def test_invalid_report_generates_fail_status():
    result = (
        generate_exported_validation_report_export_validation_report(
            create_invalid_report()
        )
    )

    assert result.status == "FAIL"


def test_invalid_report_preserves_errors():
    result = (
        generate_exported_validation_report_export_validation_report(
            create_invalid_report()
        )
    )

    assert result.errors


def test_failed_underlying_gate_can_have_valid_export_report():
    result = (
        generate_exported_validation_report_export_validation_report(
            create_valid_fail_underlying_gate_report()
        )
    )

    assert result.valid is True
    assert result.status == "PASS"
    assert result.errors == []


def test_failed_underlying_gate_is_preserved():
    result = (
        generate_exported_validation_report_export_validation_report(
            create_valid_fail_underlying_gate_report()
        )
    )

    assert result.report["quality_gate"]["valid"] is False
    assert result.report["quality_gate"]["status"] == "FAIL"


def test_report_to_dict_returns_dictionary():
    result = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    converted = (
        exported_validation_report_export_validation_report_to_dict(
            result
        )
    )

    assert isinstance(converted, dict)


def test_report_to_dict_contains_expected_fields():
    result = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    converted = (
        exported_validation_report_export_validation_report_to_dict(
            result
        )
    )

    assert set(converted.keys()) == {
        "report",
        "valid",
        "status",
        "errors",
    }


def test_report_to_dict_preserves_report():
    report = create_valid_pass_report()

    result = (
        generate_exported_validation_report_export_validation_report(
            report
        )
    )

    converted = (
        exported_validation_report_export_validation_report_to_dict(
            result
        )
    )

    assert converted["report"] == report


def test_report_to_dict_preserves_valid_value():
    result = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    converted = (
        exported_validation_report_export_validation_report_to_dict(
            result
        )
    )

    assert converted["valid"] is True


def test_report_to_dict_preserves_status():
    result = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    converted = (
        exported_validation_report_export_validation_report_to_dict(
            result
        )
    )

    assert converted["status"] == "PASS"


def test_report_to_dict_preserves_errors():
    result = (
        generate_exported_validation_report_export_validation_report(
            create_invalid_report()
        )
    )

    converted = (
        exported_validation_report_export_validation_report_to_dict(
            result
        )
    )

    assert converted["errors"] == result.errors


def test_status_function_returns_pass():
    assert (
        determine_exported_validation_report_export_validation_report_status(
            True
        )
        == "PASS"
    )


def test_status_function_returns_fail():
    assert (
        determine_exported_validation_report_export_validation_report_status(
            False
        )
        == "FAIL"
    )


def test_report_status_helper_returns_pass():
    result = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    assert (
        exported_validation_report_export_validation_report_status(
            result
        )
        == "PASS"
    )


def test_report_status_helper_returns_fail():
    result = (
        generate_exported_validation_report_export_validation_report(
            create_invalid_report()
        )
    )

    assert (
        exported_validation_report_export_validation_report_status(
            result
        )
        == "FAIL"
    )


def test_default_generator_returns_dataclass():
    result = (
        generate_default_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    assert isinstance(
        result,
        ExportedValidationReportExportValidationReport,
    )


def test_default_generator_preserves_values():
    result = (
        generate_default_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    assert result.valid is True
    assert result.status == "PASS"
    assert result.errors == []


def test_default_generator_preserves_nested_report():
    report = create_valid_pass_report()

    result = (
        generate_default_exported_validation_report_export_validation_report(
            report
        )
    )

    assert result.report == report


def test_dataclass_fields_are_accessible():
    result = (
        generate_exported_validation_report_export_validation_report(
            create_valid_pass_report()
        )
    )

    assert hasattr(result, "report")
    assert hasattr(result, "valid")
    assert hasattr(result, "status")
    assert hasattr(result, "errors")


def test_invalid_report_dict_conversion():
    result = (
        generate_exported_validation_report_export_validation_report(
            create_invalid_report()
        )
    )

    converted = (
        exported_validation_report_export_validation_report_to_dict(
            result
        )
    )

    assert converted["valid"] is False
    assert converted["status"] == "FAIL"
    assert converted["errors"]


def test_valid_fail_underlying_gate_dict_conversion():
    result = (
        generate_exported_validation_report_export_validation_report(
            create_valid_fail_underlying_gate_report()
        )
    )

    converted = (
        exported_validation_report_export_validation_report_to_dict(
            result
        )
    )

    assert converted["valid"] is True
    assert converted["status"] == "PASS"
    assert converted["report"]["quality_gate"]["valid"] is False