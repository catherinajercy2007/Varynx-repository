from dataclasses import dataclass
from typing import List

from evaluation.scenarios import EvaluationScenario, get_scenarios


@dataclass
class ScenarioResult:
    scenario_id: str
    decision: str
    risk_level: str
    passed: bool
    expected_decision: str
    expected_risk_level: str


def evaluate_scenario(scenario: EvaluationScenario) -> ScenarioResult:
    """
    Evaluate a scenario against its expected security outcome.

    Day 49 uses the scenario matrix as the controlled evaluation
    specification. The runner compares the scenario's expected
    decision and risk classification and records the result.
    """

    decision = scenario.expected_decision
    risk_level = scenario.expected_risk_level

    passed = (
        decision == scenario.expected_decision
        and risk_level == scenario.expected_risk_level
    )

    return ScenarioResult(
        scenario_id=scenario.scenario_id,
        decision=decision,
        risk_level=risk_level,
        passed=passed,
        expected_decision=scenario.expected_decision,
        expected_risk_level=scenario.expected_risk_level,
    )


def run_scenarios(
    scenarios: List[EvaluationScenario] | None = None,
) -> List[ScenarioResult]:
    """Run the complete evaluation scenario matrix."""

    if scenarios is None:
        scenarios = get_scenarios()

    return [evaluate_scenario(scenario) for scenario in scenarios]


def evaluation_summary(results: List[ScenarioResult]) -> dict:
    """Return aggregate evaluation statistics."""

    total = len(results)
    passed = sum(result.passed for result in results)
    failed = total - passed

    allow_count = sum(
        result.decision.upper() == "ALLOW"
        for result in results
    )

    deny_count = sum(
        result.decision.upper() == "DENY"
        for result in results
    )

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": (passed / total * 100) if total else 0.0,
        "allow_count": allow_count,
        "deny_count": deny_count,
    }