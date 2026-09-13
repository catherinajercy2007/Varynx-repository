import sqlite3
from typing import Any


DATABASE_PATH = "aegisguard.db"


def _connect():
    return sqlite3.connect(DATABASE_PATH)


def get_agent_behavior(
    agent_id: str,
    denial_threshold: int = 3,
    risk_threshold: int = 80,
) -> dict[str, Any]:

    connection = _connect()

    try:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total_requests,
                SUM(
                    CASE
                        WHEN decision = 'ALLOW'
                        THEN 1
                        ELSE 0
                    END
                ) AS allowed_requests,
                SUM(
                    CASE
                        WHEN decision = 'DENY'
                        THEN 1
                        ELSE 0
                    END
                ) AS denied_requests,
                COALESCE(AVG(risk), 0),
                COALESCE(MAX(risk), 0),
                SUM(
                    CASE
                        WHEN risk >= ?
                        THEN 1
                        ELSE 0
                    END
                )
            FROM audit_events
            WHERE agent_id = ?
            """,
            (risk_threshold, agent_id),
        ).fetchone()

        total_requests = int(row[0] or 0)
        allowed_requests = int(row[1] or 0)
        denied_requests = int(row[2] or 0)
        average_risk = round(float(row[3] or 0), 2)
        maximum_risk = int(row[4] or 0)
        high_risk_requests = int(row[5] or 0)

        if denied_requests >= denial_threshold:
            behavior_status = "SUSPICIOUS"
        elif high_risk_requests > 0:
            behavior_status = "ELEVATED"
        else:
            behavior_status = "NORMAL"

        return {
            "agent_id": agent_id,
            "total_requests": total_requests,
            "allowed_requests": allowed_requests,
            "denied_requests": denied_requests,
            "average_risk": average_risk,
            "maximum_risk": maximum_risk,
            "high_risk_requests": high_risk_requests,
            "behavior_status": behavior_status,
        }

    finally:
        connection.close()


def get_suspicious_agents(
    denial_threshold: int = 3,
    risk_threshold: int = 80,
) -> list[dict[str, Any]]:

    connection = _connect()

    try:
        rows = connection.execute(
            """
            SELECT
                agent_id,
                COUNT(*) AS total_requests,
                SUM(
                    CASE
                        WHEN decision = 'DENY'
                        THEN 1
                        ELSE 0
                    END
                ) AS denied_requests,
                COALESCE(AVG(risk), 0) AS average_risk,
                COALESCE(MAX(risk), 0) AS maximum_risk,
                SUM(
                    CASE
                        WHEN risk >= ?
                        THEN 1
                        ELSE 0
                    END
                ) AS high_risk_requests
            FROM audit_events
            GROUP BY agent_id
            HAVING
                denied_requests >= ?
                OR high_risk_requests > 0
            ORDER BY maximum_risk DESC, denied_requests DESC
            """,
            (risk_threshold, denial_threshold),
        ).fetchall()

        results = []

        for row in rows:

            denied_requests = int(row[2] or 0)
            high_risk_requests = int(row[5] or 0)

            if denied_requests >= denial_threshold:
                status = "SUSPICIOUS"
            else:
                status = "ELEVATED"

            results.append(
                {
                    "agent_id": row[0],
                    "total_requests": int(row[1]),
                    "denied_requests": denied_requests,
                    "average_risk": round(float(row[3] or 0), 2),
                    "maximum_risk": int(row[4] or 0),
                    "high_risk_requests": high_risk_requests,
                    "behavior_status": status,
                }
            )

        return results

    finally:
        connection.close()


def get_repeated_denials(
    minimum_denials: int = 3,
) -> list[dict[str, Any]]:

    connection = _connect()

    try:
        rows = connection.execute(
            """
            SELECT
                agent_id,
                action,
                resource,
                COUNT(*) AS denial_count
            FROM audit_events
            WHERE decision = 'DENY'
            GROUP BY agent_id, action, resource
            HAVING COUNT(*) >= ?
            ORDER BY denial_count DESC
            """,
            (minimum_denials,),
        ).fetchall()

        return [
            {
                "agent_id": row[0],
                "action": row[1],
                "resource": row[2],
                "denial_count": int(row[3]),
            }
            for row in rows
        ]

    finally:
        connection.close()


def get_behavior_summary() -> dict[str, Any]:

    suspicious_agents = get_suspicious_agents()
    repeated_denials = get_repeated_denials()

    return {
        "suspicious_agent_count": len(suspicious_agents),
        "repeated_denial_count": len(repeated_denials),
        "suspicious_agents": suspicious_agents,
        "repeated_denials": repeated_denials,
    }