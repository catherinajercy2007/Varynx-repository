"""
Varynx Day 77 - Reproducible Experiment Harness

Purpose
-------
Provides a deterministic, read-only harness for executing research
experiments with controlled seeds and repeated executions.

Research principle
------------------
Different seeds are allowed to produce different experimental outcomes.

Reproducibility is established when, for each seed, repeated executions
under the same experiment configuration produce the same output.

This module does not modify Varynx security decisions, execute enforcement,
infer malicious intent, or create a universal security score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Any, Callable, Mapping, Sequence


HARNESS_VERSION = "DAY77-V2"

RUN_STATUS_SUCCESS = "SUCCESS"
RUN_STATUS_FAILED = "FAILED"

REPRODUCIBILITY_REPRODUCIBLE = "REPRODUCIBLE"
REPRODUCIBILITY_NON_REPRODUCIBLE = "NON_REPRODUCIBLE"


def _validate_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")

    return value


def _validate_positive_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")

    if value <= 0:
        raise ValueError(f"{field_name} must be greater than zero")

    return value


def _canonicalize(value: Any) -> Any:
    """
    Convert supported Python values into deterministic JSON-compatible
    structures.

    Dictionaries are sorted by key representation.
    Sets are sorted by canonical representation.
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

        items.sort(key=lambda item: item[0])

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
        canonical_items = [
            _canonicalize(item)
            for item in value
        ]

        canonical_items.sort(
            key=lambda item: json.dumps(
                item,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            )
        )

        return canonical_items

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if hasattr(value, "__dict__"):
        return _canonicalize(vars(value))

    return repr(value)


