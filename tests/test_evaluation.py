import pandas as pd
import pytest

from app.evaluation import (
    calculate_metrics,
    baseline_predict,
    aegisguard_predict,
    evaluate_detector,
    compare_detectors,
    build_threshold_sweep,
    build_baseline_sweep,
    build_aegisguard_sweep,
    get_best_threshold,
    get_confusion_matrix,
    generate_comparison_summary,
)


# ============================================================
# TEST DATA
# ============================================================

SAMPLE_DATASET = [
    {
        "event_id": "E001",
        "decision": "ALLOW",
        "risk_score": 10,
        "ground_truth": "BENIGN",
    },
    {
        "event_id": "E002",
        "decision": "DENY",
        "risk_score": 90,
        "ground_truth": "MALICIOUS",
    },
    {
        "event_id": "E003",
        "decision": "ALLOW",
        "risk_score": 85,
        "ground_truth": "MALICIOUS",
    },
    {
        "event_id": "E004",
        "decision": "ALLOW",
        "risk_score": 20,
        "ground_truth": "BENIGN",
    },
    {
        "event_id": "E005",
        "decision": "DENY",
        "risk_score": 80,
        "ground_truth": "SUSPICIOUS",
    },
]


# ============================================================
# METRIC TESTS
# ============================================================

def test_calculate_metrics_perfect_classifier():

    actual = [
        True,
        True,
        False,
        False,
    ]

    predicted = [
        True,
        True,
        False,
        False,
    ]

    metrics = calculate_metrics(
        actual,
        predicted,
    )

    assert metrics["TP"] == 2
    assert metrics["TN"] == 2
    assert metrics["FP"] == 0
    assert metrics["FN"] == 0

    assert metrics["Accuracy"] == 1.0
    assert metrics["Precision"] == 1.0
    assert metrics["Recall"] == 1.0
    assert metrics["F1"] == 1.0
    assert metrics["Specificity"] == 1.0


def test_calculate_metrics_known_values():

    actual = [
        True,
        True,
        False,
        False,
    ]

    predicted = [
        True,
        False,
        True,
        False,
    ]

    metrics = calculate_metrics(
        actual,
        predicted,
    )

    assert metrics["TP"] == 1
    assert metrics["TN"] == 1
    assert metrics["FP"] == 1
    assert metrics["FN"] == 1

    assert metrics["Accuracy"] == 0.5
    assert metrics["Precision"] == 0.5
    assert metrics["Recall"] == 0.5
    assert metrics["F1"] == 0.5
    assert metrics["Specificity"] == 0.5
    assert metrics["FPR"] == 0.5
    assert metrics["FNR"] == 0.5


def test_calculate_metrics_length_mismatch():

    with pytest.raises(ValueError):

        calculate_metrics(
            [True, False],
            [True],
        )


def test_empty_metrics():

    metrics = calculate_metrics(
        [],
        [],
    )

    assert metrics["TP"] == 0
    assert metrics["TN"] == 0
    assert metrics["FP"] == 0
    assert metrics["FN"] == 0

    assert metrics["Accuracy"] == 0.0
    assert metrics["Precision"] == 0.0
    assert metrics["Recall"] == 0.0
    assert metrics["F1"] == 0.0


# ============================================================
# DETECTOR TESTS
# ============================================================

def test_baseline_detects_deny():

    event = {
        "decision": "DENY",
        "risk_score": 10,
    }

    assert (
        baseline_predict(
            event,
            baseline_threshold=70,
        )
        is True
    )


def test_baseline_detects_high_risk():

    event = {
        "decision": "ALLOW",
        "risk_score": 90,
    }

    assert (
        baseline_predict(
            event,
            baseline_threshold=70,
        )
        is True
    )


def test_baseline_allows_low_risk_allow():

    event = {
        "decision": "ALLOW",
        "risk_score": 20,
    }

    assert (
        baseline_predict(
            event,
            baseline_threshold=70,
        )
        is False
    )


def test_aegisguard_detects_deny():

    event = {
        "decision": "DENY",
        "risk_score": 10,
    }

    assert (
        aegisguard_predict(
            event,
            risk_threshold=70,
        )
        is True
    )


def test_aegisguard_detects_high_risk():

    event = {
        "decision": "ALLOW",
        "risk_score": 95,
    }

    assert (
        aegisguard_predict(
            event,
            risk_threshold=70,
        )
        is True
    )


def test_aegisguard_rejects_low_risk_allow():

    event = {
        "decision": "ALLOW",
        "risk_score": 20,
    }

    assert (
        aegisguard_predict(
            event,
            risk_threshold=70,
        )
        is False
    )


# ============================================================
# DATASET EVALUATION
# ============================================================

def test_evaluate_detector():

    metrics = evaluate_detector(
        SAMPLE_DATASET,
        lambda event:
            event["risk_score"] >= 70,
    )

    assert metrics["TP"] == 2
    assert metrics["TN"] == 2
    assert metrics["FP"] == 1
    assert metrics["FN"] == 0

    assert metrics["Accuracy"] == pytest.approx(
        4 / 5
    )


