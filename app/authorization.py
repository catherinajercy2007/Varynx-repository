from app.identity import (
    verify_agent,
    verify_task,
    get_task
)

from app.policy import check_policy

from app.audit import log_authorization_event

from app.risk import calculate_risk


class AuthorizationService:
    """
    Central authorization service for AegisGuard.

    The service performs:

    1. Agent verification
    2. Task verification
    3. Trusted intent retrieval
    4. Policy evaluation
    5. Risk evaluation
    6. Audit logging
    """

    @staticmethod
    def _deny(
        agent_id: str,
        task_id: str,
        action: str,
        resource: str,
        risk: int,
        reason: str
    ):
        """
        Create, risk-evaluate and audit a DENY decision.
        """

        result = {
            "decision": "DENY",
            "risk": risk,
            "reason": reason
        }

        log_authorization_event(
            agent_id=agent_id,
            task_id=task_id,
            action=action,
            resource=resource,
            decision=result["decision"],
            risk=result["risk"],
            reason=result["reason"]
        )

        return result

    @staticmethod
    def authorize(
        agent_id: str,
        api_key: str,
        task_id: str,
        action: str,
        resource: str
    ):
        """
        Execute the complete authorization workflow.
        """

        # ----------------------------------------------------
        # 1. VERIFY AGENT
        # ----------------------------------------------------

        if not verify_agent(
            agent_id,
            api_key
        ):

            return AuthorizationService._deny(
                agent_id=agent_id,
                task_id=task_id,
                action=action,
                resource=resource,
                risk=100,
                reason="Invalid agent identity"
            )

        # ----------------------------------------------------
        # 2. VERIFY TASK
        # ----------------------------------------------------

        if not verify_task(
            task_id,
            agent_id
        ):

            return AuthorizationService._deny(
                agent_id=agent_id,
                task_id=task_id,
                action=action,
                resource=resource,
                risk=95,
                reason="Invalid or expired task"
            )

        # ----------------------------------------------------
        # 3. GET TASK
        # ----------------------------------------------------

        task = get_task(
            task_id,
            agent_id
        )

        if task is None:

            return AuthorizationService._deny(
                agent_id=agent_id,
                task_id=task_id,
                action=action,
                resource=resource,
                risk=95,
                reason="Task not found"
            )

        # ----------------------------------------------------
        # 4. GET TRUSTED TASK INTENT
        # ----------------------------------------------------

        intent = task["intent"]

        # ----------------------------------------------------
        # 5. POLICY EVALUATION
        # ----------------------------------------------------

        policy_result = check_policy(
            agent_id=agent_id,
            intent=intent,
            action=action,
            resource=resource
        )

        decision = policy_result["decision"]
        reason = policy_result["reason"]

        # ----------------------------------------------------
        # 6. RISK EVALUATION
        # ----------------------------------------------------

        risk = calculate_risk(
            decision=decision,
            action=action,
            resource=resource,
            reason=reason
        )

        result = {
            "decision": decision,
            "risk": risk,
            "reason": reason
        }

        # ----------------------------------------------------
        # 7. AUDIT
        # ----------------------------------------------------

        log_authorization_event(
            agent_id=agent_id,
            task_id=task_id,
            action=action,
            resource=resource,
            decision=decision,
            risk=risk,
            reason=reason
        )

        # ----------------------------------------------------
        # 8. RETURN
        # ----------------------------------------------------

        return result