from __future__ import annotations

from typing import Any, Dict, Iterable, List


MALICIOUS = "MALICIOUS"


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _ground_truth_is_malicious(
    event: Dict[str, Any],
) -> bool:

    return (
        str(
            event.get(
                "ground_truth",
                "",
            )
        ).upper()
        == MALICIOUS
    )


def baseline_predict(
    event: Dict[str, Any],
    threshold: float = 70.0,
) -> bool:
    """
    Simple risk-only baseline.

    The baseline intentionally ignores:
        - behavioral history
        - anomaly detection
        - repeated denials
        - integrated intelligence

    It only uses the event's risk score.
    """

    risk_score = _safe_float(
        event.get(
            "risk_score",
            0,
        )
    )

    return risk_score >= threshold


def aegisguard_predict(
    event: Dict[str, Any],
    threshold: float = 70.0,
) -> bool:
    """
    Behavior-aware AegisGuard prediction.

    The detector combines:
        - risk score
        - authorization decision
        - behavioral indicators
        - anomaly indicators

    The function deliberately accepts flexible field names
    so it can work with datasets produced by earlier stages.
    """

    risk_score = _safe_float(
        event.get(
            "risk_score",
            0,
        )
    )

    decision = str(
        event.get(
            "decision",
            "",
        )
    ).upper()

    denial_count = _safe_int(
        event.get(
            "denial_count",
            0,
        )
    )

    anomaly_score = _safe_float(
        event.get(
            "anomaly_score",
            0,
        )
    )

    behavioral_risk = _safe_float(
        event.get(
            "behavioral_risk",
            event.get(
                "behavior_score",
                0,
            ),
        )
    )

    high_risk_signal = (
        risk_score >= threshold
    )

    denial_signal = (
        denial_count >= 3
    )

    anomaly_signal = (
        anomaly_score >= 1.0
    )

    behavioral_signal = (
        behavioral_risk >= 60
    )

    authorization_signal = (
        decision == "DENY"
    )

    signals = sum(
        [
            high_risk_signal,
            denial_signal,
            anomaly_signal,
            behavioral_signal,
            authorization_signal,
        ]
    )

    # Require either:
    #
    # 1. a very high risk signal, or
    # 2. multiple independent security signals.
    #
    # This prevents a single weak signal from automatically
    # classifying an event as malicious.

    if risk_score >= 90:
        return True

    return signals >= 2


def _confusion_counts(
    actual: Iterable[bool],
    predicted: Iterable[bool],
) -> Dict[str, int]:

    true_positive = 0
    true_negative = 0
    false_positive = 0
    false_negative = 0

    for actual_value, predicted_value in zip(
        actual,
        predicted,
    ):

        if actual_value and predicted_value:
            true_positive += 1

        elif not actual_value and not predicted_value:
            true_negative += 1

        elif not actual_value and predicted_value:
            false_positive += 1

        elif actual_value and not predicted_value:
            false_negative += 1

    return {
        "true_positive": true_positive,
        "true_negative": true_negative,
        "false_positive": false_positive,
        "false_negative": false_negative,
    }


