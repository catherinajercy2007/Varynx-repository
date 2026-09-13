"""
Varynx Day 32
Adaptive Response Integration Layer

Purpose
-------
Combine already-computed security evidence from the existing
risk, behavioral, multi-resolution, and cross-context layers
into one canonical evidence object for the adaptive response
engine.

Architectural principle
-----------------------
This module assembles evidence.

It does NOT independently recalculate:

- authorization policy
- risk
- behavioral anomaly
- multi-resolution analysis
- cross-context correlation

Those responsibilities remain in their respective modules.

Pipeline
--------
Existing security evidence
        ↓
Canonical evidence assembly
        ↓
Adaptive Response Engine
        ↓
Graduated security response
"""

from __future__ import annotations

from typing import Any, Mapping

from app.adaptive_response import (
    calculate_adaptive_response,
)


# ============================================================
# CANONICAL EVIDENCE KEYS
# ============================================================

EVIDENCE_KEYS = (
    "risk_score",
    "anomaly_score",
    "repeated_denial_score",
    "cross_context_score",
    "multi_resolution_score",
    "context_entropy_score",
    "capability_resource_spread",
)


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _first_present(
    evidence: Mapping[str, Any],
    *keys: str,
    default: Any = 0,
) -> Any:
    """
    Return the first available evidence value.

    None is treated as missing so that fallback keys can
    still be considered.
    """

    for key in keys:
        if key in evidence and evidence[key] is not None:
            return evidence[key]

    return default


# ============================================================
# EVIDENCE ASSEMBLY
# ============================================================

def build_adaptive_evidence(
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Build the canonical evidence object consumed by the
    adaptive response engine.

    Existing aliases are accepted so that upstream modules
    do not need to be rewritten simply to match the adaptive
    response API.
    """

    if evidence is None:
        evidence = {}

    return {
        "risk_score": _first_present(
            evidence,
            "risk_score",
            "behavioral_risk_index",
        ),

        "anomaly_score": _first_present(
            evidence,
            "anomaly_score",
            "behavioral_anomaly_score",
        ),

        "repeated_denial_score": _first_present(
            evidence,
            "repeated_denial_score",
            "denial_score",
        ),

        "cross_context_score": _first_present(
            evidence,
            "cross_context_score",
            "correlation_score",
        ),

        "multi_resolution_score": _first_present(
            evidence,
            "multi_resolution_score",
            "resolution_risk",
        ),

        "context_entropy_score": _first_present(
            evidence,
            "context_entropy_score",
            "context_entropy",
        ),

        "capability_resource_spread": _first_present(
            evidence,
            "capability_resource_spread",
            "behavioral_spread",
        ),
    }


# ============================================================
# RESPONSE EVALUATION
# ============================================================

def evaluate_adaptive_evidence(
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Evaluate canonicalized evidence through the existing
    adaptive response engine.

    The returned object contains:

        evidence
        response

    Keeping both together makes the security decision
    auditable and explainable.
    """

    canonical_evidence = build_adaptive_evidence(
        evidence
    )

    response = calculate_adaptive_response(
        canonical_evidence
    )

    return {
        "evidence": canonical_evidence,
        "response": response,
    }


# ============================================================
# EVENT-STYLE INTEGRATION
# ============================================================

def integrate_security_evidence(
    *,
    risk_score: Any = 0,
    anomaly_score: Any = 0,
    repeated_denial_score: Any = 0,
    cross_context_score: Any = 0,
    multi_resolution_score: Any = 0,
    context_entropy_score: Any = 0,
    capability_resource_spread: Any = 0,
    **additional_evidence: Any,
) -> dict[str, Any]:
    """
    Convenience API for application/dashboard integration.

    Additional fields are preserved separately so application
    metadata does not get mixed into the canonical adaptive
    evidence vector.
    """

    evidence = {
        "risk_score": risk_score,
        "anomaly_score": anomaly_score,
        "repeated_denial_score": repeated_denial_score,
        "cross_context_score": cross_context_score,
        "multi_resolution_score": multi_resolution_score,
        "context_entropy_score": context_entropy_score,
        "capability_resource_spread": capability_resource_spread,
    }

    result = evaluate_adaptive_evidence(
        evidence
    )

    if additional_evidence:
        result["metadata"] = dict(
            additional_evidence
        )

    return result


__all__ = [
    "EVIDENCE_KEYS",
    "build_adaptive_evidence",
    "evaluate_adaptive_evidence",
    "integrate_security_evidence",
]