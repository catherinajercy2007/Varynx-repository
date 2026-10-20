from pathlib import Path

from app.evaluation_framework_audit import (
    AuditStatus,
    audit_repository,
    render_audit_markdown,
)


ROOT = Path(__file__).resolve().parents[1]


def test_day46_audit_finds_existing_evaluation_components():
    audit = audit_repository(ROOT)

    components = {
        finding.component
        for finding in audit.findings
    }

    assert "experimental_dataset" in components
    assert "quantitative_evaluation" in components
    assert "baseline_comparison" in components
    assert "ablation" in components
    assert "threshold_sensitivity" in components
    assert "robustness" in components
    assert "statistical_evaluation" in components
    assert "performance" in components
    assert "dynamic_behavioral_trust" in components


def test_day46_audit_marks_core_reusable_frameworks_compatible():
    audit = audit_repository(ROOT)

    statuses = {
        finding.component: finding.status
        for finding in audit.findings
    }

    assert (
        statuses["quantitative_evaluation"]
        is AuditStatus.COMPATIBLE
    )

    assert (
        statuses["statistical_evaluation"]
        is AuditStatus.COMPATIBLE
    )

    assert (
        statuses["performance"]
        is AuditStatus.COMPATIBLE
    )

    assert (
        statuses["dynamic_behavioral_trust"]
        is AuditStatus.COMPATIBLE
    )


def test_day46_audit_identifies_required_extensions():
    audit = audit_repository(ROOT)

    statuses = {
        finding.component: finding.status
        for finding in audit.findings
    }

    assert (
        statuses["experimental_dataset"]
        is AuditStatus.EXTENSION_REQUIRED
    )

    assert (
        statuses["baseline_comparison"]
        is AuditStatus.EXTENSION_REQUIRED
    )

    assert (
        statuses["ablation"]
        is AuditStatus.EXTENSION_REQUIRED
    )

    assert (
        statuses["threshold_sensitivity"]
        is AuditStatus.EXTENSION_REQUIRED
    )

    assert (
        statuses["robustness"]
        is AuditStatus.EXTENSION_REQUIRED
    )


def test_day46_audit_does_not_report_missing_core_modules():
    audit = audit_repository(ROOT)

    assert all(
        finding.status is not AuditStatus.NOT_ESTABLISHED
        for finding in audit.findings
    )


def test_day46_audit_markdown_is_deterministic_and_informative():
    audit = audit_repository(ROOT)

    markdown = render_audit_markdown(audit)

    assert markdown.startswith(
        "# Day 46 — Evaluation Framework Audit"
    )

    assert "experimental_dataset" in markdown
    assert "dynamic_behavioral_trust" in markdown
    assert "Day 47 Dependency" in markdown