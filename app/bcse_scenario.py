"""
Varynx Day 51
Behavioral Counterfactual Security Engine (BCSE)
Counterfactual Scenario Foundation.

This module constructs deterministic, bounded, explainable
counterfactual scenarios from observed behavioral intelligence.

The module does NOT:
- execute actions
- authorize actions
- block actions
- predict exact attacker behavior
- claim malicious intent
- modify runtime state
- trigger adaptive response

It only represents a hypothetical behavioral change so that
future BCSE components can estimate possible security consequences.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional


SCORE_MIN = 0.0
SCORE_MAX = 100.0


def _validate_score(
    value: float,
    field_name: str,
) -> float:
    """Validate a normalized score."""
    if not isinstance(value, (int, float)):
        raise TypeError(
            f"{field_name} must be numeric"
        )

    value = float(value)

    if value < SCORE_MIN or value > SCORE_MAX:
        raise ValueError(
            f"{field_name} must be between "
            f"{SCORE_MIN} and {SCORE_MAX}"
        )

    return value


def _validate_text(
    value: str,
    field_name: str,
) -> str:
    """Validate a required textual field."""
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string"
        )

    if not value.strip():
        raise ValueError(
            f"{field_name} must be non-empty"
        )

    return value


def _copy_mapping(
    values: Mapping[str, object],
    field_name: str,
) -> Dict[str, object]:
    """Return a defensive copy of a mapping."""
    if not isinstance(values, Mapping):
        raise TypeError(
            f"{field_name} must be a mapping"
        )

    return dict(values)


@dataclass(frozen=True)
class BehavioralContext:
    """
    Representation of the current behavioral/security context.
    """

    trust_score: float
    state_score: float
    deviation_score: float
    attributes: Dict[str, object] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "trust_score",
            _validate_score(
                self.trust_score,
                "trust_score",
            ),
        )

        object.__setattr__(
            self,
            "state_score",
            _validate_score(
                self.state_score,
                "state_score",
            ),
        )

        object.__setattr__(
            self,
            "deviation_score",
            _validate_score(
                self.deviation_score,
                "deviation_score",
            ),
        )

        object.__setattr__(
            self,
            "attributes",
            _copy_mapping(
                self.attributes,
                "attributes",
            ),
        )


@dataclass(frozen=True)
class CounterfactualChange:
    """
    Hypothetical behavioral change.

    This describes what would be different in the counterfactual
    scenario. It does not execute the change.
    """

    dimension: str
    current_value: object
    hypothetical_value: object
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "dimension",
            _validate_text(
                self.dimension,
                "dimension",
            ),
        )

        object.__setattr__(
            self,
            "reason",
            _validate_text(
                self.reason,
                "reason",
            ),
        )


@dataclass(frozen=True)
class CounterfactualScenario:
    """
    Immutable counterfactual scenario representation.
    """

    scenario_id: str
    agent_id: str

    current_context: BehavioralContext
    hypothetical_context: BehavioralContext

    changes: List[CounterfactualChange]

    evidence: List[str] = field(
        default_factory=list
    )

    assumptions: List[str] = field(
        default_factory=list
    )


class CounterfactualScenarioBuilder:
    """
    Deterministic builder for BCSE counterfactual scenarios.

    The builder creates hypothetical representations only.
    """

    def __init__(self) -> None:
        self._scenario_counts: Dict[str, int] = {}

    def create_scenario(
        self,
        agent_id: str,
        *,
        current_context: BehavioralContext,
        hypothetical_context: BehavioralContext,
        changes: List[CounterfactualChange],
        evidence: Optional[List[str]] = None,
        assumptions: Optional[List[str]] = None,
        scenario_id: Optional[str] = None,
    ) -> CounterfactualScenario:
        """
        Construct a counterfactual scenario.
        """
        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        if not isinstance(
            current_context,
            BehavioralContext,
        ):
            raise TypeError(
                "current_context must be BehavioralContext"
            )

        if not isinstance(
            hypothetical_context,
            BehavioralContext,
        ):
            raise TypeError(
                "hypothetical_context must be BehavioralContext"
            )

        if not isinstance(changes, list):
            raise TypeError(
                "changes must be a list"
            )

        if not all(
            isinstance(change, CounterfactualChange)
            for change in changes
        ):
            raise TypeError(
                "changes must contain CounterfactualChange objects"
            )

        if scenario_id is None:
            count = self._scenario_counts.get(
                agent_id,
                0,
            ) + 1

            self._scenario_counts[agent_id] = count

            scenario_id = (
                f"{agent_id}-cf-{count}"
            )
        else:
            scenario_id = _validate_text(
                scenario_id,
                "scenario_id",
            )

        return CounterfactualScenario(
            scenario_id=scenario_id,
            agent_id=agent_id,
            current_context=current_context,
            hypothetical_context=hypothetical_context,
            changes=list(changes),
            evidence=list(evidence or []),
            assumptions=list(assumptions or []),
        )

    @staticmethod
    def compare_contexts(
        current: BehavioralContext,
        hypothetical: BehavioralContext,
    ) -> Dict[str, float]:
        """
        Compare normalized behavioral/security context dimensions.

        The result is descriptive only.
        """
        if not isinstance(
            current,
            BehavioralContext,
        ):
            raise TypeError(
                "current must be BehavioralContext"
            )

        if not isinstance(
            hypothetical,
            BehavioralContext,
        ):
            raise TypeError(
                "hypothetical must be BehavioralContext"
            )

        return {
            "trust_delta": round(
                hypothetical.trust_score
                - current.trust_score,
                4,
            ),
            "state_delta": round(
                hypothetical.state_score
                - current.state_score,
                4,
            ),
            "deviation_delta": round(
                hypothetical.deviation_score
                - current.deviation_score,
                4,
            ),
        }

    @staticmethod
    def changed_dimensions(
        current: BehavioralContext,
        hypothetical: BehavioralContext,
    ) -> List[str]:
        """
        Return behavioral dimensions whose normalized values differ.
        """
        deltas = (
            CounterfactualScenarioBuilder.compare_contexts(
                current,
                hypothetical,
            )
        )

        return [
            name
            for name, value in deltas.items()
            if value != 0
        ]

    def history_count(
        self,
        agent_id: str,
    ) -> int:
        """Return the number of automatically generated scenarios."""
        return self._scenario_counts.get(
            agent_id,
            0,
        )