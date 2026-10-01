from evaluation.experiment_export import report_to_json_dict
from evaluation.experiment_report import generate_default_report
from evaluation.experiment_quality_gate import (
    evaluate_experiment_quality,
    evaluate_quality_gate,
    generate_default_quality_gate,
    quality_gate_to_dict,
)


def test_valid_quality_gate():
    report = generate_default_report(5)
    data = report_to_json_dict(report)

    result = evaluate_quality_gate(data)

    assert result.valid is True
    assert result.status == "PASS"
    assert result.missing_fields == []
    assert result.value_errors == []
    assert result.consistency_errors == []


def test_experiment_quality():
    report = generate_default_report(5)

    result = evaluate_experiment_quality(report)

    assert result.valid is True
    assert result.status == "PASS"


def test_default_quality_gate():
    result = generate_default_quality_gate(5)

    assert result.valid is True
    assert result.status == "PASS"


def test_invalid_quality_gate():
    report = generate_default_report(5)
    data = report_to_json_dict(report)

    data["average_pass_rate"] = 150.0

    result = evaluate_quality_gate(data)

    assert result.valid is False
    assert result.status == "FAIL"
    assert result.value_errors


def test_missing_field_quality_gate():
    report = generate_default_report(5)
    data = report_to_json_dict(report)

    del data["average_pass_rate"]

    result = evaluate_quality_gate(data)

    assert result.valid is False
    assert result.status == "FAIL"
    assert "average_pass_rate" in result.missing_fields


def test_inconsistent_quality_gate():
    report = generate_default_report(5)
    data = report_to_json_dict(report)

    data["minimum_pass_rate"] = 100.0
    data["maximum_pass_rate"] = 90.0

    result = evaluate_quality_gate(data)

    assert result.valid is False
    assert result.status == "FAIL"
    assert result.consistency_errors


def test_quality_gate_dictionary():
    result = generate_default_quality_gate(5)

    data = quality_gate_to_dict(result)

    assert data["valid"] is True
    assert data["status"] == "PASS"
    assert data["missing_fields"] == []
    assert data["value_errors"] == []
    assert data["consistency_errors"] == []


def test_quality_gate_dictionary_invalid():
    report = generate_default_report(5)
    data = report_to_json_dict(report)

    data["average_deny_count"] = 20.0

    result = evaluate_quality_gate(data)
    output = quality_gate_to_dict(result)

    assert output["valid"] is False
    assert output["status"] == "FAIL"
    assert output["consistency_errors"]