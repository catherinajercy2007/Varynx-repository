from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
import random


# ============================================================
# DAY 22 — ATTACK SCENARIO TYPES
# ============================================================

ATTACK_UNAUTHORIZED_RESOURCE = (
    "UNAUTHORIZED_RESOURCE_ACCESS"
)

ATTACK_REPEATED_DENIAL = (
    "REPEATED_AUTHORIZATION_DENIAL"
)

ATTACK_PRIVILEGE_EXPANSION = (
    "PRIVILEGE_EXPANSION"
)

ATTACK_HIGH_RISK_BURST = (
    "HIGH_RISK_BURST"
)

ATTACK_RESOURCE_ENUMERATION = (
    "RESOURCE_ENUMERATION"
)

ATTACK_BEHAVIORAL_DRIFT = (
    "BEHAVIORAL_DRIFT"
)

ATTACK_LEGITIMATE_HIGH_ACTIVITY = (
    "LEGITIMATE_HIGH_ACTIVITY"
)

ATTACK_MIXED_SEQUENCE = (
    "MIXED_ATTACK_SEQUENCE"
)


ATTACK_SCENARIO_TYPES = [
    ATTACK_UNAUTHORIZED_RESOURCE,
    ATTACK_REPEATED_DENIAL,
    ATTACK_PRIVILEGE_EXPANSION,
    ATTACK_HIGH_RISK_BURST,
    ATTACK_RESOURCE_ENUMERATION,
    ATTACK_BEHAVIORAL_DRIFT,
    ATTACK_LEGITIMATE_HIGH_ACTIVITY,
    ATTACK_MIXED_SEQUENCE,
]


# ============================================================
# DATA MODEL
# ============================================================

@dataclass(frozen=True)
class AttackScenario:

    scenario_id: str
    scenario_type: str
    name: str
    agent_id: str
    task_id: str
    actions: tuple[str, ...]
    resources: tuple[str, ...]
    severity: str
    ground_truth: str
    expected_signal: str
    description: str
    evaluation_purpose: str


# ============================================================
# CONTROLLED ATTACK SCENARIO CATALOG
# ============================================================

ATTACK_SCENARIOS = [

    AttackScenario(
        scenario_id="ATTACK-001",
        scenario_type=ATTACK_UNAUTHORIZED_RESOURCE,
        name="Unauthorized Resource Access",
        agent_id="data-analysis-agent",
        task_id="sales-analysis",
        actions=(
            "s3:GetObject",
        ),
        resources=(
            "private/customer.csv",
        ),
        severity="HIGH",
        ground_truth="MALICIOUS",
        expected_signal="authorization_violation",
        description=(
            "An otherwise legitimate analytical agent "
            "attempts to access a resource outside its "
            "authorized scope."
        ),
        evaluation_purpose=(
            "Evaluate detection of direct resource "
            "authorization violations."
        ),
    ),

    AttackScenario(
        scenario_id="ATTACK-002",
        scenario_type=ATTACK_REPEATED_DENIAL,
        name="Repeated Authorization Denial",
        agent_id="unknown-agent",
        task_id="unknown-task",
        actions=(
            "s3:GetObject",
        ),
        resources=(
            "public/sales.csv",
        ),
        severity="MEDIUM",
        ground_truth="MALICIOUS",
        expected_signal="repeated_denial_pattern",
        description=(
            "An agent repeatedly attempts an operation "
            "that is denied by the authorization layer."
        ),
        evaluation_purpose=(
            "Evaluate behavioral detection of repeated "
            "authorization abuse."
        ),
    ),

    AttackScenario(
        scenario_id="ATTACK-003",
        scenario_type=ATTACK_PRIVILEGE_EXPANSION,
        name="Privilege Expansion Attempt",
        agent_id="compromised-agent",
        task_id="privilege-escalation",
        actions=(
            "iam:CreateUser",
            "iam:AttachRolePolicy",
        ),
        resources=(
            "admin/users",
            "admin/roles",
        ),
        severity="CRITICAL",
        ground_truth="MALICIOUS",
        expected_signal="privilege_escalation",
        description=(
            "An agent attempts operations associated with "
            "expanding its effective privileges."
        ),
        evaluation_purpose=(
            "Evaluate detection of high-impact privilege "
            "manipulation behavior."
        ),
    ),

    AttackScenario(
        scenario_id="ATTACK-004",
        scenario_type=ATTACK_HIGH_RISK_BURST,
        name="High-Risk Request Burst",
        agent_id="burst-risk-agent",
        task_id="rapid-operation-sequence",
        actions=(
            "s3:DeleteObject",
            "iam:CreateUser",
            "s3:GetObject",
            "iam:AttachRolePolicy",
        ),
        resources=(
            "private/customer.csv",
            "admin/users",
            "private/credentials.csv",
            "admin/roles",
        ),
        severity="CRITICAL",
        ground_truth="MALICIOUS",
        expected_signal="high_risk_burst",
        description=(
            "Multiple high-risk operations occur within "
            "a short controlled activity window."
        ),
        evaluation_purpose=(
            "Evaluate whether temporal concentration of "
            "high-risk actions increases detection confidence."
        ),
    ),

    AttackScenario(
        scenario_id="ATTACK-005",
        scenario_type=ATTACK_RESOURCE_ENUMERATION,
        name="Resource Enumeration",
        agent_id="enumeration-agent",
        task_id="resource-discovery",
        actions=(
            "s3:ListBucket",
            "s3:GetObject",
            "s3:GetObject",
            "s3:GetObject",
        ),
        resources=(
            "public/",
            "private/",
            "admin/",
            "restricted/",
        ),
        severity="HIGH",
        ground_truth="MALICIOUS",
        expected_signal="resource_enumeration",
        description=(
            "An agent systematically probes multiple "
            "resource locations in a controlled sequence."
        ),
        evaluation_purpose=(
            "Evaluate detection of broad resource discovery "
            "behavior."
        ),
    ),

    AttackScenario(
        scenario_id="ATTACK-006",
        scenario_type=ATTACK_BEHAVIORAL_DRIFT,
        name="Behavioral Drift",
        agent_id="normally-benign-agent",
        task_id="routine-analysis",
        actions=(
            "s3:GetObject",
            "s3:GetObject",
            "s3:DeleteObject",
            "iam:CreateUser",
        ),
        resources=(
            "public/sales.csv",
            "public/reports.csv",
            "public/reports.csv",
            "admin/users",
        ),
        severity="HIGH",
        ground_truth="MALICIOUS",
        expected_signal="behavioral_deviation",
        description=(
            "An agent begins with expected behavior and "
            "then transitions into actions inconsistent "
            "with its established behavioral profile."
        ),
        evaluation_purpose=(
            "Evaluate detection of deviations from an "
            "established behavioral baseline."
        ),
    ),

    AttackScenario(
        scenario_id="ATTACK-007",
        scenario_type=ATTACK_LEGITIMATE_HIGH_ACTIVITY,
        name="Legitimate High Activity",
        agent_id="batch-processing-agent",
        task_id="scheduled-batch",
        actions=(
            "s3:GetObject",
            "s3:GetObject",
            "s3:GetObject",
            "s3:GetObject",
        ),
        resources=(
            "public/sales.csv",
            "public/reports.csv",
            "public/support.csv",
            "public/analytics.csv",
        ),
        severity="LOW",
        ground_truth="BENIGN",
        expected_signal="high_volume_benign",
        description=(
            "A trusted batch-processing agent generates "
            "high activity while remaining within its "
            "authorized resource scope."
        ),
        evaluation_purpose=(
            "Evaluate whether high activity alone causes "
            "false-positive classifications."
        ),
    ),

    AttackScenario(
        scenario_id="ATTACK-008",
        scenario_type=ATTACK_MIXED_SEQUENCE,
        name="Mixed Multi-Step Attack Sequence",
        agent_id="compromised-agent",
        task_id="multi-stage-operation",
        actions=(
            "s3:ListBucket",
            "s3:GetObject",
            "iam:CreateUser",
            "s3:GetObject",
            "s3:DeleteObject",
        ),
        resources=(
            "public/",
            "private/customer.csv",
            "admin/users",
            "private/credentials.csv",
            "private/customer.csv",
        ),
        severity="CRITICAL",
        ground_truth="MALICIOUS",
        expected_signal="multi_stage_attack",
        description=(
            "A controlled sequence combines discovery, "
            "sensitive access, privilege manipulation and "
            "destructive behavior."
        ),
        evaluation_purpose=(
            "Evaluate detection of multi-stage behavioral "
            "attack sequences."
        ),
    ),
]


