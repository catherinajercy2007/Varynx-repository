from app.database import save_audit_event


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
    Store an authorization decision in the
    persistent SQLite audit database.
    """

    return save_audit_event(
        agent_id=agent_id,
        task_id=task_id,
        action=action,
        resource=resource,
        decision=decision,
        risk=risk,
        reason=reason
    )