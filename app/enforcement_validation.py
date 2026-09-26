"""
Varynx Day 66 - Enforcement Request Validation and Safety Gate.

This module validates an EnforcementRequest before it is handed to an
external enforcement system.

IMPORTANT SECURITY BOUNDARY
----------------------------
This module performs validation only.

It does not execute ALLOW, BLOCK, MONITOR, or any other security action.
It does not modify authorization, policy, adaptive response, or agent
permissions.

Pipeline:

Security Decision
    ->
Runtime Security Coordinator
    ->
Enforcement Boundary Adapter
    ->
Day 66 Validation Gate
    ->
External Enforcement System
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from app.enforcement_boundary import (
    BOUNDARY_ESCALATED,
    DECISION_ALLOW,
    DECISION_BLOCK,
    DECISION_HUMAN_REVIEW,
    DECISION_MONITOR,
    DECISION_REDUCE_SCOPE,
    DECISION_STEP_UP,
    EnforcementRequest,
)


# ---------------------------------------------------------------------------
# Validation results
# ---------------------------------------------------------------------------

VALIDATION_PASSED = "VALIDATION_PASSED"
VALIDATION_FAILED = "VALIDATION_FAILED"

VALIDATION_READY = "VALIDATION_READY"
VALIDATION_REQUIRES_REVIEW = "VALIDATION_REQUIRES_REVIEW"

VALIDATION_OK = "OK"
VALIDATION_WARNING = "WARNING"
VALIDATION_ERROR = "ERROR"


# ---------------------------------------------------------------------------
# Supported decisions
# ---------------------------------------------------------------------------

VALID_DECISIONS = frozenset(
    {
        DECISION_ALLOW,
        DECISION_MONITOR,
        DECISION_STEP_UP,
        DECISION_REDUCE_SCOPE,
        DECISION_HUMAN_REVIEW,
        DECISION_BLOCK,
    }
)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")

    return value.strip()


def _validate_optional_score(
    value: Optional[float],
    field_name: str,
) -> Optional[float]:
    if value is None:
        return None

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be numeric or None")

    value = float(value)

    if not 0.0 <= value <= 100.0:
        raise ValueError(
            f"{field_name} must be between 0 and 100"
        )

    return value


def _validate_request(
    request: EnforcementRequest,
) -> EnforcementRequest:
    if not isinstance(request, EnforcementRequest):
        raise TypeError(
            "request must be an EnforcementRequest"
        )

    return request


# ---------------------------------------------------------------------------
# Validation issue
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ValidationIssue:
    """
    Immutable description of a validation finding.
    """

    code: str
    severity: str
    message: str


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EnforcementValidationResult:
    """
    Immutable validation result.

    The original enforcement request is preserved through the evidence
    structure. The request itself is never modified.
    """

    request_id: str
    agent_id: str
    decision: str

    validation_status: str
    validation_state: str

    safe_to_forward: bool

    issues: tuple[ValidationIssue, ...]
    evidence: dict[str, Any]


# ---------------------------------------------------------------------------
# Individual validation checks
# ---------------------------------------------------------------------------


def validate_request_identity(
    request: EnforcementRequest,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if not isinstance(request.request_id, str) or not request.request_id.strip():
        issues.append(
            ValidationIssue(
                code="MISSING_REQUEST_ID",
                severity=VALIDATION_ERROR,
                message="Enforcement request has no request identifier.",
            )
        )

    if not isinstance(request.agent_id, str) or not request.agent_id.strip():
        issues.append(
            ValidationIssue(
                code="MISSING_AGENT_ID",
                severity=VALIDATION_ERROR,
                message="Enforcement request has no agent identifier.",
            )
        )

    return issues


def validate_decision(
    request: EnforcementRequest,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if request.decision not in VALID_DECISIONS:
        issues.append(
            ValidationIssue(
                code="INVALID_DECISION",
                severity=VALIDATION_ERROR,
                message=(
                    "Enforcement request contains an unsupported decision."
                ),
            )
        )

    return issues


def validate_boundary_consistency(
    request: EnforcementRequest,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    expected_escalated = request.decision in {
        DECISION_HUMAN_REVIEW,
        DECISION_BLOCK,
    }

    if (
        expected_escalated
        and request.boundary_state != BOUNDARY_ESCALATED
    ):
        issues.append(
            ValidationIssue(
                code="BOUNDARY_STATE_MISMATCH",
                severity=VALIDATION_ERROR,
                message=(
                    "Escalated decision does not have an escalated "
                    "boundary state."
                ),
            )
        )

    if (
        not expected_escalated
        and request.boundary_state == BOUNDARY_ESCALATED
    ):
        issues.append(
            ValidationIssue(
                code="UNEXPECTED_ESCALATION_STATE",
                severity=VALIDATION_WARNING,
                message=(
                    "Decision is not normally escalated but the request "
                    "contains an escalated boundary state."
                ),
            )
        )

    return issues


def validate_request_mode(
    request: EnforcementRequest,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if request.request_mode != "REQUEST_ONLY":
        issues.append(
            ValidationIssue(
                code="INVALID_REQUEST_MODE",
                severity=VALIDATION_ERROR,
                message=(
                    "Request mode is not REQUEST_ONLY. "
                    "Day 66 requires explicit downstream execution."
                ),
            )
        )

    return issues


def validate_enforcement_boundary(
    request: EnforcementRequest,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if request.enforcement_required is not True:
        issues.append(
            ValidationIssue(
                code="ENFORCEMENT_FLAG_INVALID",
                severity=VALIDATION_ERROR,
                message=(
                    "Enforcement boundary flag must explicitly require "
                    "external enforcement."
                ),
            )
        )

    execution_flag = request.evidence.get(
        "execution_performed_here"
    )

    if execution_flag is not False:
        issues.append(
            ValidationIssue(
                code="LOCAL_EXECUTION_FLAG_INVALID",
                severity=VALIDATION_ERROR,
                message=(
                    "The enforcement request must explicitly indicate "
                    "that execution was not performed by Varynx."
                ),
            )
        )

    return issues


def validate_security_scores(
    request: EnforcementRequest,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    score_fields = (
        ("projected_score", request.projected_score),
        ("consequence_score", request.consequence_score),
        ("deviation_score", request.deviation_score),
    )

    for field_name, value in score_fields:
        try:
            _validate_optional_score(value, field_name)
        except (TypeError, ValueError) as exc:
            issues.append(
                ValidationIssue(
                    code=f"INVALID_{field_name.upper()}",
                    severity=VALIDATION_ERROR,
                    message=str(exc),
                )
            )

    return issues


def validate_evidence(
    request: EnforcementRequest,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if not isinstance(request.evidence, Mapping):
        issues.append(
            ValidationIssue(
                code="INVALID_EVIDENCE",
                severity=VALIDATION_ERROR,
                message="Evidence must be a mapping.",
            )
        )
        return issues

    required_evidence_fields = {
        "decision",
        "boundary_state",
        "execution_performed_here",
        "external_enforcement_required",
    }

    missing = required_evidence_fields.difference(
        request.evidence.keys()
    )

    if missing:
        issues.append(
            ValidationIssue(
                code="INCOMPLETE_EVIDENCE",
                severity=VALIDATION_ERROR,
                message=(
                    "Required boundary evidence is missing: "
                    + ", ".join(sorted(missing))
                ),
            )
        )

    if request.evidence.get("decision") != request.decision:
        issues.append(
            ValidationIssue(
                code="EVIDENCE_DECISION_MISMATCH",
                severity=VALIDATION_ERROR,
                message=(
                    "Evidence decision does not match the enforcement "
                    "request decision."
                ),
            )
        )

    if (
        request.evidence.get("boundary_state")
        != request.boundary_state
    ):
        issues.append(
            ValidationIssue(
                code="EVIDENCE_BOUNDARY_MISMATCH",
                severity=VALIDATION_ERROR,
                message=(
                    "Evidence boundary state does not match the request."
                ),
            )
        )

    if request.evidence.get(
        "execution_performed_here"
    ) is not False:
        issues.append(
            ValidationIssue(
                code="LOCAL_EXECUTION_FLAG_INVALID",
                severity=VALIDATION_ERROR,
                message=(
                    "Evidence indicates that execution was performed "
                    "inside Varynx."
                ),
            )
        )

    if request.evidence.get(
        "external_enforcement_required"
    ) is not True:
        issues.append(
            ValidationIssue(
                code="EVIDENCE_ENFORCEMENT_MISMATCH",
                severity=VALIDATION_ERROR,
                message=(
                    "Evidence does not explicitly require external "
                    "enforcement."
                ),
            )
        )

    return issues


# ---------------------------------------------------------------------------
# Source-evidence extraction
# ---------------------------------------------------------------------------


def _extract_source_evidence(
    request: EnforcementRequest,
) -> dict[str, Any]:
    """
    Extract the actual upstream source evidence.

    Day 65's EnforcementRequest already wraps upstream evidence inside:

        request.evidence["source_evidence"]

    Day 66 must preserve that original payload rather than wrapping the
    wrapper again.

    If source_evidence does not exist, the complete Day 65 evidence is
    preserved as a fallback.
    """

    request_evidence = request.evidence

    source_evidence = request_evidence.get(
        "source_evidence"
    )

    if isinstance(source_evidence, Mapping):
        return deepcopy(dict(source_evidence))

    return deepcopy(dict(request_evidence))


# ---------------------------------------------------------------------------
# Validation evidence
# ---------------------------------------------------------------------------


def build_validation_evidence(
    request: EnforcementRequest,
    issues: tuple[ValidationIssue, ...],
) -> dict[str, Any]:
    """
    Build structured validation evidence without changing the request.

    The original Day 65 source evidence is preserved at:

        result.evidence["source_evidence"]

    Boundary-level evidence is preserved separately at:

        result.evidence["boundary_evidence"]
    """

    source_evidence = _extract_source_evidence(request)

    return {
        "request_id": request.request_id,
        "agent_id": request.agent_id,
        "decision": request.decision,
        "issue_count": len(issues),
        "error_count": sum(
            issue.severity == VALIDATION_ERROR
            for issue in issues
        ),
        "warning_count": sum(
            issue.severity == VALIDATION_WARNING
            for issue in issues
        ),
        "safe_to_forward": not any(
            issue.severity == VALIDATION_ERROR
            for issue in issues
        ),
        "execution_performed_here": False,

        # Original upstream evidence, not nested twice.
        "source_evidence": source_evidence,

        # Complete Day 65 boundary evidence remains available separately.
        "boundary_evidence": deepcopy(dict(request.evidence)),
    }


# ---------------------------------------------------------------------------
# Main validation function
# ---------------------------------------------------------------------------


def validate_enforcement_request(
    request: EnforcementRequest,
) -> EnforcementValidationResult:
    """
    Validate an EnforcementRequest without executing it.
    """

    request = _validate_request(request)

    issues: list[ValidationIssue] = []

    issues.extend(
        validate_request_identity(request)
    )

    issues.extend(
        validate_decision(request)
    )

    issues.extend(
        validate_boundary_consistency(request)
    )

    issues.extend(
        validate_request_mode(request)
    )

    issues.extend(
        validate_enforcement_boundary(request)
    )

    issues.extend(
        validate_security_scores(request)
    )

    issues.extend(
        validate_evidence(request)
    )

    issues_tuple = tuple(issues)

    has_errors = any(
        issue.severity == VALIDATION_ERROR
        for issue in issues_tuple
    )

    has_warnings = any(
        issue.severity == VALIDATION_WARNING
        for issue in issues_tuple
    )

    if has_errors:
        validation_status = VALIDATION_FAILED
        validation_state = VALIDATION_REQUIRES_REVIEW
        safe_to_forward = False

    else:
        validation_status = VALIDATION_PASSED

        if has_warnings:
            validation_state = VALIDATION_REQUIRES_REVIEW
        else:
            validation_state = VALIDATION_READY

        safe_to_forward = True

    return EnforcementValidationResult(
        request_id=request.request_id,
        agent_id=request.agent_id,
        decision=request.decision,
        validation_status=validation_status,
        validation_state=validation_state,
        safe_to_forward=safe_to_forward,
        issues=issues_tuple,
        evidence=build_validation_evidence(
            request,
            issues_tuple,
        ),
    )


# ---------------------------------------------------------------------------
# Stateful validation gate
# ---------------------------------------------------------------------------


class EnforcementValidationGate:
    """
    Stateful wrapper around the deterministic validation function.

    The gate stores validation results for auditability and testing.

    It does not execute enforcement.
    """

    def __init__(self) -> None:
        self._history: dict[
            str,
            list[EnforcementValidationResult],
        ] = {}

    def validate(
        self,
        request: EnforcementRequest,
    ) -> EnforcementValidationResult:
        result = validate_enforcement_request(request)

        self._history.setdefault(
            result.agent_id,
            [],
        ).append(result)

        return result

    def latest(
        self,
        agent_id: str,
    ) -> Optional[EnforcementValidationResult]:
        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        results = self._history.get(agent_id)

        if not results:
            return None

        return results[-1]

    def history(
        self,
        agent_id: str,
    ) -> tuple[EnforcementValidationResult, ...]:
        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        return tuple(
            self._history.get(agent_id, ())
        )

    def snapshot_all(
        self,
    ) -> dict[
        str,
        tuple[EnforcementValidationResult, ...],
    ]:
        return {
            agent_id: tuple(results)
            for agent_id, results in self._history.items()
        }

    def reset(
        self,
        agent_id: Optional[str] = None,
    ) -> None:
        if agent_id is None:
            self._history.clear()
            return

        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        self._history.pop(
            agent_id,
            None,
        )


# ---------------------------------------------------------------------------
# Architectural invariant
# ---------------------------------------------------------------------------


def enforcement_is_executed_here() -> bool:
    """
    Day 66 is a validation boundary only.

    No enforcement action is executed here.
    """

    return False