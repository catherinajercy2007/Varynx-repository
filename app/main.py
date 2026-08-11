from fastapi import FastAPI

from app.models import (
    AuthorizationRequest,
    AuthorizationResponse,
    AgentRegistrationRequest,
    AgentRegistrationResponse,
    TaskRequest
)

from app.policy import check_policy

from app.identity import (
    register_agent,
    verify_agent,
    create_task,
    verify_task,
    get_task
)


app = FastAPI(
    title="Aegis AI Agent Cloud Firewall",
    description="Intent-Aware Dynamic Authorization Gateway",
    version="0.3.0"
)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return {
        "project": "Aegis AI Agent Cloud Firewall",
        "version": "0.3.0",
        "status": "running",
        "security_features": [
            "Agent Identity",
            "API Key Verification",
            "Task Identity",
            "Task Expiration",
            "Intent-Aware Authorization",
            "Resource Scope Validation"
        ]
    }


# ============================================================
# AGENT REGISTRATION
# ============================================================

@app.post(
    "/agents/register",
    response_model=AgentRegistrationResponse
)
def register_agent_endpoint(
    request: AgentRegistrationRequest
):
    """
    Register a new AI agent.

    A unique API key is generated for the agent.
    """

    api_key = register_agent(
        request.agent_id,
        request.name
    )

    if api_key is None:
        return {
            "agent_id": request.agent_id,
            "api_key": "Agent already exists"
        }

    return {
        "agent_id": request.agent_id,
        "api_key": api_key
    }


# ============================================================
# TASK CREATION
# ============================================================

@app.post("/tasks/create")
def create_task_endpoint(
    request: TaskRequest
):
    """
    Create a temporary task for an authenticated agent.
    """

    # --------------------------------------------------------
    # Step 1: Verify agent identity
    # --------------------------------------------------------

    if not verify_agent(
        request.agent_id,
        request.api_key
    ):
        return {
            "decision": "DENY",
            "reason": "Invalid agent identity"
        }

    # --------------------------------------------------------
    # Step 2: Create task
    # --------------------------------------------------------

    task = create_task(
        request.task_id,
        request.agent_id,
        request.intent,
        request.duration_minutes
    )

    if task is None:
        return {
            "decision": "DENY",
            "reason": "Task already exists"
        }

    return {
        "decision": "ALLOW",
        "task_id": request.task_id,
        "agent_id": request.agent_id,
        "intent": request.intent,
        "expires_at": task["expires_at"]
    }


# ============================================================
# AUTHORIZATION
# ============================================================

@app.post(
    "/authorize",
    response_model=AuthorizationResponse
)
def authorize(
    request: AuthorizationRequest
):
    """
    Main Aegis authorization endpoint.

    Authorization flow:

    1. Verify agent identity
    2. Verify task
    3. Retrieve task intent
    4. Apply deterministic security policy
    5. Return ALLOW or DENY
    """

    # ========================================================
    # STEP 1 — VERIFY AGENT IDENTITY
    # ========================================================

    if not verify_agent(
        request.agent_id,
        request.api_key
    ):
        return {
            "decision": "DENY",
            "risk": 100,
            "reason": "Invalid agent identity"
        }

    # ========================================================
    # STEP 2 — VERIFY TASK
    # ========================================================

    if not verify_task(
        request.task_id,
        request.agent_id
    ):
        return {
            "decision": "DENY",
            "risk": 95,
            "reason": "Invalid or expired task"
        }

    # ========================================================
    # STEP 3 — RETRIEVE TASK
    # ========================================================

    task = get_task(
        request.task_id,
        request.agent_id
    )

    if task is None:
        return {
            "decision": "DENY",
            "risk": 95,
            "reason": "Task could not be retrieved"
        }

    # ========================================================
    # STEP 4 — EXTRACT TASK INTENT
    # ========================================================

    intent = task["intent"]

    # ========================================================
    # STEP 5 — APPLY SECURITY POLICY
    # ========================================================

    result = check_policy(
        request.agent_id,
        request.action,
        request.resource,
        intent
    )

    # ========================================================
    # STEP 6 — RETURN DECISION
    # ========================================================

    return result


# ============================================================
# DEBUG ENDPOINT
# ============================================================
# This is useful during development.
#
# IMPORTANT:
# Remove this endpoint before deploying the application
# publicly because it exposes internal agent information.
# ============================================================

@app.get("/debug/agents")
def debug_agents():
    from app.identity import AGENTS

    return {
        "registered_agents": list(AGENTS.keys())
    }


# ============================================================
# DEBUG TASK ENDPOINT
# ============================================================
# Development only.
# Remove before production deployment.
# ============================================================

@app.get("/debug/tasks")
def debug_tasks():
    from app.identity import TASKS

    return {
        "registered_tasks": {
            task_id: {
                "agent_id": task["agent_id"],
                "intent": task["intent"],
                "active": task["active"],
                "expires_at": task["expires_at"]
            }
            for task_id, task in TASKS.items()
        }
    }