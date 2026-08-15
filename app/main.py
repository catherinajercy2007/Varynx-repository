from fastapi import FastAPI
from pathlib import Path
import json

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

from app.audit import log_authorization_event


app = FastAPI(
    title="AegisGuard",
    description="Intent-Aware Dynamic Authorization Gateway for AI Agents",
    version="0.5.0"
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def root():
    return {
        "project": "AegisGuard",
        "status": "running",
        "version": "0.5.0"
    }


# ============================================================
# AGENT REGISTRATION
# ============================================================

@app.post(
    "/agents/register",
    response_model=AgentRegistrationResponse
)
def register_new_agent(request: AgentRegistrationRequest):

    api_key = register_agent(
        agent_id=request.agent_id,
        name=request.name
    )

    if api_key is None:
        return {
            "agent_id": request.agent_id,
            "api_key": ""
        }

    return {
        "agent_id": request.agent_id,
        "api_key": api_key
    }


# ============================================================
# TASK CREATION
# ============================================================

@app.post("/tasks/create")
def create_new_task(request: TaskRequest):

    if not verify_agent(
        request.agent_id,
        request.api_key
    ):
        return {
            "decision": "DENY",
            "risk": 100,
            "reason": "Invalid agent identity"
        }

    result = create_task(
        task_id=request.task_id,
        agent_id=request.agent_id,
        intent=request.intent,
        duration_minutes=request.duration_minutes
    )

    return result


# ============================================================
# CENTRAL AUTHORIZATION
# ============================================================

@app.post(
    "/authorize",
    response_model=AuthorizationResponse
)
def authorize(request: AuthorizationRequest):

    # --------------------------------------------------------
    # 1. VERIFY AGENT
    # --------------------------------------------------------

    if not verify_agent(
        request.agent_id,
        request.api_key
    ):

        result = {
            "decision": "DENY",
            "risk": 100,
            "reason": "Invalid agent identity"
        }

        log_authorization_event(
            agent_id=request.agent_id,
            task_id=request.task_id,
            action=request.action,
            resource=request.resource,
            decision=result["decision"],
            risk=result["risk"],
            reason=result["reason"]
        )

        return result

    # --------------------------------------------------------
    # 2. VERIFY TASK
    # --------------------------------------------------------

    if not verify_task(
        request.task_id,
        request.agent_id
    ):

        result = {
            "decision": "DENY",
            "risk": 95,
            "reason": "Invalid or expired task"
        }

        log_authorization_event(
            agent_id=request.agent_id,
            task_id=request.task_id,
            action=request.action,
            resource=request.resource,
            decision=result["decision"],
            risk=result["risk"],
            reason=result["reason"]
        )

        return result

    # --------------------------------------------------------
    # 3. GET TASK
    # --------------------------------------------------------

    task = get_task(
        request.task_id,
        request.agent_id
    )

    if task is None:

        result = {
            "decision": "DENY",
            "risk": 95,
            "reason": "Task not found"
        }

        log_authorization_event(
            agent_id=request.agent_id,
            task_id=request.task_id,
            action=request.action,
            resource=request.resource,
            decision=result["decision"],
            risk=result["risk"],
            reason=result["reason"]
        )

        return result

    # --------------------------------------------------------
    # 4. GET TRUSTED INTENT
    # --------------------------------------------------------

    intent = task["intent"]

    # --------------------------------------------------------
    # 5. CHECK POLICY
    # --------------------------------------------------------

    result = check_policy(
        agent_id=request.agent_id,
        intent=intent,
        action=request.action,
        resource=request.resource
    )

    # --------------------------------------------------------
    # 6. AUDIT DECISION
    # --------------------------------------------------------

    log_authorization_event(
        agent_id=request.agent_id,
        task_id=request.task_id,
        action=request.action,
        resource=request.resource,
        decision=result["decision"],
        risk=result["risk"],
        reason=result["reason"]
    )

    # --------------------------------------------------------
    # 7. RETURN RESULT
    # --------------------------------------------------------

    return result


# ============================================================
# DEBUG - AGENTS
# ============================================================

@app.get("/debug/agents")
def debug_agents():

    from app.identity import AGENTS

    return {
        "registered_agents": AGENTS
    }


# ============================================================
# DEBUG - TASKS
# ============================================================

@app.get("/debug/tasks")
def debug_tasks():

    from app.identity import TASKS

    return {
        "registered_tasks": TASKS
    }


# ============================================================
# AUDIT LOGS
# ============================================================

@app.get("/audit/logs")
def get_audit_logs():

    audit_file = Path("audit_logs.jsonl")

    if not audit_file.exists():
        return {
            "events": []
        }

    events = []

    with audit_file.open(
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            try:
                event = json.loads(line)

                if isinstance(event, dict):
                    events.append(event)

            except json.JSONDecodeError:
                continue

    return {
        "events": events
    }