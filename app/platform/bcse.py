"""
Varynx Day 51
Platform integration for Behavioral Counterfactual Security Engine (BCSE).

This module provides a lightweight platform boundary around the Day 51
counterfactual scenario representation.

The adapter:
- stores immutable counterfactual scenario representations
- keeps history isolated per agent
- exposes latest/history accessors
- provides API-safe serialization
- supports per-agent and global reset

The adapter does NOT:
- execute hypothetical actions
- authorize actions
- block actions
- calculate risk scores
- infer malicious intent
- modify runtime state
- trigger adaptive response
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.bcse_scenario import (
    BehavioralContext,
    CounterfactualChange,
    CounterfactualScenario,
)


class BCSEPlatformAdapter:
    """
    Platform adapter for Day 51 counterfactual scenarios.

    Scenarios are stored by agent ID so that one agent's hypothetical
    scenarios cannot contaminate another agent's history.
    """

    def __init__(self) -> None:
        self._scenario_history: Dict[
            str,
            List[CounterfactualScenario],
        ] = {}

    @staticmethod
    def _serialize_context(
        context: BehavioralContext,
    ) -> Dict[str, Any]:
        """Serialize a behavioral context into an API-safe dictionary."""
        return {
            "trust_score": context.trust_score,
            "state_score": context.state_score,
            "deviation_score": context.deviation_score,
            "attributes": dict(context.attributes),
        }

    @staticmethod
    def _serialize_change(
        change: CounterfactualChange,
    ) -> Dict[str, Any]:
        """Serialize a counterfactual change."""
        return {
            "dimension": change.dimension,
            "current_value": change.current_value,
            "hypothetical_value": change.hypothetical_value,
            "reason": change.reason,
        }

    @classmethod
    def _serialize_scenario(
        cls,
        scenario: CounterfactualScenario,
    ) -> Dict[str, Any]:
        """Serialize a complete counterfactual scenario."""
        return {
            "scenario_id": scenario.scenario_id,
            "agent_id": scenario.agent_id,
            "current_context": cls._serialize_context(
                scenario.current_context,
            ),
            "hypothetical_context": cls._serialize_context(
                scenario.hypothetical_context,
            ),
            "changes": [
                cls._serialize_change(change)
                for change in scenario.changes
            ],
            "evidence": list(scenario.evidence),
            "assumptions": list(scenario.assumptions),
        }

    def record_scenario(
        self,
        scenario: CounterfactualScenario,
    ) -> Dict[str, Any]:
        """
        Record a counterfactual scenario and return its API representation.

        Recording is observational only. The hypothetical scenario is
        never executed or applied to runtime state.
        """
        if not isinstance(
            scenario,
            CounterfactualScenario,
        ):
            raise TypeError(
                "scenario must be CounterfactualScenario"
            )

        agent_history = self._scenario_history.setdefault(
            scenario.agent_id,
            [],
        )

        agent_history.append(scenario)

        return self._serialize_scenario(scenario)

    def latest_scenario(
        self,
        agent_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Return the latest scenario for an agent."""
        history = self._scenario_history.get(agent_id)

        if not history:
            return None

        return self._serialize_scenario(history[-1])

    def scenario_history(
        self,
        agent_id: str,
    ) -> List[Dict[str, Any]]:
        """Return serialized scenario history for an agent."""
        history = self._scenario_history.get(agent_id, [])

        return [
            self._serialize_scenario(scenario)
            for scenario in history
        ]

    def history_count(
        self,
        agent_id: str,
    ) -> int:
        """Return the number of recorded scenarios for an agent."""
        return len(
            self._scenario_history.get(
                agent_id,
                [],
            )
        )

    def reset_scenarios(
        self,
        agent_id: Optional[str] = None,
    ) -> None:
        """
        Reset scenario history.

        If agent_id is supplied, only that agent's history is removed.
        Otherwise, all scenario history is removed.
        """
        if agent_id is None:
            self._scenario_history.clear()
            return

        self._scenario_history.pop(
            agent_id,
            None,
        )