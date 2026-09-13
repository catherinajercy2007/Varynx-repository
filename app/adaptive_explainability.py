"""
Varynx Day 33
Adaptive Response Explainability

Purpose
-------
Convert an adaptive security decision into a structured,
auditable explanation.

This module does not calculate risk and does not make a new
security decision.

Responsibilities:
- summarize supplied evidence
- identify significant evidence signals
- explain the selected response
- expose recommended controls
- produce an audit-friendly representation

Decision making remains in adaptive_response.py.
"""

from __future__ import annotations

from typing import Any, Mapping

from app.adaptive_response import (
    ResponseAction,
    calculate_adaptive_response,
)


SIGNAL_DEFINITIONS = {
    "risk_score": {
        "label": "Primary Risk",
        "threshold": 60.0,
    },
    "anomaly_score": {
        "label": "Behavioral Anomaly",
        "threshold": 60.0,
    },
    "repeated_denial_score": {
        "label": "Repeated Denials",
        "threshold": 60.0,
    },
    "cross_context_score": {
        "label": "Cross-Context Correlation",
        "threshold": 60.0,
    },
    "multi_resolution_score": {
        "label": "Multi-Resolution Risk",
        "threshold": 60.0,
    },
    "context_entropy_score": {
        "label": "Context Entropy",
        "threshold": 60.0,
    },
    "capability_resource_spread": {
        "label": "Capability/Resource Spread",
        "threshold": 60.0,
    },
}


RESPONSE_DESCRIPTIONS = {
    ResponseAction.ALLOW.value: (
        "The supplied evidence does not require an escalated "
        "security response."
    ),
    ResponseAction.ALLOW_WITH_MONITORING.value: (
        "The evidence warrants continued execution with "
        "increased behavioral monitoring."
    ),
    ResponseAction.STEP_UP_VERIFICATION.value: (
        "The evidence warrants additional identity or "
        "authorization verification before continued trust."
    ),
    ResponseAction.REDUCE_SCOPE.value: (
        "The evidence warrants restricting the requested "
        "capability or accessible resources."
    ),
    ResponseAction.HUMAN_REVIEW.value: (
        "The evidence is sufficiently severe to require "
        "human investigation before continuation."
    ),
    ResponseAction.BLOCK.value: (
        "The evidence warrants rejecting the requested action."
    ),
}


def _number(value: Any) -> float:
    """Safely convert a value to float."""

    try:
        number = float(value)

        if number != number:
            return 0.0

        return number

    except (TypeError, ValueError):
        return 0.0


def _normalise(value: Any) -> float:
    """
    Normalize a score to the 0-100 representation used by
    the adaptive response engine.
    """

    score = _number(value)

    if 0.0 <= score <= 1.0:
        score *= 100.0

    return max(
        0.0,
        min(
            100.0,
            score,
        ),
    )


def build_evidence_summary(
    evidence: Mapping[str, Any],
) -> dict[str, float]:
    """
    Build a stable representation of the security evidence
    used for explanation.
    """

    if evidence is None:
        evidence = {}

    return {
        key: round(
            _normalise(
                evidence.get(
                    key,
                    0,
                )
            ),
            4,
        )
        for key in SIGNAL_DEFINITIONS
    }


def identify_triggered_signals(
    evidence: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """
    Identify evidence dimensions that cross their explanatory
    threshold.

    These thresholds are explanatory indicators only. They do
    not replace the actual adaptive response rules.
    """

    summary = build_evidence_summary(evidence)

    triggered = []

    for key, definition in SIGNAL_DEFINITIONS.items():
        value = summary[key]
        threshold = definition["threshold"]

        if value >= threshold:
            triggered.append(
                {
                    "signal": key,
                    "label": definition["label"],
                    "value": value,
                    "threshold": threshold,
                }
            )

    return triggered


def build_decision_rationale(
    action: str,
    evidence: Mapping[str, Any],
    response: Mapping[str, Any],
) -> str:
    """
    Produce a concise human-readable rationale.

    Correlation or anomaly is described as evidence, not proof
    of malicious intent.
    """

    triggered = identify_triggered_signals(evidence)

    description = RESPONSE_DESCRIPTIONS.get(
        action,
        "The adaptive response engine selected a security action.",
    )

    if triggered:
        labels = ", ".join(
            item["label"]
            for item in triggered
        )

        signal_text = (
            f"Significant evidence signals: {labels}."
        )
    else:
        signal_text = (
            "No individual evidence dimension crossed the "
            "explanatory significance threshold."
        )

    score = response.get("score", 0.0)
    severity = response.get("severity", "UNKNOWN")

    return (
        f"Adaptive score {score} produced a "
        f"{severity} severity response. "
        f"{description} "
        f"{signal_text}"
    )


def explain_adaptive_decision(
    evidence: Mapping[str, Any],
    response: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Produce a complete structured explanation.

    If response is not supplied, the existing adaptive response
    engine is used.
    """

    if evidence is None:
        evidence = {}

    if response is None:
        response = calculate_adaptive_response(evidence)

    action = str(
        response.get(
            "action",
            ResponseAction.ALLOW.value,
        )
    )

    return {
        "decision": {
            "action": action,
            "severity": response.get(
                "severity",
                "UNKNOWN",
            ),
            "score": response.get(
                "score",
                0.0,
            ),
        },
        "evidence": build_evidence_summary(evidence),
        "triggered_signals": identify_triggered_signals(
            evidence
        ),
        "rationale": build_decision_rationale(
            action,
            evidence,
            response,
        ),
        "reasons": list(
            response.get(
                "reasons",
                [],
            )
        ),
        "recommended_controls": list(
            response.get(
                "recommended_controls",
                [],
            )
        ),
    }


def evaluate_explainable_decision(
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Evaluate evidence and explain the resulting decision."""

    response = calculate_adaptive_response(evidence)

    return explain_adaptive_decision(
        evidence,
        response,
    )


def build_audit_record(
    evidence: Mapping[str, Any],
    explanation: Mapping[str, Any],
    *,
    agent_id: str | None = None,
    event_id: str | None = None,
) -> dict[str, Any]:
    """
    Produce a compact audit representation.

    Identifiers are optional so this module remains independent
    of the persistence layer.
    """

    decision = explanation.get(
        "decision",
        {},
    )

    record = {
        "action": decision.get(
            "action",
            ResponseAction.ALLOW.value,
        ),
        "severity": decision.get(
            "severity",
            "UNKNOWN",
        ),
        "adaptive_score": decision.get(
            "score",
            0.0,
        ),
        "triggered_signals": list(
            explanation.get(
                "triggered_signals",
                [],
            )
        ),
        "rationale": explanation.get(
            "rationale",
            "",
        ),
        "evidence": dict(
            explanation.get(
                "evidence",
                {},
            )
        ),
    }

    if agent_id is not None:
        record["agent_id"] = agent_id

    if event_id is not None:
        record["event_id"] = event_id

    return record


__all__ = [
    "SIGNAL_DEFINITIONS",
    "RESPONSE_DESCRIPTIONS",
    "build_evidence_summary",
    "identify_triggered_signals",
    "build_decision_rationale",
    "explain_adaptive_decision",
    "evaluate_explainable_decision",
    "build_audit_record",
]