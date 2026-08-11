ALLOWED_ACTIONS = {
    "research-agent": [
        "s3:GetObject"
    ]
}


def check_policy(agent_id: str, action: str, resource: str):
    if agent_id not in ALLOWED_ACTIONS:
        return {
            "decision": "DENY",
            "risk": 90,
            "reason": "Unknown agent"
        }

    if action not in ALLOWED_ACTIONS[agent_id]:
        return {
            "decision": "DENY",
            "risk": 90,
            "reason": "Action not allowed for this agent"
        }

    if not resource.startswith("public/"):
        return {
            "decision": "DENY",
            "risk": 80,
            "reason": "Resource is outside the allowed public area"
        }

    return {
        "decision": "ALLOW",
        "risk": 5,
        "reason": "Request satisfies security policy"
    }