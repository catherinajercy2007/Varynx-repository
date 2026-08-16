import sqlite3

import app.analytics as analytics


def create_test_database(tmp_path, monkeypatch):

    database_path = tmp_path / "test_aegisguard.db"

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
            "agent-a",
            "task-001",
            "s3:GetObject",
            "public/sales.csv",
            "ALLOW",
            5,
            "Allowed request",
        ),
        (
            "agent-a",
            "task-002",
            "s3:DeleteObject",
            "private/customer.csv",
            "DENY",
            100,
            "Unauthorized action",
        ),
        (
            "agent-b",
            "task-003",
            "s3:GetObject",
            "public/data.csv",
            "DENY",
            85,
            "Unauthorized resource",
        ),
        (
            "agent-b",
            "task-004",
            "s3:GetObject",
            "public/report.csv",
            "ALLOW",
            10,
            "Allowed request",
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
        analytics,
        "DATABASE_PATH",
        str(database_path),
    )


def test_total_events(tmp_path, monkeypatch):

    create_test_database(tmp_path, monkeypatch)

    assert analytics.get_total_events() == 4


def test_decision_counts(tmp_path, monkeypatch):

    create_test_database(tmp_path, monkeypatch)

    result = analytics.get_decision_counts()

    assert result["ALLOW"] == 2
    assert result["DENY"] == 2


def test_risk_summary(tmp_path, monkeypatch):

    create_test_database(tmp_path, monkeypatch)

    result = analytics.get_risk_summary()

    assert result["total_events"] == 4
    assert result["average_risk"] == 50.0
    assert result["maximum_risk"] == 100
    assert result["critical_events"] == 2
    assert result["high_risk_events"] == 0


def test_agent_activity(tmp_path, monkeypatch):

    create_test_database(tmp_path, monkeypatch)

    result = analytics.get_agent_activity()

    assert len(result) == 2

    agent_a = next(
        item
        for item in result
        if item["agent_id"] == "agent-a"
    )

    assert agent_a["total_requests"] == 2
    assert agent_a["allowed_requests"] == 1
    assert agent_a["denied_requests"] == 1
    assert agent_a["maximum_risk"] == 100


def test_high_risk_events(tmp_path, monkeypatch):

    create_test_database(tmp_path, monkeypatch)

    result = analytics.get_high_risk_events()

    assert len(result) == 2
    assert result[0]["risk"] == 100
    assert result[1]["risk"] == 85


def test_denied_events(tmp_path, monkeypatch):

    create_test_database(tmp_path, monkeypatch)

    result = analytics.get_denied_events()

    assert len(result) == 2

    for event in result:
        assert event["decision"] == "DENY"


def test_security_summary(tmp_path, monkeypatch):

    create_test_database(tmp_path, monkeypatch)

    result = analytics.get_security_summary()

    assert result["total_events"] == 4
    assert result["decisions"]["ALLOW"] == 2
    assert result["decisions"]["DENY"] == 2
    assert len(result["agents"]) == 2
    assert len(result["high_risk_events"]) == 2
    assert len(result["denied_events"]) == 2