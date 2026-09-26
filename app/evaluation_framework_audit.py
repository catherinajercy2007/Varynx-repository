"""
Varynx Day 46
Evaluation Framework Audit

Purpose
-------
Document and machine-check the compatibility between the established
Days 23-45 research/evaluation framework and the Phase III Dynamic
Behavioral Trust component.

This module is intentionally an audit layer. It does not execute
experiments, alter detector behavior, or replace the existing
research modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, Mapping


class AuditStatus(str, Enum):
    """Compatibility status for an evaluation capability."""

    COMPATIBLE = "compatible"
    EXTENSION_REQUIRED = "extension_required"
    NOT_ESTABLISHED = "not_established"


@dataclass(frozen=True)
class AuditFinding:
    """One auditable evaluation-framework finding."""

    component: str
    status: AuditStatus
    evidence: str
    required_extension: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "component": self.component,
            "status": self.status.value,
            "evidence": self.evidence,
            "required_extension": self.required_extension,
        }


@dataclass(frozen=True)
class EvaluationFrameworkAudit:
    """Structured Day 46 audit result."""

    findings: tuple[AuditFinding, ...]
    principles: tuple[str, ...] = field(default_factory=tuple)

    @property
    def compatible(self) -> tuple[AuditFinding, ...]:
        return tuple(
            finding
            for finding in self.findings
            if finding.status is AuditStatus.COMPATIBLE
        )

    @property
    def extensions_required(self) -> tuple[AuditFinding, ...]:
        return tuple(
            finding
            for finding in self.findings
            if finding.status is AuditStatus.EXTENSION_REQUIRED
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "findings": [finding.to_dict() for finding in self.findings],
            "compatible_components": [
                finding.component for finding in self.compatible
            ],
            "extension_components": [
                finding.component for finding in self.extensions_required
            ],
            "principles": list(self.principles),
        }


def _has_any(path: Path, names: Iterable[str]) -> bool:
    return any((path / name).exists() for name in names)


def audit_repository(root: str | Path) -> EvaluationFrameworkAudit:
    """Audit the known research/evaluation interfaces in a Varynx tree.

    The audit is deliberately based on repository artifacts rather than
    importing application modules. This keeps the audit independent from
    runtime services and avoids initializing the project's SQLite database.
    """

    root_path = Path(root)
    app = root_path / "app"
    tests = root_path / "tests"

    findings: list[AuditFinding] = []

    dataset_present = (app / "experimental_dataset.py").exists()

    findings.append(
        AuditFinding(
            "experimental_dataset",
            (
                AuditStatus.EXTENSION_REQUIRED
                if dataset_present
                else AuditStatus.NOT_ESTABLISHED
            ),
            "Existing experimental_dataset.py defines reproducible events "
            "but no dynamic trust-state fields.",
            "Add a trust-aware evaluation adapter or optional trust snapshot "
            "fields without breaking the existing dataset contract.",
        )
    )

    evaluation_present = (app / "evaluation.py").exists()

    findings.append(
        AuditFinding(
            "quantitative_evaluation",
            (
                AuditStatus.COMPATIBLE
                if evaluation_present
                else AuditStatus.NOT_ESTABLISHED
            ),
            "Existing evaluation.py provides generic binary metrics and "
            "detector evaluation.",
            "Preserve the metric definitions; feed trust-aware predictions "
            "through the existing evaluator.",
        )
    )

    comparison_present = (app / "comparison.py").exists()

    findings.append(
        AuditFinding(
            "baseline_comparison",
            (
                AuditStatus.EXTENSION_REQUIRED
                if comparison_present
                else AuditStatus.NOT_ESTABLISHED
            ),
            "Existing comparison.py supports risk/authorization detector "
            "comparisons.",
            "Add a Dynamic Behavioral Trust condition as an explicit "
            "controlled baseline/configuration.",
        )
    )

    ablation_present = (app / "ablation.py").exists()

    findings.append(
        AuditFinding(
            "ablation",
            (
                AuditStatus.EXTENSION_REQUIRED
                if ablation_present
                else AuditStatus.NOT_ESTABLISHED
            ),
            "Existing ablation.py defines controlled Varynx component "
            "configurations.",
            "Add a trust-disabled versus trust-enabled condition while "
            "keeping the same dataset, seeds, and metric definitions.",
        )
    )

    threshold_present = (app / "threshold_sensitivity.py").exists()

    findings.append(
        AuditFinding(
            "threshold_sensitivity",
            (
                AuditStatus.EXTENSION_REQUIRED
                if threshold_present
                else AuditStatus.NOT_ESTABLISHED
            ),
            "Existing threshold sensitivity varies adaptive-response "
            "thresholds.",
            "Add trust-boundary sensitivity only after the trust evaluation "
            "contract is established; do not change existing defaults.",
        )
    )

    robustness_present = (app / "robustness_evaluation.py").exists()

    findings.append(
        AuditFinding(
            "robustness",
            (
                AuditStatus.EXTENSION_REQUIRED
                if robustness_present
                else AuditStatus.NOT_ESTABLISHED
            ),
            "Existing robustness evaluation supports seed, volume, "
            "distribution, attack-ratio, and noise conditions.",
            "Extend the condition runner to include trust-state "
            "perturbation/drift conditions without replacing existing "
            "robustness dimensions.",
        )
    )

    statistics_present = (app / "statistical_evaluation.py").exists()

    findings.append(
        AuditFinding(
            "statistical_evaluation",
            (
                AuditStatus.COMPATIBLE
                if statistics_present
                else AuditStatus.NOT_ESTABLISHED
            ),
            "Existing statistical evaluation operates on paired metric "
            "results and does not require a trust-specific statistic.",
            "Reuse the existing paired statistical procedures for "
            "trust-enabled versus control conditions once paired outputs "
            "exist.",
        )
    )

    performance_present = (app / "performance_evaluation.py").exists()

    findings.append(
        AuditFinding(
            "performance",
            (
                AuditStatus.COMPATIBLE
                if performance_present
                else AuditStatus.NOT_ESTABLISHED
            ),
            "Existing performance evaluation benchmarks arbitrary "
            "operations through a callable interface.",
            "Benchmark trust updates through the existing callable "
            "benchmark interface; no parallel performance framework is "
            "required.",
        )
    )

    trust_present = (app / "behavioral_trust.py").exists()

    findings.append(
        AuditFinding(
            "dynamic_behavioral_trust",
            (
                AuditStatus.COMPATIBLE
                if trust_present
                else AuditStatus.NOT_ESTABLISHED
            ),
            "behavioral_trust.py provides bounded deterministic trust "
            "scores and immutable snapshots.",
            "Expose snapshots through the evaluation adapter; do not "
            "duplicate trust calculation inside the research layer.",
        )
    )

    tests_present = tests.exists() and _has_any(
        tests,
        {
            "test_evaluation.py",
            "test_experimental_dataset.py",
            "test_ablation.py",
            "test_threshold_sensitivity.py",
            "test_robustness_evaluation.py",
            "test_statistical_evaluation.py",
            "test_performance_evaluation.py",
        },
    )

    findings.append(
        AuditFinding(
            "evaluation_regression_tests",
            (
                AuditStatus.COMPATIBLE
                if tests_present
                else AuditStatus.NOT_ESTABLISHED
            ),
            "Existing focused tests cover the principal Days 23-45 "
            "evaluation modules.",
            "Add trust-specific tests alongside the existing suites "
            "rather than replacing them.",
        )
    )

    principles = (
        "Reuse existing evaluation infrastructure before adding new infrastructure.",
        "Keep Dynamic Behavioral Trust separate from risk and authorization semantics.",
        "Use identical datasets, seeds, labels, and metric definitions for controlled comparisons.",
        "Do not treat an implementation label as experimental evidence of integration.",
        "Preserve existing defaults and backwards compatibility.",
        "Do not claim improvement until controlled experiments provide evidence.",
    )

    return EvaluationFrameworkAudit(
        findings=tuple(findings),
        principles=principles,
    )


def render_audit_markdown(
    audit: EvaluationFrameworkAudit,
) -> str:
    """Render an audit result as deterministic Markdown."""

    lines = [
        "# Day 46 — Evaluation Framework Audit",
        "",
        "## Scope",
        "",
        (
            "Audit the established research/evaluation infrastructure "
            "for compatibility with Dynamic Behavioral Trust without "
            "replacing Days 23–45 capabilities."
        ),
        "",
        "## Findings",
        "",
        "| Component | Status | Evidence | Required extension |",
        "|---|---|---|---|",
    ]

    for finding in audit.findings:
        evidence = finding.evidence.replace("|", "\\|")
        extension = finding.required_extension.replace("|", "\\|")

        lines.append(
            f"| `{finding.component}` | "
            f"`{finding.status.value}` | "
            f"{evidence} | {extension} |"
        )

    lines.extend(
        [
            "",
            "## Research Principles",
            "",
        ]
    )

    lines.extend(
        f"- {principle}"
        for principle in audit.principles
    )

    lines.extend(
        [
            "",
            "## Day 47 Dependency",
            "",
            (
                "Implement a trust-aware evaluation adapter that consumes "
                "the actual DynamicBehavioralTrust snapshots and exposes "
                "them to the existing experiment/evaluation interfaces "
                "without duplicating trust computation."
            ),
            "",
        ]
    )

    return "\n".join(lines)


__all__ = [
    "AuditFinding",
    "AuditStatus",
    "EvaluationFrameworkAudit",
    "audit_repository",
    "render_audit_markdown",
]