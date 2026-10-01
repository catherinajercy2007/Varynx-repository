import json
from pathlib import Path
from typing import Any, Dict

from evaluation.final_evaluation_report import (
    FinalEvaluationReport,
    final_report_to_dict,
    generate_default_final_report,
)


def final_report_to_json_dict(
    report: FinalEvaluationReport,
) -> Dict[str, Any]:
    """
    Convert a final evaluation report into a JSON-compatible dictionary.
    """
    return final_report_to_dict(report)


def final_report_to_json(
    report: FinalEvaluationReport,
    indent: int = 2,
) -> str:
    """
    Serialize a final evaluation report to JSON.
    """
    data = final_report_to_json_dict(report)

    return json.dumps(
        data,
        indent=indent,
        sort_keys=True,
    )


def generate_default_final_json_report(
    repetitions: int = 5,
    indent: int = 2,
) -> str:
    """
    Generate the default final evaluation report and serialize it to JSON.
    """
    report = generate_default_final_report(repetitions)

    return final_report_to_json(
        report,
        indent=indent,
    )


def save_final_report_json(
    report: FinalEvaluationReport,
    file_path: str,
    indent: int = 2,
) -> Path:
    """
    Save a final evaluation report as a JSON file.

    Returns:
        Path: The path of the saved JSON artifact.
    """
    path = Path(file_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        final_report_to_json(report, indent=indent),
        encoding="utf-8",
    )

    return path


def load_final_report_json(
    file_path: str,
) -> Dict[str, Any]:
    """
    Load a previously saved final evaluation report JSON artifact.
    """
    path = Path(file_path)

    return json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )