"""
Varynx Day 63 - Security Decision Reconciliation Engine.

This module reconciles independent behavioral and predictive security
signals into a single explainable advisory outcome.

Architectural boundary:
- Does not authorize actions.
- Does not execute controls.
- Does not modify authorization policy.
- Does not replace adaptive_response.py.
- Does not replace the existing risk engine.
- Does not infer malicious intent.
- Does not execute BCSE scenarios.
- Does not create a universal Varynx security score.

The reconciler determines whether independent evidence supports,
weakens, or escalates a proposed security decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional


CONFIDENCE_LOW = "LOW"
CONFIDENCE_MODERATE = "MODERATE"
CONFIDENCE_HIGH = "HIGH"

DIRECTION_IMPROVING = "IMPROVING"
DIRECTION_STABLE = "STABLE"
DIRECTION_DETERIORATING = "DETERIORATING"

DECISION_ALLOW = "ALLOW"
DECISION_MONITOR = "MONITOR"
DECISION_STEP_UP = "STEP_UP_VERIFICATION"
DECISION_REDUCE_SCOPE = "REDUCE_SCOPE"
DECISION_HUMAN_REVIEW = "HUMAN_REVIEW"
DECISION_BLOCK = "BLOCK"

RECONCILIATION_SUPPORTED = "SUPPORTED"
RECONCILIATION_WEAKENED = "WEAKENED"
RECONCILIATION_ESCALATED = "ESCALATED"

DECISION_ORDER = {
    DECISION_ALLOW: 0,
    DECISION_MONITOR: 1,
    DECISION_STEP_UP: 2,
    DECISION_REDUCE_SCOPE: 3,
    DECISION_HUMAN_REVIEW: 4,
    DECISION_BLOCK: 5,
}

SCORE_MIN = 0.0
SCORE_MAX = 100.0


def _validate_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")

    return value.strip()


def _validate_score(value: float, name: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc

    if not SCORE_MIN <= numeric <= SCORE_MAX:
        raise ValueError(
            f"{name} must be between {SCORE_MIN} and {SCORE_MAX}"
        )

    return numeric


def _validate_slope(value: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("slope must be numeric") from exc


def _validate_confidence(value: str) -> str:
    value = _validate_text(value, "confidence").upper()

    allowed = {
        CONFIDENCE_LOW,
        CONFIDENCE_MODERATE,
        CONFIDENCE_HIGH,
    }

    if value not in allowed:
        raise ValueError(f"Unsupported confidence: {value}")

    return value


def _validate_direction(value: str) -> str:
    value = _validate_text(value, "direction").upper()

    allowed = {
        DIRECTION_IMPROVING,
        DIRECTION_STABLE,
        DIRECTION_DETERIORATING,
    }

    if value not in allowed:
        raise ValueError(f"Unsupported direction: {value}")

    return value


def _validate_decision(value: str) -> str:
    value = _validate_text(value, "decision").upper()

    if value not in DECISION_ORDER:
        raise ValueError(f"Unsupported decision: {value}")

    return value


def _validate_evidence(
    evidence: Optional[Iterable[str]],
) -> List[str]:
    if evidence is None:
        return []

    if isinstance(evidence, (str, bytes)):
        raise ValueError("evidence must be an iterable of strings")

    result: List[str] = []

    for item in evidence:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                "evidence entries must be non-empty strings"
            )

        result.append(item.strip())

    return result


def reconcile_decision(
    *,
    proposed_decision: str,
    projected_score: float,
    direction: str,
    confidence: str,
    consequence_score: Optional[float] = None,
    deviation_score: Optional[float] = None,
) -> tuple[str, str]:
    """
    Reconcile the proposed decision against independent evidence.

    Returns:
        (reconciled_decision, reconciliation_status)

    This function does not execute the returned decision.
    """

    proposed_decision = _validate_decision(proposed_decision)
    projected_score = _validate_score(
        projected_score,
        "projected_score",
    )
    direction = _validate_direction(direction)
    confidence = _validate_confidence(confidence)

    if consequence_score is not None:
        consequence_score = _validate_score(
            consequence_score,
            "consequence_score",
        )

    if deviation_score is not None:
        deviation_score = _validate_score(
            deviation_score,
            "deviation_score",
        )

    proposed_order = DECISION_ORDER[proposed_decision]

    escalation_evidence = False
    weakening_evidence = False

    if direction == DIRECTION_DETERIORATING:
        escalation_evidence = True

    if consequence_score is not None and consequence_score >= 70:
        escalation_evidence = True

    if deviation_score is not None and deviation_score >= 70:
        escalation_evidence = True

    if direction == DIRECTION_IMPROVING:
        weakening_evidence = True

    if (
        consequence_score is not None
        and consequence_score < 20
    ):
        weakening_evidence = True

    if (
        deviation_score is not None
        and deviation_score < 20
    ):
        weakening_evidence = True

        # Strong independent evidence can escalate the advisory even when
    # the projected score has not reached the critical threshold.
    #
    # This prevents a high-confidence combination of deteriorating
    # behavior, high consequence exposure, and high deviation from
    # being ignored merely because projected_score < 70.
    strong_independent_evidence = (
        (
            consequence_score is not None
            and consequence_score >= 70
        )
        and (
            deviation_score is not None
            and deviation_score >= 70
        )
    )

    if (
        escalation_evidence
        and confidence == CONFIDENCE_HIGH
        and (
            projected_score >= 70
            or strong_independent_evidence
        )
    ):
        reconciled_order = min(
            DECISION_ORDER[DECISION_BLOCK],
            proposed_order + 1,
        )

        reconciled = next(
            decision
            for decision, order in DECISION_ORDER.items()
            if order == reconciled_order
        )

        return reconciled, RECONCILIATION_ESCALATED

    # Improving behavior or low supporting evidence can weaken
    # an unnecessarily strong recommendation.
    if (
        weakening_evidence
        and direction == DIRECTION_IMPROVING
        and confidence == CONFIDENCE_LOW
        and proposed_order >= DECISION_ORDER[DECISION_HUMAN_REVIEW]
    ):
        reconciled_order = max(0, proposed_order - 1)

        reconciled = next(
            decision
            for decision, order in DECISION_ORDER.items()
            if order == reconciled_order
        )

        return reconciled, RECONCILIATION_WEAKENED

    return proposed_decision, RECONCILIATION_SUPPORTED


def build_reconciliation_evidence(
    *,
    proposed_decision: str,
    reconciled_decision: str,
    status: str,
    projected_score: float,
    direction: str,
    confidence: str,
    consequence_score: Optional[float],
    deviation_score: Optional[float],
    source_evidence: Optional[Iterable[str]] = None,
) -> List[str]:
    """Build explainable reconciliation evidence."""

    proposed_decision = _validate_decision(proposed_decision)
    reconciled_decision = _validate_decision(reconciled_decision)

    projected_score = _validate_score(
        projected_score,
        "projected_score",
    )

    direction = _validate_direction(direction)
    confidence = _validate_confidence(confidence)

    status = _validate_text(status, "status").upper()

    allowed_statuses = {
        RECONCILIATION_SUPPORTED,
        RECONCILIATION_WEAKENED,
        RECONCILIATION_ESCALATED,
    }

    if status not in allowed_statuses:
        raise ValueError(f"Unsupported reconciliation status: {status}")

    evidence = [
        f"Proposed decision: {proposed_decision}",
        f"Reconciled decision: {reconciled_decision}",
        f"Reconciliation status: {status}",
        f"Projected security score: {projected_score:.2f}",
        f"Behavioral direction: {direction}",
        f"Prediction confidence: {confidence}",
    ]

    if consequence_score is not None:
        evidence.append(
            f"Consequence score: {consequence_score:.2f}"
        )

    if deviation_score is not None:
        evidence.append(
            f"Behavioral deviation score: {deviation_score:.2f}"
        )

    evidence.extend(_validate_evidence(source_evidence))

    return evidence


@dataclass(frozen=True)
class SecurityDecisionReconciliation:
    """Immutable reconciled security advisory."""

    agent_id: str
    proposed_decision: str
    reconciled_decision: str
    reconciliation_status: str
    projected_score: float
    direction: str
    slope: float
    confidence: str
    consequence_score: Optional[float]
    deviation_score: Optional[float]
    evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_text(self.agent_id, "agent_id")
        _validate_decision(self.proposed_decision)
        _validate_decision(self.reconciled_decision)

        status = _validate_text(
            self.reconciliation_status,
            "reconciliation_status",
        ).upper()

        if status not in {
            RECONCILIATION_SUPPORTED,
            RECONCILIATION_WEAKENED,
            RECONCILIATION_ESCALATED,
        }:
            raise ValueError(
                f"Unsupported reconciliation status: {status}"
            )

        _validate_score(
            self.projected_score,
            "projected_score",
        )

        _validate_direction(self.direction)
        _validate_confidence(self.confidence)
        _validate_slope(self.slope)

        if self.consequence_score is not None:
            _validate_score(
                self.consequence_score,
                "consequence_score",
            )

        if self.deviation_score is not None:
            _validate_score(
                self.deviation_score,
                "deviation_score",
            )

        _validate_evidence(self.evidence)


class SecurityDecisionReconciliationEngine:
    """
    Stateful reconciliation engine.

    State is isolated per agent.
    """

    def __init__(self) -> None:
        self._history: Dict[
            str,
            List[SecurityDecisionReconciliation],
        ] = {}

        self._latest: Dict[
            str,
            SecurityDecisionReconciliation,
        ] = {}

    def reconcile(
        self,
        *,
        agent_id: str,
        proposed_decision: str,
        projected_score: float,
        direction: str,
        slope: float,
        confidence: str,
        consequence_score: Optional[float] = None,
        deviation_score: Optional[float] = None,
        evidence: Optional[Iterable[str]] = None,
    ) -> SecurityDecisionReconciliation:
        """Reconcile a proposed decision into an advisory outcome."""

        agent_id = _validate_text(agent_id, "agent_id")

        slope = _validate_slope(slope)

        reconciled_decision, status = reconcile_decision(
            proposed_decision=proposed_decision,
            projected_score=projected_score,
            direction=direction,
            confidence=confidence,
            consequence_score=consequence_score,
            deviation_score=deviation_score,
        )

        decision_evidence = build_reconciliation_evidence(
            proposed_decision=proposed_decision,
            reconciled_decision=reconciled_decision,
            status=status,
            projected_score=projected_score,
            direction=direction,
            confidence=confidence,
            consequence_score=consequence_score,
            deviation_score=deviation_score,
            source_evidence=evidence,
        )

        snapshot = SecurityDecisionReconciliation(
            agent_id=agent_id,
            proposed_decision=_validate_decision(
                proposed_decision
            ),
            reconciled_decision=reconciled_decision,
            reconciliation_status=status,
            projected_score=float(projected_score),
            direction=_validate_direction(direction),
            slope=slope,
            confidence=_validate_confidence(confidence),
            consequence_score=(
                None
                if consequence_score is None
                else float(consequence_score)
            ),
            deviation_score=(
                None
                if deviation_score is None
                else float(deviation_score)
            ),
            evidence=tuple(decision_evidence),
        )

        self._history.setdefault(agent_id, []).append(snapshot)
        self._latest[agent_id] = snapshot

        return snapshot

    def latest(
        self,
        agent_id: str,
    ) -> Optional[SecurityDecisionReconciliation]:
        agent_id = _validate_text(agent_id, "agent_id")
        return self._latest.get(agent_id)

    def history(
        self,
        agent_id: str,
    ) -> List[SecurityDecisionReconciliation]:
        agent_id = _validate_text(agent_id, "agent_id")
        return list(self._history.get(agent_id, []))

    def snapshot_all(
        self,
    ) -> Dict[str, SecurityDecisionReconciliation]:
        return dict(self._latest)

    def reset(self, agent_id: Optional[str] = None) -> None:
        if agent_id is None:
            self._history.clear()
            self._latest.clear()
            return

        agent_id = _validate_text(agent_id, "agent_id")

        self._history.pop(agent_id, None)
        self._latest.pop(agent_id, None)