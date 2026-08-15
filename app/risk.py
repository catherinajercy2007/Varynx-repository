class RiskEngine:
    """
    Deterministic prototype risk engine for AegisGuard.

    Risk score:
        0   = very low risk
        100 = critical risk

    The risk engine does not replace policy.
    Policy determines whether the request is authorized.
    The risk engine evaluates the security risk of the request.
    """

    SENSITIVE_RESOURCE_KEYWORDS = (
        "private/",
        "confidential/",
        "secret/",
        "secrets/",
        "admin/",
        "credentials/",
        "customer/"
    )

    HIGH_RISK_ACTION_KEYWORDS = (
        "delete",
        "destroy",
        "terminate",
        "drop",
        "remove"
    )

    PRIVILEGED_ACTION_KEYWORDS = (
        "iam:",
        "admin",
        "root",
        "privilege"
    )

    @staticmethod
    def calculate_risk(
        decision: str,
        action: str,
        resource: str,
        reason: str = ""
    ) -> int:
        """
        Calculate a deterministic risk score from 0 to 100.
        """

        decision = decision.upper()
        action_lower = action.lower()
        resource_lower = resource.lower()
        reason_lower = reason.lower()

        # ----------------------------------------------------
        # BASE RISK
        # ----------------------------------------------------

        if decision == "ALLOW":
            risk = 5
        else:
            risk = 50

        # ----------------------------------------------------
        # DENIED REQUEST
        # ----------------------------------------------------

        if decision == "DENY":
            risk += 20

        # ----------------------------------------------------
        # SENSITIVE RESOURCE
        # ----------------------------------------------------

        if any(
            keyword in resource_lower
            for keyword in RiskEngine.SENSITIVE_RESOURCE_KEYWORDS
        ):
            risk += 25

        # ----------------------------------------------------
        # HIGH-RISK ACTION
        # ----------------------------------------------------

        if any(
            keyword in action_lower
            for keyword in RiskEngine.HIGH_RISK_ACTION_KEYWORDS
        ):
            risk += 35

        # ----------------------------------------------------
        # PRIVILEGED ACTION
        # ----------------------------------------------------

        if any(
            keyword in action_lower
            for keyword in RiskEngine.PRIVILEGED_ACTION_KEYWORDS
        ):
            risk += 30

        # ----------------------------------------------------
        # POLICY DENIAL REASON
        # ----------------------------------------------------

        if "unauthorized" in reason_lower:
            risk += 10

        # ----------------------------------------------------
        # LIMIT SCORE
        # ----------------------------------------------------

        return min(max(risk, 0), 100)


def calculate_risk(
    decision: str,
    action: str,
    resource: str,
    reason: str = ""
) -> int:
    """
    Convenience function for calculating request risk.
    """

    return RiskEngine.calculate_risk(
        decision=decision,
        action=action,
        resource=resource,
        reason=reason
    )