def canonical_json(value: Any) -> str:
    """
    Return a deterministic JSON representation of a value.
    """

    canonical_value = _canonicalize(value)

    return json.dumps(
        canonical_value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def fingerprint(value: Any) -> str:
    """
    Return a SHA-256 fingerprint of a canonicalized value.
    """

    canonical = canonical_json(value)

    return sha256(
        canonical.encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class ExperimentConfig:
    """
    Immutable experiment configuration.

    repetitions
        Number of distinct experiment seeds.

    seeds
        Optional explicit seed sequence.

    If seeds are omitted, deterministic seeds are generated from
    experiment_id and repetition index.
    """

    experiment_id: str
    scenario: str
    repetitions: int
    seeds: tuple[int, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _validate_text(
            self.experiment_id,
            "experiment_id",
        )

        _validate_text(
            self.scenario,
            "scenario",
        )

        _validate_positive_int(
            self.repetitions,
            "repetitions",
        )

        normalized_seeds = tuple(self.seeds)

        for index, seed in enumerate(normalized_seeds):
            if isinstance(seed, bool) or not isinstance(seed, int):
                raise TypeError(
                    f"seeds[{index}] must be an integer"
                )

        if normalized_seeds:
            if len(normalized_seeds) != self.repetitions:
                raise ValueError(
                    "Number of explicit seeds must equal repetitions"
                )

        object.__setattr__(
            self,
            "seeds",
            normalized_seeds,
        )


@dataclass(frozen=True)
class ExperimentRun:
    """
    Immutable record for one execution.

    repeat_index identifies which repeated execution was performed
    for the corresponding seed.

    repeat_index is zero-based.
    """

    run_index: int
    seed: int
    repeat_index: int
    status: str
    output: Any
    output_fingerprint: str


@dataclass(frozen=True)
class ReproducibilityReport:
    """
    Immutable research reproducibility report.
    """

    experiment_id: str
    scenario: str
    repetitions: int
    seeds: tuple[int, ...]
    runs: tuple[ExperimentRun, ...]
    reproducibility: str
    configuration_fingerprint: str
    output_fingerprints: tuple[str, ...]
    evidence: Mapping[str, Any]


def _generate_seeds(
    experiment_id: str,
    repetitions: int,
) -> tuple[int, ...]:
    """
    Generate deterministic seeds.

    The generated sequence depends only on experiment_id and the
    repetition index.
    """

    seeds: list[int] = []

    for index in range(repetitions):
        material = f"{experiment_id}|{index}"

        digest = sha256(
            material.encode("utf-8")
        ).hexdigest()

        # Keep the generated seed within a practical positive integer range.
        seed = int(digest[:16], 16)

        seeds.append(seed)

    return tuple(seeds)


ExperimentFunction = Callable[[int], Any]


class ReproducibleExperimentHarness:
    """
    Deterministic experiment execution harness.

    For every configured seed, the experiment is executed twice.

    Example:

        seed 101 -> execution A
        seed 101 -> execution B

        seed 202 -> execution A
        seed 202 -> execution B

    Reproducibility is established by comparing the corresponding
    outputs for each seed.

    This intentionally does NOT require:

        output(seed=101) == output(seed=202)

    because different seeds may legitimately produce different
    experimental outcomes.
    """

    def resolve_seeds(
        self,
        config: ExperimentConfig,
    ) -> tuple[int, ...]:
        """
        Resolve explicit or deterministic seeds.
        """

        if config.seeds:
            return config.seeds

        return _generate_seeds(
            config.experiment_id,
            config.repetitions,
        )

    def run(
        self,
        config: ExperimentConfig,
        experiment: ExperimentFunction,
    ) -> ReproducibilityReport:
        """
        Execute the configured experiment twice for every seed.

        The returned report preserves every execution, including failures.
        """

        if not isinstance(
            config,
            ExperimentConfig,
        ):
            raise TypeError(
                "config must be an ExperimentConfig"
            )

        if not callable(experiment):
            raise TypeError(
                "experiment must be callable"
            )

        seeds = self.resolve_seeds(config)

        runs: list[ExperimentRun] = []

        run_index = 0

        for seed in seeds:
            for repeat_index in range(2):
                try:
                    output = experiment(seed)

                    status = RUN_STATUS_SUCCESS

                    output_fp = fingerprint(output)

                except Exception as exc:
                    output = {
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    }

                    status = RUN_STATUS_FAILED

                    output_fp = fingerprint(output)

                runs.append(
                    ExperimentRun(
                        run_index=run_index,
                        seed=seed,
                        repeat_index=repeat_index,
                        status=status,
                        output=output,
                        output_fingerprint=output_fp,
                    )
                )

                run_index += 1

        configuration_payload = {
            "harness_version": HARNESS_VERSION,
            "experiment_id": config.experiment_id,
            "scenario": config.scenario,
            "repetitions": config.repetitions,
            "seeds": list(seeds),
            "repeat_executions_per_seed": 2,
        }

        configuration_fingerprint = fingerprint(
            configuration_payload
        )

        output_fingerprints = tuple(
            run.output_fingerprint
            for run in runs
        )

        successful_runs = [
            run
            for run in runs
            if run.status == RUN_STATUS_SUCCESS
        ]

        failed_runs = [
            run
            for run in runs
            if run.status == RUN_STATUS_FAILED
        ]

        reproducible = (
            len(failed_runs) == 0
            and len(successful_runs) == len(runs)
            and self._seed_outputs_are_repeatable(
                runs
            )
        )

        reproducibility = (
            REPRODUCIBILITY_REPRODUCIBLE
            if reproducible
            else REPRODUCIBILITY_NON_REPRODUCIBLE
        )

        outputs_identical = (
            len(set(output_fingerprints)) <= 1
            if output_fingerprints
            else True
        )

        evidence = {
            "harness_version": HARNESS_VERSION,
            "seed_count": len(seeds),
            "repeat_executions_per_seed": 2,
            "total_runs": len(runs),
            "successful_runs": len(successful_runs),
            "failed_runs": len(failed_runs),
            "outputs_identical": outputs_identical,
            "seed_level_repeatability": reproducible,
            "read_only": True,
            "security_decision_modified": False,
            "enforcement_executed": False,
            "malicious_intent_inferred": False,
        }

        return ReproducibilityReport(
            experiment_id=config.experiment_id,
            scenario=config.scenario,
            repetitions=config.repetitions,
            seeds=seeds,
            runs=tuple(runs),
            reproducibility=reproducibility,
            configuration_fingerprint=configuration_fingerprint,
            output_fingerprints=output_fingerprints,
            evidence=evidence,
        )

    @staticmethod
    def _seed_outputs_are_repeatable(
        runs: Sequence[ExperimentRun],
    ) -> bool:
        """
        Verify that every seed produced the same output in both
        repeated executions.
        """

        grouped: dict[int, list[ExperimentRun]] = {}

        for run in runs:
            grouped.setdefault(
                run.seed,
                [],
            ).append(run)

        if not grouped:
            return False

        for seed, seed_runs in grouped.items():
            if len(seed_runs) != 2:
                return False

            first = seed_runs[0]
            second = seed_runs[1]

            if first.status != RUN_STATUS_SUCCESS:
                return False

            if second.status != RUN_STATUS_SUCCESS:
                return False

            if (
                first.output_fingerprint
                != second.output_fingerprint
            ):
                return False

        return True


def experiment_harness_is_deterministic() -> bool:
    """
    The harness itself uses deterministic seed generation and
    deterministic fingerprinting.
    """

    return True


def experiment_harness_is_read_only() -> bool:
    """
    The harness does not modify Varynx security state.
    """

    return True


def security_decision_is_modified_here() -> bool:
    """
    Day77 does not modify security decisions.
    """

    return False


def enforcement_is_executed_here() -> bool:
    """
    Day77 does not execute runtime enforcement.
    """

    return False


def malicious_intent_is_inferred_here() -> bool:
    """
    Day77 does not infer malicious intent.
    """

    return False


def creates_universal_security_score() -> bool:
    """
    Day77 does not create a universal security score.
    """

    return False