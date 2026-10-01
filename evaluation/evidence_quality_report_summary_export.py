import json
from pathlib import Path
from typing import Any, Dict

from evaluation.evidence_quality_report_summary import (
    evidence_quality_report_summary_to_dict,
    generate_evidence_quality_report_summary,
)


def summary_to_json_dict(
    summary: Dict[str, Any],
) -> Dict[str, Any]:
    return evidence_quality_report_summary_to_dict(
        summary
    )


def summary_to_json(
    summary: Dict[str, Any],
    indent: int = 2,
) -> str:
    return json.dumps(
        summary_to_json_dict(summary),
        indent=indent,
        sort_keys=True,
    )


def save_evidence_quality_summary(
    summary: Dict[str, Any],
    file_path: str,
    indent: int = 2,
) -> Path:
    path = Path(file_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        summary_to_json(
            summary,
            indent=indent,
        ),
        encoding="utf-8",
    )

    return path


def load_evidence_quality_summary(
    file_path: str,
) -> Dict[str, Any]:
    path = Path(file_path)

    return json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )


def generate_and_export_evidence_quality_summary(
    report: Dict[str, Any],
    file_path: str,
    indent: int = 2,
) -> Path:
    generated = (
        generate_evidence_quality_report_summary(
            report
        )
    )

    summary = generated["summary"]

    return save_evidence_quality_summary(
        summary,
        file_path,
        indent=indent,
    )


def export_summary_json(
    report: Dict[str, Any],
    indent: int = 2,
) -> str:
    generated = (
        generate_evidence_quality_report_summary(
            report
        )
    )

    return summary_to_json(
        generated["summary"],
        indent=indent,
    )