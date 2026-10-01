import json

from evaluation.experiment_export import (
    generate_default_json_report,
    report_to_json,
    report_to_json_dict,
    save_report_json,
)
from evaluation.experiment_report import (
    generate_default_report,
    generate_report,
)
from evaluation.reproducibility import run_repeated_experiments


def test_report_to_json_dict():
    report = generate_default_report(5)

    data = report_to_json_dict(report)

    assert data["total_runs"] == 5
    assert data["scenarios_per_run"] == 8
    assert data["stable"] is True
    assert data["average_pass_rate"] == 100.0
    assert data["average_allow_count"] == 2.0
    assert data["average_deny_count"] == 6.0


def test_report_to_json():
    report = generate_default_report(5)

    json_data = report_to_json(report)

    data = json.loads(json_data)

    assert data["total_runs"] == 5
    assert data["scenarios_per_run"] == 8
    assert data["stable"] is True
    assert data["average_pass_rate"] == 100.0


def test_json_is_serializable():
    report = generate_default_report(5)

    json_data = report_to_json(report)

    assert isinstance(json_data, str)
    assert json.loads(json_data)


def test_generate_default_json_report():
    json_data = generate_default_json_report(5)

    data = json.loads(json_data)

    assert data["total_runs"] == 5
    assert data["scenarios_per_run"] == 8
    assert data["average_pass_rate"] == 100.0
    assert data["average_allow_count"] == 2.0
    assert data["average_deny_count"] == 6.0


def test_save_report_json(tmp_path):
    report = generate_default_report(5)

    output_file = tmp_path / "experiment_report.json"

    save_report_json(
        report,
        str(output_file),
    )

    assert output_file.exists()

    with open(
        output_file,
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    assert data["total_runs"] == 5
    assert data["scenarios_per_run"] == 8
    assert data["stable"] is True


def test_empty_report_json():
    report = generate_report([])

    json_data = report_to_json(report)

    data = json.loads(json_data)

    assert data["total_runs"] == 0
    assert data["scenarios_per_run"] == 0
    assert data["stable"] is True
    assert data["average_pass_rate"] == 0.0


def test_json_report_preserves_metrics():
    runs = run_repeated_experiments(5)

    report = generate_report(runs)

    data = json.loads(report_to_json(report))

    assert data["minimum_pass_rate"] == 100.0
    assert data["maximum_pass_rate"] == 100.0
    assert data["average_allow_count"] == 2.0
    assert data["average_deny_count"] == 6.0