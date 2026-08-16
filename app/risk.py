from typing import Any


class RiskEngine:
    """
    Day 9 risk-adaptive authorization engine.

    Produces:
        - risk score: 0-100
        - risk level
        - risk factors
        - recommended decision
    """

    SENSITIVE_RESOURCE_KEYWORDS = (
        "private/",
        "confidential/",
        "secret/",
        "secrets/",
        "credentials/",
        "customer/",
        "admin/",
    )

    HIGH_RISK_ACTION_KEYWORDS = (
        "delete",
        "destroy",
        "terminate",
        "drop",
        "remove",
    )

    PRIVILEGED_ACTION_KEYWORDS = (
        "iam:",
        "admin",
        "root",
        "privilege",
    )

    @staticmethod
    def calculate(
        decision: str,
        action: str,
        resource: str,
        reason: str = "",
    ) -> dict[str, Any]:

        decision = decision.upper()

        action_lower = action.lower()
        resource_lower = resource.lower()
        reason_lower = reason.lower()

        score = 5
        factors = []

        # --------------------------------------------------
        # POLICY DECISION
        # --------------------------------------------------

        if decision == "DENY":
            score += 40
            factors.append("Policy denied the request")

        # --------------------------------------------------
        # SENSITIVE RESOURCE
        # --------------------------------------------------

        if any(
            keyword in resource_lower
            for keyword in RiskEngine.SENSITIVE_RESOURCE_KEYWORDS
        ):
            score += 25
            factors.append("Sensitive resource")

        # --------------------------------------------------
        # HIGH-RISK ACTION
        # --------------------------------------------------

        if any(
            keyword in action_lower
            for keyword in RiskEngine.HIGH_RISK_ACTION_KEYWORDS
        ):
            score += 35
            factors.append("High-risk action")

        # --------------------------------------------------
        # PRIVILEGED ACTION
        # --------------------------------------------------

        if any(
            keyword in action_lower
            for keyword in RiskEngine.PRIVILEGED_ACTION_KEYWORDS
        ):
            score += 30
            factors.append("Privileged action")

        # --------------------------------------------------
        # UNAUTHORIZED REQUEST
        # --------------------------------------------------

        if "unauthorized" in reason_lower:
            score += 20
            factors.append("Unauthorized request")

        # --------------------------------------------------
        # INVALID IDENTITY
        # --------------------------------------------------

        if "invalid agent" in reason_lower:
            score += 50
            factors.append("Invalid agent identity")

        # --------------------------------------------------
        # INVALID TASK
        # --------------------------------------------------

        if "invalid or expired task" in reason_lower:
            score += 40
            factors.append("Invalid or expired task")

        # --------------------------------------------------
        # CAP SCORE
        # --------------------------------------------------

        score = min(max(score, 0), 100)

        # --------------------------------------------------
        # RISK LEVEL
        # --------------------------------------------------

        if score <= 20:
            level = "LOW"

        elif score <= 50:
            level = "MEDIUM"

        elif score <= 80:
            level = "HIGH"

        else:
            level = "CRITICAL"

        # --------------------------------------------------
        # RISK-ADAPTIVE DECISION
        # --------------------------------------------------

        if decision == "DENY":
            final_decision = "DENY"

        elif score >= 80:
            final_decision = "DENY"

        else:
            final_decision = "ALLOW"

        return {
            "risk": score,
            "risk_level": level,
            "risk_factors": factors,
            "decision": final_decision,
        }


def calculate_risk(
    decision: str,
    action: str,
    resource: str,
    reason: str = "",
) -> int:

    result = RiskEngine.calculate(
        decision=decision,
        action=action,
        resource=resource,
        reason=reason,
    )

    return result["risk"]


def evaluate_risk(
    decision: str,
    action: str,
    resource: str,
    reason: str = "",
) -> dict[str, Any]:

    return RiskEngine.calculate(
        decision=decision,
        action=action,
        resource=resource,
        reason=reason,
    )