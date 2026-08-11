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
    verify_task
)


app = FastAPI(
    title="Aegis AI Agent Cloud Firewall",
    version="0.2.0"
)


@app.get("/")
def home():
    return {
        "project": "Aegis AI Agent Cloud Firewall",
        "version": "0.2.0",
        "status": "running"
    }


@app.post(
    "/agents/register",
    response_model=AgentRegistrationResponse
)
def register_agent_endpoint(
    request: AgentRegistrationRequest
):

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


@app.post("/tasks/create")
def create_task_endpoint(
    request: TaskRequest
):

    if not verify_agent(
        request.agent_id,
        request.api_key
    ):
        return {
            "decision": "DENY",
            "reason": "Invalid agent identity"
        }

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


@app.post(
    "/authorize",
    response_model=AuthorizationResponse
)
def authorize(
    request: AuthorizationRequest
):

    # Step 1: Verify agent identity

    if not verify_agent(
        request.agent_id,
        request.api_key
    ):
        return {
            "decision": "DENY",
            "risk": 100,
            "reason": "Invalid agent identity"
        }

    # Step 2: Verify task

    if not verify_task(
        request.task_id,
        request.agent_id
    ):
        return {
            "decision": "DENY",
            "risk": 95,
            "reason": "Invalid or expired task"
        }

    # Step 3: Apply authorization policy

    result = check_policy(
        request.agent_id,
        request.action,
        request.resource
    )

    return result