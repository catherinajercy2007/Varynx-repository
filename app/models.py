from pydantic import BaseModel


class AuthorizationRequest(BaseModel):
    agent_id: str
    api_key: str
    task_id: str
    action: str
    resource: str


class AuthorizationResponse(BaseModel):
    decision: str
    risk: int
    reason: str


class AgentRegistrationRequest(BaseModel):
    agent_id: str
    name: str


class AgentRegistrationResponse(BaseModel):
    agent_id: str
    api_key: str


class TaskRequest(BaseModel):
    agent_id: str
    api_key: str
    task_id: str
    intent: str
    duration_minutes: int = 10