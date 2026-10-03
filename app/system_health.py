"""
Varynx Day 76 - System Health & Readiness Gate.

This module adds a deterministic, read-only readiness layer over the
validated Day75 Varynx system result.

The module does not:
- authorize actions
- execute enforcement
- modify security decisions
- infer malicious intent
- create a universal security score
- replace behavioral, trust, predictive, correlation, or investigation logic

It answers a narrower operational question:

    "Is the supplied Varynx system result structurally complete enough
     to be considered ready for downstream validation/operations?"
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping, Optional

from app.varynx_system import (
    INCIDENT_STAGE,
    TIMELINE_STAGE,
    CORRELATION_STAGE,
    BEHAVIORAL_STAGE,
    TRUST_STAGE,
    PREDICTIVE_STAGE,
    DECISION_STAGE,
    VarynxSystemResult,
)


# ---------------------------------------------------------------------------
# Readiness states
# ---------------------------------------------------------------------------

READINESS_READY = "READY"
READINESS_PARTIAL = "PARTIAL"
READINESS_NOT_READY = "NOT_READY"


# ---------------------------------------------------------------------------
# Health-check states
# ---------------------------------------------------------------------------

CHECK_PASS = "PASS"
CHECK_FAIL = "FAIL"
CHECK_NOT_APPLICABLE = "NOT_APPLICABLE"


# ---------------------------------------------------------------------------
# Required pipeline stages
# ---------------------------------------------------------------------------

REQUIRED_CORE_STAGES = (
    BEHAVIORAL_STAGE,
    TRUST_STAGE,
    PREDICTIVE_STAGE,
    DECISION_STAGE,
)

REQUIRED_EVIDENCE_STAGES = (
    TIMELINE_STAGE,
    CORRELATION_STAGE,
    INCIDENT_STAGE,
)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _validate_text(value: Any, field_name: str) -> str:
    """
    Validate a required non-empty string.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{field_name} must be a non-empty string"
        )

    return value.strip()


