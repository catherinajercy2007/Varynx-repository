"""
Varynx Day 78 - Repeated Experiment Evaluation

Purpose
-------
Provides a deterministic, read-only research layer for aggregating
multiple controlled experiment executions.

Day 77 establishes reproducibility for repeated executions of the
same seed.

Day 78 evaluates the aggregate outcomes produced across multiple
controlled seeds.

Research boundary
-----------------
This module performs descriptive aggregation only.

It does not:
- modify security decisions
- execute enforcement
- infer malicious intent
- modify behavioral trust
- modify BCSE
- create a universal security score
- claim statistical significance
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Mapping, Sequence


DAY78_VERSION = "DAY78-V1"

OUTCOME_SUCCESS = "SUCCESS"
OUTCOME_FAILED = "FAILED"

AGGREGATION_COMPLETE = "COMPLETE"
AGGREGATION_PARTIAL = "PARTIAL"
AGGREGATION_FAILED = "FAILED"


def _validate_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")

    return value


def _validate_positive_int(
    value: int,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f"{field_name} must be an integer"
        )

    if value <= 0:
        raise ValueError(
            f"{field_name} must be greater than zero"
        )

    return value


def _validate_number(
    value: float,
    field_name: str,
) -> float:
    if isinstance(value, bool):
        raise TypeError(
            f"{field_name} must be numeric"
        )

    if not isinstance(value, (int, float)):
        raise TypeError(
            f"{field_name} must be numeric"
        )

    numeric = float(value)

    if not isfinite(numeric):
        raise ValueError(
            f"{field_name} must be finite"
        )

    return numeric


def _canonicalize(value: Any) -> Any:
    """
    Convert supported values into deterministic JSON-compatible
    structures.
    """

    if isinstance(value, Mapping):
        items = []

        for key, item in value.items():
            canonical_key = str(key)

            items.append(
                (
                    canonical_key,
                    _canonicalize(item),
                )
            )

        items.sort(
            key=lambda item: item[0]
        )

        return {
            key: item
            for key, item in items
        }

    if isinstance(value, (list, tuple)):
        return [
            _canonicalize(item)
            for item in value
        ]

    if isinstance(value, set):
        items = [
            _canonicalize(item)
            for item in value
        ]

        items.sort(
            key=lambda item: json.dumps(
                item,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            )
        )

        return items

    if value is None:
        return None

    if isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    if hasattr(value, "__dict__"):
        return _canonicalize(
            vars(value)
        )

    return repr(value)


def canonical_json(value: Any) -> str:
    """
    Produce deterministic JSON.
    """

    return json.dumps(
        _canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def fingerprint(value: Any) -> str:
    """
    Produce a deterministic SHA-256 fingerprint.
    """

    return sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class RepeatedExperimentConfig:
    """
    Configuration for repeated experiment evaluation.

    seeds
        Independent controlled experiment seeds.

    minimum_successful_runs
        Minimum number of successful runs required for a complete
        aggregation.
    """

    experiment_id: str
    scenario: str
    seeds: tuple[int, ...]
    minimum_successful_runs: int = 1

    def __post_init__(self) -> None:
        _validate_text(
            self.experiment_id,
            "experiment_id",
        )

        _validate_text(
            self.scenario,
            "scenario",
        )

        if not self.seeds:
            raise ValueError(
                "seeds must contain at least one seed"
            )

        normalized_seeds = tuple(self.seeds)

        for index, seed in enumerate(
            normalized_seeds
        ):
            if (
                isinstance(seed, bool)
                or not isinstance(seed, int)
            ):
                raise TypeError(
                    f"seeds[{index}] must be an integer"
                )

        _validate_positive_int(
            self.minimum_successful_runs,
            "minimum_successful_runs",
        )

        if (
            self.minimum_successful_runs
            > len(normalized_seeds)
        ):
            raise ValueError(
                "minimum_successful_runs cannot exceed "
                "the number of seeds"
            )

        object.__setattr__(
            self,
            "seeds",
            normalized_seeds,
        )


@dataclass(frozen=True)
class ExperimentOutcome:
    """
    One controlled experiment outcome.
    """

    seed: int
    status: str
    output: Any
    output_fingerprint: str


@dataclass(frozen=True)
class NumericSummary:
    """
    Descriptive summary for a numeric metric.
    """

    metric_name: str
    count: int
    minimum: float
    maximum: float
    mean: float
    total: float


@dataclass(frozen=True)
class RepeatedExperimentReport:
    """
    Immutable Day78 evaluation report.
    """

    experiment_id: str
    scenario: str
    seeds: tuple[int, ...]
    outcomes: tuple[ExperimentOutcome, ...]
    successful_runs: int
    failed_runs: int
    aggregation_status: str
    configuration_fingerprint: str
    outcome_fingerprints: tuple[str, ...]
    numeric_summaries: tuple[NumericSummary, ...]
    evidence: Mapping[str, Any]


ExperimentFunction = Any


class RepeatedExperimentEvaluator:
    """
    Read-only evaluator for controlled repeated experiments.

    Each configured seed is executed exactly once.

    Day 77 is responsible for same-seed repeatability.

    Day 78 is responsible for aggregate evaluation across
    independently controlled seeds.
    """

    def run(
        self,
        config: RepeatedExperimentConfig,
        experiment: ExperimentFunction,
    ) -> RepeatedExperimentReport:
        """
        Execute the experiment once for every configured seed.
        """

        if not isinstance(
            config,
            RepeatedExperimentConfig,
        ):
            raise TypeError(
                "config must be a "
                "RepeatedExperimentConfig"
            )

        if not callable(experiment):
            raise TypeError(
                "experiment must be callable"
            )

        outcomes: list[ExperimentOutcome] = []

        for seed in config.seeds:
            try:
                output = experiment(seed)

                status = OUTCOME_SUCCESS

            except Exception as exc:
                output = {
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }

                status = OUTCOME_FAILED

            outcomes.append(
                ExperimentOutcome(
                    seed=seed,
                    status=status,
                    output=output,
                    output_fingerprint=fingerprint(
                        output
                    ),
                )
            )

        successful = [
            outcome
            for outcome in outcomes
            if outcome.status == OUTCOME_SUCCESS
        ]

        failed = [
            outcome
            for outcome in outcomes
            if outcome.status == OUTCOME_FAILED
        ]

        successful_count = len(successful)
        failed_count = len(failed)

        if successful_count == 0:
            aggregation_status = (
                AGGREGATION_FAILED
            )

        elif (
            successful_count
            >= config.minimum_successful_runs
            and failed_count == 0
        ):
            aggregation_status = (
                AGGREGATION_COMPLETE
            )

        else:
            aggregation_status = (
                AGGREGATION_PARTIAL
            )

        configuration_payload = {
            "day78_version": DAY78_VERSION,
            "experiment_id": config.experiment_id,
            "scenario": config.scenario,
            "seeds": list(config.seeds),
            "minimum_successful_runs": (
                config.minimum_successful_runs
            ),
        }

        configuration_fingerprint = fingerprint(
            configuration_payload
        )

        outcome_fingerprints = tuple(
            outcome.output_fingerprint
            for outcome in outcomes
        )

        numeric_summaries = (
            self._summarize_numeric_metrics(
                successful
            )
        )

        evidence = {
            "day78_version": DAY78_VERSION,
            "seed_count": len(config.seeds),
            "successful_runs": successful_count,
            "failed_runs": failed_count,
            "aggregation_status": (
                aggregation_status
            ),
            "read_only": True,
            "security_decision_modified": False,
            "enforcement_executed": False,
            "malicious_intent_inferred": False,
            "universal_security_score_created": False,
            "statistical_significance_claimed": False,
        }

        return RepeatedExperimentReport(
            experiment_id=config.experiment_id,
            scenario=config.scenario,
            seeds=config.seeds,
            outcomes=tuple(outcomes),
            successful_runs=successful_count,
            failed_runs=failed_count,
            aggregation_status=aggregation_status,
            configuration_fingerprint=(
                configuration_fingerprint
            ),
            outcome_fingerprints=(
                outcome_fingerprints
            ),
            numeric_summaries=(
                numeric_summaries
            ),
            evidence=evidence,
        )

    @staticmethod
    def _summarize_numeric_metrics(
        outcomes: Sequence[ExperimentOutcome],
    ) -> tuple[NumericSummary, ...]:
        """
        Aggregate numeric metrics that appear consistently across
        successful mapping outputs.

        Only top-level numeric fields are summarized.

        This is descriptive aggregation, not statistical inference.
        """

        metric_values: dict[str, list[float]] = {}

        for outcome in outcomes:
            if not isinstance(
                outcome.output,
                Mapping,
            ):
                continue

            for key, value in outcome.output.items():
                if isinstance(value, bool):
                    continue

                if not isinstance(
                    value,
                    (int, float),
                ):
                    continue

                numeric = _validate_number(
                    value,
                    f"metric:{key}",
                )

                metric_values.setdefault(
                    str(key),
                    [],
                ).append(numeric)

        summaries: list[NumericSummary] = []

        for metric_name in sorted(
            metric_values
        ):
            values = metric_values[
                metric_name
            ]

            total = sum(values)

            mean = (
                total / len(values)
                if values
                else 0.0
            )

            summaries.append(
                NumericSummary(
                    metric_name=metric_name,
                    count=len(values),
                    minimum=min(values),
                    maximum=max(values),
                    mean=mean,
                    total=total,
                )
            )

        return tuple(summaries)


def repeated_evaluation_is_read_only() -> bool:
    """
    Day78 only evaluates experiment outcomes.
    """

    return True


def security_decision_is_modified_here() -> bool:
    """
    Day78 does not modify security decisions.
    """

    return False


def enforcement_is_executed_here() -> bool:
    """
    Day78 does not execute enforcement.
    """

    return False


def malicious_intent_is_inferred_here() -> bool:
    """
    Day78 does not infer malicious intent.
    """

    return False


def universal_security_score_is_created() -> bool:
    """
    Day78 does not create a universal security score.
    """

    return False


def statistical_significance_is_claimed_here() -> bool:
    """
    Day78 provides descriptive aggregation only.

    Formal statistical significance belongs to a later
    statistical-validation stage.
    """

    return False