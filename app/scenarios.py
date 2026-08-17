from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
import random


# ============================================================
# SCENARIO TYPES
# ============================================================

BENIGN = "BENIGN"
SUSPICIOUS = "SUSPICIOUS"
MALICIOUS = "MALICIOUS"


SCENARIO_TYPES = [
    BENIGN,
    SUSPICIOUS,
    MALICIOUS,
]


# ============================================================
# SECURITY SCENARIO
# ============================================================

@dataclass(frozen=True)
class SecurityScenario:
    scenario_id: str
    scenario_type: str
    agent_id: str
    task_id: str
    action: str
    resource: str
    description: str
    expected_behavior: str


# ============================================================
# CONTROLLED SCENARIO CATALOG
# ============================================================

SCENARIO_CATALOG = [
    SecurityScenario(
        scenario_id="BENIGN-001",
        scenario_type=BENIGN,
        agent_id="customer-support-agent",
        task_id="support-ticket",
        action="s3:GetObject",
        resource="public/support-faq.csv",
        description=(
            "Agent accesses a permitted public support dataset."
        ),
        expected_behavior="ALLOW",
    ),

    SecurityScenario(
        scenario_id="BENIGN-002",
        scenario_type=BENIGN,
        agent_id="data-analysis-agent",
        task_id="sales-analysis",
        action="s3:GetObject",
        resource="public/sales.csv",
        description=(
            "Agent reads an authorized public sales dataset."
        ),
        expected_behavior="ALLOW",
    ),

    SecurityScenario(
        scenario_id="BENIGN-003",
        scenario_type=BENIGN,
        agent_id="reporting-agent",
        task_id="report-generation",
        action="s3:GetObject",
        resource="public/reports.csv",
        description=(
            "Agent reads a permitted reporting resource."
        ),
        expected_behavior="ALLOW",
    ),

    SecurityScenario(
        scenario_id="SUSPICIOUS-001",
        scenario_type=SUSPICIOUS,
        agent_id="data-analysis-agent",
        task_id="sales-analysis",
        action="s3:GetObject",
        resource="private/customer.csv",
        description=(
            "Agent attempts to access a resource outside "
            "its normal behavioral profile."
        ),
        expected_behavior="DENY",
    ),

    SecurityScenario(
        scenario_id="SUSPICIOUS-002",
        scenario_type=SUSPICIOUS,
        agent_id="reporting-agent",
        task_id="report-generation",
        action="s3:DeleteObject",
        resource="public/reports.csv",
        description=(
            "Reporting agent attempts a destructive action."
        ),
        expected_behavior="DENY",
    ),

    SecurityScenario(
        scenario_id="SUSPICIOUS-003",
        scenario_type=SUSPICIOUS,
        agent_id="unknown-agent",
        task_id="unknown-task",
        action="s3:GetObject",
        resource="public/sales.csv",
        description=(
            "Unknown agent attempts resource access."
        ),
        expected_behavior="DENY",
    ),

    SecurityScenario(
        scenario_id="MALICIOUS-001",
        scenario_type=MALICIOUS,
        agent_id="compromised-agent",
        task_id="privilege-escalation",
        action="iam:CreateUser",
        resource="public/users",
        description=(
            "Agent attempts unauthorized identity "
            "and privilege manipulation."
        ),
        expected_behavior="DENY",
    ),

    SecurityScenario(
        scenario_id="MALICIOUS-002",
        scenario_type=MALICIOUS,
        agent_id="compromised-agent",
        task_id="data-exfiltration",
        action="s3:GetObject",
        resource="private/customer.csv",
        description=(
            "Agent attempts access to sensitive customer data."
        ),
        expected_behavior="DENY",
    ),

    SecurityScenario(
        scenario_id="MALICIOUS-003",
        scenario_type=MALICIOUS,
        agent_id="../admin",
        task_id="privilege-escalation",
        action="iam:CreateUser",
        resource="admin/users",
        description=(
            "Controlled path-traversal-like agent identifier "
            "combined with a privileged action."
        ),
        expected_behavior="DENY",
    ),
]


# ============================================================
# CATALOG ACCESS
# ============================================================

def get_scenario_catalog() -> list[dict[str, Any]]:
    return [
        asdict(
            scenario
        )
        for scenario in SCENARIO_CATALOG
    ]


# ============================================================
# FILTER SCENARIOS
# ============================================================

def get_scenarios(
    scenario_type: str | None = None,
) -> list[dict[str, Any]]:

    scenarios = SCENARIO_CATALOG

    if scenario_type is not None:

        scenario_type = (
            scenario_type.upper()
        )

        scenarios = [
            scenario
            for scenario in scenarios
            if scenario.scenario_type
            == scenario_type
        ]

    return [
        asdict(
            scenario
        )
        for scenario in scenarios
    ]


# ============================================================
# SINGLE SCENARIO
# ============================================================

def get_scenario(
    scenario_id: str,
) -> dict[str, Any] | None:

    for scenario in SCENARIO_CATALOG:

        if scenario.scenario_id == scenario_id:

            return asdict(
                scenario
            )

    return None


# ============================================================
# SCENARIO COUNTS
# ============================================================

def get_scenario_summary() -> dict[str, int]:

    return {
        "total": len(
            SCENARIO_CATALOG
        ),
        "benign": sum(
            scenario.scenario_type
            == BENIGN
            for scenario
            in SCENARIO_CATALOG
        ),
        "suspicious": sum(
            scenario.scenario_type
            == SUSPICIOUS
            for scenario
            in SCENARIO_CATALOG
        ),
        "malicious": sum(
            scenario.scenario_type
            == MALICIOUS
            for scenario
            in SCENARIO_CATALOG
        ),
    }


# ============================================================
# REPRODUCIBLE SCENARIO SAMPLING
# ============================================================

def sample_scenarios(
    count: int = 10,
    seed: int = 42,
) -> list[dict[str, Any]]:

    if count < 1:

        raise ValueError(
            "count must be greater than zero"
        )

    rng = random.Random(
        seed
    )

    scenarios = list(
        SCENARIO_CATALOG
    )

    if count >= len(scenarios):

        selected = scenarios

    else:

        selected = rng.sample(
            scenarios,
            count,
        )

    return [
        asdict(
            scenario
        )
        for scenario
        in selected
    ]