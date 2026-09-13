AGENT_POLICIES = {
    "research-agent": {
        "intents": {
            "summarize_public_documents": {
                "allowed_actions": ["s3:GetObject"],
                "allowed_resource_prefixes": ["public/"]
            }
        }
    },

    "data-analysis-agent": {
        "intents": {
            "analyze_public_data": {
                "allowed_actions": ["s3:GetObject"],
                "allowed_resource_prefixes": ["public/"]
            }
        }
    },

    "security-audit-agent": {
        "intents": {
            "audit_public_logs": {
                "allowed_actions": ["s3:GetObject"],
                "allowed_resource_prefixes": ["public/audit/"]
            }
        }
    },

    "risk-test-agent": {
        "intents": {
            "analyze_public_data": {
                "allowed_actions": ["s3:GetObject"],
                "allowed_resource_prefixes": ["public/"]
            }
        }
    },

    "risk-test-agent-2": {
        "intents": {
            "analyze_public_data": {
                "allowed_actions": ["s3:GetObject"],
                "allowed_resource_prefixes": ["public/"]
            }
        }
    },

    "day8-risk-agent": {
        "intents": {
            "analyze_public_data": {
                "allowed_actions": ["s3:GetObject"],
                "allowed_resource_prefixes": ["public/"]
            }
        }
    },

    "day9-risk-agent": {
        "intents": {
            "analyze_public_data": {
                "allowed_actions": ["s3:GetObject"],
                "allowed_resource_prefixes": ["public/"]
            }
        }
    }
}


def check_policy(
    agent_id: str,
    action: str,
    resource: str,
    intent: str
):
    # --------------------------------------------------------
    # 1. VERIFY AGENT
    # --------------------------------------------------------

    if agent_id not in AGENT_POLICIES:
        return {
            "decision": "DENY",
            "risk": 95,
            "reason": "Agent is not authorized"
        }

    agent_policy = AGENT_POLICIES[agent_id]

    # --------------------------------------------------------
    # 2. VERIFY INTENT
    # --------------------------------------------------------

    if intent not in agent_policy["intents"]:
        return {
            "decision": "DENY",
            "risk": 85,
            "reason": "Intent is not authorized for this agent"
        }

    intent_policy = agent_policy["intents"][intent]

    # --------------------------------------------------------
    # 3. VERIFY ACTION
    # --------------------------------------------------------

    if action not in intent_policy["allowed_actions"]:
        return {
            "decision": "DENY",
            "risk": 90,
            "reason": "Action is not permitted for this task intent"
        }

    # --------------------------------------------------------
    # 4. VERIFY RESOURCE
    # --------------------------------------------------------

    resource_allowed = any(
        resource.startswith(prefix)
        for prefix in intent_policy["allowed_resource_prefixes"]
    )

    if not resource_allowed:
        return {
            "decision": "DENY",
            "risk": 85,
            "reason": "Resource is outside the task scope"
        }

    # --------------------------------------------------------
    # 5. ALLOW
    # --------------------------------------------------------

    return {
        "decision": "ALLOW",
        "risk": 5,
        "reason": "Identity, task intent, action and resource satisfy policy"
    }