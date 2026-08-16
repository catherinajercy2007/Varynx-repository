import sqlite3
from typing import Any


DATABASE_PATH = "aegisguard.db"


def _connect():
    return sqlite3.connect(DATABASE_PATH)


def get_total_events() -> int:
    connection = _connect()

    try:
        result = connection.execute(
            "SELECT COUNT(*) FROM audit_events"
        ).fetchone()

        return int(result[0])
    finally:
        connection.close()


def get_decision_counts() -> dict[str, int]:
    connection = _connect()

    try:
        rows = connection.execute(
            """
            SELECT decision, COUNT(*)
            FROM audit_events
            GROUP BY decision
            ORDER BY decision
            """
        ).fetchall()

        return {
            str(decision): int(count)
            for decision, count in rows
        }

    finally:
        connection.close()


def get_risk_summary() -> dict[str, Any]:
    connection = _connect()

    try:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total_events,
                COALESCE(AVG(risk), 0) AS average_risk,
                COALESCE(MAX(risk), 0) AS maximum_risk,
                COALESCE(SUM(
                    CASE
                        WHEN risk >= 80 THEN 1
                        ELSE 0
                    END
                ), 0) AS critical_events,
                COALESCE(SUM(
                    CASE
                        WHEN risk BETWEEN 51 AND 79 THEN 1
                        ELSE 0
                    END
                ), 0) AS high_risk_events
            FROM audit_events
            """
        ).fetchone()

        return {
            "total_events": int(row[0]),
            "average_risk": round(float(row[1]), 2),
            "maximum_risk": int(row[2]),
            "critical_events": int(row[3]),
            "high_risk_events": int(row[4]),
        }

    finally:
        connection.close()


def get_agent_activity() -> list[dict[str, Any]]:
    connection = _connect()

    try:
        rows = connection.execute(
            """
            SELECT
                agent_id,
                COUNT(*) AS total_requests,
                SUM(
                    CASE
                        WHEN decision = 'ALLOW' THEN 1
                        ELSE 0
                    END
                ) AS allowed_requests,
                SUM(
                    CASE
                        WHEN decision = 'DENY' THEN 1
                        ELSE 0
                    END
                ) AS denied_requests,
                COALESCE(MAX(risk), 0) AS maximum_risk
            FROM audit_events
            GROUP BY agent_id
            ORDER BY total_requests DESC
            """
        ).fetchall()

        return [
            {
                "agent_id": row[0],
                "total_requests": int(row[1]),
                "allowed_requests": int(row[2] or 0),
                "denied_requests": int(row[3] or 0),
                "maximum_risk": int(row[4] or 0),
            }
            for row in rows
        ]

    finally:
        connection.close()


def get_high_risk_events(
    minimum_risk: int = 80,
) -> list[dict[str, Any]]:
    connection = _connect()

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                agent_id,
                task_id,
                action,
                resource,
                decision,
                risk,
                reason
            FROM audit_events
            WHERE risk >= ?
            ORDER BY risk DESC, id DESC
            """,
            (minimum_risk,),
        ).fetchall()

        return [
            {
                "id": int(row[0]),
                "agent_id": row[1],
                "task_id": row[2],
                "action": row[3],
                "resource": row[4],
                "decision": row[5],
                "risk": int(row[6]),
                "reason": row[7],
            }
            for row in rows
        ]

    finally:
        connection.close()


def get_denied_events() -> list[dict[str, Any]]:
    connection = _connect()

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                agent_id,
                task_id,
                action,
                resource,
                decision,
                risk,
                reason
            FROM audit_events
            WHERE decision = 'DENY'
            ORDER BY id DESC
            """
        ).fetchall()

        return [
            {
                "id": int(row[0]),
                "agent_id": row[1],
                "task_id": row[2],
                "action": row[3],
                "resource": row[4],
                "decision": row[5],
                "risk": int(row[6]),
                "reason": row[7],
            }
            for row in rows
        ]

    finally:
        connection.close()


def get_security_summary() -> dict[str, Any]:
    return {
        "total_events": get_total_events(),
        "decisions": get_decision_counts(),
        "risk": get_risk_summary(),
        "agents": get_agent_activity(),
        "high_risk_events": get_high_risk_events(),
        "denied_events": get_denied_events(),
    }