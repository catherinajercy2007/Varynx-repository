import sqlite3
from typing import Any


DATABASE_PATH = "aegisguard.db"


def _connect():
    """
    Create a connection to the AegisGuard database.
    """

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


def _safe_ratio(
    numerator: float,
    denominator: float,
) -> float:
    """
    Safely calculate a ratio.
    """

    if denominator == 0:
        return 0.0

    return numerator / denominator


def get_behavioral_features() -> list[dict[str, Any]]:
    """
    Generate behavioral security features for each agent.

    Features are derived from the audit event history.
    """

    connection = _connect()

    try:

        rows = connection.execute(
            """
            SELECT
                agent_id,
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

                AVG(risk) AS average_risk,

                MAX(risk) AS maximum_risk,

                SUM(
                    CASE
                        WHEN risk >= 50
                        THEN 1
                        ELSE 0
                    END
                ) AS high_risk_requests,

                SUM(
                    CASE
                        WHEN risk >= 80
                        THEN 1
                        ELSE 0
                    END
                ) AS critical_requests,

                COUNT(DISTINCT action)
                    AS unique_actions,

                COUNT(DISTINCT resource)
                    AS unique_resources,

                COUNT(DISTINCT task_id)
                    AS unique_tasks

            FROM audit_events

            GROUP BY agent_id

            ORDER BY
                average_risk DESC,
                total_requests DESC
            """
        ).fetchall()

        features = []

        for row in rows:

            data = dict(row)

            total_requests = int(
                data["total_requests"] or 0
            )

            allowed_requests = int(
                data["allowed_requests"] or 0
            )

            denied_requests = int(
                data["denied_requests"] or 0
            )

            unique_actions = int(
                data["unique_actions"] or 0
            )

            unique_resources = int(
                data["unique_resources"] or 0
            )

            unique_tasks = int(
                data["unique_tasks"] or 0
            )

            allow_rate = _safe_ratio(
                allowed_requests,
                total_requests,
            )

            denial_rate = _safe_ratio(
                denied_requests,
                total_requests,
            )

            action_diversity = _safe_ratio(
                unique_actions,
                total_requests,
            )

            resource_diversity = _safe_ratio(
                unique_resources,
                total_requests,
            )

            task_diversity = _safe_ratio(
                unique_tasks,
                total_requests,
            )

            features.append(
                {
                    "agent_id": data["agent_id"],
                    "total_requests": total_requests,
                    "allowed_requests": allowed_requests,
                    "denied_requests": denied_requests,
                    "allow_rate": round(
                        allow_rate,
                        4,
                    ),
                    "denial_rate": round(
                        denial_rate,
                        4,
                    ),
                    "average_risk": round(
                        float(
                            data["average_risk"] or 0
                        ),
                        2,
                    ),
                    "maximum_risk": int(
                        data["maximum_risk"] or 0
                    ),
                    "high_risk_requests": int(
                        data["high_risk_requests"] or 0
                    ),
                    "critical_requests": int(
                        data["critical_requests"] or 0
                    ),
                    "unique_actions": unique_actions,
                    "unique_resources": unique_resources,
                    "unique_tasks": unique_tasks,
                    "action_diversity": round(
                        action_diversity,
                        4,
                    ),
                    "resource_diversity": round(
                        resource_diversity,
                        4,
                    ),
                    "task_diversity": round(
                        task_diversity,
                        4,
                    ),
                }
            )

        return features

    finally:

        connection.close()


def get_agent_behavior(
    agent_id: str,
) -> dict[str, Any] | None:
    """
    Retrieve behavioral features for one agent.
    """

    if not agent_id:
        raise ValueError(
            "agent_id cannot be empty"
        )

    features = get_behavioral_features()

    for feature in features:

        if feature["agent_id"] == agent_id:
            return feature

    return None


def get_behavior_feature_names() -> list[str]:
    """
    Return the numeric behavioral features used
    by the research analytics layer.
    """

    return [
        "total_requests",
        "allowed_requests",
        "denied_requests",
        "allow_rate",
        "denial_rate",
        "average_risk",
        "maximum_risk",
        "high_risk_requests",
        "critical_requests",
        "unique_actions",
        "unique_resources",
        "unique_tasks",
        "action_diversity",
        "resource_diversity",
        "task_diversity",
    ]