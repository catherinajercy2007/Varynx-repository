"""
AegisGuard Research Evaluation Engine

Day 25:
Baseline vs AegisGuard quantitative evaluation.

This module contains research/evaluation logic only.
It should not depend on Streamlit.
"""

from __future__ import annotations

from typing import Callable, Iterable, Mapping, Any

import pandas as pd


# ============================================================
# CONSTANTS
# ============================================================

MALICIOUS = "MALICIOUS"


# ============================================================
# BASIC HELPERS
# ============================================================

def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """Safely convert a value to float."""

    try:
        return float(value)

    except (TypeError, ValueError):
        return default


# ============================================================
# CLASSIFICATION METRICS
# ============================================================

def calculate_metrics(
    actual: Iterable[bool],
    predicted: Iterable[bool],
) -> dict[str, float | int]:
    """
    Calculate binary classification metrics.

    Positive class:
        True  -> MALICIOUS

    Negative class:
        False -> BENIGN / SUSPICIOUS

    Returns:
        TP, TN, FP, FN,
        Accuracy, Precision, Recall,
        F1, Specificity, FPR, FNR
    """

    actual_list = list(actual)
    predicted_list = list(predicted)

    if len(actual_list) != len(predicted_list):
        raise ValueError(
            "actual and predicted must contain "
            "the same number of observations."
        )

    tp = 0
    tn = 0
    fp = 0
    fn = 0

    for actual_value, predicted_value in zip(
        actual_list,
        predicted_list,
    ):

        actual_value = bool(actual_value)
        predicted_value = bool(predicted_value)

        if actual_value and predicted_value:
            tp += 1

        elif not actual_value and not predicted_value:
            tn += 1

        elif not actual_value and predicted_value:
            fp += 1

        elif actual_value and not predicted_value:
            fn += 1

    total = tp + tn + fp + fn

    accuracy = (
        (tp + tn) / total
        if total
        else 0.0
    )

    precision = (
        tp / (tp + fp)
        if tp + fp
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if tp + fn
        else 0.0
    )

    specificity = (
        tn / (tn + fp)
        if tn + fp
        else 0.0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if precision + recall
        else 0.0
    )

    false_positive_rate = (
        fp / (fp + tn)
        if fp + tn
        else 0.0
    )

    false_negative_rate = (
        fn / (fn + tp)
        if fn + tp
        else 0.0
    )

    return {
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
        "Specificity": specificity,
        "FPR": false_positive_rate,
        "FNR": false_negative_rate,
    }


# ============================================================
# BASELINE DETECTOR
# ============================================================

def baseline_predict(
    event: Mapping[str, Any],
    baseline_threshold: float = 70,
) -> bool:
    """
    Transparent baseline detector.

    Rule:

        DENY
        OR
        risk_score >= threshold

        => MALICIOUS
    """

    decision = str(
        event.get(
            "decision",
            "",
        )
    ).upper()

    risk_score = safe_float(
        event.get(
            "risk_score",
            0,
        )
    )

    return (
        decision == "DENY"
        or risk_score >= baseline_threshold
    )


# ============================================================
# AEGISGUARD DETECTOR
# ============================================================

def aegisguard_predict(
    event: Mapping[str, Any],
    risk_threshold: float = 70,
) -> bool:
    """
    Current experimental AegisGuard detector.

    Rule:

        DENY
        OR
        risk_score >= threshold

        => MALICIOUS

    Kept explicit for reproducibility.
    """

    decision = str(
        event.get(
            "decision",
            "",
        )
    ).upper()

    risk_score = safe_float(
        event.get(
            "risk_score",
            0,
        )
    )

    return (
        decision == "DENY"
        or risk_score >= risk_threshold
    )


# ============================================================
# DATASET EVALUATION
# ============================================================

def evaluate_detector(
    dataset: Iterable[Mapping[str, Any]],
    detector: Callable[
        [Mapping[str, Any]],
        bool,
    ],
) -> dict[str, float | int]:
    """
    Evaluate a detector against ground-truth labels.

    The dataset must contain:

        ground_truth

    with MALICIOUS representing the positive class.
    """

    actual = []
    predicted = []

    for event in dataset:

        ground_truth = str(
            event.get(
                "ground_truth",
                "",
            )
        ).upper()

        actual.append(
            ground_truth == MALICIOUS
        )

        predicted.append(
            bool(detector(event))
        )

    return calculate_metrics(
        actual,
        predicted,
    )


# ============================================================
# BASELINE VS AEGISGUARD
# ============================================================

def compare_detectors(
    dataset: Iterable[Mapping[str, Any]],
    baseline_threshold: float = 70,
    aegisguard_threshold: float = 70,
) -> tuple[
    dict[str, float | int],
    dict[str, float | int],
    pd.DataFrame,
]:
    """
    Compare baseline and AegisGuard detectors.

    Returns:

        baseline_metrics
        aegisguard_metrics
        comparison_dataframe
    """

    dataset_list = list(dataset)

    baseline_metrics = evaluate_detector(
        dataset_list,
        lambda event: baseline_predict(
            event,
            baseline_threshold,
        ),
    )

    aegisguard_metrics = evaluate_detector(
        dataset_list,
        lambda event: aegisguard_predict(
            event,
            aegisguard_threshold,
        ),
    )

    metric_names = [
        "Accuracy",
        "Precision",
        "Recall",
        "F1",
        "Specificity",
        "FPR",
        "FNR",
    ]

    rows = []

    for metric in metric_names:

        baseline_value = float(
            baseline_metrics[metric]
        )

        aegisguard_value = float(
            aegisguard_metrics[metric]
        )

        rows.append(
            {
                "Metric": metric,
                "Baseline": baseline_value,
                "AegisGuard": aegisguard_value,
                "Difference": (
                    aegisguard_value
                    - baseline_value
                ),
            }
        )

    comparison_df = pd.DataFrame(
        rows
    )

    return (
        baseline_metrics,
        aegisguard_metrics,
        comparison_df,
    )


