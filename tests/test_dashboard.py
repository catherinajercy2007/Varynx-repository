from app.analytics import (
    get_total_events,
    get_decision_counts,
    get_risk_summary,
)


def test_total_events_is_non_negative():
    result = get_total_events()

    assert result >= 0


def test_decision_counts_is_dictionary():
    result = get_decision_counts()

    assert isinstance(result, dict)


def test_risk_summary_is_dictionary():
    result = get_risk_summary()

    assert isinstance(result, dict)


def test_risk_summary_contains_core_metrics():

    result = get_risk_summary()

    assert "average_risk" in result
    assert "maximum_risk" in result
    assert "high_risk_events" in result
    assert "critical_events" in result