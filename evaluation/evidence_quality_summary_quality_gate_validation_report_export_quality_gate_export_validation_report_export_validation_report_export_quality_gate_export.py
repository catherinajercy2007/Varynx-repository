import json
from pathlib import Path
from typing import Any, Dict

from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation_report_export_validation_report_export_quality_gate import (
    ExportedValidationReportExportQualityGateResult,
    evaluate_exported_validation_report_export_quality_gate,
    exported_validation_report_export_quality_gate_to_dict,
)


def quality_gate_to_json_dict(
    result: ExportedValidationReportExportQualityGateResult,
) -> Dict[str, Any]:
    return (
        exported_validation_report_export_quality_gate_to_dict(
            result
        )
    )


def quality_gate_to_json(
    result: ExportedValidationReportExportQualityGateResult,
    indent: int = 2,
) -> str:
    return json.dumps(
        quality_gate_to_json_dict(result),
        indent=indent,
        sort_keys=True,
    )


def save_exported_validation_report_export_quality_gate(
    result: ExportedValidationReportExportQualityGateResult,
    file_path: str,
    indent: int = 2,
) -> Path:
    path = Path(file_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        quality_gate_to_json(
            result,
            indent=indent,
        ),
        encoding="utf-8",
    )

    return path


def load_exported_validation_report_export_quality_gate(
    file_path: str,
) -> Dict[str, Any]:
    path = Path(file_path)

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def evaluate_and_export_validation_report_quality_gate(
    report: Dict[str, Any],
    file_path: str,
    indent: int = 2,
) -> Path:
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            report
        )
    )

    return (
        save_exported_validation_report_export_quality_gate(
            result,
            file_path,
            indent=indent,
        )
    )


def export_validation_report_quality_gate_json(
    report: Dict[str, Any],
    indent: int = 2,
) -> str:
    result = (
        evaluate_exported_validation_report_export_quality_gate(
            report
        )
    )

    return quality_gate_to_json(
        result,
        indent=indent,
    )