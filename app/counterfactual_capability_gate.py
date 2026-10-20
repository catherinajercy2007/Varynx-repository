
"""Varynx Day 86: Counterfactual Capability Gate.

Consumes existing BCSE consequence evidence to assess a proposed
capability or scope change. This module produces recommendations only.

It does not execute hypothetical actions, grant capabilities, modify
leases, authorize requests, or enforce runtime controls.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any, Mapping


VERSION = "DAY86-V1"

# Gate outcomes are recommendations, not runtime authorization decisions.
OUTCOME_ELIGIBLE = "ELIGIBLE_FOR_REVIEW"
OUTCOME_HUMAN_REVIEW = "REQUIRE_HUMAN_REVIEW"
OUTCOME_RESTRICT = "RESTRICT"
OUTCOME_REJECT = "REJECT"

REASON_WITHIN_CONFIGURED_SCOPE = "WITHIN_CONFIGURED_SCOPE"
REASON_SCOPE_EXPANSION = "CAPABILITY_SCOPE_EXPANSION"
REASON_HIGH_CONSEQUENCE = "HIGH_COUNTERFACTUAL_CONSEQUENCE"
REASON_CRITICAL_CONSEQUENCE = "CRITICAL_COUNTERFACTUAL_CONSEQUENCE"
REASON_LOW_CONFIDENCE = "LOW_BCSE_CONFIDENCE"
REASON_INSUFFICIENT_EVIDENCE = "INSUFFICIENT_BCSE_EVIDENCE"
REASON_RESTRICTED_RESOURCE = "RESOURCE_EXPLICITLY_RESTRICTED"
REASON_INVALID_BCSE_OUTPUT = "INVALID_BCSE_OUTPUT"
REASON_AUTHORITY_RESTRICTED = "AUTHORITY_ALREADY_RESTRICTED"


CONFIDENCE_LEVELS = {"LOW", "MODERATE", "HIGH"}
AUTHORITY_STATES = {"NORMAL", "REDUCED", "RESTRICTED"}


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _score(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{field} must be a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a finite number") from exc
    if not isfinite(result) or not 0.0 <= result <= 100.0:
        raise ValueError(f"{field} must be between 0 and 100")
    return result


def _scope_match(resource: str, scope: str) -> bool:
    """Exact or slash-delimited subtree match; no wildcard matching."""
    return resource == scope or resource.startswith(
        scope.rstrip("/") + "/"
    )


def _matches_any(resource: str, scopes: tuple[str, ...]) -> bool:
    return any(_scope_match(resource, scope) for scope in scopes)


@dataclass(frozen=True)
class CounterfactualGatePolicy:
    """Explicit thresholds for assessing proposed capability changes."""

    policy_id: str
    allowed_scopes: tuple[str, ...]
    restricted_scopes: tuple[str, ...] = ()
    maximum_review_consequence: float = 59.99
    critical_consequence_threshold: float = 80.0
    minimum_evidence_items: int = 1
    require_high_confidence_for_scope_expansion: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "policy_id", _required_text(self.policy_id, "policy_id")
        )

        if isinstance(self.allowed_scopes, (str, bytes)):
            raise TypeError("allowed_scopes must be a tuple of strings")
        if isinstance(self.restricted_scopes, (str, bytes)):
            raise TypeError("restricted_scopes must be a tuple of strings")

        allowed = tuple(
            _required_text(item, "allowed scope")
            for item in self.allowed_scopes
        )
        restricted = tuple(
            _required_text(item, "restricted scope")
            for item in self.restricted_scopes
        )

        if not allowed:
            raise ValueError("allowed_scopes must not be empty")
        if len(set(allowed)) != len(allowed):
            raise ValueError("allowed_scopes must not contain duplicates")
        if len(set(restricted)) != len(restricted):
            raise ValueError("restricted_scopes must not contain duplicates")

        object.__setattr__(self, "allowed_scopes", allowed)
        object.__setattr__(self, "restricted_scopes", restricted)

        review_threshold = _score(
            self.maximum_review_consequence,
            "maximum_review_consequence",
        )
        critical_threshold = _score(
            self.critical_consequence_threshold,
            "critical_consequence_threshold",
        )

        if review_threshold >= critical_threshold:
            raise ValueError(
                "maximum_review_consequence must be below "
                "critical_consequence_threshold"
            )

        if (
            isinstance(self.minimum_evidence_items, bool)
            or not isinstance(self.minimum_evidence_items, int)
            or self.minimum_evidence_items < 0
        ):
            raise ValueError("minimum_evidence_items must be >= 0")

        if not isinstance(
            self.require_high_confidence_for_scope_expansion, bool
        ):
            raise TypeError(
                "require_high_confidence_for_scope_expansion must be bool"
            )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["version"] = VERSION
        return result


@dataclass(frozen=True)
class CounterfactualGateAssessment:
    """Immutable recommendation based on supplied BCSE evidence."""

    agent_id: str
    scenario_id: str
    policy_id: str
    capability: str
    requested_resource: str
    authority_state: str
    consequence_score: float
    consequence_level: str
    confidence: str
    evidence_count: int
    scope_expansion: bool
    outcome: str
    reason_codes: tuple[str, ...]
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["version"] = VERSION
        result["reason_codes"] = list(self.reason_codes)
        result["is_authorization_decision"] = False
        result["executes_enforcement"] = False
        result["modifies_capability_lease"] = False
        return result


def assess_counterfactual_capability(
    *,
    agent_id: str,
    scenario_id: str,
    capability: str,
    requested_resource: str,
    authority_state: str,
    policy: CounterfactualGatePolicy,
    bcse_result: Any,
    scope_expansion: bool = False,
) -> CounterfactualGateAssessment:
    """Assess a proposed capability change using an existing BCSE result.

    Accepted BCSE inputs may be either:
      - a Day 52 ConsequenceEstimate; or
      - a Day 55 BCSEIntegrationResult, whose `consequence` field is
        the Day 52 estimate.

    No consequence score is recomputed here. Missing, malformed, or
    insufficient evidence results in a conservative recommendation.
    """
    agent_id = _required_text(agent_id, "agent_id")
    scenario_id = _required_text(scenario_id, "scenario_id")
    capability = _required_text(capability, "capability")
    requested_resource = _required_text(
        requested_resource, "requested_resource"
    )
    authority_state = _required_text(
        authority_state, "authority_state"
    ).upper()

    if authority_state not in AUTHORITY_STATES:
        raise ValueError(
            f"authority_state must be one of {sorted(AUTHORITY_STATES)}"
        )
    if not isinstance(policy, CounterfactualGatePolicy):
        raise TypeError("policy must be a CounterfactualGatePolicy")
    if not isinstance(scope_expansion, bool):
        raise TypeError("scope_expansion must be bool")

    # Support both the direct Day 52 result and the existing Day 55
    # integration result without importing or duplicating their logic.
    estimate = getattr(bcse_result, "consequence", bcse_result)

    required = ("scenario_id", "consequence_score", "confidence", "evidence")
    if any(not hasattr(estimate, field) for field in required):
        raise TypeError(
            "bcse_result must be a Day 52 consequence estimate or "
            "Day 55 integration result"
        )

    supplied_scenario_id = _required_text(
        estimate.scenario_id, "BCSE scenario_id"
    )
    if supplied_scenario_id != scenario_id:
        raise ValueError("scenario_id does not match the BCSE result")

    consequence_score = _score(
        estimate.consequence_score, "BCSE consequence_score"
    )
    confidence = _required_text(
        estimate.confidence, "BCSE confidence"
    ).upper()

    if confidence not in CONFIDENCE_LEVELS:
        raise ValueError("BCSE confidence must be LOW, MODERATE, or HIGH")

    consequence_level = _required_text(
        getattr(estimate, "consequence_level", "UNKNOWN"),
        "BCSE consequence_level",
    ).upper()

    evidence = estimate.evidence
    if isinstance(evidence, (str, bytes)) or not isinstance(
        evidence, (list, tuple)
    ):
        raise TypeError("BCSE evidence must be a list or tuple of strings")
    if any(not isinstance(item, str) or not item.strip() for item in evidence):
        raise ValueError("BCSE evidence entries must be non-empty strings")

    evidence_count = len(evidence)
    reasons: list[str] = []

    def make(
        outcome: str,
        recommendation: str,
        *reason_codes: str,
    ) -> CounterfactualGateAssessment:
        return CounterfactualGateAssessment(
            agent_id=agent_id,
            scenario_id=scenario_id,
            policy_id=policy.policy_id,
            capability=capability,
            requested_resource=requested_resource,
            authority_state=authority_state,
            consequence_score=consequence_score,
            consequence_level=consequence_level,
            confidence=confidence,
            evidence_count=evidence_count,
            scope_expansion=scope_expansion,
            outcome=outcome,
            reason_codes=tuple(reason_codes),
            recommendation=recommendation,
        )

    # A pre-existing restricted authority state must not be escalated by
    # a positive counterfactual estimate.
    if authority_state == "RESTRICTED":
        return make(
            OUTCOME_REJECT,
            "Do not advance the proposed capability change; route to "
            "the existing security review and enforcement workflow.",
            REASON_AUTHORITY_RESTRICTED,
        )

    # Explicit restrictions override every allowed-scope match.
    if _matches_any(requested_resource, policy.restricted_scopes):
        return make(
            OUTCOME_REJECT,
            "Reject this proposal under the configured restricted-scope "
            "rule; the runtime enforcement layer remains authoritative.",
            REASON_RESTRICTED_RESOURCE,
        )

    in_scope = _matches_any(
        requested_resource, policy.allowed_scopes
    )
    if not in_scope:
        return make(
            OUTCOME_RESTRICT,
            "Keep the proposal outside the current configured scope and "
            "request an explicit policy review before any change.",
            REASON_SCOPE_EXPANSION,
        )

    if scope_expansion:
        reasons.append(REASON_SCOPE_EXPANSION)
    else:
        reasons.append(REASON_WITHIN_CONFIGURED_SCOPE)

    if evidence_count < policy.minimum_evidence_items:
        return make(
            OUTCOME_HUMAN_REVIEW,
            "Do not treat the BCSE estimate as sufficient evidence. "
            "Collect qualifying evidence or require human review.",
            *reasons,
            REASON_INSUFFICIENT_EVIDENCE,
        )

    if confidence == "LOW":
        return make(
            OUTCOME_HUMAN_REVIEW,
            "Require human review because the BCSE result has low "
            "confidence; do not infer safety from the score alone.",
            *reasons,
            REASON_LOW_CONFIDENCE,
        )

    if consequence_score >= policy.critical_consequence_threshold:
        return make(
            OUTCOME_REJECT,
            "Reject this proposed change for the current review cycle "
            "because the estimated potential consequence is critical.",
            *reasons,
            REASON_CRITICAL_CONSEQUENCE,
        )

    if consequence_score > policy.maximum_review_consequence:
        return make(
            OUTCOME_HUMAN_REVIEW,
            "Require human review because the potential consequence "
            "exceeds the configured review threshold.",
            *reasons,
            REASON_HIGH_CONSEQUENCE,
        )

    if (
        scope_expansion
        and policy.require_high_confidence_for_scope_expansion
        and confidence != "HIGH"
    ):
        return make(
            OUTCOME_HUMAN_REVIEW,
            "Require high-confidence BCSE evidence and human review "
            "before considering a scope expansion.",
            *reasons,
            REASON_LOW_CONFIDENCE,
        )

    if authority_state == "REDUCED":
        return make(
            OUTCOME_HUMAN_REVIEW,
            "Keep the current reduced-authority state and request review; "
            "this assessment cannot restore authority.",
            *reasons,
        )

    return make(
        OUTCOME_ELIGIBLE,
        "The proposal passed this configured counterfactual gate and is "
        "eligible for the existing policy and authorization review. "
        "No capability has been granted.",
        *reasons,
    )


__all__ = [
    "VERSION",
    "CounterfactualGatePolicy",
    "CounterfactualGateAssessment",
    "assess_counterfactual_capability",
    "OUTCOME_ELIGIBLE",
    "OUTCOME_HUMAN_REVIEW",
    "OUTCOME_RESTRICT",
    "OUTCOME_REJECT",
]
