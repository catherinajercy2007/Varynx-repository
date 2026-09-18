"""
Varynx Day 49-50
Platform integration for adaptive behavioral baselines and
behavioral intelligence.

This module provides a thin platform-facing adapter around the
existing behavioral baseline and behavioral intelligence components.

Day 49 responsibilities:
- expose baseline operations through a stable interface
- convert internal baseline records into serialization-safe dictionaries
- preserve agent isolation
- keep security decisions outside the platform adapter

Day 50 responsibilities:
- accept behavioral-intelligence snapshots
- maintain per-agent intelligence history
- expose latest behavioral-intelligence state
- expose serialized behavioral-intelligence history
- preserve independent trust, state, and deviation outputs
- provide a stable platform-facing representation

The underlying behavioral components remain responsible for their
own algorithms and analytical logic.

This module does not:
- authorize requests
- block agents
- modify permissions
- calculate dynamic trust
- perform BCSE analysis
- calculate a new aggregate risk score
- select adaptive security responses
- infer malicious intent
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from app.behavioral_baseline import (
    AdaptiveBehavioralBaseline,
    BaselineUpdate,
)

from app.behavioral_intelligence import (
    BehavioralIntelligenceSnapshot,
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
    Platform-facing adapter for behavioral baselines and
    behavioral intelligence.

    Day 49:
        Delegates behavioral-baseline operations to
        AdaptiveBehavioralBaseline.

    Day 50:
        Stores and exposes read-only BehavioralIntelligenceSnapshot
        objects for later API, gateway, dashboard, and runtime use.

    The adapter does not duplicate behavioral algorithms or make
    security decisions.
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

        self._intelligence_history: dict[
            str,
            list[BehavioralIntelligenceSnapshot],
        ] = {}

    @property
    def manager(self) -> AdaptiveBehavioralBaseline:
        """Return the underlying baseline manager."""
        return self._manager

    # ------------------------------------------------------------------
    # Day 49 - Behavioral baseline platform integration
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Day 50 - Behavioral intelligence platform integration
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize_intelligence(
        snapshot: BehavioralIntelligenceSnapshot,
    ) -> dict[str, Any]:
        """
        Convert a behavioral-intelligence snapshot into a
        JSON-safe platform representation.

        Individual component outputs remain independent.
        No aggregate risk or security decision is introduced.
        """
        return {
            "agent_id": snapshot.agent_id,
            "trust_score": snapshot.trust_score,
            "trust_band": snapshot.trust_band,
            "state_score": snapshot.state_score,
            "state_level": snapshot.state_level,
            "deviation_score": snapshot.deviation_score,
            "deviation_level": snapshot.deviation_level,
            "baseline_adapted": snapshot.baseline_adapted,
            "evidence": list(snapshot.evidence),
            "consistency_flags": list(
                snapshot.consistency_flags
            ),
        }

    def record_intelligence(
        self,
        snapshot: BehavioralIntelligenceSnapshot,
    ) -> dict[str, Any]:
        """
        Record a behavioral-intelligence snapshot.

        The snapshot is stored for platform/API/dashboard consumption.

        The underlying behavioral-intelligence snapshot is not modified,
        and the platform does not make a security decision.
        """
        if not isinstance(
            snapshot,
            BehavioralIntelligenceSnapshot,
        ):
            raise TypeError(
                "snapshot must be a BehavioralIntelligenceSnapshot"
            )

        self._intelligence_history.setdefault(
            snapshot.agent_id,
            [],
        ).append(snapshot)

        return {
            "status": "intelligence_recorded",
            "agent_id": snapshot.agent_id,
        }

    def latest_intelligence(
        self,
        agent_id: str,
    ) -> dict[str, Any]:
        """
        Return the latest behavioral-intelligence snapshot for an agent.
        """
        history = self._intelligence_history.get(
            agent_id,
            [],
        )

        latest = history[-1] if history else None

        return {
            "status": (
                "latest_available"
                if latest is not None
                else "latest_not_found"
            ),
            "agent_id": agent_id,
            "intelligence": (
                self._serialize_intelligence(latest)
                if latest is not None
                else None
            ),
        }

    def intelligence_history(
        self,
        agent_id: str,
    ) -> dict[str, Any]:
        """
        Return serialized behavioral-intelligence history for an agent.
        """
        history = self._intelligence_history.get(
            agent_id,
            [],
        )

        return {
            "status": "history_available",
            "agent_id": agent_id,
            "count": len(history),
            "intelligence": [
                self._serialize_intelligence(snapshot)
                for snapshot in history
            ],
        }

    def reset_intelligence(
        self,
        agent_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Reset stored behavioral-intelligence snapshots.

        If agent_id is supplied, only that agent's intelligence history
        is removed.

        If agent_id is omitted, all intelligence history is removed.
        """
        if agent_id is None:
            self._intelligence_history.clear()

            return {
                "status": "all_intelligence_reset",
            }

        self._intelligence_history.pop(
            agent_id,
            None,
        )

        return {
            "status": "intelligence_reset",
            "agent_id": agent_id,
        }