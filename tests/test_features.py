import sqlite3

import pytest

import app.features as features


@pytest.fixture
def test_database(tmp_path, monkeypatch):

    database_path = tmp_path / "test_features.db"

    connection = sqlite3.connect(
        database_path
    )

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
            "2026-08-16T10:00:00",
            "agent-alpha",
            "task-a",
            "s3:GetObject",
            "public/data.csv",
            "ALLOW",
            20,
            "Authorized",
        ),
        (
            "2026-08-16T10:01:00",
            "agent-alpha",
            "task-a",
            "s3:DeleteObject",
            "private/data.csv",
            "DENY",
            90,
            "High risk",
        ),
        (
            "2026-08-16T10:02:00",
            "agent-alpha",
            "task-b",
            "iam:CreateUser",
            "admin/users",
            "DENY",
            100,
            "Unauthorized",
        ),
        (
            "2026-08-16T10:03:00",
            "agent-beta",
            "task-c",
            "s3:GetObject",
            "public/report.csv",
            "ALLOW",
            30,
            "Authorized",
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
        features,
        "DATABASE_PATH",
        str(database_path),
    )

    return database_path


def test_behavioral_features_return_agents(
    test_database,
):

    results = (
        features.get_behavioral_features()
    )

    assert len(results) == 2


def test_agent_alpha_request_counts(
    test_database,
):

    result = features.get_agent_behavior(
        "agent-alpha"
    )

    assert result is not None

    assert result["total_requests"] == 3

    assert result["allowed_requests"] == 1

    assert result["denied_requests"] == 2


def test_allow_rate(
    test_database,
):

    result = features.get_agent_behavior(
        "agent-alpha"
    )

    assert result["allow_rate"] == pytest.approx(
        1 / 3,
        abs=0.0001,
    )


def test_denial_rate(
    test_database,
):

    result = features.get_agent_behavior(
        "agent-alpha"
    )

    assert result["denial_rate"] == pytest.approx(
        2 / 3,
        abs=0.0001,
    )


def test_risk_features(
    test_database,
):

    result = features.get_agent_behavior(
        "agent-alpha"
    )

    assert result["average_risk"] == pytest.approx(
        70.0
    )

    assert result["maximum_risk"] == 100

    assert result["high_risk_requests"] == 2

    assert result["critical_requests"] == 2


def test_unique_behavior_features(
    test_database,
):

    result = features.get_agent_behavior(
        "agent-alpha"
    )

    assert result["unique_actions"] == 3

    assert result["unique_resources"] == 3

    assert result["unique_tasks"] == 2


def test_behavior_diversity(
    test_database,
):

    result = features.get_agent_behavior(
        "agent-alpha"
    )

    assert result["action_diversity"] == 1.0

    assert result["resource_diversity"] == 1.0

    assert result["task_diversity"] == pytest.approx(
        2 / 3,
        abs=0.0001,
    )


def test_unknown_agent(
    test_database,
):

    result = features.get_agent_behavior(
        "does-not-exist"
    )

    assert result is None


def test_empty_agent_rejected(
    test_database,
):

    with pytest.raises(ValueError):

        features.get_agent_behavior("")
        

def test_feature_names():

    names = (
        features.get_behavior_feature_names()
    )

    assert "denial_rate" in names

    assert "average_risk" in names

    assert "action_diversity" in names

    assert "resource_diversity" in names

    assert "task_diversity" in names