import pytest

import app.anomaly as anomaly


def test_anomaly_features_exist():

    assert "denial_rate" in (
        anomaly.ANOMALY_FEATURES
    )

    assert "average_risk" in (
        anomaly.ANOMALY_FEATURES
    )

    assert "critical_requests" in (
        anomaly.ANOMALY_FEATURES
    )


def test_safe_mean():

    assert anomaly._mean([]) == 0.0

    assert anomaly._mean(
        [1.0, 2.0, 3.0]
    ) == pytest.approx(2.0)


def test_standard_deviation():

    mean = anomaly._mean(
        [1.0, 2.0, 3.0]
    )

    result = anomaly._standard_deviation(
        [1.0, 2.0, 3.0],
        mean,
    )

    assert result > 0


def test_zero_standard_deviation():

    assert anomaly._z_score(
        10,
        10,
        0,
    ) == 0.0


def test_severity():

    assert (
        anomaly._severity_from_score(
            0.1
        )
        == "NORMAL"
    )

    assert (
        anomaly._severity_from_score(
            1.0
        )
        == "LOW"
    )

    assert (
        anomaly._severity_from_score(
            2.0
        )
        == "MEDIUM"
    )

    assert (
        anomaly._severity_from_score(
            3.0
        )
        == "HIGH"
    )


def test_behavioral_baseline():

    baseline = (
        anomaly.get_behavioral_baseline()
    )

    assert isinstance(
        baseline,
        dict,
    )

    assert "denial_rate" in baseline


def test_behavioral_anomalies():

    results = (
        anomaly.get_behavioral_anomalies()
    )

    assert isinstance(
        results,
        list,
    )


def test_anomaly_result_structure():

    results = (
        anomaly.get_behavioral_anomalies()
    )

    if results:

        result = results[0]

        assert "agent_id" in result

        assert "anomaly_score" in result

        assert "anomaly_severity" in result

        assert "anomalous_features" in result

        assert "feature_scores" in result


def test_unknown_agent():

    result = (
        anomaly.get_agent_anomaly(
            "does-not-exist"
        )
    )

    assert result is None


def test_empty_agent_rejected():

    with pytest.raises(
        ValueError
    ):

        anomaly.get_agent_anomaly("")
        

def test_anomaly_summary():

    summary = (
        anomaly.get_anomaly_summary()
    )

    assert isinstance(
        summary,
        dict,
    )

    assert "agents_analyzed" in summary

    assert "high_anomaly_agents" in summary

    assert "medium_anomaly_agents" in summary

    assert "normal_agents" in summary