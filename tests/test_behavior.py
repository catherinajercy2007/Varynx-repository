import sqlite3

import app.behavior as behavior


def create_test_database(tmp_path, monkeypatch):

    database_path = tmp_path / "behavior.db"

    connection = sqlite3.connect(database_path)

    connection.execute(
        """
        CREATE TABLE audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            "normal-agent",
            "task-1",
            "s3:GetObject",
            "public/data.csv",
            "ALLOW",
            5,
            "Allowed",
        ),
        (
            "normal-agent",
            "task-2",
            "s3:GetObject",
            "public/data.csv",
            "ALLOW",
            10,
            "Allowed",
        ),
        (
            "bad-agent",
            "task-3",
            "s3:DeleteObject",
            "private/data.csv",
            "DENY",
            100,
            "Denied",
        ),
        (
            "bad-agent",
            "task-4",
            "s3:DeleteObject",
            "private/data.csv",
            "DENY",
            100,
            "Denied",
        ),
        (
            "bad-agent",
            "task-5",
            "s3:DeleteObject",
            "private/data.csv",
            "DENY",
            100,
            "Denied",
        ),
    ]

    connection.executemany(
        """
        INSERT INTO audit_events (
            agent_id,
            task_id,
            action,
            resource,
            decision,
            risk,
            reason
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        events,
    )

    connection.commit()
    connection.close()

    monkeypatch.setattr(
        behavior,
        "DATABASE_PATH",
        str(database_path),
    )


def test_normal_agent(tmp_path, monkeypatch):

    create_test_database(tmp_path, monkeypatch)

    result = behavior.get_agent_behavior(
        "normal-agent"
    )

    assert result["behavior_status"] == "NORMAL"
    assert result["total_requests"] == 2
    assert result["denied_requests"] == 0


def test_suspicious_agent(tmp_path, monkeypatch):

    create_test_database(tmp_path, monkeypatch)

    result = behavior.get_agent_behavior(
        "bad-agent"
    )

    assert result["behavior_status"] == "SUSPICIOUS"
    assert result["denied_requests"] == 3
    assert result["maximum_risk"] == 100


def test_suspicious_agents(tmp_path, monkeypatch):

    create_test_database(tmp_path, monkeypatch)

    result = behavior.get_suspicious_agents()

    assert len(result) == 1
    assert result[0]["agent_id"] == "bad-agent"


def test_repeated_denials(tmp_path, monkeypatch):

    create_test_database(tmp_path, monkeypatch)

    result = behavior.get_repeated_denials()

    assert len(result) == 1
    assert result[0]["agent_id"] == "bad-agent"
    assert result[0]["denial_count"] == 3


def test_behavior_summary(tmp_path, monkeypatch):

    create_test_database(tmp_path, monkeypatch)

    result = behavior.get_behavior_summary()

    assert result["suspicious_agent_count"] == 1
    assert result["repeated_denial_count"] == 1