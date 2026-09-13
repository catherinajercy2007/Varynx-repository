import sqlite3

import pytest

import app.investigation as investigation


@pytest.fixture
def test_database(tmp_path, monkeypatch):

    database_path = tmp_path / "test_aegisguard.db"

    connection = sqlite3.connect(database_path)

    connection.execute(
        """
        CREATE TABLE audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            action TEXT NOT NULL,
            resource TEXT NOT NULL,
            decision TEXT NOT NULL,
            risk INTEGER NOT NULL,
            reason TEXT NOT NULL
        )
        """
    )

    events = [
        (
            "2026-08-16T10:00:00+00:00",
            "agent-alpha",
            "task-analysis",
            "s3:GetObject",
            "public/data.csv",
            "ALLOW",
            20,
            "Authorized request",
        ),
        (
            "2026-08-16T10:01:00+00:00",
            "agent-alpha",
            "task-analysis",
            "s3:DeleteObject",
            "private/data.csv",
            "DENY",
            85,
            "High-risk destructive action",
        ),
        (
            "2026-08-16T10:02:00+00:00",
            "agent-beta",
            "task-report",
            "s3:GetObject",
            "public/report.csv",
            "ALLOW",
            35,
            "Authorized request",
        ),
        (
            "2026-08-16T10:03:00+00:00",
            "agent-beta",
            "task-report",
            "iam:CreateUser",
            "admin/users",
            "DENY",
            95,
            "Unauthorized administrative action",
        ),
    ]

    connection.executemany(
        """
        INSERT INTO audit_events (
            timestamp,
            agent_id,
            task_id,
            action,
            resource,
            decision,
            risk,
            reason
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        events,
    )

    connection.commit()
    connection.close()

    monkeypatch.setattr(
        investigation,
        "DATABASE_PATH",
        str(database_path),
    )

    return database_path


def test_get_all_investigation_events(test_database):

    results = investigation.get_investigation_events()

    assert len(results) == 4


def test_filter_by_agent(test_database):

    results = investigation.get_investigation_events(
        agent_id="agent-alpha"
    )

    assert len(results) == 2

    assert all(
        event["agent_id"] == "agent-alpha"
        for event in results
    )


def test_filter_by_task(test_database):

    results = investigation.get_investigation_events(
        task_id="task-report"
    )

    assert len(results) == 2


def test_filter_by_action(test_database):

    results = investigation.get_investigation_events(
        action="s3:GetObject"
    )

    assert len(results) == 2


def test_filter_by_resource(test_database):

    results = investigation.get_investigation_events(
        resource="private/data.csv"
    )

    assert len(results) == 1


def test_filter_by_decision(test_database):

    results = investigation.get_investigation_events(
        decision="DENY"
    )

    assert len(results) == 2


def test_filter_by_risk_level(test_database):

    results = investigation.get_investigation_events(
        risk_level="CRITICAL"
    )

    assert len(results) == 2


def test_filter_by_combined_conditions(test_database):

    results = investigation.get_investigation_events(
        agent_id="agent-alpha",
        decision="DENY",
        risk_level="CRITICAL",
    )

    assert len(results) == 1

    assert results[0]["action"] == "s3:DeleteObject"


def test_filter_by_explicit_risk_range(test_database):

    results = investigation.get_investigation_events(
        minimum_risk=30,
        maximum_risk=40,
    )

    assert len(results) == 1

    assert results[0]["risk"] == 35


def test_filter_by_time_range(test_database):

    results = investigation.get_investigation_events(
        start_time="2026-08-16T10:01:00+00:00",
        end_time="2026-08-16T10:02:00+00:00",
    )

    assert len(results) == 2


def test_get_event_by_id(test_database):

    results = investigation.get_investigation_events()

    event_id = results[0]["id"]

    event = investigation.get_investigation_event(
        event_id
    )

    assert event is not None

    assert event["id"] == event_id


def test_missing_event_returns_none(test_database):

    result = investigation.get_investigation_event(
        9999
    )

    assert result is None


def test_filter_options(test_database):

    options = (
        investigation.get_investigation_filter_options()
    )

    assert options["agents"] == [
        "agent-alpha",
        "agent-beta",
    ]

    assert "task-analysis" in options["tasks"]

    assert "s3:GetObject" in options["actions"]

    assert "public/data.csv" in options["resources"]


def test_invalid_decision_rejected(test_database):

    with pytest.raises(ValueError):

        investigation.get_investigation_events(
            decision="INVALID"
        )


def test_invalid_risk_level_rejected(test_database):

    with pytest.raises(ValueError):

        investigation.get_investigation_events(
            risk_level="UNKNOWN"
        )


def test_invalid_risk_range_rejected(test_database):

    with pytest.raises(ValueError):

        investigation.get_investigation_events(
            minimum_risk=90,
            maximum_risk=20,
        )


def test_invalid_limit_rejected(test_database):

    with pytest.raises(ValueError):

        investigation.get_investigation_events(
            limit=0
        )