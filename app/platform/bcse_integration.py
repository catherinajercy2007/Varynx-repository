"""
Day 55 platform integration for the Varynx BCSE pipeline.

This adapter exposes integrated Day 51-53 BCSE results through a
platform-safe storage and serialization boundary.

It does not execute hypothetical actions, infer malicious intent,
make authorization decisions, block agents, or modify adaptive
response or risk behavior.
"""

from typing import Dict, List, Optional

from app.bcse_integration import BCSEIntegrationResult


class BCSEIntegrationPlatformAdapter:
    """
    Platform-facing adapter for Day 55 BCSE integration results.

    The actual BCSE orchestration remains owned by
    app.bcse_integration.VarynxBCSEIntegration.

    This adapter only stores, retrieves, serializes, and resets
    integrated results for platform/API consumption.
    """

    def __init__(self) -> None:
        self._integration_history: Dict[
            str,
            List[BCSEIntegrationResult],
        ] = {}

    # ================================================================
    # Serialization helpers
    # ================================================================

    @staticmethod
    def _serialize_context(context) -> dict:
        """Serialize a context dataclass into an API-safe dictionary."""
        if hasattr(context, "__dataclass_fields__"):
            return {
                field_name: getattr(context, field_name)
                for field_name in context.__dataclass_fields__
            }

        if isinstance(context, dict):
            return dict(context)

        return dict(vars(context))

    @staticmethod
    def _serialize_result(
        result: BCSEIntegrationResult,
    ) -> dict:
        """Return an API-safe representation of one integration result."""
        if not isinstance(result, BCSEIntegrationResult):
            raise TypeError(
                "result must be a BCSEIntegrationResult"
            )

        scenario = result.scenario
        consequence = result.consequence
        context_aware = result.context_aware

        return {
            "agent_id": result.agent_id,
            "scenario": {
                "scenario_id": scenario.scenario_id,
                "agent_id": scenario.agent_id,
                "current_context": (
                    BCSEIntegrationPlatformAdapter._serialize_context(
                        scenario.current_context
                    )
                ),
                "hypothetical_context": (
                    BCSEIntegrationPlatformAdapter._serialize_context(
                        scenario.hypothetical_context
                    )
                ),
                "changes": [
                    {
                        "dimension": change.dimension,
                        "current_value": change.current_value,
                        "hypothetical_value": (
                            change.hypothetical_value
                        ),
                        "reason": change.reason,
                    }
                    for change in scenario.changes
                ],
                "evidence": list(scenario.evidence),
                "assumptions": list(scenario.assumptions),
            },
            "consequence": {
                "scenario_id": consequence.scenario_id,
                "consequence_score": consequence.consequence_score,
                "consequence_level": consequence.consequence_level,
                "confidence": consequence.confidence,
                "dimensions": dict(consequence.dimensions),
                "evidence": list(consequence.evidence),
                "assumptions": list(consequence.assumptions),
            },
            "context_aware": {
                "scenario_id": context_aware.scenario_id,
                "base_consequence_score": (
                    context_aware.base_consequence_score
                ),
                "context_index": context_aware.context_index,
                "context_level": context_aware.context_level,
                "context_modifier": context_aware.context_modifier,
                "adjusted_consequence_score": (
                    context_aware.adjusted_consequence_score
                ),
                "adjusted_consequence_level": (
                    context_aware.adjusted_consequence_level
                ),
                "context": dict(context_aware.context),
                "evidence": list(context_aware.evidence),
            },
            "baseline": result.baseline,
            "evaluation_version": result.evaluation_version,
            "evidence": list(result.evidence),
            "assumptions": list(result.assumptions),
        }

    # ================================================================
    # Recording
    # ================================================================

    def record_integration(
        self,
        result: BCSEIntegrationResult,
    ) -> dict:
        """
        Record one integrated BCSE result.

        The agent_id is taken from the authoritative Day 55 result.
        """
        if not isinstance(result, BCSEIntegrationResult):
            raise TypeError(
                "result must be a BCSEIntegrationResult"
            )

        agent_id = result.agent_id

        if not isinstance(agent_id, str):
            raise TypeError("result.agent_id must be a string")

        if not agent_id.strip():
            raise ValueError(
                "result.agent_id must not be empty"
            )

        self._integration_history.setdefault(
            agent_id,
            [],
        ).append(result)

        return self._serialize_result(result)

    # ================================================================
    # Retrieval
    # ================================================================

    def latest_integration(
        self,
        agent_id: str,
    ) -> Optional[dict]:
        """Return the latest serialized integration result."""
        self._validate_agent_id(agent_id)

        history = self._integration_history.get(agent_id)

        if not history:
            return None

        return self._serialize_result(history[-1])

    def integration_history(
        self,
        agent_id: str,
    ) -> tuple[dict, ...]:
        """Return serialized integration history for an agent."""
        self._validate_agent_id(agent_id)

        history = self._integration_history.get(agent_id, [])

        return tuple(
            self._serialize_result(result)
            for result in history
        )

    def history_count(
        self,
        agent_id: str,
    ) -> int:
        """Return the number of stored integration results."""
        self._validate_agent_id(agent_id)

        return len(
            self._integration_history.get(agent_id, [])
        )

    # ================================================================
    # Reset
    # ================================================================

    def reset_integrations(
        self,
        agent_id: Optional[str] = None,
    ) -> None:
        """
        Reset integration history.

        If agent_id is supplied, only that agent is cleared.
        If omitted, all integration history is cleared.
        """
        if agent_id is None:
            self._integration_history.clear()
            return

        self._validate_agent_id(agent_id)

        self._integration_history.pop(
            agent_id,
            None,
        )

    # ================================================================
    # Validation
    # ================================================================

    @staticmethod
    def _validate_agent_id(agent_id: str) -> None:
        if not isinstance(agent_id, str):
            raise TypeError("agent_id must be a string")

        if not agent_id.strip():
            raise ValueError("agent_id must not be empty")


__all__ = [
    "BCSEIntegrationPlatformAdapter",
]