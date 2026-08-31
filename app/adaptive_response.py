"""
AegisGuard Day 30
Adaptive Security Response Engine

Purpose
-------
Convert accumulated security evidence into graduated runtime
responses instead of relying only on binary allow/deny decisions.

Response levels
---------------
ALLOW
ALLOW_WITH_MONITORING
STEP_UP_VERIFICATION
REDUCE_SCOPE
HUMAN_REVIEW
BLOCK

This module is intentionally deterministic and explainable.
It is a research prototype and should not be interpreted as
a production security policy without further validation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional


class ResponseAction(str, Enum):
    """Graduated security response."""

    ALLOW = "ALLOW"
    ALLOW_WITH_MONITORING = "ALLOW_WITH_MONITORING"
    STEP_UP_VERIFICATION = "STEP_UP_VERIFICATION"
    REDUCE_SCOPE = "REDUCE_SCOPE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class ResponseDecision:
    """
    Explainable adaptive response decision.
    """

    action: ResponseAction
    severity: str
    score: float
    reasons: List[str]
    recommended_controls: List[str]

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["action"] = self.action.value
        return result


def _number(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Safely convert a value to float.
    """

    try:
        number = float(value)

        if number != number:
            return default

        return number

    except (TypeError, ValueError):
        return default


def _clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> float:
    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def _normalise_score(
    value: Any,
) -> float:
    """
    Accept either a 0-1 or 0-100 score and return 0-100.
    """

    score = _number(value)

    if 0.0 <= score <= 1.0:
        score *= 100.0

    return _clamp(score)


def calculate_adaptive_risk_score(
    evidence: Mapping[str, Any],
) -> float:
    """
    Combine available security evidence into one bounded
    adaptive-response score.

    The weighting is deliberately explicit so that the model
    can later be evaluated through ablation experiments.

    Current research weights:

        risk score                 30%
        behavioral anomaly        20%
        repeated denial           15%
        cross-context correlation 15%
        multi-resolution risk     10%
        context entropy            5%
        capability/resource spread 5%

    Missing evidence contributes zero rather than inventing
    evidence.
    """

    risk = _normalise_score(
        evidence.get(
            "risk_score",
            evidence.get(
                "behavioral_risk_index",
                0,
            ),
        )
    )

    anomaly = _normalise_score(
        evidence.get(
            "anomaly_score",
            evidence.get(
                "behavioral_anomaly_score",
                0,
            ),
        )
    )

    repeated_denial = _normalise_score(
        evidence.get(
            "repeated_denial_score",
            evidence.get(
                "denial_score",
                0,
            ),
        )
    )

    cross_context = _normalise_score(
        evidence.get(
            "cross_context_score",
            evidence.get(
                "correlation_score",
                0,
            ),
        )
    )

    multi_resolution = _normalise_score(
        evidence.get(
            "multi_resolution_score",
            evidence.get(
                "resolution_risk",
                0,
            ),
        )
    )

    context_entropy = _normalise_score(
        evidence.get(
            "context_entropy_score",
            evidence.get(
                "context_entropy",
                0,
            ),
        )
    )

    spread = _normalise_score(
        evidence.get(
            "capability_resource_spread",
            evidence.get(
                "behavioral_spread",
                0,
            ),
        )
    )

    score = (
        0.30 * risk
        + 0.20 * anomaly
        + 0.15 * repeated_denial
        + 0.15 * cross_context
        + 0.10 * multi_resolution
        + 0.05 * context_entropy
        + 0.05 * spread
    )

    return round(
        _clamp(score),
        4,
    )


def _positive_signal(
    value: Any,
    threshold: float = 60.0,
) -> bool:
    return _normalise_score(value) >= threshold


def generate_response_reasons(
    evidence: Mapping[str, Any],
) -> List[str]:
    """
    Produce human-readable explanations for the decision.
    """

    reasons: List[str] = []

    risk = _normalise_score(
        evidence.get("risk_score", 0)
    )

    anomaly = _normalise_score(
        evidence.get(
            "anomaly_score",
            evidence.get(
                "behavioral_anomaly_score",
                0,
            ),
        )
    )

    denial = _normalise_score(
        evidence.get(
            "repeated_denial_score",
            evidence.get(
                "denial_score",
                0,
            ),
        )
    )

    cross_context = _normalise_score(
        evidence.get(
            "cross_context_score",
            evidence.get(
                "correlation_score",
                0,
            ),
        )
    )

    multi_resolution = _normalise_score(
        evidence.get(
            "multi_resolution_score",
            evidence.get(
                "resolution_risk",
                0,
            ),
        )
    )

    if risk >= 80:
        reasons.append(
            "Primary risk score is in the critical range."
        )
    elif risk >= 60:
        reasons.append(
            "Primary risk score is elevated."
        )

    if anomaly >= 80:
        reasons.append(
            "Strong behavioral anomaly detected."
        )
    elif anomaly >= 60:
        reasons.append(
            "Behavior deviates materially from the expected pattern."
        )

    if denial >= 80:
        reasons.append(
            "Repeated denial behavior is strongly associated with the session."
        )
    elif denial >= 60:
        reasons.append(
            "Repeated authorization denials were observed."
        )

    if cross_context >= 80:
        reasons.append(
            "Strong cross-context behavioral correlation detected."
        )
    elif cross_context >= 60:
        reasons.append(
            "Behavior across contexts shows a suspicious relationship."
        )

    if multi_resolution >= 80:
        reasons.append(
            "Multi-resolution behavioral analysis indicates high risk."
        )
    elif multi_resolution >= 60:
        reasons.append(
            "Behavior becomes more suspicious when evaluated across resolutions."
        )

    if not reasons:
        reasons.append(
            "No strong security signal was detected in the supplied evidence."
        )

    return reasons


