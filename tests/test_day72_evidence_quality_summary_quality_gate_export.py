from pathlib import Path

from evaluation.evidence_quality_summary_quality_gate_export import (
    evaluate_and_export_evidence_quality_summary_quality_gate,
    export_quality_gate_json,
    load_evidence_quality_summary_quality_gate,
    quality_gate_to_json,
    quality_gate_to_json_dict,
    save_evidence_quality_summary_quality_gate,
)
from evaluation.evidence_quality_report_summary_quality_gate import (
    evaluate_evidence_quality_summary_quality_gate,
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


def test_quality_gate_to_json_dict():
    summary = create_valid_accepted_summary()

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    data = quality_gate_to_json_dict(result)

    assert data == {
        "valid": True,
        "status": "PASS",
        "validation_errors": [],
        "accepted": True,
        "artifact_count": 2,
        "verified_artifact_count": 2,
    }


def test_rejected_quality_gate_to_json_dict():
    summary = create_valid_rejected_summary()

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    data = quality_gate_to_json_dict(result)

    assert data["valid"] is True
    assert data["status"] == "FAIL"
    assert data["accepted"] is False


def test_quality_gate_to_json_returns_string():
    summary = create_valid_accepted_summary()

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    data = quality_gate_to_json(result)

    assert isinstance(data, str)
    assert '"status": "PASS"' in data


def test_quality_gate_json_is_parseable():
    import json

    summary = create_valid_accepted_summary()

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    data = quality_gate_to_json(result)

    parsed = json.loads(data)

    assert parsed["valid"] is True
    assert parsed["status"] == "PASS"


def test_custom_json_indent():
    summary = create_valid_accepted_summary()

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    data = quality_gate_to_json(
        result,
        indent=4,
    )

    assert isinstance(data, str)
    assert '"accepted": true' in data


def test_save_quality_gate(tmp_path):
    summary = create_valid_accepted_summary()

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    file_path = tmp_path / "quality_gate.json"

    saved_path = (
        save_evidence_quality_summary_quality_gate(
            result,
            str(file_path),
        )
    )

    assert isinstance(saved_path, Path)
    assert saved_path.exists()


def test_save_creates_parent_directory(tmp_path):
    summary = create_valid_accepted_summary()

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    file_path = (
        tmp_path
        / "nested"
        / "evidence"
        / "quality_gate.json"
    )

    saved_path = (
        save_evidence_quality_summary_quality_gate(
            result,
            str(file_path),
        )
    )

    assert saved_path.exists()


def test_load_quality_gate(tmp_path):
    summary = create_valid_accepted_summary()

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    file_path = tmp_path / "quality_gate.json"

    save_evidence_quality_summary_quality_gate(
        result,
        str(file_path),
    )

    loaded = (
        load_evidence_quality_summary_quality_gate(
            str(file_path)
        )
    )

    assert loaded["valid"] is True
    assert loaded["status"] == "PASS"
    assert loaded["accepted"] is True


def test_save_load_round_trip(tmp_path):
    summary = create_valid_accepted_summary()

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    file_path = tmp_path / "quality_gate.json"

    save_evidence_quality_summary_quality_gate(
        result,
        str(file_path),
    )

    loaded = (
        load_evidence_quality_summary_quality_gate(
            str(file_path)
        )
    )

    assert loaded == quality_gate_to_json_dict(
        result
    )


def test_rejected_save_load_round_trip(tmp_path):
    summary = create_valid_rejected_summary()

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    file_path = tmp_path / "rejected_gate.json"

    save_evidence_quality_summary_quality_gate(
        result,
        str(file_path),
    )

    loaded = (
        load_evidence_quality_summary_quality_gate(
            str(file_path)
        )
    )

    assert loaded["status"] == "FAIL"
    assert loaded["accepted"] is False


def test_export_quality_gate_json():
    summary = create_valid_accepted_summary()

    data = export_quality_gate_json(summary)

    assert isinstance(data, str)
    assert '"status": "PASS"' in data
    assert '"accepted": true' in data


def test_export_rejected_quality_gate_json():
    summary = create_valid_rejected_summary()

    data = export_quality_gate_json(summary)

    assert isinstance(data, str)
    assert '"status": "FAIL"' in data
    assert '"accepted": false' in data


def test_evaluate_and_export_creates_file(tmp_path):
    summary = create_valid_accepted_summary()

    file_path = tmp_path / "exported.json"

    saved_path = (
        evaluate_and_export_evidence_quality_summary_quality_gate(
            summary,
            str(file_path),
        )
    )

    assert saved_path.exists()

    loaded = (
        load_evidence_quality_summary_quality_gate(
            str(file_path)
        )
    )

    assert loaded["status"] == "PASS"


def test_evaluate_and_export_rejected_summary(tmp_path):
    summary = create_valid_rejected_summary()

    file_path = tmp_path / "rejected.json"

    evaluate_and_export_evidence_quality_summary_quality_gate(
        summary,
        str(file_path),
    )

    loaded = (
        load_evidence_quality_summary_quality_gate(
            str(file_path)
        )
    )

    assert loaded["status"] == "FAIL"
    assert loaded["accepted"] is False


def test_invalid_summary_can_be_exported(tmp_path):
    summary = create_valid_accepted_summary()
    summary["overall_status"] = "UNKNOWN"

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    file_path = tmp_path / "invalid.json"

    save_evidence_quality_summary_quality_gate(
        result,
        str(file_path),
    )

    loaded = (
        load_evidence_quality_summary_quality_gate(
            str(file_path)
        )
    )

    assert loaded["valid"] is False
    assert loaded["status"] == "FAIL"
    assert loaded["validation_errors"]


def test_invalid_summary_export_json():
    summary = create_valid_accepted_summary()
    summary["artifact_count"] = -1

    data = export_quality_gate_json(summary)

    assert '"status": "FAIL"' in data
    assert '"valid": false' in data


def test_loaded_artifact_counts_are_preserved(tmp_path):
    summary = create_valid_accepted_summary()

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    file_path = tmp_path / "counts.json"

    save_evidence_quality_summary_quality_gate(
        result,
        str(file_path),
    )

    loaded = (
        load_evidence_quality_summary_quality_gate(
            str(file_path)
        )
    )

    assert loaded["artifact_count"] == 2
    assert loaded["verified_artifact_count"] == 2


def test_export_uses_quality_gate_evaluation():
    summary = create_valid_accepted_summary()

    summary["accepted"] = False

    data = export_quality_gate_json(summary)

    assert '"status": "FAIL"' in data
    assert '"accepted": false' in data


def test_export_functions_are_consistent(tmp_path):
    summary = create_valid_accepted_summary()

    result = evaluate_evidence_quality_summary_quality_gate(
        summary
    )

    direct_json = quality_gate_to_json(result)

    exported_json = export_quality_gate_json(summary)

    assert direct_json == exported_json

    file_path = tmp_path / "consistent.json"

    save_evidence_quality_summary_quality_gate(
        result,
        str(file_path),
    )

    loaded = (
        load_evidence_quality_summary_quality_gate(
            str(file_path)
        )
    )

    assert loaded == quality_gate_to_json_dict(result)