
"""Varynx Day 90: End-to-End Runtime Control and Evidence Validation.

Validates the consistency of existing security artifacts before they are
handed to a downstream runtime enforcement component.

This module is a validation and handoff layer only. It does not authorize
requests, calculate a new risk score, execute controls, or claim enforcement
success.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping


VERSION = "DAY90-V1"

STATUS_VALID = "VALIDATED_FOR_HANDOFF"
STATUS_REVIEW = "REVIEW_REQUIRED"
STATUS_INVALID = "INVALID_HANDOFF"

CHECK_PASS = "PASS"
CHECK_REVIEW = "REVIEW"
CHECK_FAIL = "FAIL"

REASON_MISSING_ARTIFACT = "MISSING_REQUIRED_ARTIFACT"
REASON_INVALID_ARTIFACT = "INVALID_ARTIFACT_SHAPE"
REASON_AGENT_MISMATCH = "AGENT_ID_MISMATCH"
REASON_CASE_MISMATCH = "CASE_ID_MISMATCH"
REASON_CORRELATION_MISMATCH = "CORRELATION_ID_MISMATCH"
REASON_EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
REASON_UNBOUND_TRAJECTORY = "TRAJECTORY_EVIDENCE_NOT_BOUND"
REASON_ALERT_EVIDENCE_MISMATCH = "ALERT_EVIDENCE_MISMATCH"
REASON_RESPONSE_MISSING = "RESPONSE_RECOMMENDATION_MISSING"
REASON_BOUNDARY_VIOLATION = "UNSUPPORTED_EXECUTION_CLAIM"
REASON_EMPTY_TRAJECTORY = "EMPTY_TRAJECTORY"
REASON_DUPLICATE_EVIDENCE = "DUPLICATE_EVIDENCE_REFERENCE"


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _mapping(
    value: Any,
    field: str,
    *,
    required: bool = False,
) -> Mapping[str, Any] | None:
    if value is None and not required:
        return None
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be a mapping")
    return value


def _digest(payload: Mapping[str, Any]) -> str:
    """Return a deterministic digest for the validation report payload."""
    try:
        serialized = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Validation report must contain JSON-serializable values"
        ) from exc

    return sha256(serialized.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ValidationCheck:
    """One deterministic integration-validation result."""

    code: str
    status: str
    message: str
    artifact: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeControlValidation:
    """Immutable report for downstream runtime-control handoff."""

    validation_id: str
    status: str
    agent_id: str
    case_id: str
    correlation_id: str | None
    checks: tuple[ValidationCheck, ...]
    reason_codes: tuple[str, ...]
    evidence_entry_ids: tuple[str, ...]
    recommended_action: str | None
    alert_severity: str | None
    trajectory_finding_count: int
    is_authorization_decision: bool = False
    executes_enforcement: bool = False
    enforcement_confirmed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": VERSION,
            "validation_id": self.validation_id,
            "status": self.status,
            "agent_id": self.agent_id,
            "case_id": self.case_id,
            "correlation_id": self.correlation_id,
            "checks": [check.to_dict() for check in self.checks],
            "reason_codes": list(self.reason_codes),
            "evidence_entry_ids": list(self.evidence_entry_ids),
            "recommended_action": self.recommended_action,
            "alert_severity": self.alert_severity,
            "trajectory_finding_count": self.trajectory_finding_count,
            "is_authorization_decision": False,
            "executes_enforcement": False,
            "enforcement_confirmed": False,
        }


def _read_identifier(
    value: Any,
    field: str,
) -> str | None:
    """Read a non-empty string identifier, or return None when absent."""
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string when supplied")
    return value.strip()


def _read_string_collection(
    value: Any,
    *,
    field: str,
) -> tuple[str, ...] | None:
    """Validate a list/tuple of non-empty string references."""
    if not isinstance(value, (list, tuple)):
        return None

    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            return None
        items.append(item.strip())

    return tuple(items)


def validate_runtime_control_handoff(
    *,
    agent_id: str,
    case_id: str,
    correlation_id: str | None,
    evidence_manifest: Mapping[str, Any] | None,
    trajectory_graph: Mapping[str, Any] | None,
    alert: Mapping[str, Any] | None,
    response_decision: Mapping[str, Any] | None,
) -> RuntimeControlValidation:
    """Validate the supplied artifacts before a runtime-control handoff.

    VALIDATED_FOR_HANDOFF means the supplied records passed the implemented
    consistency checks. It does not mean the action is authorized, safe,
    or successfully enforced.

    Missing artifacts and incomplete evidence require review. Identity
    mismatches, malformed structures, and unsupported claims of enforcement
    or authorization invalidate the handoff.
    """
    agent_id = _text(agent_id, "agent_id")
    case_id = _text(case_id, "case_id")
    correlation_id = _read_identifier(correlation_id, "correlation_id")

    manifest = _mapping(evidence_manifest, "evidence_manifest")
    graph = _mapping(trajectory_graph, "trajectory_graph")
    alert_data = _mapping(alert, "alert")
    response = _mapping(response_decision, "response_decision")

    checks: list[ValidationCheck] = []
    reasons: list[str] = []
    invalid = False
    review = False

    def add(
        code: str,
        status: str,
        message: str,
        artifact: str | None = None,
    ) -> None:
        nonlocal invalid, review

        checks.append(
            ValidationCheck(
                code=code,
                status=status,
                message=message,
                artifact=artifact,
            )
        )

        if status == CHECK_FAIL:
            invalid = True
        elif status == CHECK_REVIEW:
            review = True

        if status != CHECK_PASS:
            reasons.append(code)

    # 1. Artifact availability.
    required_artifacts = (
        ("evidence_manifest", manifest),
        ("trajectory_graph", graph),
        ("alert", alert_data),
        ("response_decision", response),
    )

    for name, artifact in required_artifacts:
        if artifact is None:
            add(
                REASON_MISSING_ARTIFACT,
                CHECK_REVIEW,
                f"{name} was not supplied.",
                name,
            )
        else:
            add(
                f"{name.upper()}_PRESENT",
                CHECK_PASS,
                f"{name} was supplied.",
                name,
            )

    # 2. Validate trajectory graph identity and shape.
    graph_entry_ids: tuple[str, ...] = ()
    finding_count = 0

    if graph is not None:
        if graph.get("agent_id") != agent_id:
            add(
                REASON_AGENT_MISMATCH,
                CHECK_FAIL,
                "Trajectory graph agent_id does not match.",
                "trajectory_graph",
            )
        else:
            add(
                "GRAPH_AGENT_MATCH",
                CHECK_PASS,
                "Trajectory graph agent_id matches.",
                "trajectory_graph",
            )

        if graph.get("case_id") != case_id:
            add(
                REASON_CASE_MISMATCH,
                CHECK_FAIL,
                "Trajectory graph case_id does not match.",
                "trajectory_graph",
            )
        else:
            add(
                "GRAPH_CASE_MATCH",
                CHECK_PASS,
                "Trajectory graph case_id matches.",
                "trajectory_graph",
            )

        raw_nodes = graph.get("nodes")
        raw_findings = graph.get("findings")

        if not isinstance(raw_nodes, (list, tuple)):
            add(
                REASON_INVALID_ARTIFACT,
                CHECK_FAIL,
                "Trajectory graph nodes must be a list or tuple.",
                "trajectory_graph",
            )
        elif not isinstance(raw_findings, (list, tuple)):
            add(
                REASON_INVALID_ARTIFACT,
                CHECK_FAIL,
                "Trajectory graph findings must be a list or tuple.",
                "trajectory_graph",
            )
        else:
            node_ids: list[str] = []
            malformed_node = False

            for node in raw_nodes:
                if not isinstance(node, Mapping):
                    malformed_node = True
                    continue

                entry_id = node.get("entry_id")
                if not isinstance(entry_id, str) or not entry_id.strip():
                    malformed_node = True
                    continue

                node_ids.append(entry_id.strip())

            if malformed_node:
                add(
                    REASON_INVALID_ARTIFACT,
                    CHECK_FAIL,
                    "Trajectory graph contains a malformed node.",
                    "trajectory_graph",
                )

            graph_entry_ids = tuple(sorted(set(node_ids)))
            finding_count = len(raw_findings)

            if not raw_nodes:
                add(
                    REASON_EMPTY_TRAJECTORY,
                    CHECK_REVIEW,
                    "Trajectory graph has no observed nodes.",
                    "trajectory_graph",
                )
            elif not malformed_node:
                add(
                    "GRAPH_NODES_PRESENT",
                    CHECK_PASS,
                    "Trajectory graph contains valid observed nodes.",
                    "trajectory_graph",
                )

            if graph.get("evidence_complete") is False:
                add(
                    REASON_EVIDENCE_INCOMPLETE,
                    CHECK_REVIEW,
                    "Trajectory graph marks its evidence incomplete.",
                    "trajectory_graph",
                )

            omitted_entries = graph.get("omitted_entries", 0)
            if (
                isinstance(omitted_entries, bool)
                or not isinstance(omitted_entries, int)
                or omitted_entries < 0
            ):
                add(
                    REASON_INVALID_ARTIFACT,
                    CHECK_FAIL,
                    "Trajectory graph omitted_entries must be a non-negative integer.",
                    "trajectory_graph",
                )
            elif omitted_entries > 0:
                add(
                    REASON_EVIDENCE_INCOMPLETE,
                    CHECK_REVIEW,
                    "Trajectory graph reports omitted entries.",
                    "trajectory_graph",
                )

    # 3. Validate Day 83 evidence manifest.
    manifest_artifact_ids: tuple[str, ...] = ()

    if manifest is not None:
        manifest_correlation = manifest.get("correlation_id")

        if (
            correlation_id is not None
            and manifest_correlation != correlation_id
        ):
            add(
                REASON_CORRELATION_MISMATCH,
                CHECK_FAIL,
                "Evidence manifest correlation_id does not match.",
                "evidence_manifest",
            )
        elif correlation_id is not None:
            add(
                "MANIFEST_CORRELATION_MATCH",
                CHECK_PASS,
                "Evidence manifest correlation_id matches.",
                "evidence_manifest",
            )

        manifest_status = manifest.get("status")
        if manifest_status == "BINDING_INVALID":
            add(
                REASON_EVIDENCE_INCOMPLETE,
                CHECK_REVIEW,
                "Evidence manifest reports BINDING_INVALID.",
                "evidence_manifest",
            )
        elif manifest_status == "BINDING_PARTIAL":
            add(
                REASON_EVIDENCE_INCOMPLETE,
                CHECK_REVIEW,
                "Evidence manifest reports BINDING_PARTIAL.",
                "evidence_manifest",
            )
        elif manifest_status is not None and manifest_status != "BINDING_COMPLETE":
            add(
                REASON_INVALID_ARTIFACT,
                CHECK_FAIL,
                "Evidence manifest contains an unknown status.",
                "evidence_manifest",
            )

        references = manifest.get("references")
        if not isinstance(references, (list, tuple)):
            add(
                REASON_INVALID_ARTIFACT,
                CHECK_FAIL,
                "Evidence manifest references must be a list or tuple.",
                "evidence_manifest",
            )
        else:
            artifact_ids: list[str] = []
            malformed_reference = False

            for reference in references:
                if not isinstance(reference, Mapping):
                    malformed_reference = True
                    continue

                artifact_id = reference.get("artifact_id")
                if not isinstance(artifact_id, str) or not artifact_id.strip():
                    malformed_reference = True
                    continue

                artifact_ids.append(artifact_id.strip())

            if malformed_reference:
                add(
                    REASON_INVALID_ARTIFACT,
                    CHECK_FAIL,
                    "Evidence manifest contains a malformed reference.",
                    "evidence_manifest",
                )

            manifest_artifact_ids = tuple(sorted(set(artifact_ids)))

            if len(manifest_artifact_ids) != len(artifact_ids):
                add(
                    REASON_DUPLICATE_EVIDENCE,
                    CHECK_REVIEW,
                    "Evidence manifest contains duplicate artifact IDs.",
                    "evidence_manifest",
                )
            elif not malformed_reference:
                add(
                    "MANIFEST_REFERENCES_VALID",
                    CHECK_PASS,
                    "Evidence manifest references have valid artifact IDs.",
                    "evidence_manifest",
                )

        missing_stages = manifest.get("missing_stages")
        if missing_stages is not None:
            if not isinstance(missing_stages, (list, tuple)):
                add(
                    REASON_INVALID_ARTIFACT,
                    CHECK_FAIL,
                    "Evidence manifest missing_stages must be a list or tuple.",
                    "evidence_manifest",
                )
            elif missing_stages:
                add(
                    REASON_EVIDENCE_INCOMPLETE,
                    CHECK_REVIEW,
                    "Evidence manifest reports missing required stages.",
                    "evidence_manifest",
                )

        # Artifact IDs and trajectory entry IDs may use different namespaces.
        # Only compare them as a conservative overlap signal, not as proof that
        # all evidence has been bound.
        if graph_entry_ids and manifest_artifact_ids:
            if set(graph_entry_ids).intersection(manifest_artifact_ids):
                add(
                    "TRAJECTORY_EVIDENCE_OVERLAP",
                    CHECK_PASS,
                    "At least one trajectory entry ID overlaps a manifest artifact ID.",
                    "evidence_manifest",
                )
            else:
                add(
                    REASON_UNBOUND_TRAJECTORY,
                    CHECK_REVIEW,
                    "No trajectory entry ID overlaps a manifest artifact ID; verify the mapping.",
                    "evidence_manifest",
                )
        elif graph_entry_ids and not manifest_artifact_ids:
            add(
                REASON_UNBOUND_TRAJECTORY,
                CHECK_REVIEW,
                "No manifest artifact IDs are available to compare with trajectory entries.",
                "evidence_manifest",
            )

    # 4. Validate Day 88 alert.
    alert_severity: str | None = None

    if alert_data is not None:
        if alert_data.get("agent_id") != agent_id:
            add(
                REASON_AGENT_MISMATCH,
                CHECK_FAIL,
                "Alert agent_id does not match.",
                "alert",
            )
        else:
            add(
                "ALERT_AGENT_MATCH",
                CHECK_PASS,
                "Alert agent_id matches.",
                "alert",
            )

        alert_correlation = alert_data.get("correlation_id")

        if (
            correlation_id is not None
            and alert_correlation is not None
            and alert_correlation != correlation_id
        ):
            add(
                REASON_CORRELATION_MISMATCH,
                CHECK_FAIL,
                "Alert correlation_id does not match.",
                "alert",
            )
        elif (
            correlation_id is not None
            and alert_correlation == correlation_id
        ):
            add(
                "ALERT_CORRELATION_MATCH",
                CHECK_PASS,
                "Alert correlation_id matches.",
                "alert",
            )

        severity = alert_data.get("severity")
        allowed_severities = {
            "INFO",
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        }

        if isinstance(severity, str) and severity in allowed_severities:
            alert_severity = severity
            add(
                "ALERT_SEVERITY_VALID",
                CHECK_PASS,
                "Alert severity is recognized.",
                "alert",
            )
        else:
            add(
                REASON_INVALID_ARTIFACT,
                CHECK_FAIL,
                "Alert severity is missing or invalid.",
                "alert",
            )

        if alert_data.get("evidence_complete") is False:
            add(
                REASON_EVIDENCE_INCOMPLETE,
                CHECK_REVIEW,
                "Alert marks its evidence incomplete.",
                "alert",
            )

        alert_refs = _read_string_collection(
            alert_data.get("evidence_references", []),
            field="alert.evidence_references",
        )

        if alert_refs is None:
            add(
                REASON_INVALID_ARTIFACT,
                CHECK_FAIL,
                "Alert evidence_references must contain non-empty strings.",
                "alert",
            )
        elif graph_entry_ids and alert_refs:
            if set(alert_refs).intersection(graph_entry_ids):
                add(
                    "ALERT_EVIDENCE_OVERLAP",
                    CHECK_PASS,
                    "Alert evidence overlaps trajectory entry IDs.",
                    "alert",
                )
            else:
                add(
                    REASON_ALERT_EVIDENCE_MISMATCH,
                    CHECK_REVIEW,
                    "Alert references do not overlap trajectory entry IDs; verify the identifier mapping.",
                    "alert",
                )

    # 5. Validate the existing Day 30 adaptive-response recommendation.
    recommended_action: str | None = None

    if response is not None:
        action = response.get("action", response.get("recommended_action"))

        # ResponseDecision.to_dict() serializes the Enum to its string value.
        if hasattr(action, "value"):
            action = action.value

        allowed_actions = {
            "ALLOW",
            "ALLOW_WITH_MONITORING",
            "STEP_UP_VERIFICATION",
            "REDUCE_SCOPE",
            "HUMAN_REVIEW",
            "BLOCK",
        }

        if isinstance(action, str) and action.strip().upper() in allowed_actions:
            recommended_action = action.strip().upper()
            add(
                "RESPONSE_RECOMMENDATION_PRESENT",
                CHECK_PASS,
                "A recognized adaptive-response recommendation is present.",
                "response_decision",
            )
        else:
            add(
                REASON_RESPONSE_MISSING,
                CHECK_REVIEW,
                "Response decision has no recognized action.",
                "response_decision",
            )

        if response.get("executes_enforcement") is True:
            add(
                REASON_BOUNDARY_VIOLATION,
                CHECK_FAIL,
                "Response artifact claims enforcement execution.",
                "response_decision",
            )

        if response.get("is_authorization_decision") is True:
            add(
                REASON_BOUNDARY_VIOLATION,
                CHECK_FAIL,
                "Response artifact claims authorization authority.",
                "response_decision",
            )

    # Invalid relationships take precedence over review-required findings.
    if invalid:
        status = STATUS_INVALID
    elif review:
        status = STATUS_REVIEW
    else:
        status = STATUS_VALID

    unique_reasons = tuple(sorted(set(reasons)))

    report_payload = {
        "version": VERSION,
        "agent_id": agent_id,
        "case_id": case_id,
        "correlation_id": correlation_id,
        "status": status,
        "checks": [check.to_dict() for check in checks],
        "reason_codes": list(unique_reasons),
        "evidence_entry_ids": list(graph_entry_ids),
        "recommended_action": recommended_action,
        "alert_severity": alert_severity,
        "trajectory_finding_count": finding_count,
    }

    validation_id = "day90-" + _digest(report_payload)[:20]

    return RuntimeControlValidation(
        validation_id=validation_id,
        status=status,
        agent_id=agent_id,
        case_id=case_id,
        correlation_id=correlation_id,
        checks=tuple(checks),
        reason_codes=unique_reasons,
        evidence_entry_ids=graph_entry_ids,
        recommended_action=recommended_action,
        alert_severity=alert_severity,
        trajectory_finding_count=finding_count,
    )
