import sqlite3
from typing import Any


DATABASE_PATH = "aegisguard.db"

VALID_DECISIONS = {
    "ALLOW",
    "DENY",
}

VALID_RISK_LEVELS = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
}


def _connect():
    """
    Create a connection to the AegisGuard SQLite database.
    """

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    return connection


def _risk_condition(
    risk_level: str,
) -> tuple[str, list[int]]:
    """
    Convert a risk-level label into a SQL condition.

    Risk classification:

    LOW       = 0-20
    MEDIUM    = 21-50
    HIGH      = 51-79
    CRITICAL  = 80-100
    """

    normalized = risk_level.upper()

    if normalized == "LOW":
        return "risk BETWEEN ? AND ?", [0, 20]

    if normalized == "MEDIUM":
        return "risk BETWEEN ? AND ?", [21, 50]

    if normalized == "HIGH":
        return "risk BETWEEN ? AND ?", [51, 79]

    if normalized == "CRITICAL":
        return "risk >= ?", [80]

    raise ValueError(
        f"Unsupported risk level: {risk_level}"
    )


def get_investigation_events(
    agent_id: str | None = None,
    task_id: str | None = None,
    action: str | None = None,
    resource: str | None = None,
    decision: str | None = None,
    risk_level: str | None = None,
    minimum_risk: int | None = None,
    maximum_risk: int | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """
    Retrieve security events using investigation filters.

    All filters are optional.

    The function uses parameterized SQL queries to avoid
    dynamically inserting user-controlled values into SQL.
    """

    if limit <= 0:
        raise ValueError("limit must be greater than zero")

    if limit > 5000:
        raise ValueError("limit cannot exceed 5000")

    if decision is not None:

        normalized_decision = decision.upper()

        if normalized_decision not in VALID_DECISIONS:
            raise ValueError(
                f"Unsupported decision: {decision}"
            )

        decision = normalized_decision

    if risk_level is not None:

        normalized_risk = risk_level.upper()

        if normalized_risk not in VALID_RISK_LEVELS:
            raise ValueError(
                f"Unsupported risk level: {risk_level}"
            )

        risk_level = normalized_risk

    if minimum_risk is not None:

        if not 0 <= minimum_risk <= 100:
            raise ValueError(
                "minimum_risk must be between 0 and 100"
            )

    if maximum_risk is not None:

        if not 0 <= maximum_risk <= 100:
            raise ValueError(
                "maximum_risk must be between 0 and 100"
            )

    if (
        minimum_risk is not None
        and maximum_risk is not None
        and minimum_risk > maximum_risk
    ):
        raise ValueError(
            "minimum_risk cannot exceed maximum_risk"
        )

    conditions = []
    parameters = []

    # --------------------------------------------------------
    # Agent
    # --------------------------------------------------------

    if agent_id:

        conditions.append(
            "agent_id = ?"
        )

        parameters.append(agent_id)

    # --------------------------------------------------------
    # Task
    # --------------------------------------------------------

    if task_id:

        conditions.append(
            "task_id = ?"
        )

        parameters.append(task_id)

    # --------------------------------------------------------
    # Action
    # --------------------------------------------------------

    if action:

        conditions.append(
            "action = ?"
        )

        parameters.append(action)

    # --------------------------------------------------------
    # Resource
    # --------------------------------------------------------

    if resource:

        conditions.append(
            "resource = ?"
        )

        parameters.append(resource)

    # --------------------------------------------------------
    # Decision
    # --------------------------------------------------------

    if decision:

        conditions.append(
            "decision = ?"
        )

        parameters.append(decision)

    # --------------------------------------------------------
    # Risk Level
    # --------------------------------------------------------

    if risk_level:

        condition, values = _risk_condition(
            risk_level
        )

        conditions.append(condition)

        parameters.extend(values)

    # --------------------------------------------------------
    # Explicit Risk Range
    # --------------------------------------------------------

    if minimum_risk is not None:

        conditions.append(
            "risk >= ?"
        )

        parameters.append(minimum_risk)

    if maximum_risk is not None:

        conditions.append(
            "risk <= ?"
        )

        parameters.append(maximum_risk)

    # --------------------------------------------------------
    # Time Range
    # --------------------------------------------------------

    if start_time:

        conditions.append(
            "timestamp >= ?"
        )

        parameters.append(start_time)

    if end_time:

        conditions.append(
            "timestamp <= ?"
        )

        parameters.append(end_time)

    # --------------------------------------------------------
    # Build Query
    # --------------------------------------------------------

    query = """
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
    """

    if conditions:

        query += (
            "\nWHERE "
            + "\nAND ".join(conditions)
        )

    query += """
        ORDER BY id DESC
        LIMIT ?
    """

    parameters.append(limit)

    connection = _connect()

    try:

        rows = connection.execute(
            query,
            parameters,
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


def get_investigation_event(
    event_id: int,
) -> dict[str, Any] | None:
    """
    Retrieve one security event by its ID.
    """

    if event_id <= 0:
        raise ValueError(
            "event_id must be greater than zero"
        )

    connection = _connect()

    try:

        row = connection.execute(
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
            WHERE id = ?
            """,
            (event_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:

        connection.close()


def get_investigation_filter_options() -> dict[str, list[str]]:
    """
    Return available values for investigation filters.
    """

    connection = _connect()

    try:

        agents = connection.execute(
            """
            SELECT DISTINCT agent_id
            FROM audit_events
            WHERE agent_id IS NOT NULL
            ORDER BY agent_id
            """
        ).fetchall()

        tasks = connection.execute(
            """
            SELECT DISTINCT task_id
            FROM audit_events
            WHERE task_id IS NOT NULL
            ORDER BY task_id
            """
        ).fetchall()

        actions = connection.execute(
            """
            SELECT DISTINCT action
            FROM audit_events
            WHERE action IS NOT NULL
            ORDER BY action
            """
        ).fetchall()

        resources = connection.execute(
            """
            SELECT DISTINCT resource
            FROM audit_events
            WHERE resource IS NOT NULL
            ORDER BY resource
            """
        ).fetchall()

        return {
            "agents": [
                row[0]
                for row in agents
            ],
            "tasks": [
                row[0]
                for row in tasks
            ],
            "actions": [
                row[0]
                for row in actions
            ],
            "resources": [
                row[0]
                for row in resources
            ],
        }

    finally:

        connection.close()


def count_investigation_events(
    **filters,
) -> int:
    """
    Return the number of events matching investigation filters.
    """

    # Reuse the same filtering logic instead of duplicating SQL.
    return len(
        get_investigation_events(
            **filters,
            limit=5000,
        )
    )