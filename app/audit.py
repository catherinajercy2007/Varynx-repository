import json
from datetime import datetime, timezone
from pathlib import Path


AUDIT_FILE = Path("audit_logs.jsonl")


def log_authorization_event(
    agent_id: str,
    task_id: str,
    action: str,
    resource: str,
    decision: str,
    risk: int,
    reason: str
):
    """
    Store one authorization decision as a JSON Lines event.
    """

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_id": agent_id,
        "task_id": task_id,
        "action": action,
        "resource": resource,
        "decision": decision,
        "risk": risk,
        "reason": reason
    }

    with AUDIT_FILE.open(
        "a",
        encoding="utf-8"
    ) as file:
        file.write(
            json.dumps(event) + "\n"
        )

    return event