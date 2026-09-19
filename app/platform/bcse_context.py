"""
Varynx Day 53
Platform integration for context-aware BCSE consequence modeling.

This module provides a platform boundary around the Day 53
ContextAwareConsequenceEstimate representation.

The adapter:
- stores context-aware estimates per agent
- provides latest/history access
- provides API-safe serialization
- preserves context and evidence
- keeps agent histories isolated
- supports per-agent and global reset

The adapter does NOT:
- authorize actions
- block agents
- execute hypothetical actions
- modify runtime risk state
- trigger adaptive response
- infer malicious intent
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.bcse_context import ContextAwareConsequenceEstimate


class BCSEContextPlatformAdapter:
    """
    Platform adapter for Day 53 context-aware consequence estimates.

    The Day 53 core model groups history by scenario_id. The platform
    layer additionally groups records by agent_id so platform history
    remains isolated between agents.
    """

    def __init__(self) -> None:
        self._estimate_history: Dict[
            str,
            List[ContextAwareConsequenceEstimate],
        ] = {}

    @staticmethod
    def _serialize_estimate(
        estimate: ContextAwareConsequenceEstimate,
    ) -> Dict[str, Any]:
        """Serialize a Day 53 estimate into an API-safe dictionary."""
        return {
            "scenario_id": estimate.scenario_id,
            "base_consequence_score": estimate.base_consequence_score,
            "context_index": estimate.context_index,
            "context_level": estimate.context_level,
            "context_modifier": estimate.context_modifier,
            "adjusted_consequence_score": (
                estimate.adjusted_consequence_score
            ),
            "adjusted_consequence_level": (
                estimate.adjusted_consequence_level
            ),
            "context": dict(estimate.context),
            "evidence": list(estimate.evidence),
        }

    def record_estimate(
        self,
        agent_id: str,
        estimate: ContextAwareConsequenceEstimate,
    ) -> Dict[str, Any]:
        """
        Record a context-aware consequence estimate for an agent.

        Recording is observational only. The estimate is not converted
        into an authorization or runtime security decision.
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
            ContextAwareConsequenceEstimate,
        ):
            raise TypeError(
                "estimate must be ContextAwareConsequenceEstimate"
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
        """Return the latest context-aware estimate for an agent."""
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
        """Return serialized context-aware estimate history."""
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
        Reset context-aware estimate history.

        If agent_id is supplied, only that agent's history is removed.
        Otherwise, all platform history is removed.
        """
        if agent_id is None:
            self._estimate_history.clear()
            return

        self._estimate_history.pop(
            agent_id,
            None,
        )