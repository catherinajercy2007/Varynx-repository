"""
Varynx BCSE Integration
Day 55: BCSE Integration with Varynx.

Pipeline:
    Day 51 -> Counterfactual Scenario
    Day 52 -> Security Consequence Estimation
    Day 53 -> Context-Aware Consequence Modeling

Day 55 is an orchestration layer only.

It does NOT:
- execute hypothetical actions
- infer malicious intent
- make authorization decisions
- block agents
- modify adaptive response
- modify the existing Varynx risk engine
"""

from dataclasses import dataclass
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Tuple,
)

from app.bcse_scenario import (
    BehavioralContext,
    CounterfactualChange,
    CounterfactualScenario,
    CounterfactualScenarioBuilder,
)

from app.bcse_consequence import (
    ConsequenceEstimate,
    SecurityConsequenceEstimator,
)

from app.bcse_context import (
    ContextAwareConsequenceEstimate,
    ContextAwareConsequenceModel,
)


BASELINE_NAME = "FULL_VARYNX_BCSE"
EVALUATION_VERSION = "day55-v1"


@dataclass(frozen=True)
class BCSEIntegrationResult:
    """
    Immutable combined result from the Day 51-53 BCSE pipeline.
    """

    agent_id: str
    scenario: CounterfactualScenario
    consequence: ConsequenceEstimate
    context_aware: ContextAwareConsequenceEstimate
    baseline: str
    evaluation_version: str
    evidence: Tuple[str, ...]
    assumptions: Tuple[str, ...]


