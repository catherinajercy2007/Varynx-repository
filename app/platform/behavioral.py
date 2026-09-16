"""
Varynx Day 49
Platform integration for adaptive behavioral baselines.

This module provides a thin platform-facing adapter around the
existing app.behavioral_baseline implementation.

The platform layer is responsible for:
- exposing baseline operations through a stable interface
- converting internal baseline records into serialization-safe dictionaries
- preserving agent isolation
- keeping security decisions outside the platform adapter

The underlying AdaptiveBehavioralBaseline remains the owner of
baseline learning and deviation logic.

This module does not:
- authorize requests
- block agents
- modify permissions
- calculate dynamic trust
- perform BCSE analysis
- select adaptive security responses
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from app.behavioral_baseline import (
    AdaptiveBehavioralBaseline,
    BaselineUpdate,
)


def _serialize_update(update: BaselineUpdate) -> dict[str, Any]:
    """Convert a BaselineUpdate into a JSON-safe dictionary."""
    return {
        "agent_id": update.agent_id,
        "accepted": update.accepted,
        "mean_deviation": update.mean_deviation,
        "previous_baseline": dict(update.previous_baseline),
        "observation": dict(update.observation),
        "updated_baseline": dict(update.updated_baseline),
        "reason": update.reason,
        "update_index": update.update_index,
    }


class BehavioralPlatformAdapter:
    """
    Platform-facing adapter for Varynx behavioral baselines.

    The adapter delegates all behavioral baseline decisions to the
    existing AdaptiveBehavioralBaseline implementation rather than
    duplicating its logic.
    """

    def __init__(
        self,
        baseline_manager: Optional[
            AdaptiveBehavioralBaseline
        ] = None,
    ) -> None:
        self._manager = (
            baseline_manager
            if baseline_manager is not None
            else AdaptiveBehavioralBaseline()
        )

    @property
    def manager(self) -> AdaptiveBehavioralBaseline:
        """Return the underlying baseline manager."""
        return self._manager

    def set_baseline(
        self,
        agent_id: str,
        dimensions: Mapping[str, float],
    ) -> dict[str, Any]:
        """
        Register or replace an agent behavioral baseline.

        Returns a serialization-safe platform response.
        """
        self._manager.set_baseline(
            agent_id,
            dimensions,
        )

        baseline = self._manager.get_baseline(agent_id)

        return {
            "status": "baseline_set",
            "agent_id": agent_id,
            "baseline": baseline,
        }

    def get_baseline(
        self,
        agent_id: str,
    ) -> dict[str, Any]:
        """Return the current baseline for an agent."""
        baseline = self._manager.get_baseline(agent_id)

        return {
            "status": (
                "baseline_available"
                if baseline is not None
                else "baseline_not_found"
            ),
            "agent_id": agent_id,
            "baseline": baseline,
        }

    def observe(
        self,
        agent_id: str,
        observation: Mapping[str, float],
    ) -> dict[str, Any]:
        """
        Submit a behavioral observation through the platform layer.

        The underlying baseline manager determines whether the
        observation is safe to learn from.
        """
        result = self._manager.observe(
            agent_id,
            observation,
        )

        return {
            "status": "observation_processed",
            "result": _serialize_update(result),
        }

    def history(
        self,
        agent_id: str,
    ) -> dict[str, Any]:
        """Return serialized baseline update history."""
        history = self._manager.history(agent_id)

        return {
            "status": "history_available",
            "agent_id": agent_id,
            "count": len(history),
            "history": [
                _serialize_update(update)
                for update in history
            ],
        }

    def latest(
        self,
        agent_id: str,
    ) -> dict[str, Any]:
        """Return the latest baseline update."""
        latest = self._manager.latest(agent_id)

        return {
            "status": (
                "latest_available"
                if latest is not None
                else "latest_not_found"
            ),
            "agent_id": agent_id,
            "latest": (
                _serialize_update(latest)
                if latest is not None
                else None
            ),
        }

    def reset(
        self,
        agent_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Reset one agent or all platform-managed behavioral baselines.
        """
        self._manager.reset(agent_id)

        if agent_id is None:
            return {
                "status": "all_baselines_reset",
            }

        return {
            "status": "baseline_reset",
            "agent_id": agent_id,
        }