def _freeze_mapping(
    value: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Validate and copy a mapping.

    A shallow copy is sufficient here because the health report only
    stores supplied evidence as metadata.
    """
    if not isinstance(value, Mapping):
        raise TypeError(
            "evidence must be a mapping"
        )

    return dict(value)


def _deterministic_id(*parts: Any) -> str:
    """
    Build a deterministic report identifier.

    The same input values produce the same identifier.
    """
    payload = "|".join(
        repr(part)
        for part in parts
    )

    digest = sha256(
        payload.encode("utf-8")
    ).hexdigest()[:20]

    return f"health-{digest}"


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HealthCheck:
    """
    One deterministic readiness check.
    """

    name: str
    status: str
    detail: str

    def __post_init__(self) -> None:
        _validate_text(
            self.name,
            "name",
        )

        _validate_text(
            self.status,
            "status",
        )

        _validate_text(
            self.detail,
            "detail",
        )

        if self.status not in {
            CHECK_PASS,
            CHECK_FAIL,
            CHECK_NOT_APPLICABLE,
        }:
            raise ValueError(
                "unsupported health-check status"
            )


# ---------------------------------------------------------------------------
# System health report
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SystemHealthReport:
    """
    Immutable readiness report for one Varynx system result.
    """

    report_id: str
    result_id: str
    agent_id: str
    case_status: str
    readiness: str

    checks: tuple[HealthCheck, ...]

    passed_checks: int
    failed_checks: int

    missing_stages: tuple[str, ...]

    evidence: Mapping[str, Any]

    def __post_init__(self) -> None:
        _validate_text(
            self.report_id,
            "report_id",
        )

        _validate_text(
            self.result_id,
            "result_id",
        )

        _validate_text(
            self.agent_id,
            "agent_id",
        )

        _validate_text(
            self.case_status,
            "case_status",
        )

        if self.readiness not in {
            READINESS_READY,
            READINESS_PARTIAL,
            READINESS_NOT_READY,
        }:
            raise ValueError(
                "unsupported readiness value"
            )

        if not isinstance(
            self.checks,
            tuple,
        ):
            raise TypeError(
                "checks must be a tuple"
            )

        if (
            self.passed_checks < 0
            or self.failed_checks < 0
        ):
            raise ValueError(
                "check counts cannot be negative"
            )

        if (
            self.passed_checks
            + self.failed_checks
            > len(self.checks)
        ):
            raise ValueError(
                "check counts exceed check collection"
            )

        if not isinstance(
            self.missing_stages,
            tuple,
        ):
            raise TypeError(
                "missing_stages must be a tuple"
            )

        if not isinstance(
            self.evidence,
            Mapping,
        ):
            raise TypeError(
                "evidence must be a mapping"
            )

        object.__setattr__(
            self,
            "evidence",
            dict(self.evidence),
        )


# ---------------------------------------------------------------------------
# System health gate
# ---------------------------------------------------------------------------

class SystemHealthGate:
    """
    Deterministic, read-only readiness evaluator for Day75 results.

    READY:
        - validated events exist
        - all core stages are represented
        - timeline, correlation, and incident artifacts exist

    PARTIAL:
        - core pipeline is present
        - one or more evidence stages are missing

    NOT_READY:
        - a core stage is missing
        - no events are available
        - or a required evidence artifact is missing
    """

    def evaluate(
        self,
        result: VarynxSystemResult,
        *,
        evidence: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> SystemHealthReport:

        # ---------------------------------------------------------------
        # Result validation
        # ---------------------------------------------------------------

        if not isinstance(
            result,
            VarynxSystemResult,
        ):
            raise TypeError(
                "result must be a VarynxSystemResult"
            )

        supplied_evidence = (
            {}
            if evidence is None
            else _freeze_mapping(evidence)
        )

        # ---------------------------------------------------------------
        # Stage information
        # ---------------------------------------------------------------

        present = set(
            result.stages_present
        )

        missing = set(
            result.stages_missing
        )

        checks: list[HealthCheck] = []

        # ---------------------------------------------------------------
        # Check 1: result identity
        # ---------------------------------------------------------------

        checks.append(
            HealthCheck(
                name="result_identity",
                status=CHECK_PASS,
                detail=(
                    "A validated Day75 system result "
                    "is present."
                ),
            )
        )

        # ---------------------------------------------------------------
        # Check 2: event presence
        # ---------------------------------------------------------------

        event_count = len(
            result.events
        )

        checks.append(
            HealthCheck(
                name="event_presence",
                status=(
                    CHECK_PASS
                    if event_count > 0
                    else CHECK_FAIL
                ),
                detail=(
                    f"{event_count} validated "
                    "event(s) are available."
                    if event_count > 0
                    else
                    "No validated events are available."
                ),
            )
        )

        # ---------------------------------------------------------------
        # Check 3: core-stage coverage
        # ---------------------------------------------------------------

        core_missing = tuple(
            stage
            for stage in REQUIRED_CORE_STAGES
            if stage not in present
        )

        checks.append(
            HealthCheck(
                name="core_stage_coverage",
                status=(
                    CHECK_PASS
                    if not core_missing
                    else CHECK_FAIL
                ),
                detail=(
                    "All core behavioral/security "
                    "stages are represented."
                    if not core_missing
                    else
                    (
                        "Missing core stage(s): "
                        + ", ".join(core_missing)
                    )
                ),
            )
        )

        # ---------------------------------------------------------------
        # Check 4: evidence-stage coverage
        # ---------------------------------------------------------------

        evidence_missing = tuple(
            stage
            for stage in REQUIRED_EVIDENCE_STAGES
            if stage not in present
        )

        checks.append(
            HealthCheck(
                name="evidence_stage_coverage",
                status=(
                    CHECK_PASS
                    if not evidence_missing
                    else CHECK_NOT_APPLICABLE
                ),
                detail=(
                    "Timeline, correlation, and "
                    "incident stages are represented."
                    if not evidence_missing
                    else
                    (
                        "Evidence stage gap(s): "
                        + ", ".join(evidence_missing)
                    )
                ),
            )
        )

        # ---------------------------------------------------------------
        # Check 5: timeline artifact
        # ---------------------------------------------------------------

        checks.append(
            HealthCheck(
                name="timeline_artifact",
                status=(
                    CHECK_PASS
                    if result.timeline is not None
                    else CHECK_FAIL
                ),
                detail=(
                    "Timeline artifact is present."
                    if result.timeline is not None
                    else
                    "Timeline artifact is missing."
                ),
            )
        )

        # ---------------------------------------------------------------
        # Check 6: correlation artifact
        # ---------------------------------------------------------------

        checks.append(
            HealthCheck(
                name="correlation_artifact",
                status=(
                    CHECK_PASS
                    if result.correlation is not None
                    else CHECK_FAIL
                ),
                detail=(
                    "Correlation artifact is present."
                    if result.correlation is not None
                    else
                    "Correlation artifact is missing."
                ),
            )
        )

        # ---------------------------------------------------------------
        # Check 7: incident artifact
        # ---------------------------------------------------------------

        checks.append(
            HealthCheck(
                name="incident_artifact",
                status=(
                    CHECK_PASS
                    if result.incident is not None
                    else CHECK_FAIL
                ),
                detail=(
                    "Incident reconstruction artifact "
                    "is present."
                    if result.incident is not None
                    else
                    "Incident reconstruction artifact "
                    "is missing."
                ),
            )
        )

        # ---------------------------------------------------------------
        # Readiness classification
        # ---------------------------------------------------------------

        failed = tuple(
            check
            for check in checks
            if check.status == CHECK_FAIL
        )

        passed = tuple(
            check
            for check in checks
            if check.status == CHECK_PASS
        )

        if failed:
            readiness = READINESS_NOT_READY

        elif evidence_missing:
            readiness = READINESS_PARTIAL

        else:
            readiness = READINESS_READY

        # ---------------------------------------------------------------
        # Deterministic report identifier
        # ---------------------------------------------------------------

        report_id = _deterministic_id(
            result.result_id,
            result.agent_id,
            result.status,
            tuple(result.stages_present),
            tuple(result.stages_missing),
            event_count,
        )

        # ---------------------------------------------------------------
        # Readiness evidence
        # ---------------------------------------------------------------

        report_evidence = {
            "event_count": event_count,
            "core_stage_count": len(
                REQUIRED_CORE_STAGES
            ),
            "core_stage_missing_count": len(
                core_missing
            ),
            "evidence_stage_count": len(
                REQUIRED_EVIDENCE_STAGES
            ),
            "evidence_stage_missing_count": len(
                evidence_missing
            ),
            "read_only": True,
            "decision_modified": False,
            "enforcement_executed": False,
            "malicious_intent_inferred": False,
        }

        report_evidence.update(
            supplied_evidence
        )

        # ---------------------------------------------------------------
        # Final immutable report
        # ---------------------------------------------------------------

        return SystemHealthReport(
            report_id=report_id,
            result_id=result.result_id,
            agent_id=result.agent_id,
            case_status=result.status,
            readiness=readiness,
            checks=tuple(checks),
            passed_checks=len(passed),
            failed_checks=len(failed),
            missing_stages=tuple(
                sorted(
                    set(missing)
                    | set(core_missing)
                    | set(evidence_missing)
                )
            ),
            evidence=report_evidence,
        )


# ---------------------------------------------------------------------------
# Architectural boundary helpers
# ---------------------------------------------------------------------------

def system_health_is_read_only() -> bool:
    """
    Declare the module's architectural boundary.
    """
    return True


def decision_is_modified_here() -> bool:
    """
    Day76 never changes an existing security decision.
    """
    return False


def enforcement_is_executed_here() -> bool:
    """
    Day76 never executes enforcement.
    """
    return False


def malicious_intent_is_inferred_here() -> bool:
    """
    Day76 never infers attacker intent.
    """
    return False