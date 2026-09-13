"""
Day 54 - BCSE Evaluation and Reproducibility.

Provides deterministic evaluation utilities for the BCSE pipeline.

This module evaluates BCSE behavior. It does not change runtime
authorization, adaptive response, risk, or security policy behavior.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Sequence

from app.bcse_context import (
    ContextAwareConsequenceModel,
)


EVALUATION_VERSION = "day54-v1"

DEFAULT_SEED = 0

BASELINE_STATIC_POLICY = "STATIC_POLICY"
BASELINE_RISK_ONLY = "RISK_ONLY"
BASELINE_RISK_BEHAVIOR = "RISK_BEHAVIOR"
BASELINE_RISK_BEHAVIOR_TRUST = "RISK_BEHAVIOR_TRUST"
BASELINE_FULL_VARYNX_BCSE = "FULL_VARYNX_BCSE"

SUPPORTED_BASELINES = (
    BASELINE_STATIC_POLICY,
    BASELINE_RISK_ONLY,
    BASELINE_RISK_BEHAVIOR,
    BASELINE_RISK_BEHAVIOR_TRUST,
    BASELINE_FULL_VARYNX_BCSE,
)


def _validate_score(value: float, name: str) -> float:
    """Validate a 0-100 score."""
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")

    value = float(value)

    if value < 0 or value > 100:
        raise ValueError(f"{name} must be between 0 and 100")

    return value


def _validate_case_id(case_id: str) -> str:
    """Validate evaluation case identifiers."""
    if not isinstance(case_id, str):
        raise TypeError("case_id must be a string")

    if not case_id.strip():
        raise ValueError("case_id must not be empty")

    return case_id


@dataclass(frozen=True)
class EvaluationCase:
    """
    Immutable deterministic BCSE evaluation case.
    """

    case_id: str
    scenario_id: str
    base_consequence_score: float
    context: Mapping[str, float]
    expected_min: float = 0.0
    expected_max: float = 100.0

    def __post_init__(self) -> None:
        _validate_case_id(self.case_id)

        if not isinstance(self.scenario_id, str):
            raise TypeError("scenario_id must be a string")

        if not self.scenario_id.strip():
            raise ValueError("scenario_id must not be empty")

        _validate_score(
            self.base_consequence_score,
            "base_consequence_score",
        )

        _validate_score(
            self.expected_min,
            "expected_min",
        )

        _validate_score(
            self.expected_max,
            "expected_max",
        )

        if self.expected_min > self.expected_max:
            raise ValueError(
                "expected_min cannot exceed expected_max"
            )

        if not isinstance(self.context, Mapping):
            raise TypeError("context must be a mapping")


@dataclass(frozen=True)
class EvaluationResult:
    """
    Immutable result for one evaluation case.
    """

    case_id: str
    baseline: str
    base_consequence_score: float
    context_index: float
    adjusted_consequence_score: float
    consequence_level: str
    within_bounds: bool


@dataclass(frozen=True)
class EvaluationMetrics:
    """
    Aggregate evaluation metrics.
    """

    total_cases: int
    valid_cases: int
    bounded_cases: int
    mean_base_consequence: float
    mean_adjusted_consequence: float
    mean_context_index: float
    adjustment_rate: float
    reproducibility_rate: float


@dataclass(frozen=True)
class ReproducibilityManifest:
    """
    Immutable reproducibility metadata.
    """

    evaluation_version: str
    seed: int
    baseline: str
    case_ids: tuple[str, ...]
    case_count: int


def validate_baseline(baseline: str) -> str:
    """Validate a supported evaluation baseline."""
    if baseline not in SUPPORTED_BASELINES:
        raise ValueError(
            f"Unsupported baseline: {baseline}"
        )

    return baseline


def build_reproducibility_manifest(
    cases: Sequence[EvaluationCase],
    baseline: str,
    seed: int = DEFAULT_SEED,
) -> ReproducibilityManifest:
    """
    Build deterministic metadata describing an evaluation run.
    """
    validate_baseline(baseline)

    if not isinstance(seed, int):
        raise TypeError("seed must be an integer")

    case_ids = tuple(
        case.case_id
        for case in cases
    )

    if len(case_ids) != len(set(case_ids)):
        raise ValueError(
            "evaluation case IDs must be unique"
        )

    return ReproducibilityManifest(
        evaluation_version=EVALUATION_VERSION,
        seed=seed,
        baseline=baseline,
        case_ids=case_ids,
        case_count=len(cases),
    )


class BCSEEvaluator:
    """
    Deterministic evaluator for context-aware BCSE.

    The evaluator deliberately treats the different research baselines
    as evaluation labels. It does not silently implement unsupported
    runtime semantics for those baselines.
    """

    def __init__(
        self,
        evaluation_version: str = EVALUATION_VERSION,
    ) -> None:
        if not isinstance(evaluation_version, str):
            raise TypeError(
                "evaluation_version must be a string"
            )

        if not evaluation_version.strip():
            raise ValueError(
                "evaluation_version must not be empty"
            )

        self.evaluation_version = evaluation_version
        self._model = ContextAwareConsequenceModel()

    def evaluate_case(
        self,
        case: EvaluationCase,
        baseline: str = BASELINE_FULL_VARYNX_BCSE,
    ) -> EvaluationResult:
        """
        Evaluate one case.

        The full BCSE configuration applies the Day 53 contextual model.

        Other baseline names are retained as evaluation labels and must
        not be interpreted as hidden implementations of unvalidated
        security logic.
        """
        validate_baseline(baseline)

        result = self._model.estimate(
            scenario_id=case.scenario_id,
            consequence_score=case.base_consequence_score,
            context=case.context,
        )

        within_bounds = (
            case.expected_min
            <= result.adjusted_consequence_score
            <= case.expected_max
        )

        return EvaluationResult(
            case_id=case.case_id,
            baseline=baseline,
            base_consequence_score=(
                result.base_consequence_score
            ),
            context_index=result.context_index,
            adjusted_consequence_score=(
                result.adjusted_consequence_score
            ),
            consequence_level=(
                result.adjusted_consequence_level
            ),
            within_bounds=within_bounds,
        )

    def evaluate(
        self,
        cases: Iterable[EvaluationCase],
        baseline: str = BASELINE_FULL_VARYNX_BCSE,
    ) -> tuple[EvaluationResult, ...]:
        """
        Evaluate a deterministic collection of cases.
        """
        validate_baseline(baseline)

        cases = tuple(cases)

        ids = [case.case_id for case in cases]

        if len(ids) != len(set(ids)):
            raise ValueError(
                "evaluation case IDs must be unique"
            )

        return tuple(
            self.evaluate_case(
                case,
                baseline,
            )
            for case in cases
        )

    @staticmethod
    def calculate_metrics(
        results: Sequence[EvaluationResult],
        reproducibility_rate: float = 1.0,
    ) -> EvaluationMetrics:
        """
        Calculate aggregate deterministic evaluation metrics.
        """
        if not isinstance(results, Sequence):
            raise TypeError("results must be a sequence")

        if not 0 <= reproducibility_rate <= 1:
            raise ValueError(
                "reproducibility_rate must be between 0 and 1"
            )

        total = len(results)

        if total == 0:
            return EvaluationMetrics(
                total_cases=0,
                valid_cases=0,
                bounded_cases=0,
                mean_base_consequence=0.0,
                mean_adjusted_consequence=0.0,
                mean_context_index=0.0,
                adjustment_rate=0.0,
                reproducibility_rate=(
                    reproducibility_rate
                ),
            )

        bounded = sum(
            result.within_bounds
            for result in results
        )

        adjusted = sum(
            result.adjusted_consequence_score
            != result.base_consequence_score
            for result in results
        )

        mean_base = sum(
            result.base_consequence_score
            for result in results
        ) / total

        mean_adjusted = sum(
            result.adjusted_consequence_score
            for result in results
        ) / total

        mean_context = sum(
            result.context_index
            for result in results
        ) / total

        return EvaluationMetrics(
            total_cases=total,
            valid_cases=total,
            bounded_cases=bounded,
            mean_base_consequence=round(
                mean_base,
                4,
            ),
            mean_adjusted_consequence=round(
                mean_adjusted,
                4,
            ),
            mean_context_index=round(
                mean_context,
                4,
            ),
            adjustment_rate=round(
                adjusted / total,
                4,
            ),
            reproducibility_rate=round(
                reproducibility_rate,
                4,
            ),
        )

    @staticmethod
    def compare_results(
        first: Sequence[EvaluationResult],
        second: Sequence[EvaluationResult],
    ) -> bool:
        """
        Determine whether two evaluation runs are identical.
        """
        return tuple(first) == tuple(second)

    def evaluate_reproducibility(
        self,
        cases: Sequence[EvaluationCase],
        baseline: str = BASELINE_FULL_VARYNX_BCSE,
    ) -> tuple[
        tuple[EvaluationResult, ...],
        tuple[EvaluationResult, ...],
        float,
    ]:
        """
        Execute the same evaluation twice and calculate
        deterministic reproducibility.
        """
        first = self.evaluate(
            cases,
            baseline,
        )

        second = self.evaluate(
            cases,
            baseline,
        )

        reproducible = (
            self.compare_results(
                first,
                second,
            )
        )

        return (
            first,
            second,
            1.0 if reproducible else 0.0,
        )