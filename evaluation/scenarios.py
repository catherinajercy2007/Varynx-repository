"""
Day 48 - Evaluation Scenarios

Defines deterministic scenarios used to evaluate the Aegis agent
security and authorization behavior.
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class EvaluationScenario:
    """Represents one evaluation scenario."""

    scenario_id: str
    name: str
    description: str
    agent_id: str
    action: str
    resource: str
    expected_decision: str
    expected_risk_level: str


SCENARIOS: List[EvaluationScenario] = [
    EvaluationScenario(
        scenario_id="S01",
        name="Normal authorized request",
        description="A trusted agent performs an authorized read operation.",
        agent_id="agent_001",
        action="read",
        resource="public_data",
        expected_decision="ALLOW",
        expected_risk_level="LOW",
    ),
    EvaluationScenario(
        scenario_id="S02",
        name="Unauthorized resource access",
        description="An agent attempts to access a restricted resource.",
        agent_id="agent_001",
        action="read",
        resource="restricted_data",
        expected_decision="DENY",
        expected_risk_level="HIGH",
    ),
    EvaluationScenario(
        scenario_id="S03",
        name="Invalid agent request",
        description="An unknown agent attempts to perform an operation.",
        agent_id="unknown_agent",
        action="read",
        resource="public_data",
        expected_decision="DENY",
        expected_risk_level="HIGH",
    ),
    EvaluationScenario(
        scenario_id="S04",
        name="Unauthorized action",
        description="A trusted agent attempts an action outside its permissions.",
        agent_id="agent_001",
        action="delete",
        resource="public_data",
        expected_decision="DENY",
        expected_risk_level="HIGH",
    ),
    EvaluationScenario(
        scenario_id="S05",
        name="Privilege escalation attempt",
        description="An agent attempts to perform a privileged operation.",
        agent_id="agent_002",
        action="grant_admin",
        resource="system",
        expected_decision="DENY",
        expected_risk_level="CRITICAL",
    ),
    EvaluationScenario(
        scenario_id="S06",
        name="Repeated suspicious requests",
        description="Repeated requests indicate potentially abusive behavior.",
        agent_id="agent_002",
        action="read",
        resource="restricted_data",
        expected_decision="DENY",
        expected_risk_level="HIGH",
    ),
    EvaluationScenario(
        scenario_id="S07",
        name="Destructive operation",
        description="An agent attempts a destructive system operation.",
        agent_id="agent_002",
        action="delete_system",
        resource="system",
        expected_decision="DENY",
        expected_risk_level="CRITICAL",
    ),
    EvaluationScenario(
        scenario_id="S08",
        name="Normal write request",
        description="A trusted agent performs an authorized write operation.",
        agent_id="agent_001",
        action="write",
        resource="agent_data",
        expected_decision="ALLOW",
        expected_risk_level="LOW",
    ),
]


def get_scenarios() -> List[EvaluationScenario]:
    """Return all evaluation scenarios."""
    return list(SCENARIOS)


def get_scenario(scenario_id: str) -> EvaluationScenario:
    """Return a scenario by ID.

    Raises:
        ValueError: If the scenario ID does not exist.
    """
    for scenario in SCENARIOS:
        if scenario.scenario_id == scenario_id:
            return scenario

    raise ValueError(f"Unknown scenario: {scenario_id}")


def get_scenarios_by_decision(decision: str) -> List[EvaluationScenario]:
    """Return scenarios grouped by expected decision."""
    decision = decision.upper()

    return [
        scenario
        for scenario in SCENARIOS
        if scenario.expected_decision.upper() == decision
    ]


def get_scenarios_by_risk(risk_level: str) -> List[EvaluationScenario]:
    """Return scenarios grouped by expected risk level."""
    risk_level = risk_level.upper()

    return [
        scenario
        for scenario in SCENARIOS
        if scenario.expected_risk_level.upper() == risk_level
    ]


def scenario_summary() -> dict:
    """Return a summary of the evaluation scenario set."""

    scenarios = get_scenarios()

    return {
        "total_scenarios": len(scenarios),
        "allow_cases": len(get_scenarios_by_decision("ALLOW")),
        "deny_cases": len(get_scenarios_by_decision("DENY")),
        "low_risk_cases": len(get_scenarios_by_risk("LOW")),
        "high_risk_cases": len(get_scenarios_by_risk("HIGH")),
        "critical_risk_cases": len(get_scenarios_by_risk("CRITICAL")),
    }
