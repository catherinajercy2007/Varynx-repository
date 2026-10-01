from evaluation.evidence_index import (
    create_evidence_index,
)
from evaluation.evidence_quality_report_validation import (
    evidence_quality_report_validation_status,
    generate_evidence_quality_report_validation,
    validate_evidence_quality_report,
    validate_report_consistency,
    validate_report_structure,
    validate_report_values,
    validate_quality_gate,
)
from evaluation.evidence_quality_report import (
    generate_evidence_quality_report,
)


def create_valid_report():
    index = create_evidence_index()

    return generate_evidence_quality_report(
        index,
    )


def create_valid_accepted_report(tmp_path):
    artifact = tmp_path / "artifact.json"

    artifact.write_text(
        '{"status": "valid"}',
        encoding="utf-8",
    )

    from evaluation.evidence_index import (
        register_artifact,
    )

    index = create_evidence_index()

    register_artifact(
        index,
        str(artifact),
    )

    return generate_evidence_quality_report(
        index,
        base_directory=str(tmp_path),
    )


def test_valid_rejected_report_structure():
    report = create_valid_report()

    errors = validate_report_structure(
        {
            "evidence_index": report.evidence_index,
            "quality_gate": report.quality_gate,
            "overall_status": report.overall_status,
            "accepted": report.accepted,
        }
    )

    assert errors == []


def test_missing_report_field_is_detected():
    errors = validate_report_structure(
        {
            "evidence_index": {},
        }
    )

    assert any(
        "Missing report field" in error
        for error in errors
    )


def test_valid_report_values():
    report = create_valid_report()

    errors = validate_report_values(
        {
            "evidence_index": report.evidence_index,
            "quality_gate": report.quality_gate,
            "overall_status": report.overall_status,
            "accepted": report.accepted,
        }
    )

    assert errors == []


def test_invalid_overall_status_is_detected():
    errors = validate_report_values(
        {
            "evidence_index": {},
            "quality_gate": {},
            "overall_status": "UNKNOWN",
            "accepted": False,
        }
    )

    assert "Invalid overall_status value." in errors


def test_invalid_accepted_type_is_detected():
    errors = validate_report_values(
        {
            "evidence_index": {},
            "quality_gate": {},
            "overall_status": "REJECTED",
            "accepted": "false",
        }
    )

    assert (
        "Accepted field must be a boolean."
        in errors
    )


def test_valid_quality_gate():
    report = create_valid_report()

    errors = validate_quality_gate(
        report.quality_gate
    )

    assert errors == []


def test_invalid_quality_gate_status():
    report = create_valid_report()

    report.quality_gate["status"] = "UNKNOWN"

    errors = validate_quality_gate(
        report.quality_gate
    )

    assert "Invalid quality gate status." in errors

def test_report_consistency_for_rejected_report():
    report = create_valid_report()

    errors = validate_report_consistency(
        {
            "overall_status": report.overall_status,
            "accepted": report.accepted,
            "quality_gate": report.quality_gate,
        }
    )

    assert errors == []


def test_report_consistency_detects_mismatch():
    errors = validate_report_consistency(
        {
            "overall_status": "ACCEPTED",
            "accepted": False,
            "quality_gate": {
                "status": "FAIL",
                "accepted": False,
            },
        }
    )

    assert any(
        "inconsistent" in error.lower()
        for error in errors
    )


def test_quality_gate_consistency_detects_mismatch():
    errors = validate_report_consistency(
        {
            "overall_status": "ACCEPTED",
            "accepted": True,
            "quality_gate": {
                "status": "FAIL",
                "accepted": False,
            },
        }
    )

    assert any(
        "quality gate" in error.lower()
        for error in errors
    )


def test_full_validation_returns_pass():
    report = create_valid_report()

    data = {
        "evidence_index": report.evidence_index,
        "quality_gate": report.quality_gate,
        "overall_status": report.overall_status,
        "accepted": report.accepted,
    }

    validation = validate_evidence_quality_report(
        data
    )

    assert validation["valid"] is True
    assert validation["errors"] == []


def test_full_validation_returns_fail():
    validation = validate_evidence_quality_report(
        {
            "overall_status": "UNKNOWN",
            "accepted": "invalid",
        }
    )

    assert validation["valid"] is False
    assert validation["errors"]


def test_validation_status_pass():
    validation = {
        "valid": True,
        "errors": [],
    }

    assert (
        evidence_quality_report_validation_status(
            validation
        )
        == "PASS"
    )


def test_validation_status_fail():
    validation = {
        "valid": False,
        "errors": [
            "Invalid report",
        ],
    }

    assert (
        evidence_quality_report_validation_status(
            validation
        )
        == "FAIL"
    )


def test_generate_validation_report():
    report = create_valid_report()

    data = {
        "evidence_index": report.evidence_index,
        "quality_gate": report.quality_gate,
        "overall_status": report.overall_status,
        "accepted": report.accepted,
    }

    validation = (
        generate_evidence_quality_report_validation(
            data
        )
    )

    assert validation["valid"] is True
    assert validation["status"] == "PASS"
    assert validation["errors"] == []


def test_accepted_report_can_be_validated(tmp_path):
    report = create_valid_accepted_report(
        tmp_path
    )

    data = {
        "evidence_index": report.evidence_index,
        "quality_gate": report.quality_gate,
        "overall_status": report.overall_status,
        "accepted": report.accepted,
    }

    validation = validate_evidence_quality_report(
        data
    )

    assert validation["valid"] is True
    assert report.overall_status == "ACCEPTED"
    assert report.accepted is True