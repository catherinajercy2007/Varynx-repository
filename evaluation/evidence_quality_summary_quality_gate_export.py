import json
from pathlib import Path
from typing import Any, Dict

from evaluation.evidence_quality_report_summary_quality_gate import (
    EvidenceQualitySummaryQualityGateResult,
    evidence_quality_summary_quality_gate_to_dict,
    evaluate_evidence_quality_summary_quality_gate,
)


def quality_gate_to_json_dict(
    result: EvidenceQualitySummaryQualityGateResult,
) -> Dict[str, Any]:
    return evidence_quality_summary_quality_gate_to_dict(
        result
    )


def quality_gate_to_json(
    result: EvidenceQualitySummaryQualityGateResult,
    indent: int = 2,
) -> str:
    return json.dumps(
        quality_gate_to_json_dict(result),
        indent=indent,
        sort_keys=True,
    )


def save_evidence_quality_summary_quality_gate(
    result: EvidenceQualitySummaryQualityGateResult,
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


def load_evidence_quality_summary_quality_gate(
    file_path: str,
) -> Dict[str, Any]:
    path = Path(file_path)

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def evaluate_and_export_evidence_quality_summary_quality_gate(
    summary: Dict[str, Any],
    file_path: str,
    indent: int = 2,
) -> Path:
    result = (
        evaluate_evidence_quality_summary_quality_gate(
            summary
        )
    )

    return save_evidence_quality_summary_quality_gate(
        result,
        file_path,
        indent=indent,
    )


def export_quality_gate_json(
    summary: Dict[str, Any],
    indent: int = 2,
) -> str:
    result = (
        evaluate_evidence_quality_summary_quality_gate(
            summary
        )
    )

    return quality_gate_to_json(
        result,
        indent=indent,
    )