"""
Varynx Day 50
Behavioral Intelligence Integration and Validation.

This module provides a read-only orchestration layer over the
behavioral intelligence components developed during Days 46-49.

It combines:
- dynamic behavioral trust
- behavioral state
- behavioral deviation
- adaptive baseline information

The orchestrator does not:
- authorize requests
- block agents
- modify permissions
- trigger adaptive response
- infer malicious intent
- directly modify the underlying engines
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional


VALID_TRUST_BANDS = {
    "HIGH",
    "MODERATE",
    "LOW",
    "CRITICAL",
}

VALID_STATE_LEVELS = {
    "STABLE",
    "MOSTLY_STABLE",
    "VARIABLE",
    "UNSTABLE",
    "HIGHLY_UNSTABLE",
}

VALID_DEVIATION_LEVELS = {
    "NONE",
    "LOW",
    "MODERATE",
    "HIGH",
    "CRITICAL",
}


def _validate_score(
    value: float,
    field_name: str,
) -> float:
    """Validate a 0-100 normalized score."""
    if not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be numeric")

    value = float(value)

    if value < 0 or value > 100:
        raise ValueError(
            f"{field_name} must be between 0 and 100"
        )

    return value


def _validate_agent_id(agent_id: str) -> str:
    """Validate an agent identifier."""
    if not isinstance(agent_id, str) or not agent_id.strip():
        raise ValueError(
            "agent_id must be a non-empty string"
        )

    return agent_id


def _validate_band(
    value: str,
    allowed: set[str],
    field_name: str,
) -> str:
    """Validate a categorical behavioral label."""
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string"
        )

    if value not in allowed:
        raise ValueError(
            f"Invalid {field_name}: {value}"
        )

    return value


@dataclass(frozen=True)
class BehavioralIntelligenceSnapshot:
    """
    Combined read-only behavioral intelligence representation.

    The individual component outputs remain separately represented
    rather than being collapsed into a new security score.
    """

    agent_id: str

    trust_score: float
    trust_band: str

    state_score: float
    state_level: str

    deviation_score: float
    deviation_level: str

    baseline_adapted: bool

    evidence: List[str] = field(default_factory=list)

    consistency_flags: List[str] = field(
        default_factory=list
    )


class BehavioralIntelligenceOrchestrator:
    """
    Read-only integration layer for Varynx behavioral intelligence.

    This class does not own the underlying trust, state, deviation,
    or baseline algorithms. It receives their outputs and combines
    them into an explainable snapshot.
    """

    def __init__(self) -> None:
        self._history: Dict[
            str,
            List[BehavioralIntelligenceSnapshot],
        ] = {}

    def build_snapshot(
        self,
        agent_id: str,
        *,
        trust_score: float,
        trust_band: str,
        state_score: float,
        state_level: str,
        deviation_score: float,
        deviation_level: str,
        baseline_adapted: bool = False,
        evidence: Optional[List[str]] = None,
    ) -> BehavioralIntelligenceSnapshot:
        """
        Construct a combined behavioral intelligence snapshot.
        """
        agent_id = _validate_agent_id(agent_id)

        trust_score = _validate_score(
            trust_score,
            "trust_score",
        )

        state_score = _validate_score(
            state_score,
            "state_score",
        )

        deviation_score = _validate_score(
            deviation_score,
            "deviation_score",
        )

        trust_band = _validate_band(
            trust_band,
            VALID_TRUST_BANDS,
            "trust_band",
        )

        state_level = _validate_band(
            state_level,
            VALID_STATE_LEVELS,
            "state_level",
        )

        deviation_level = _validate_band(
            deviation_level,
            VALID_DEVIATION_LEVELS,
            "deviation_level",
        )

        if not isinstance(baseline_adapted, bool):
            raise TypeError(
                "baseline_adapted must be boolean"
            )

        evidence_copy = list(evidence or [])

        consistency_flags = self._detect_consistency_flags(
            trust_score=trust_score,
            trust_band=trust_band,
            state_score=state_score,
            state_level=state_level,
            deviation_score=deviation_score,
            deviation_level=deviation_level,
        )

        snapshot = BehavioralIntelligenceSnapshot(
            agent_id=agent_id,
            trust_score=trust_score,
            trust_band=trust_band,
            state_score=state_score,
            state_level=state_level,
            deviation_score=deviation_score,
            deviation_level=deviation_level,
            baseline_adapted=baseline_adapted,
            evidence=evidence_copy,
            consistency_flags=consistency_flags,
        )

        self._history.setdefault(
            agent_id,
            [],
        ).append(snapshot)

        return snapshot

    @staticmethod
    def _detect_consistency_flags(
        *,
        trust_score: float,
        trust_band: str,
        state_score: float,
        state_level: str,
        deviation_score: float,
        deviation_level: str,
    ) -> List[str]:
        """
        Identify potentially interesting relationships between
        component outputs.

        These are analytical flags, not security decisions.
        """
        flags: List[str] = []

        if (
            trust_score >= 80
            and deviation_score >= 60
        ):
            flags.append(
                "HIGH_TRUST_WITH_HIGH_DEVIATION"
            )

        if (
            trust_score < 40
            and deviation_score < 20
        ):
            flags.append(
                "LOW_TRUST_WITH_LOW_DEVIATION"
            )

        if (
            state_score >= 80
            and deviation_score >= 60
        ):
            flags.append(
                "STABLE_STATE_WITH_HIGH_DEVIATION"
            )

        if (
            state_score < 40
            and deviation_score < 20
        ):
            flags.append(
                "UNSTABLE_STATE_WITH_LOW_DEVIATION"
            )

        if (
            trust_band == "HIGH"
            and state_level in {
                "UNSTABLE",
                "HIGHLY_UNSTABLE",
            }
        ):
            flags.append(
                "HIGH_TRUST_WITH_UNSTABLE_STATE"
            )

        if (
            deviation_level == "CRITICAL"
            and trust_band == "CRITICAL"
        ):
            flags.append(
                "CRITICAL_DEVIATION_AND_TRUST"
            )

        return flags

    def history(
        self,
        agent_id: str,
    ) -> List[BehavioralIntelligenceSnapshot]:
        """Return integration history for one agent."""
        return list(
            self._history.get(agent_id, [])
        )

    def latest(
        self,
        agent_id: str,
    ) -> Optional[BehavioralIntelligenceSnapshot]:
        """Return the latest combined snapshot."""
        history = self._history.get(agent_id, [])

        if not history:
            return None

        return history[-1]

    def reset(
        self,
        agent_id: Optional[str] = None,
    ) -> None:
        """Reset one agent or all orchestration history."""
        if agent_id is None:
            self._history.clear()
            return

        self._history.pop(agent_id, None)