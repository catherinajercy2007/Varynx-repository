import json
from pathlib import Path
from typing import Any, Dict

from evaluation.evidence_quality_summary_quality_gate_validation_report import (
    EvidenceQualitySummaryQualityGateValidationReport,
    evidence_quality_summary_quality_gate_validation_report_to_dict,
    generate_evidence_quality_summary_quality_gate_validation_report,
)


def validation_report_to_json_dict(
    report: EvidenceQualitySummaryQualityGateValidationReport,
) -> Dict[str, Any]:
    return (
        evidence_quality_summary_quality_gate_validation_report_to_dict(
            report
        )
    )


def validation_report_to_json(
    report: EvidenceQualitySummaryQualityGateValidationReport,
    indent: int = 2,
) -> str:
    return json.dumps(
        validation_report_to_json_dict(report),
        indent=indent,
        sort_keys=True,
    )


def save_quality_gate_validation_report(
    report: EvidenceQualitySummaryQualityGateValidationReport,
    file_path: str,
    indent: int = 2,
) -> Path:
    path = Path(file_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        validation_report_to_json(
            report,
            indent=indent,
        ),
        encoding="utf-8",
    )

    return path


def load_quality_gate_validation_report(
    file_path: str,
) -> Dict[str, Any]:
    path = Path(file_path)

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def generate_and_export_quality_gate_validation_report(
    quality_gate: Dict[str, Any],
    file_path: str,
    indent: int = 2,
) -> Path:
    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            quality_gate
        )
    )

    return save_quality_gate_validation_report(
        report,
        file_path,
        indent=indent,
    )


def export_quality_gate_validation_report_json(
    quality_gate: Dict[str, Any],
    indent: int = 2,
) -> str:
    report = (
        generate_evidence_quality_summary_quality_gate_validation_report(
            quality_gate
        )
    )

    return validation_report_to_json(
        report,
        indent=indent,
    )