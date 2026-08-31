"""
Varynx Day 35
Controlled Adversarial Evaluation Bridge

Purpose
-------
Connect controlled adversarial scenario metadata to the
existing adaptive-response engine.

This module does not claim that a scenario is detected.
It provides a reproducible way to evaluate a supplied
evidence vector against known ground truth.
"""

from __future__ import annotations

from typing import Any, Mapping

from app.adaptive_explainability import (
    evaluate_explainable_decision,
)

from app.adversarial_scenarios import (
    build_scenario_ground_truth,
    get_adversarial_scenario,
)


def evaluate_adversarial_scenario(
    scenario_id: str,
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Evaluate supplied evidence against a known adversarial
    scenario.

    Ground truth is kept separate from the model response.
    """

    scenario = get_adversarial_scenario(
        scenario_id
    )

    explanation = evaluate_explainable_decision(
        evidence
    )

    return {
        "scenario": build_scenario_ground_truth(
            scenario_id
        ),
        "evidence": dict(evidence),
        "decision": explanation,
        "ground_truth": scenario.ground_truth,
        "scenario_severity": scenario.severity,
    }


def build_evaluation_record(
    scenario_id: str,
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Build a flat record suitable for later quantitative
    evaluation.
    """

    result = evaluate_adversarial_scenario(
        scenario_id,
        evidence,
    )

    decision = result["decision"]["decision"]

    return {
        "scenario_id": scenario_id,
        "scenario_category": result["scenario"]["category"],
        "ground_truth": result["ground_truth"],
        "scenario_severity": result["scenario_severity"],
        "adaptive_action": decision["action"],
        "adaptive_severity": decision["severity"],
        "adaptive_score": decision["score"],
    }


__all__ = [
    "evaluate_adversarial_scenario",
    "build_evaluation_record",
]