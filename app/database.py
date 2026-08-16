import sqlite3
from pathlib import Path
from datetime import datetime, timezone


DATABASE_FILE = Path("aegisguard.db")


def get_connection():
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_events (
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

    connection.commit()
    connection.close()


def save_audit_event(
    agent_id: str,
    task_id: str,
    action: str,
    resource: str,
    decision: str,
    risk: int,
    reason: str
):
    timestamp = datetime.now(timezone.utc).isoformat()

    connection = get_connection()

    cursor = connection.execute(
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
        (
            timestamp,
            agent_id,
            task_id,
            action,
            resource,
            decision,
            risk,
            reason
        )
    )

    connection.commit()

    event_id = cursor.lastrowid

    connection.close()

    return {
        "id": event_id,
        "timestamp": timestamp,
        "agent_id": agent_id,
        "task_id": task_id,
        "action": action,
        "resource": resource,
        "decision": decision,
        "risk": risk,
        "reason": reason
    }


def get_audit_events():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            id,
            timestamp,
            agent_id,
            task_id,
            action,
            resource,
            decision,
            risk,
            reason
        FROM audit_events
        ORDER BY id ASC
        """
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]