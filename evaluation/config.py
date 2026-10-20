"""
Day 46 - Experimental Evaluation Configuration

This module defines the experimental conditions that Member 3
will use to evaluate the incremental contribution of Varynx
components.

Important:
These are evaluation definitions only.
They do NOT implement Dynamic Behavioral Trust or BCSE.
"""

from dataclasses import dataclass


BASELINES = (
    "policy_only",
    "risk",
    "risk_behavior",
    "risk_behavior_trust",
    "full_varynx_bcse",
)


@dataclass(frozen=True)
class ExperimentConfig:
    """
    Configuration for one controlled experiment.

    Attributes:
        name: Name of the experiment.
        baseline: Experimental condition being evaluated.
        seed: Reproducibility seed.
        threshold: Decision threshold used by the experiment.
        dataset_version: Version/name of the evaluation dataset.
    """

    name: str
    baseline: str
    seed: int = 42
    threshold: float = 0.5
    dataset_version: str = "day46-initial"

    def __post_init__(self) -> None:
        if self.baseline not in BASELINES:
            raise ValueError(
                f"Unknown baseline '{self.baseline}'. "
                f"Expected one of: {BASELINES}"
            )

        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError(
                "threshold must be between 0.0 and 1.0"
            )

        if self.seed < 0:
            raise ValueError(
                "seed must be a non-negative integer"
            )