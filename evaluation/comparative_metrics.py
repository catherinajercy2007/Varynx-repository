from dataclasses import dataclass
from typing import List

from evaluation.scenario_runner import ScenarioResult


@dataclass
class ComparativeMetrics:
    total: int
    passed: int
    failed: int
    pass_rate: float
    allow_count: int
    deny_count: int
    high_risk_count: int
    critical_risk_count: int


def calculate_metrics(results: List[ScenarioResult]) -> ComparativeMetrics:
    """
    Calculate aggregate security evaluation metrics from scenario results.
    """

    total = len(results)

    passed = sum(
        result.passed
        for result in results
    )

    failed = total - passed

    allow_count = sum(
        result.decision.upper() == "ALLOW"
        for result in results
    )

    deny_count = sum(
        result.decision.upper() == "DENY"
        for result in results
    )

    high_risk_count = sum(
        result.risk_level.upper() == "HIGH"
        for result in results
    )

    critical_risk_count = sum(
        result.risk_level.upper() == "CRITICAL"
        for result in results
    )

    pass_rate = (
        (passed / total) * 100
        if total
        else 0.0
    )

    return ComparativeMetrics(
        total=total,
        passed=passed,
        failed=failed,
        pass_rate=pass_rate,
        allow_count=allow_count,
        deny_count=deny_count,
        high_risk_count=high_risk_count,
        critical_risk_count=critical_risk_count,
    )


def compare_with_baseline(
    metrics: ComparativeMetrics,
    baseline_pass_rate: float = 100.0,
) -> dict:
    """
    Compare measured evaluation performance against a baseline pass rate.
    """

    difference = metrics.pass_rate - baseline_pass_rate

    return {
        "measured_pass_rate": metrics.pass_rate,
        "baseline_pass_rate": baseline_pass_rate,
        "difference": difference,
        "meets_baseline": metrics.pass_rate >= baseline_pass_rate,
    }


def security_distribution(metrics: ComparativeMetrics) -> dict:
    """
    Return the distribution of ALLOW and DENY decisions.
    """

    total = metrics.total

    if total == 0:
        return {
            "allow_percentage": 0.0,
            "deny_percentage": 0.0,
        }

    return {
        "allow_percentage": (
            metrics.allow_count / total
        ) * 100,
        "deny_percentage": (
            metrics.deny_count / total
        ) * 100,
    }