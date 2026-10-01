from typing import Any, Dict


def summarize_evidence_quality_report(
    report: Dict[str, Any],
) -> Dict[str, Any]:
    quality_gate = report.get("quality_gate", {})
    evidence_index = report.get("evidence_index", {})

    artifacts = evidence_index.get("artifacts", [])

    verified_artifacts = sum(
        1
        for artifact in artifacts
        if artifact.get("verified") is True
    )

    return {
        "overall_status": report.get(
            "overall_status"
        ),
        "accepted": report.get(
            "accepted"
        ),
        "quality_gate_status": quality_gate.get(
            "status"
        ),
        "integrity_verified": quality_gate.get(
            "integrity_verified"
        ),
        "artifact_count": len(artifacts),
        "verified_artifact_count": verified_artifacts,
        "validation_error_count": len(
            quality_gate.get(
                "validation_errors",
                [],
            )
        ),
    }


def evidence_quality_report_summary_status(
    summary: Dict[str, Any],
) -> str:
    if summary.get("accepted") is True:
        return "ACCEPTED"

    return "REJECTED"


def evidence_quality_report_summary_to_dict(
    summary: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "overall_status": summary.get(
            "overall_status"
        ),
        "accepted": summary.get(
            "accepted"
        ),
        "quality_gate_status": summary.get(
            "quality_gate_status"
        ),
        "integrity_verified": summary.get(
            "integrity_verified"
        ),
        "artifact_count": summary.get(
            "artifact_count"
        ),
        "verified_artifact_count": summary.get(
            "verified_artifact_count"
        ),
        "validation_error_count": summary.get(
            "validation_error_count"
        ),
    }


def generate_evidence_quality_report_summary(
    report: Dict[str, Any],
) -> Dict[str, Any]:
    summary = summarize_evidence_quality_report(
        report
    )

    return {
        "summary": evidence_quality_report_summary_to_dict(
            summary
        ),
        "status": evidence_quality_report_summary_status(
            summary
        ),
    }