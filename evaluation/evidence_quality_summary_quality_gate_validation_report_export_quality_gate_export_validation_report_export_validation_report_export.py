import json
from pathlib import Path
from typing import Any, Dict

from evaluation.evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation_report_export_validation_report import (
    ExportedValidationReportExportValidationReport,
    exported_validation_report_export_validation_report_to_dict,
    generate_exported_validation_report_export_validation_report,
)


def validation_report_to_json_dict(
    report: ExportedValidationReportExportValidationReport,
) -> Dict[str, Any]:
    return (
        exported_validation_report_export_validation_report_to_dict(
            report
        )
    )


def validation_report_to_json(
    report: ExportedValidationReportExportValidationReport,
    indent: int = 2,
) -> str:
    return json.dumps(
        validation_report_to_json_dict(report),
        indent=indent,
        sort_keys=True,
    )


def save_exported_validation_report_export_validation_report(
    report: ExportedValidationReportExportValidationReport,
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


def load_exported_validation_report_export_validation_report(
    file_path: str,
) -> Dict[str, Any]:
    path = Path(file_path)

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def generate_and_export_validation_report(
    report: Dict[str, Any],
    file_path: str,
    indent: int = 2,
) -> Path:
    validation_report = (
        generate_exported_validation_report_export_validation_report(
            report
        )
    )

    return (
        save_exported_validation_report_export_validation_report(
            validation_report,
            file_path,
            indent=indent,
        )
    )


def export_validation_report_json(
    report: Dict[str, Any],
    indent: int = 2,
) -> str:
    validation_report = (
        generate_exported_validation_report_export_validation_report(
            report
        )
    )

    return validation_report_to_json(
        validation_report,
        indent=indent,
    )