"""
Day 46 - Member 3 Evaluation Tests
"""

import sys
from pathlib import Path


# Allow imports from:
# member3-research-evaluation/evaluation/
EVALUATION_DIR = (
    Path(__file__).resolve().parents[1] / "evaluation"
)

sys.path.insert(0, str(EVALUATION_DIR))


from baselines import get_baseline, get_baselines
from config import BASELINES, ExperimentConfig
from metrics import binary_metrics


def test_baseline_ladder_contains_five_conditions():
    baselines = get_baselines()

    assert len(baselines) == 5

    names = [baseline.name for baseline in baselines]

    assert names == list(BASELINES)


def test_policy_only_baseline():
    baseline = get_baseline("policy_only")

    assert baseline.components == (
        "policy",
        "authorization",
    )


def test_dynamic_trust_is_an_experimental_condition():
    baseline = get_baseline("risk_behavior_trust")

    assert "dynamic_trust" in baseline.components
    assert "bcse" not in baseline.components


def test_full_varynx_contains_bcse():
    baseline = get_baseline("full_varynx_bcse")

    assert "dynamic_trust" in baseline.components
    assert "bcse" in baseline.components
    assert "adaptive_response" in baseline.components


def test_experiment_configuration():
    config = ExperimentConfig(
        name="baseline-comparison",
        baseline="risk_behavior",
        seed=42,
        threshold=0.5,
    )

    assert config.name == "baseline-comparison"
    assert config.baseline == "risk_behavior"
    assert config.seed == 42
    assert config.threshold == 0.5


def test_invalid_baseline_is_rejected():
    try:
        ExperimentConfig(
            name="invalid",
            baseline="unknown_baseline",
        )
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_invalid_threshold_is_rejected():
    try:
        ExperimentConfig(
            name="invalid-threshold",
            baseline="risk",
            threshold=1.5,
        )
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_binary_metrics():
    y_true = [1, 1, 0, 0]
    y_pred = [1, 0, 1, 0]

    metrics = binary_metrics(y_true, y_pred)

    assert metrics.true_positive == 1
    assert metrics.true_negative == 1
    assert metrics.false_positive == 1
    assert metrics.false_negative == 1

    assert metrics.accuracy == 0.5
    assert metrics.precision == 0.5
    assert metrics.recall == 0.5
    assert metrics.f1 == 0.5


def test_zero_denominator_metrics_are_safe():
    metrics = binary_metrics(
        [0, 0, 0],
        [0, 0, 0],
    )

    assert metrics.precision == 0.0
    assert metrics.recall == 0.0
    assert metrics.f1 == 0.0