def calculate_metrics(
    actual: List[bool],
    predicted: List[bool],
) -> Dict[str, float]:

    counts = _confusion_counts(
        actual,
        predicted,
    )

    tp = counts["true_positive"]
    tn = counts["true_negative"]
    fp = counts["false_positive"]
    fn = counts["false_negative"]

    total = (
        tp
        + tn
        + fp
        + fn
    )

    accuracy = (
        (tp + tn) / total
        if total
        else 0.0
    )

    precision = (
        tp / (tp + fp)
        if (tp + fp)
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn)
        else 0.0
    )

    specificity = (
        tn / (tn + fp)
        if (tn + fp)
        else 0.0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    false_positive_rate = (
        fp / (fp + tn)
        if (fp + tn)
        else 0.0
    )

    false_negative_rate = (
        fn / (fn + tp)
        if (fn + tp)
        else 0.0
    )

    return {
        **counts,

        "accuracy": round(
            accuracy,
            4,
        ),

        "precision": round(
            precision,
            4,
        ),

        "recall": round(
            recall,
            4,
        ),

        "specificity": round(
            specificity,
            4,
        ),

        "f1_score": round(
            f1,
            4,
        ),

        "false_positive_rate": round(
            false_positive_rate,
            4,
        ),

        "false_negative_rate": round(
            false_negative_rate,
            4,
        ),
    }


def evaluate_detector(
    dataset: Iterable[Dict[str, Any]],
    detector,
    threshold: float = 70.0,
) -> Dict[str, float]:

    dataset = list(dataset)

    actual = [
        _ground_truth_is_malicious(
            event
        )
        for event in dataset
    ]

    predicted = [
        bool(
            detector(
                event,
                threshold,
            )
        )
        for event in dataset
    ]

    return calculate_metrics(
        actual,
        predicted,
    )


def compare_detectors(
    dataset: Iterable[Dict[str, Any]],
    threshold: float = 70.0,
) -> Dict[str, Dict[str, float]]:

    dataset = list(dataset)

    baseline_metrics = evaluate_detector(
        dataset,
        baseline_predict,
        threshold,
    )

    aegisguard_metrics = evaluate_detector(
        dataset,
        aegisguard_predict,
        threshold,
    )

    return {
        "baseline": baseline_metrics,
        "aegisguard": aegisguard_metrics,
    }


def calculate_improvement(
    baseline: Dict[str, float],
    aegisguard: Dict[str, float],
) -> Dict[str, float]:

    metrics = [
        "accuracy",
        "precision",
        "recall",
        "specificity",
        "f1_score",
        "false_positive_rate",
        "false_negative_rate",
    ]

    result = {}

    for metric in metrics:

        baseline_value = _safe_float(
            baseline.get(
                metric,
                0,
            )
        )

        aegisguard_value = _safe_float(
            aegisguard.get(
                metric,
                0,
            )
        )

        result[metric] = round(
            aegisguard_value
            - baseline_value,
            4,
        )

    return result


def build_comparison_table(
    comparison: Dict[str, Dict[str, float]],
):

    import pandas as pd

    baseline = comparison[
        "baseline"
    ]

    aegisguard = comparison[
        "aegisguard"
    ]

    rows = []

    metrics = [
        (
            "Accuracy",
            "accuracy",
        ),
        (
            "Precision",
            "precision",
        ),
        (
            "Recall",
            "recall",
        ),
        (
            "F1 Score",
            "f1_score",
        ),
        (
            "Specificity",
            "specificity",
        ),
        (
            "False Positive Rate",
            "false_positive_rate",
        ),
        (
            "False Negative Rate",
            "false_negative_rate",
        ),
    ]

    for display_name, key in metrics:

        rows.append(
            {
                "Metric":
                    display_name,

                "Baseline":
                    round(
                        baseline.get(
                            key,
                            0,
                        )
                        * 100,
                        2,
                    ),

                "AegisGuard":
                    round(
                        aegisguard.get(
                            key,
                            0,
                        )
                        * 100,
                        2,
                    ),

                "Difference":
                    round(
                        (
                            aegisguard.get(
                                key,
                                0,
                            )
                            - baseline.get(
                                key,
                                0,
                            )
                        )
                        * 100,
                        2,
                    ),
            }
        )

    return pd.DataFrame(
        rows
    )


def build_event_comparison(
    dataset: Iterable[Dict[str, Any]],
    threshold: float = 70.0,
):

    import pandas as pd

    rows = []

    for event in dataset:

        actual = (
            _ground_truth_is_malicious(
                event
            )
        )

        baseline = (
            baseline_predict(
                event,
                threshold,
            )
        )

        aegisguard = (
            aegisguard_predict(
                event,
                threshold,
            )
        )

        rows.append(
            {
                "event_id":
                    event.get(
                        "event_id",
                        "",
                    ),

                "scenario_id":
                    event.get(
                        "scenario_id",
                        "",
                    ),

                "ground_truth":
                    event.get(
                        "ground_truth",
                        "",
                    ),

                "risk_score":
                    event.get(
                        "risk_score",
                        0,
                    ),

                "baseline_prediction":
                    (
                        "MALICIOUS"
                        if baseline
                        else "NON-MALICIOUS"
                    ),

                "aegisguard_prediction":
                    (
                        "MALICIOUS"
                        if aegisguard
                        else "NON-MALICIOUS"
                    ),

                "baseline_correct":
                    baseline == actual,

                "aegisguard_correct":
                    aegisguard == actual,
            }
        )

    return pd.DataFrame(
        rows
    )