# ============================================================
# THRESHOLD SWEEP
# ============================================================

def build_threshold_sweep(
    dataset: Iterable[Mapping[str, Any]],
    thresholds: Iterable[float],
    detector_type: str = "baseline",
) -> pd.DataFrame:
    """
    Evaluate a detector across multiple risk thresholds.

    detector_type:
        "baseline"
        "aegisguard"
    """

    dataset_list = list(dataset)

    detector_type = detector_type.lower()

    if detector_type not in {
        "baseline",
        "aegisguard",
    }:

        raise ValueError(
            "detector_type must be "
            "'baseline' or 'aegisguard'."
        )

    rows = []

    for threshold in thresholds:

        threshold = float(threshold)

        if detector_type == "baseline":

            metrics = evaluate_detector(
                dataset_list,
                lambda event,
                threshold=threshold:
                    baseline_predict(
                        event,
                        threshold,
                    ),
            )

        else:

            metrics = evaluate_detector(
                dataset_list,
                lambda event,
                threshold=threshold:
                    aegisguard_predict(
                        event,
                        threshold,
                    ),
            )

        rows.append(
            {
                "Threshold": threshold,
                "Accuracy": metrics["Accuracy"],
                "Precision": metrics["Precision"],
                "Recall": metrics["Recall"],
                "F1": metrics["F1"],
                "Specificity": metrics["Specificity"],
                "FPR": metrics["FPR"],
                "FNR": metrics["FNR"],
            }
        )

    return pd.DataFrame(
        rows
    )


def build_baseline_sweep(
    dataset: Iterable[Mapping[str, Any]],
    thresholds: Iterable[float],
) -> pd.DataFrame:
    """Convenience wrapper for baseline threshold sweep."""

    return build_threshold_sweep(
        dataset,
        thresholds,
        detector_type="baseline",
    )


def build_aegisguard_sweep(
    dataset: Iterable[Mapping[str, Any]],
    thresholds: Iterable[float],
) -> pd.DataFrame:
    """Convenience wrapper for AegisGuard threshold sweep."""

    return build_threshold_sweep(
        dataset,
        thresholds,
        detector_type="aegisguard",
    )


# ============================================================
# BEST THRESHOLD
# ============================================================

def get_best_threshold(
    sweep_df: pd.DataFrame,
    metric: str = "F1",
) -> dict[str, float]:
    """
    Return the threshold producing the highest metric.

    Example:

        get_best_threshold(
            sweep,
            "F1"
        )
    """

    if sweep_df.empty:
        raise ValueError(
            "Cannot select a threshold from an empty DataFrame."
        )

    if "Threshold" not in sweep_df.columns:
        raise ValueError(
            "Sweep DataFrame must contain 'Threshold'."
        )

    if metric not in sweep_df.columns:
        raise ValueError(
            f"Sweep DataFrame does not contain '{metric}'."
        )

    best_row = (
        sweep_df
        .sort_values(
            by=metric,
            ascending=False,
        )
        .iloc[0]
    )

    return {
        "Threshold": float(
            best_row["Threshold"]
        ),
        metric: float(
            best_row[metric]
        ),
    }


# ============================================================
# CONFUSION MATRIX
# ============================================================

def get_confusion_matrix(
    metrics: Mapping[str, Any],
) -> pd.DataFrame:
    """
    Convert metric dictionary into a readable
    2x2 confusion matrix.
    """

    required = {
        "TN",
        "FP",
        "FN",
        "TP",
    }

    missing = (
        required
        - set(metrics.keys())
    )

    if missing:

        raise ValueError(
            "Missing confusion matrix values: "
            + ", ".join(
                sorted(missing)
            )
        )

    return pd.DataFrame(
        [
            [
                int(metrics["TN"]),
                int(metrics["FP"]),
            ],
            [
                int(metrics["FN"]),
                int(metrics["TP"]),
            ],
        ],
        index=[
            "Actual Non-Malicious",
            "Actual Malicious",
        ],
        columns=[
            "Predicted Non-Malicious",
            "Predicted Malicious",
        ],
    )


# ============================================================
# RESEARCH SUMMARY
# ============================================================

def generate_comparison_summary(
    baseline_metrics: Mapping[str, Any],
    aegisguard_metrics: Mapping[str, Any],
) -> dict[str, float | str]:
    """
    Produce a concise machine-readable interpretation.

    This does NOT claim statistical significance.
    """

    f1_difference = (
        float(aegisguard_metrics["F1"])
        - float(baseline_metrics["F1"])
    )

    precision_difference = (
        float(aegisguard_metrics["Precision"])
        - float(baseline_metrics["Precision"])
    )

    recall_difference = (
        float(aegisguard_metrics["Recall"])
        - float(baseline_metrics["Recall"])
    )

    if f1_difference > 0:
        outcome = "AEGISGUARD_HIGHER_F1"

    elif f1_difference < 0:
        outcome = "BASELINE_HIGHER_F1"

    else:
        outcome = "EQUAL_F1"

    return {
        "outcome": outcome,
        "f1_difference": f1_difference,
        "precision_difference": precision_difference,
        "recall_difference": recall_difference,
    }