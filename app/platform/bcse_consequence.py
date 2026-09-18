"""
Varynx Day 52
Platform integration for BCSE Security Consequence Estimation.

This module provides a lightweight platform boundary around the
Day 52 ConsequenceEstimate representation.

The adapter:
- stores consequence estimates per agent
- provides latest/history access
- provides API-safe serialization
- preserves evidence and assumptions
- keeps agent histories isolated
- supports per-agent and global reset

The adapter does NOT:
- execute hypothetical actions
- authorize actions
- block agents
- modify runtime risk state
- trigger adaptive response
- infer malicious intent
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.bcse_consequence import ConsequenceEstimate


class BCSEConsequencePlatformAdapter:
    """
    Platform adapter for Day 52 consequence estimates.

    Consequence estimates are grouped by agent. Since the Day 52
    estimate itself identifies a scenario rather than an agent, the
    platform accepts agent_id explicitly when recording it.
    """

    def __init__(self) -> None:
        self._estimate_history: Dict[
            str,
            List[ConsequenceEstimate],
        ] = {}

    @staticmethod
    def _serialize_estimate(
        estimate: ConsequenceEstimate,
    ) -> Dict[str, Any]:
        """Serialize a consequence estimate into an API-safe dictionary."""
        return {
            "scenario_id": estimate.scenario_id,
            "consequence_score": estimate.consequence_score,
            "consequence_level": estimate.consequence_level,
            "confidence": estimate.confidence,
            "dimensions": dict(estimate.dimensions),
            "evidence": list(estimate.evidence),
            "assumptions": list(estimate.assumptions),
        }

    def record_estimate(
        self,
        agent_id: str,
        estimate: ConsequenceEstimate,
    ) -> Dict[str, Any]:
        """
        Record a consequence estimate for an agent.

        This only records the estimate. It does not turn the estimate
        into a security or authorization decision.
        """
        if not isinstance(agent_id, str):
            raise TypeError(
                "agent_id must be a string"
            )

        if not agent_id.strip():
            raise ValueError(
                "agent_id must be non-empty"
            )

        if not isinstance(
            estimate,
            ConsequenceEstimate,
        ):
            raise TypeError(
                "estimate must be ConsequenceEstimate"
            )

        history = self._estimate_history.setdefault(
            agent_id,
            [],
        )

        history.append(estimate)

        return self._serialize_estimate(estimate)

    def latest_estimate(
        self,
        agent_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Return the latest consequence estimate for an agent."""
        history = self._estimate_history.get(agent_id)

        if not history:
            return None

        return self._serialize_estimate(
            history[-1]
        )

    def estimate_history(
        self,
        agent_id: str,
    ) -> List[Dict[str, Any]]:
        """Return serialized consequence-estimate history for an agent."""
        history = self._estimate_history.get(
            agent_id,
            [],
        )

        return [
            self._serialize_estimate(estimate)
            for estimate in history
        ]

    def history_count(
        self,
        agent_id: str,
    ) -> int:
        """Return the number of recorded estimates for an agent."""
        return len(
            self._estimate_history.get(
                agent_id,
                [],
            )
        )

    def reset_estimates(
        self,
        agent_id: Optional[str] = None,
    ) -> None:
        """
        Reset consequence-estimate history.

        If agent_id is supplied, only that agent's history is removed.
        Otherwise, all estimate history is removed.
        """
        if agent_id is None:
            self._estimate_history.clear()
            return

        self._estimate_history.pop(
            agent_id,
            None,
        )