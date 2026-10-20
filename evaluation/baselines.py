"""
Day 46 - Varynx Experimental Baselines

These definitions describe experimental conditions.

They are NOT separate security engines.
They allow research experiments to identify the
incremental contribution of each Varynx capability.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class BaselineDefinition:
    """Description of one experimental condition."""

    name: str
    description: str
    components: Tuple[str, ...]


def get_baselines() -> Tuple[BaselineDefinition, ...]:
    """
    Return the controlled baseline ladder for Varynx evaluation.
    """

    return (
        BaselineDefinition(
            name="policy_only",
            description="Static authorization / policy-only control.",
            components=(
                "policy",
                "authorization",
            ),
        ),
        BaselineDefinition(
            name="risk",
            description="Risk-based security control.",
            components=(
                "policy",
                "authorization",
                "risk",
            ),
        ),
        BaselineDefinition(
            name="risk_behavior",
            description="Risk control combined with behavioral analysis.",
            components=(
                "policy",
                "authorization",
                "risk",
                "behavior",
            ),
        ),
        BaselineDefinition(
            name="risk_behavior_trust",
            description=(
                "Risk and behavioral analysis combined with "
                "dynamic behavioral trust."
            ),
            components=(
                "policy",
                "authorization",
                "risk",
                "behavior",
                "dynamic_trust",
            ),
        ),
        BaselineDefinition(
            name="full_varynx_bcse",
            description=(
                "Risk, behavior, dynamic trust, BCSE, "
                "and adaptive runtime response."
            ),
            components=(
                "policy",
                "authorization",
                "risk",
                "behavior",
                "dynamic_trust",
                "bcse",
                "adaptive_response",
            ),
        ),
    )


def get_baseline(name: str) -> BaselineDefinition:
    """Return a baseline by name."""

    for baseline in get_baselines():
        if baseline.name == name:
            return baseline

    valid_names = [baseline.name for baseline in get_baselines()]

    raise ValueError(
        f"Unknown baseline '{name}'. "
        f"Expected one of: {valid_names}"
    )