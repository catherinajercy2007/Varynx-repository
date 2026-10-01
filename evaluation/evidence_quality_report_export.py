import json
from pathlib import Path
from typing import Any, Dict

from evaluation.evidence_index import create_evidence_index
from evaluation.evidence_quality_report import (
    EvidenceQualityReport,
    evidence_quality_report_to_dict,
    generate_evidence_quality_report,
)


def report_to_json_dict(
    report: EvidenceQualityReport,
) -> Dict[str, Any]:
    return evidence_quality_report_to_dict(report)


def report_to_json(
    report: EvidenceQualityReport,
    indent: int = 2,
) -> str:
    return json.dumps(
        report_to_json_dict(report),
        indent=indent,
        sort_keys=True,
    )


def save_evidence_quality_report(
    report: EvidenceQualityReport,
    file_path: str,
    indent: int = 2,
) -> Path:
    path = Path(file_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        report_to_json(
            report,
            indent=indent,
        ),
        encoding="utf-8",
    )

    return path


def load_evidence_quality_report(
    file_path: str,
) -> Dict[str, Any]:
    path = Path(file_path)

    return json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )


def generate_default_evidence_quality_report(
    base_directory: str = ".",
) -> EvidenceQualityReport:
    index = create_evidence_index()

    return generate_evidence_quality_report(
        index,
        base_directory=base_directory,
    )


def save_default_evidence_quality_report(
    file_path: str,
    base_directory: str = ".",
    indent: int = 2,
) -> Path:
    report = generate_default_evidence_quality_report(
        base_directory=base_directory,
    )

    return save_evidence_quality_report(
        report,
        file_path,
        indent=indent,
    )