# ============================================================
# COMPARISON TEST
# ============================================================

def test_compare_detectors():

    baseline, aegisguard, comparison = (
        compare_detectors(
            SAMPLE_DATASET,
            baseline_threshold=70,
            aegisguard_threshold=70,
        )
    )

    assert isinstance(
        baseline,
        dict,
    )

    assert isinstance(
        aegisguard,
        dict,
    )

    assert isinstance(
        comparison,
        pd.DataFrame,
    )

    assert list(
        comparison["Metric"]
    ) == [
        "Accuracy",
        "Precision",
        "Recall",
        "F1",
        "Specificity",
        "FPR",
        "FNR",
    ]


# ============================================================
# THRESHOLD SWEEP
# ============================================================

def test_threshold_sweep():

    thresholds = [
        0,
        50,
        70,
        100,
    ]

    result = build_threshold_sweep(
        SAMPLE_DATASET,
        thresholds,
        detector_type="baseline",
    )

    assert isinstance(
        result,
        pd.DataFrame,
    )

    assert len(result) == 4

    assert list(
        result["Threshold"]
    ) == [
        0.0,
        50.0,
        70.0,
        100.0,
    ]


def test_baseline_sweep():

    result = build_baseline_sweep(
        SAMPLE_DATASET,
        [50, 70, 90],
    )

    assert len(result) == 3

    assert "F1" in result.columns
    assert "Recall" in result.columns


def test_aegisguard_sweep():

    result = build_aegisguard_sweep(
        SAMPLE_DATASET,
        [50, 70, 90],
    )

    assert len(result) == 3

    assert "F1" in result.columns
    assert "Precision" in result.columns


def test_invalid_detector_type():

    with pytest.raises(ValueError):

        build_threshold_sweep(
            SAMPLE_DATASET,
            [50, 70],
            detector_type="unknown",
        )


# ============================================================
# BEST THRESHOLD
# ============================================================

def test_get_best_threshold():

    sweep = pd.DataFrame(
        {
            "Threshold": [
                50,
                70,
                90,
            ],

            "F1": [
                0.60,
                0.90,
                0.70,
            ],
        }
    )

    result = get_best_threshold(
        sweep,
        metric="F1",
    )

    assert result["Threshold"] == 70
    assert result["F1"] == pytest.approx(
        0.90
    )


def test_get_best_threshold_empty():

    empty_df = pd.DataFrame(
        columns=[
            "Threshold",
            "F1",
        ]
    )

    with pytest.raises(ValueError):

        get_best_threshold(
            empty_df
        )


# ============================================================
# CONFUSION MATRIX
# ============================================================

def test_get_confusion_matrix():

    metrics = {
        "TP": 10,
        "TN": 20,
        "FP": 3,
        "FN": 2,
    }

    matrix = get_confusion_matrix(
        metrics
    )

    assert isinstance(
        matrix,
        pd.DataFrame,
    )

    assert matrix.loc[
        "Actual Non-Malicious",
        "Predicted Non-Malicious",
    ] == 20

    assert matrix.loc[
        "Actual Non-Malicious",
        "Predicted Malicious",
    ] == 3

    assert matrix.loc[
        "Actual Malicious",
        "Predicted Non-Malicious",
    ] == 2

    assert matrix.loc[
        "Actual Malicious",
        "Predicted Malicious",
    ] == 10


# ============================================================
# RESEARCH SUMMARY
# ============================================================

def test_comparison_summary_higher_f1():

    baseline = {
        "Precision": 0.70,
        "Recall": 0.60,
        "F1": 0.65,
    }

    aegisguard = {
        "Precision": 0.80,
        "Recall": 0.70,
        "F1": 0.75,
    }

    result = generate_comparison_summary(
        baseline,
        aegisguard,
    )

    assert (
        result["outcome"]
        == "AEGISGUARD_HIGHER_F1"
    )

    assert result[
        "f1_difference"
    ] == pytest.approx(
        0.10
    )


def test_comparison_summary_lower_f1():

    baseline = {
        "Precision": 0.80,
        "Recall": 0.80,
        "F1": 0.80,
    }

    aegisguard = {
        "Precision": 0.60,
        "Recall": 0.60,
        "F1": 0.60,
    }

    result = generate_comparison_summary(
        baseline,
        aegisguard,
    )

    assert (
        result["outcome"]
        == "BASELINE_HIGHER_F1"
    )


def test_comparison_summary_equal_f1():

    baseline = {
        "Precision": 0.70,
        "Recall": 0.70,
        "F1": 0.70,
    }

    aegisguard = {
        "Precision": 0.70,
        "Recall": 0.70,
        "F1": 0.70,
    }

    result = generate_comparison_summary(
        baseline,
        aegisguard,
    )

    assert (
        result["outcome"]
        == "EQUAL_F1"
    )