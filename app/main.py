from fastapi import FastAPI

from app.models import (
    AuthorizationRequest,
    AuthorizationResponse,
    AgentRegistrationRequest,
    AgentRegistrationResponse,
    TaskRequest,
)

from app.identity import (
    register_agent,
    verify_agent,
    create_task,
)

from app.authorization import AuthorizationService

from app.database import (
    initialize_database,
    get_audit_events,
)


app = FastAPI(
    title="AegisGuard",
    description="Intent-Aware Dynamic Authorization Gateway for Autonomous AI Agents",
    version="0.9.0",
)


initialize_database()


@app.get("/")
def root():

    return {
        "project": "AegisGuard",
        "status": "running",
        "version": "0.9.0",
    }


@app.post(
    "/agents/register",
    response_model=AgentRegistrationResponse,
)
def register_new_agent(
    request: AgentRegistrationRequest,
):

    api_key = register_agent(
        agent_id=request.agent_id,
        name=request.name,
    )

    if api_key is None:

        return {
            "agent_id": request.agent_id,
            "api_key": "",
        }

    return {
        "agent_id": request.agent_id,
        "api_key": api_key,
    }


@app.post("/tasks/create")
def create_new_task(
    request: TaskRequest,
):

    if not verify_agent(
        request.agent_id,
        request.api_key,
    ):

        return {
            "decision": "DENY",
            "risk": 100,
            "reason": "Invalid agent identity",
        }

    return create_task(
        task_id=request.task_id,
        agent_id=request.agent_id,
        intent=request.intent,
        duration_minutes=request.duration_minutes,
    )


@app.post(
    "/authorize",
    response_model=AuthorizationResponse,
)
def authorize(
    request: AuthorizationRequest,
):

    return AuthorizationService.authorize(
        agent_id=request.agent_id,
        api_key=request.api_key,
        task_id=request.task_id,
        action=request.action,
        resource=request.resource,
    )


@app.get("/debug/agents")
def debug_agents():

    from app.identity import AGENTS

    return {
        "registered_agents": AGENTS,
    }


@app.get("/debug/tasks")
def debug_tasks():

    from app.identity import TASKS

    return {
        "registered_tasks": TASKS,
    }


@app.get("/audit/logs")
def get_audit_logs():

    return {
        "events": get_audit_events(),
    }