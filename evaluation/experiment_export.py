import json
from typing import Any, Dict

from evaluation.experiment_report import (
    ExperimentReport,
    generate_default_report,
)


def report_to_json_dict(report: ExperimentReport) -> Dict[str, Any]:
    """
    Convert an ExperimentReport into a JSON-compatible dictionary.
    """

    return {
        "total_runs": report.total_runs,
        "scenarios_per_run": report.scenarios_per_run,
        "stable": report.stable,
        "average_pass_rate": report.average_pass_rate,
        "minimum_pass_rate": report.minimum_pass_rate,
        "maximum_pass_rate": report.maximum_pass_rate,
        "average_allow_count": report.average_allow_count,
        "average_deny_count": report.average_deny_count,
    }


def report_to_json(
    report: ExperimentReport,
) -> str:
    """
    Serialize an ExperimentReport into a JSON string.
    """

    data = report_to_json_dict(report)

    return json.dumps(
        data,
        indent=2,
        sort_keys=True,
    )


def generate_default_json_report(
    repetitions: int = 5,
) -> str:
    """
    Generate the default experiment report and serialize it as JSON.
    """

    report = generate_default_report(repetitions)

    return report_to_json(report)


def save_report_json(
    report: ExperimentReport,
    file_path: str,
) -> None:
    """
    Save an ExperimentReport as a JSON file.
    """

    data = report_to_json_dict(report)

    with open(
        file_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            sort_keys=True,
        )