# ============================================================
# BASIC ACCESS
# ============================================================

def get_attack_scenarios() -> list[dict[str, Any]]:

    return [
        asdict(
            scenario
        )
        for scenario in ATTACK_SCENARIOS
    ]


def get_attack_scenario(
    scenario_id: str,
) -> dict[str, Any] | None:

    for scenario in ATTACK_SCENARIOS:

        if scenario.scenario_id == scenario_id:

            return asdict(
                scenario
            )

    return None


# ============================================================
# FILTERING
# ============================================================

def get_attack_scenarios_by_type(
    scenario_type: str,
) -> list[dict[str, Any]]:

    normalized = (
        scenario_type.upper()
    )

    return [
        asdict(
            scenario
        )
        for scenario
        in ATTACK_SCENARIOS
        if scenario.scenario_type
        == normalized
    ]


def get_attack_scenarios_by_severity(
    severity: str,
) -> list[dict[str, Any]]:

    normalized = (
        severity.upper()
    )

    return [
        asdict(
            scenario
        )
        for scenario
        in ATTACK_SCENARIOS
        if scenario.severity
        == normalized
    ]


# ============================================================
# SUMMARY
# ============================================================

def get_attack_scenario_summary() -> dict[str, Any]:

    total = len(
        ATTACK_SCENARIOS
    )

    malicious = sum(
        scenario.ground_truth
        == "MALICIOUS"
        for scenario
        in ATTACK_SCENARIOS
    )

    benign = sum(
        scenario.ground_truth
        == "BENIGN"
        for scenario
        in ATTACK_SCENARIOS
    )

    critical = sum(
        scenario.severity
        == "CRITICAL"
        for scenario
        in ATTACK_SCENARIOS
    )

    high = sum(
        scenario.severity
        == "HIGH"
        for scenario
        in ATTACK_SCENARIOS
    )

    medium = sum(
        scenario.severity
        == "MEDIUM"
        for scenario
        in ATTACK_SCENARIOS
    )

    low = sum(
        scenario.severity
        == "LOW"
        for scenario
        in ATTACK_SCENARIOS
    )

    return {
        "total": total,
        "malicious": malicious,
        "benign": benign,
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,
    }


# ============================================================
# REPRODUCIBLE SAMPLING
# ============================================================

def sample_attack_scenarios(
    count: int = 8,
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
        ATTACK_SCENARIOS
    )

    if count >= len(
        scenarios
    ):

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