def recommend_controls(
    action: ResponseAction,
) -> List[str]:
    """
    Map each response level to concrete controls.
    """

    controls = {
        ResponseAction.ALLOW: [
            "Permit requested action.",
            "Continue normal telemetry collection.",
        ],

        ResponseAction.ALLOW_WITH_MONITORING: [
            "Permit requested action.",
            "Increase behavioral telemetry.",
            "Monitor subsequent actions closely.",
        ],

        ResponseAction.STEP_UP_VERIFICATION: [
            "Require additional identity or authorization verification.",
            "Do not expand privileges during verification.",
            "Record the verification result.",
        ],

        ResponseAction.REDUCE_SCOPE: [
            "Restrict requested capability.",
            "Restrict accessible resources.",
            "Allow only the minimum necessary operation.",
            "Continue monitoring after scope reduction.",
        ],

        ResponseAction.HUMAN_REVIEW: [
            "Pause sensitive action.",
            "Create an investigation record.",
            "Require human approval before continuation.",
            "Preserve relevant behavioral evidence.",
        ],

        ResponseAction.BLOCK: [
            "Reject the requested action.",
            "Preserve security evidence.",
            "Prevent automatic retry escalation.",
            "Raise a security alert.",
        ],
    }

    return list(
        controls[action]
    )


def determine_response_action(
    score: float,
    evidence: Optional[Mapping[str, Any]] = None,
) -> ResponseAction:
    """
    Convert an adaptive score into a graduated response.

    Additional evidence can escalate the response where a
    single score would otherwise hide a severe signal.
    """

    evidence = evidence or {}

    risk = _normalise_score(
        evidence.get(
            "risk_score",
            0,
        )
    )

    anomaly = _normalise_score(
        evidence.get(
            "anomaly_score",
            evidence.get(
                "behavioral_anomaly_score",
                0,
            ),
        )
    )

    denial = _normalise_score(
        evidence.get(
            "repeated_denial_score",
            evidence.get(
                "denial_score",
                0,
            ),
        )
    )

    cross_context = _normalise_score(
        evidence.get(
            "cross_context_score",
            evidence.get(
                "correlation_score",
                0,
            ),
        )
    )

    if score >= 90:
        return ResponseAction.BLOCK

    if (
        score >= 80
        or risk >= 95
        or (
            anomaly >= 90
            and cross_context >= 75
        )
    ):
        return ResponseAction.HUMAN_REVIEW

    if (
        score >= 70
        or (
            cross_context >= 85
            and denial >= 60
        )
    ):
        return ResponseAction.REDUCE_SCOPE

    if (
        score >= 55
        or anomaly >= 80
        or denial >= 80
    ):
        return ResponseAction.STEP_UP_VERIFICATION

    if score >= 30:
        return ResponseAction.ALLOW_WITH_MONITORING

    return ResponseAction.ALLOW


def calculate_adaptive_response(
    evidence: Mapping[str, Any],
) -> Dict[str, Any]:
    """
    Main public API.

    Returns a fully explainable response object.
    """

    score = calculate_adaptive_risk_score(
        evidence
    )

    action = determine_response_action(
        score,
        evidence,
    )

    if action == ResponseAction.BLOCK:
        severity = "CRITICAL"

    elif action == ResponseAction.HUMAN_REVIEW:
        severity = "HIGH"

    elif action in (
        ResponseAction.REDUCE_SCOPE,
        ResponseAction.STEP_UP_VERIFICATION,
    ):
        severity = "ELEVATED"

    elif action == ResponseAction.ALLOW_WITH_MONITORING:
        severity = "MODERATE"

    else:
        severity = "LOW"

    decision = ResponseDecision(
        action=action,
        severity=severity,
        score=score,
        reasons=generate_response_reasons(
            evidence
        ),
        recommended_controls=recommend_controls(
            action
        ),
    )

    return decision.to_dict()


def evaluate_events(
    events: Iterable[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Evaluate multiple events independently.
    """

    results: List[Dict[str, Any]] = []

    for index, event in enumerate(events):
        evidence = dict(event)

        response = calculate_adaptive_response(
            evidence
        )

        result = dict(response)

        result["event_index"] = index

        if "agent_id" in event:
            result["agent_id"] = event[
                "agent_id"
            ]

        results.append(
            result
        )

    return results


def summarize_responses(
    responses: Iterable[Mapping[str, Any]],
) -> Dict[str, Any]:
    """
    Produce aggregate response statistics.
    """

    rows = list(
        responses
    )

    counts = {
        action.value: 0
        for action in ResponseAction
    }

    for row in rows:
        action = str(
            row.get(
                "action",
                "",
            )
        )

        if action in counts:
            counts[action] += 1

    total = len(rows)

    blocked = counts[
        ResponseAction.BLOCK.value
    ]

    human_review = counts[
        ResponseAction.HUMAN_REVIEW.value
    ]

    escalated = (
        counts[
            ResponseAction.STEP_UP_VERIFICATION.value
        ]
        + counts[
            ResponseAction.REDUCE_SCOPE.value
        ]
        + human_review
        + blocked
    )

    return {
        "total_events": total,
        "response_counts": counts,
        "blocked_events": blocked,
        "human_review_events": human_review,
        "escalated_events": escalated,
        "escalation_rate": (
            round(
                escalated / total,
                4,
            )
            if total
            else 0.0
        ),
    }


__all__ = [
    "ResponseAction",
    "ResponseDecision",
    "calculate_adaptive_risk_score",
    "determine_response_action",
    "calculate_adaptive_response",
    "evaluate_events",
    "summarize_responses",
    "generate_response_reasons",
    "recommend_controls",
]