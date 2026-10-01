from pathlib import Path

from evaluation.final_evaluation_report import (
    generate_default_final_report,
)
from evaluation.final_report_export import (
    final_report_to_json,
    final_report_to_json_dict,
    generate_default_final_json_report,
    load_final_report_json,
    save_final_report_json,
)


def test_final_report_to_json_dict():
    report = generate_default_final_report(5)

    data = final_report_to_json_dict(report)

    assert data["overall_status"] == "PASS"
    assert data["experiment"]["total_runs"] == 5
    assert data["quality_gate"]["valid"] is True
    assert data["comparison"]["baseline_aligned"] is True


def test_final_report_to_json():
    report = generate_default_final_report(5)

    json_data = final_report_to_json(report)

    assert isinstance(json_data, str)
    assert '"overall_status": "PASS"' in json_data
    assert '"total_runs": 5' in json_data


def test_json_report_is_deterministic():
    report = generate_default_final_report(5)

    first = final_report_to_json(report)
    second = final_report_to_json(report)

    assert first == second


def test_default_final_json_report():
    json_data = generate_default_final_json_report(5)

    assert isinstance(json_data, str)
    assert '"overall_status": "PASS"' in json_data
    assert '"scenarios_per_run": 8' in json_data


def test_custom_json_indent():
    report = generate_default_final_report(5)

    json_data = final_report_to_json(
        report,
        indent=4,
    )

    assert isinstance(json_data, str)
    assert '"overall_status": "PASS"' in json_data


def test_save_final_report_json(tmp_path):
    report = generate_default_final_report(5)

    output_file = tmp_path / "final_evaluation_report.json"

    saved_path = save_final_report_json(
        report,
        str(output_file),
    )

    assert saved_path == Path(output_file)
    assert output_file.exists()


def test_saved_report_contains_all_sections(tmp_path):
    report = generate_default_final_report(5)

    output_file = tmp_path / "final_report.json"

    save_final_report_json(
        report,
        str(output_file),
    )

    data = load_final_report_json(
        str(output_file),
    )

    assert "experiment" in data
    assert "quality_gate" in data
    assert "comparison" in data
    assert "overall_status" in data


def test_json_round_trip(tmp_path):
    report = generate_default_final_report(5)

    output_file = tmp_path / "round_trip_report.json"

    save_final_report_json(
        report,
        str(output_file),
    )

    loaded = load_final_report_json(
        str(output_file),
    )

    original = final_report_to_json_dict(report)

    assert loaded == original