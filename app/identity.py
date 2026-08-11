import secrets
import hashlib


# Temporary in-memory agent registry.
# We will replace this with a database later.
AGENTS = {}


def register_agent(agent_id: str, name: str):
    """
    Register an agent and generate a secret API key.
    """

    if agent_id in AGENTS:
        return None

    raw_key = secrets.token_urlsafe(32)

    key_hash = hashlib.sha256(
        raw_key.encode()
    ).hexdigest()

    AGENTS[agent_id] = {
        "name": name,
        "key_hash": key_hash,
        "active": True
    }

    return raw_key


def verify_agent(agent_id: str, api_key: str):
    """
    Verify that the supplied API key belongs to the agent.
    """

    agent = AGENTS.get(agent_id)

    if not agent:
        return False

    if not agent["active"]:
        return False

    supplied_hash = hashlib.sha256(
        api_key.encode()
    ).hexdigest()

    return secrets.compare_digest(
        supplied_hash,
        agent["key_hash"]
    )
from datetime import datetime, timedelta, timezone


TASKS = {}


def create_task(
    task_id: str,
    agent_id: str,
    intent: str,
    duration_minutes: int = 10
):
    """
    Create a temporary task for an authenticated agent.
    """

    if task_id in TASKS:
        return None

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(minutes=duration_minutes)
    )

    TASKS[task_id] = {
        "agent_id": agent_id,
        "intent": intent,
        "created_at": datetime.now(timezone.utc),
        "expires_at": expires_at,
        "active": True
    }

    return TASKS[task_id]


def verify_task(
    task_id: str,
    agent_id: str
):
    """
    Verify that the task exists,
    belongs to the agent,
    and has not expired.
    """

    task = TASKS.get(task_id)

    if not task:
        return False

    if not task["active"]:
        return False

    if task["agent_id"] != agent_id:
        return False

    now = datetime.now(timezone.utc)

    if now >= task["expires_at"]:
        task["active"] = False
        return False

    return True
def get_task(task_id: str, agent_id: str):
    """
    Return task information if the task belongs
    to the specified agent and is still active.
    """

    task = TASKS.get(task_id)

    if not task:
        return None

    if not task["active"]:
        return None

    if task["agent_id"] != agent_id:
        return None

    now = datetime.now(timezone.utc)

    if now >= task["expires_at"]:
        task["active"] = False
        return None

    return task