"""Day 79: deterministic reason codes for existing security decisions.

This module explains an already-produced decision using supplied evidence.
It does not calculate, authorize, override, or execute a security decision.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any, Mapping

VERSION = "DAY79-V1"

# Stable machine-readable codes; order is the explanation priority.
_SIGNAL_RULES = (
    (
        "PRIMARY_RISK_CRITICAL",
        "risk_score",
        80.0,
        "Primary risk evidence is critical.",
    ),
    (
        "PRIMARY_RISK_ELEVATED",
        "risk_score",
        60.0,
        "Primary risk evidence is elevated.",
    ),
    (
        "BEHAVIORAL_ANOMALY_CRITICAL",
        "anomaly_score",
        80.0,
        "Behavioral anomaly evidence is critical.",
    ),
    (
        "BEHAVIORAL_DEVIATION_ELEVATED",
        "anomaly_score",
        60.0,
        "Behavioral deviation evidence is elevated.",
    ),
    (
        "REPEATED_DENIAL_PATTERN",
        "repeated_denial_score",
        60.0,
        "Repeated authorization denials were observed.",
    ),
    (
        "CROSS_CONTEXT_CORRELATION",
        "cross_context_score",
        60.0,
        "Correlated evidence across contexts was observed.",
    ),
    (
        "MULTI_RESOLUTION_CONCERN",
        "multi_resolution_score",
        60.0,
        "Multi-resolution analysis indicates elevated concern.",
    ),
    (
        "CONTEXT_ENTROPY_CONCERN",
        "context_entropy_score",
        60.0,
        "Context entropy is elevated in the supplied evidence.",
    ),
    (
        "RESOURCE_SPREAD_EXPANSION",
        "capability_resource_spread",
        60.0,
        "Capability or resource spread is elevated.",
    ),
)

_DECISION_MESSAGES = {
    "ALLOW": "The existing decision permits the action.",
    "ALLOW_WITH_MONITORING": (
        "The existing decision permits the action with monitoring."
    ),
    "MONITOR": "The existing decision calls for monitoring.",
    "STEP_UP_VERIFICATION": (
        "The existing decision requires additional verification."
    ),
    "REDUCE_SCOPE": (
        "The existing decision reduces the permitted scope."
    ),
    "HUMAN_REVIEW": (
        "The existing decision requires human review."
    ),
    "BLOCK": "The existing decision blocks the action.",
    "DENY": "The existing decision denies the action.",
    "RESTRICT": "The existing decision restricts the action.",
}


def _text(value: Any, field: str) -> str:
    """Validate and normalize a required text field."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{field} must be a non-empty string"
        )

    return value.strip()


def _score(value: Any, field: str) -> float:
    """Validate a finite numeric score in the 0–100 range."""
    if isinstance(value, bool):
        raise ValueError(
            f"{field} must be numeric"
        )

    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{field} must be numeric"
        ) from exc

    if not isfinite(result) or not 0.0 <= result <= 100.0:
        raise ValueError(
            f"{field} must be finite and between 0 and 100"
        )

    return result


def _normalise_score(value: Any, field: str) -> float:
    """Convert normalized fractions to percentages."""
    result = _score(value, field)

    return result * 100.0 if result <= 1.0 else result


@dataclass(frozen=True)
class SecurityReasonCode:
    """One explainable reason attached to an existing decision."""

    code: str
    message: str
    category: str
    decision: str
    source_key: str | None = None
    observed_value: float | None = None
    threshold: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable copy of this record."""
        return asdict(self)


def generate_security_reason_codes(
    *,
    decision: str,
    evidence: Mapping[str, Any],
) -> tuple[SecurityReasonCode, ...]:
    """Generate stable explanations without changing the decision.

    Missing evidence is not inferred. Only explicitly supplied numeric
    signals are considered. Scores in [0, 1] are treated as normalized
    fractions; scores in (1, 100] are treated as percentages.
    """
    decision_value = _text(
        decision,
        "decision",
    ).upper()

    if not isinstance(evidence, Mapping):
        raise TypeError(
            "evidence must be a mapping"
        )

    records: list[SecurityReasonCode] = [
        SecurityReasonCode(
            code="EXISTING_DECISION_RECORDED",
            message=_DECISION_MESSAGES.get(
                decision_value,
                f"The existing decision is {decision_value}.",
            ),
            category="DECISION",
            decision=decision_value,
        )
    ]

    aliases = {
        "risk_score": (
            "risk_score",
            "behavioral_risk_index",
        ),
        "anomaly_score": (
            "anomaly_score",
            "behavioral_anomaly_score",
        ),
        "repeated_denial_score": (
            "repeated_denial_score",
            "denial_score",
        ),
        "cross_context_score": (
            "cross_context_score",
            "correlation_score",
        ),
        "multi_resolution_score": (
            "multi_resolution_score",
            "resolution_risk",
        ),
        "context_entropy_score": (
            "context_entropy_score",
            "context_entropy",
        ),
        "capability_resource_spread": (
            "capability_resource_spread",
            "behavioral_spread",
        ),
    }

    emitted_keys: set[str] = set()

    for code, key, threshold, message in _SIGNAL_RULES:
        actual_key = next(
            (
                candidate
                for candidate in aliases[key]
                if candidate in evidence
            ),
            None,
        )

        if actual_key is None:
            continue

        observed = _normalise_score(
            evidence[actual_key],
            actual_key,
        )

        if observed < threshold:
            continue

        # Emit only the strongest applicable reason for each signal.
        if key in emitted_keys:
            continue

        emitted_keys.add(key)

        records.append(
            SecurityReasonCode(
                code=code,
                message=message,
                category="BEHAVIORAL_EVIDENCE",
                decision=decision_value,
                source_key=actual_key,
                observed_value=round(observed, 4),
                threshold=threshold,
            )
        )

    return tuple(records)


def reason_codes_to_dicts(
    reasons: tuple[SecurityReasonCode, ...],
) -> list[dict[str, Any]]:
    """Serialize reason codes without mutating the source records."""
    if not isinstance(reasons, tuple) or any(
        not isinstance(item, SecurityReasonCode)
        for item in reasons
    ):
        raise TypeError(
            "reasons must be a tuple of SecurityReasonCode records"
        )

    return [
        item.to_dict()
        for item in reasons
    ]


def reason_code_generation_is_read_only() -> bool:
    """Report that reason-code generation is explanatory only."""
    return True


def reason_codes_modify_decision() -> bool:
    """Reason codes do not modify the existing decision."""
    return False


def reason_codes_execute_enforcement() -> bool:
    """Reason-code generation does not enforce security controls."""
    return False


def reason_codes_infer_malicious_intent() -> bool:
    """Reason codes do not infer an agent's intent."""
    return False


__all__ = [
    "VERSION",
    "SecurityReasonCode",
    "generate_security_reason_codes",
    "reason_codes_to_dicts",
    "reason_code_generation_is_read_only",
    "reason_codes_modify_decision",
    "reason_codes_execute_enforcement",
    "reason_codes_infer_malicious_intent",
]