class VarynxBCSEIntegration:
    """
    Day 55 BCSE orchestration layer.

    The class connects:

        Day 51
            Counterfactual Scenario
                 |
                 v
        Day 52
            Security Consequence
                 |
                 v
        Day 53
            Context-Aware Consequence
                 |
                 v
        Day 55
            Integrated Result

    Existing Day 51-53 implementations remain authoritative.
    """

    BASELINE_NAME = BASELINE_NAME
    EVALUATION_VERSION = EVALUATION_VERSION

    def __init__(self) -> None:
        self._scenario_builder = CounterfactualScenarioBuilder()
        self._consequence_estimator = SecurityConsequenceEstimator()
        self._context_model = ContextAwareConsequenceModel()

        self._history: List[BCSEIntegrationResult] = []

    # ================================================================
    # Validation helpers
    # ================================================================

    @staticmethod
    def _validate_agent_id(agent_id: str) -> None:
        if not isinstance(agent_id, str):
            raise TypeError("agent_id must be a string")

        if not agent_id.strip():
            raise ValueError("agent_id must not be empty")

    @staticmethod
    def _validate_context(
        context: BehavioralContext,
        name: str,
    ) -> None:
        if not isinstance(context, BehavioralContext):
            raise TypeError(
                f"{name} must be a BehavioralContext"
            )

    @staticmethod
    def _validate_mapping(
        value: Mapping[str, Any],
        name: str,
    ) -> None:
        if not isinstance(value, Mapping):
            raise TypeError(
                f"{name} must be a mapping"
            )

    @staticmethod
    def _copy_text_list(
        values: Optional[Iterable[str]],
        name: str,
    ) -> List[str]:
        if values is None:
            return []

        if isinstance(values, (str, bytes)):
            raise TypeError(
                f"{name} must be an iterable of strings"
            )

        result: List[str] = []

        for value in values:
            if not isinstance(value, str):
                raise TypeError(
                    f"Every item in {name} must be a string"
                )

            value = value.strip()

            if value:
                result.append(value)

        return result

    @staticmethod
    def _validate_changes(
        changes: Iterable[CounterfactualChange],
    ) -> None:
        if changes is None:
            raise TypeError("changes must not be None")

        if isinstance(changes, (str, bytes)):
            raise TypeError(
                "changes must be an iterable of CounterfactualChange"
            )

        for change in changes:
            if not isinstance(change, CounterfactualChange):
                raise TypeError(
                    "Every item in changes must be a "
                    "CounterfactualChange"
                )

    # ================================================================
    # Day 51
    # ================================================================

    def create_scenario(
        self,
        *,
        agent_id: str,
        current_context: BehavioralContext,
        hypothetical_context: BehavioralContext,
        changes: Iterable[CounterfactualChange],
        evidence: Optional[Iterable[str]] = None,
        assumptions: Optional[Iterable[str]] = None,
    ) -> CounterfactualScenario:
        """
        Create an explicit Day 51 counterfactual scenario.

        The hypothetical context is supplied explicitly.
        Day 55 does not invent or calculate it.
        """

        self._validate_agent_id(agent_id)

        self._validate_context(
            current_context,
            "current_context",
        )

        self._validate_context(
            hypothetical_context,
            "hypothetical_context",
        )

        self._validate_changes(changes)

        evidence_list = self._copy_text_list(
            evidence,
            "evidence",
        )

        assumptions_list = self._copy_text_list(
            assumptions,
            "assumptions",
        )

        return self._scenario_builder.create_scenario(
            agent_id=agent_id,
            current_context=current_context,
            hypothetical_context=hypothetical_context,
            changes=list(changes),
            evidence=evidence_list,
            assumptions=assumptions_list,
        )

    # ================================================================
    # Complete Day 51-53 pipeline
    # ================================================================

    def evaluate(
        self,
        *,
        agent_id: str,
        current_context: BehavioralContext,
        hypothetical_context: BehavioralContext,
        changes: Iterable[CounterfactualChange],
        consequence_dimensions: Mapping[str, float],
        security_context: Mapping[str, float],
        evidence: Optional[Iterable[str]] = None,
        assumptions: Optional[Iterable[str]] = None,
    ) -> BCSEIntegrationResult:
        """
        Execute the complete Day 51-53 BCSE pipeline.

        Day 51:
            Builds the counterfactual scenario.

        Day 52:
            Estimates security consequence.

        Day 53:
            Applies context-aware consequence modeling.

        IMPORTANT:
        The actual Day 53 API accepts:

            scenario_id
            consequence_score
            context

        It does NOT accept an evidence keyword.

        Therefore evidence is preserved by Day 55 itself rather than
        being incorrectly passed into Day 53.
        """

        # ------------------------------------------------------------
        # Validate inputs
        # ------------------------------------------------------------

        self._validate_agent_id(agent_id)

        self._validate_context(
            current_context,
            "current_context",
        )

        self._validate_context(
            hypothetical_context,
            "hypothetical_context",
        )

        self._validate_changes(changes)

        self._validate_mapping(
            consequence_dimensions,
            "consequence_dimensions",
        )

        self._validate_mapping(
            security_context,
            "security_context",
        )

        evidence_list = self._copy_text_list(
            evidence,
            "evidence",
        )

        assumptions_list = self._copy_text_list(
            assumptions,
            "assumptions",
        )

        changes_list = list(changes)

        # ------------------------------------------------------------
        # Day 51: Counterfactual Scenario
        # ------------------------------------------------------------

        scenario = self.create_scenario(
            agent_id=agent_id,
            current_context=current_context,
            hypothetical_context=hypothetical_context,
            changes=changes_list,
            evidence=evidence_list,
            assumptions=assumptions_list,
        )

        # ------------------------------------------------------------
        # Day 52: Security Consequence Estimation
        # ------------------------------------------------------------

        consequence = self._consequence_estimator.estimate(
            scenario_id=scenario.scenario_id,
            dimensions=dict(consequence_dimensions),
            evidence=evidence_list,
            assumptions=assumptions_list,
        )

        # ------------------------------------------------------------
        # Day 53: Context-Aware Consequence Modeling
        #
        # ACTUAL Day 53 interface:
        #
        #     scenario_id
        #     consequence_score
        #     context
        #
        # Do NOT pass evidence here.
        # ------------------------------------------------------------

        context_aware = self._context_model.estimate(
            scenario_id=scenario.scenario_id,
            consequence_score=consequence.consequence_score,
            context=dict(security_context),
        )

        # ------------------------------------------------------------
        # Evidence preservation
        # ------------------------------------------------------------

        combined_evidence: List[str] = []

        def add_unique(items: Iterable[str]) -> None:
            for item in items:
                if item not in combined_evidence:
                    combined_evidence.append(item)

        add_unique(evidence_list)

        scenario_evidence = getattr(
            scenario,
            "evidence",
            (),
        )
        add_unique(scenario_evidence)

        consequence_evidence = getattr(
            consequence,
            "evidence",
            (),
        )
        add_unique(consequence_evidence)

        context_evidence = getattr(
            context_aware,
            "evidence",
            (),
        )
        add_unique(context_evidence)

        # ------------------------------------------------------------
        # Assumption preservation
        # ------------------------------------------------------------

        combined_assumptions: List[str] = []

        def add_unique_assumption(items: Iterable[str]) -> None:
            for item in items:
                if item not in combined_assumptions:
                    combined_assumptions.append(item)

        add_unique_assumption(assumptions_list)

        scenario_assumptions = getattr(
            scenario,
            "assumptions",
            (),
        )
        add_unique_assumption(scenario_assumptions)

        consequence_assumptions = getattr(
            consequence,
            "assumptions",
            (),
        )
        add_unique_assumption(consequence_assumptions)

        context_assumptions = getattr(
            context_aware,
            "assumptions",
            (),
        )
        add_unique_assumption(context_assumptions)

        # ------------------------------------------------------------
        # Final integrated result
        # ------------------------------------------------------------

        result = BCSEIntegrationResult(
            agent_id=agent_id,
            scenario=scenario,
            consequence=consequence,
            context_aware=context_aware,
            baseline=self.BASELINE_NAME,
            evaluation_version=self.EVALUATION_VERSION,
            evidence=tuple(combined_evidence),
            assumptions=tuple(combined_assumptions),
        )

        self._history.append(result)

        return result

    # ================================================================
    # History management
    # ================================================================

    def history(self) -> Tuple[BCSEIntegrationResult, ...]:
        """
        Return immutable integration history.
        """

        return tuple(self._history)

    def latest(self) -> Optional[BCSEIntegrationResult]:
        """
        Return the latest integration result.
        """

        if not self._history:
            return None

        return self._history[-1]

    def history_count(self) -> int:
        """
        Return number of stored integration results.
        """

        return len(self._history)

    def reset(self) -> None:
        """
        Clear only Day 55 integration history.
        """

        self._history.clear()


__all__ = [
    "BASELINE_NAME",
    "EVALUATION_VERSION",
    "BCSEIntegrationResult",
    "VarynxBCSEIntegration",
]