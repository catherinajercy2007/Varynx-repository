"""
Day 54 platform integration for BCSE evaluation and reproducibility.

This adapter exposes Day 54 evaluation results through a platform-safe
storage boundary. It does not implement evaluation logic, authorization,
adaptive response, or security policy decisions.
"""

from typing import Dict, List, Optional

from app.bcse_evaluation import (
    EvaluationMetrics,
    EvaluationResult,
    ReproducibilityManifest,
)


class BCSEEvaluationPlatformAdapter:
    """
    Platform-facing adapter for deterministic BCSE evaluation results.

    Evaluation logic remains owned by app.bcse_evaluation.BCSEEvaluator.
    This class only stores, retrieves, serializes, and resets evaluation
    results for platform/API consumption.
    """

    def __init__(self) -> None:
        self._evaluation_history: Dict[str, List[EvaluationResult]] = {}

    # ================================================================
    # Serialization helpers
    # ================================================================

    @staticmethod
    def _serialize_result(
        result: EvaluationResult,
    ) -> dict:
        """Return an API-safe representation of one evaluation result."""
        if not isinstance(result, EvaluationResult):
            raise TypeError("result must be an EvaluationResult")

        return {
            "case_id": result.case_id,
            "baseline": result.baseline,
            "base_consequence_score": result.base_consequence_score,
            "context_index": result.context_index,
            "adjusted_consequence_score": (
                result.adjusted_consequence_score
            ),
            "consequence_level": result.consequence_level,
            "within_bounds": result.within_bounds,
        }

    @staticmethod
    def serialize_metrics(
        metrics: EvaluationMetrics,
    ) -> dict:
        """Return an API-safe representation of evaluation metrics."""
        if not isinstance(metrics, EvaluationMetrics):
            raise TypeError("metrics must be an EvaluationMetrics")

        return {
            "total_cases": metrics.total_cases,
            "valid_cases": metrics.valid_cases,
            "bounded_cases": metrics.bounded_cases,
            "mean_base_consequence": metrics.mean_base_consequence,
            "mean_adjusted_consequence": (
                metrics.mean_adjusted_consequence
            ),
            "mean_context_index": metrics.mean_context_index,
            "adjustment_rate": metrics.adjustment_rate,
            "reproducibility_rate": metrics.reproducibility_rate,
        }

    @staticmethod
    def serialize_manifest(
        manifest: ReproducibilityManifest,
    ) -> dict:
        """Return an API-safe representation of reproducibility metadata."""
        if not isinstance(manifest, ReproducibilityManifest):
            raise TypeError(
                "manifest must be a ReproducibilityManifest"
            )

        return {
            "evaluation_version": manifest.evaluation_version,
            "seed": manifest.seed,
            "baseline": manifest.baseline,
            "case_ids": list(manifest.case_ids),
            "case_count": manifest.case_count,
        }

    # ================================================================
    # Recording
    # ================================================================

    def record_evaluation(
        self,
        agent_id: str,
        result: EvaluationResult,
    ) -> dict:
        """
        Record one evaluation result for an agent.

        The supplied result is stored internally while a fresh serialized
        representation is returned to the caller.
        """
        if not isinstance(agent_id, str):
            raise TypeError("agent_id must be a string")

        if not agent_id.strip():
            raise ValueError("agent_id must not be empty")

        if not isinstance(result, EvaluationResult):
            raise TypeError("result must be an EvaluationResult")

        self._evaluation_history.setdefault(agent_id, []).append(result)

        return self._serialize_result(result)

    # ================================================================
    # Retrieval
    # ================================================================

    def latest_evaluation(
        self,
        agent_id: str,
    ) -> Optional[dict]:
        """Return the latest serialized evaluation for an agent."""
        if not isinstance(agent_id, str):
            raise TypeError("agent_id must be a string")

        if not agent_id.strip():
            raise ValueError("agent_id must not be empty")

        history = self._evaluation_history.get(agent_id)

        if not history:
            return None

        return self._serialize_result(history[-1])

    def evaluation_history(
        self,
        agent_id: str,
    ) -> tuple[dict, ...]:
        """Return serialized evaluation history for an agent."""
        if not isinstance(agent_id, str):
            raise TypeError("agent_id must be a string")

        if not agent_id.strip():
            raise ValueError("agent_id must not be empty")

        history = self._evaluation_history.get(agent_id, [])

        return tuple(
            self._serialize_result(result)
            for result in history
        )

    def history_count(
        self,
        agent_id: str,
    ) -> int:
        """Return the number of evaluations stored for an agent."""
        if not isinstance(agent_id, str):
            raise TypeError("agent_id must be a string")

        if not agent_id.strip():
            raise ValueError("agent_id must not be empty")

        return len(self._evaluation_history.get(agent_id, []))

    # ================================================================
    # Reset
    # ================================================================

    def reset_evaluations(
        self,
        agent_id: Optional[str] = None,
    ) -> None:
        """
        Reset evaluation history.

        If agent_id is supplied, only that agent's history is removed.
        If omitted, all stored evaluation history is removed.
        """
        if agent_id is None:
            self._evaluation_history.clear()
            return

        if not isinstance(agent_id, str):
            raise TypeError("agent_id must be a string")

        if not agent_id.strip():
            raise ValueError("agent_id must not be empty")

        self._evaluation_history.pop(agent_id, None)


__all__ = [
    "BCSEEvaluationPlatformAdapter",
]