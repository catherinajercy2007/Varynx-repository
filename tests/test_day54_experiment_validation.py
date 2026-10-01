from evaluation.experiment_export import report_to_json_dict
from evaluation.experiment_report import generate_default_report
from evaluation.experiment_validation import (
    validate_report,
    validate_report_consistency,
    validate_report_structure,
    validate_report_values,
)


def test_valid_report_structure():
    report = generate_default_report(5)
    data = report_to_json_dict(report)

    missing = validate_report_structure(data)

    assert missing == []


def test_valid_report_values():
    report = generate_default_report(5)
    data = report_to_json_dict(report)

    errors = validate_report_values(data)

    assert errors == []


def test_valid_report_consistency():
    report = generate_default_report(5)
    data = report_to_json_dict(report)

    errors = validate_report_consistency(data)

    assert errors == []


def test_complete_report_validation():
    report = generate_default_report(5)
    data = report_to_json_dict(report)

    result = validate_report(data)

    assert result["valid"] is True
    assert result["missing_fields"] == []
    assert result["value_errors"] == []
    assert result["consistency_errors"] == []


def test_missing_field_detection():
    report = generate_default_report(5)
    data = report_to_json_dict(report)

    del data["average_pass_rate"]

    missing = validate_report_structure(data)

    assert "average_pass_rate" in missing


def test_invalid_pass_rate_detection():
    report = generate_default_report(5)
    data = report_to_json_dict(report)

    data["average_pass_rate"] = 150.0

    errors = validate_report_values(data)

    assert errors


def test_invalid_pass_rate_range():
    report = generate_default_report(5)
    data = report_to_json_dict(report)

    data["minimum_pass_rate"] = 110.0

    result = validate_report(data)

    assert result["valid"] is False
    assert result["value_errors"]


def test_inconsistent_pass_rates():
    report = generate_default_report(5)
    data = report_to_json_dict(report)

    data["minimum_pass_rate"] = 100.0
    data["maximum_pass_rate"] = 90.0

    errors = validate_report_consistency(data)

    assert "minimum_pass_rate cannot exceed maximum_pass_rate" in errors


def test_inconsistent_average_pass_rate():
    report = generate_default_report(5)
    data = report_to_json_dict(report)

    data["minimum_pass_rate"] = 90.0
    data["average_pass_rate"] = 80.0
    data["maximum_pass_rate"] = 100.0

    errors = validate_report_consistency(data)

    assert (
        "average_pass_rate must be between minimum and maximum pass rates"
        in errors
    )


def test_invalid_decision_counts():
    report = generate_default_report(5)
    data = report_to_json_dict(report)

    data["average_allow_count"] = 10.0
    data["average_deny_count"] = 10.0

    errors = validate_report_consistency(data)

    assert errors


def test_empty_report_validation():
    report = {
        "total_runs": 0,
        "scenarios_per_run": 0,
        "stable": True,
        "average_pass_rate": 0.0,
        "minimum_pass_rate": 0.0,
        "maximum_pass_rate": 0.0,
        "average_allow_count": 0.0,
        "average_deny_count": 0.0,
    }

    result = validate_report(report)

    assert result["valid"] is True


def test_missing_multiple_fields():
    report = {
        "total_runs": 5,
        "stable": True,
    }

    missing = validate_report_structure(report)

    assert "scenarios_per_run" in missing
    assert "average_pass_rate" in missing
    assert "average_allow_count" in missing