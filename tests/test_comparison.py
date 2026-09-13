from app.comparison import (
    baseline_predict,
    aegisguard_predict,
    calculate_metrics,
    compare_detectors,
    calculate_improvement,
)


def test_baseline_high_risk_prediction():

    event = {
        "risk_score": 90,
    }

    assert (
        baseline_predict(
            event,
            70,
        )
        is True
    )


def test_baseline_low_risk_prediction():

    event = {
        "risk_score": 30,
    }

    assert (
        baseline_predict(
            event,
            70,
        )
        is False
    )


def test_metrics_perfect_classifier():

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

    assert metrics[
        "accuracy"
    ] == 1.0

    assert metrics[
        "precision"
    ] == 1.0

    assert metrics[
        "recall"
    ] == 1.0

    assert metrics[
        "f1_score"
    ] == 1.0


def test_metrics_detect_false_positive():

    actual = [
        True,
        False,
    ]

    predicted = [
        True,
        True,
    ]

    metrics = calculate_metrics(
        actual,
        predicted,
    )

    assert metrics[
        "true_positive"
    ] == 1

    assert metrics[
        "false_positive"
    ] == 1


def test_aegisguard_combines_signals():

    event = {
        "risk_score": 40,
        "decision": "DENY",
        "denial_count": 5,
        "anomaly_score": 1.5,
    }

    assert (
        aegisguard_predict(
            event,
            70,
        )
        is True
    )


def test_detector_comparison():

    dataset = [
        {
            "event_id": "1",
            "ground_truth": "MALICIOUS",
            "risk_score": 95,
        },
        {
            "event_id": "2",
            "ground_truth": "BENIGN",
            "risk_score": 20,
        },
    ]

    result = compare_detectors(
        dataset,
        70,
    )

    assert "baseline" in result

    assert "aegisguard" in result

    assert (
        result[
            "baseline"
        ]["accuracy"]
        >= 0
    )


def test_improvement_calculation():

    baseline = {
        "accuracy": 0.60,
        "precision": 0.50,
        "recall": 0.50,
        "specificity": 0.70,
        "f1_score": 0.50,
        "false_positive_rate": 0.30,
        "false_negative_rate": 0.50,
    }

    aegisguard = {
        "accuracy": 0.80,
        "precision": 0.75,
        "recall": 0.70,
        "specificity": 0.85,
        "f1_score": 0.72,
        "false_positive_rate": 0.15,
        "false_negative_rate": 0.30,
    }

    improvement = calculate_improvement(
        baseline,
        aegisguard,
    )

    assert improvement[
        "accuracy"
    ] == 0.20

    assert improvement[
        "f1_score"
    ] == 0.22