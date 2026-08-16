from app.identity import (
    verify_agent,
    verify_task,
    get_task,
)

from app.policy import check_policy

from app.audit import log_authorization_event

from app.risk import evaluate_risk


class AuthorizationService:
    """
    Central authorization service.

    Day 9 adds risk-adaptive authorization to the
    existing identity, task, policy and audit flow.
    """

    @staticmethod
    def _deny(
        agent_id: str,
        task_id: str,
        action: str,
        resource: str,
        reason: str,
        risk: int = 100,
    ):

        result = {
            "decision": "DENY",
            "risk": risk,
            "reason": reason,
        }

        log_authorization_event(
            agent_id=agent_id,
            task_id=task_id,
            action=action,
            resource=resource,
            decision="DENY",
            risk=risk,
            reason=reason,
        )

        return result

    @staticmethod
    def authorize(
        agent_id: str,
        api_key: str,
        task_id: str,
        action: str,
        resource: str,
    ):

        # ====================================================
        # 1. VERIFY AGENT
        # ====================================================

        if not verify_agent(
            agent_id,
            api_key,
        ):
            return AuthorizationService._deny(
                agent_id=agent_id,
                task_id=task_id,
                action=action,
                resource=resource,
                risk=100,
                reason="Invalid agent identity",
            )

        # ====================================================
        # 2. VERIFY TASK
        # ====================================================

        if not verify_task(
            task_id,
            agent_id,
        ):
            return AuthorizationService._deny(
                agent_id=agent_id,
                task_id=task_id,
                action=action,
                resource=resource,
                risk=100,
                reason="Invalid or expired task",
            )

        # ====================================================
        # 3. GET TASK
        # ====================================================

        task = get_task(
            task_id,
            agent_id,
        )

        if task is None:
            return AuthorizationService._deny(
                agent_id=agent_id,
                task_id=task_id,
                action=action,
                resource=resource,
                risk=100,
                reason="Task not found",
            )

        # ====================================================
        # 4. TRUSTED TASK INTENT
        # ====================================================

        intent = task["intent"]

        # ====================================================
        # 5. POLICY EVALUATION
        # ====================================================

        policy_result = check_policy(
            agent_id=agent_id,
            action=action,
            resource=resource,
            intent=intent,
        )

        policy_decision = policy_result["decision"]
        policy_reason = policy_result["reason"]

        # ====================================================
        # 6. RISK EVALUATION
        # ====================================================

        risk_result = evaluate_risk(
            decision=policy_decision,
            action=action,
            resource=resource,
            reason=policy_reason,
        )

        final_decision = risk_result["decision"]
        risk = risk_result["risk"]

        # ====================================================
        # 7. BUILD RESPONSE
        # ====================================================

        if risk_result["risk_factors"]:

            factor_text = ", ".join(
                risk_result["risk_factors"]
            )

            final_reason = (
                f"{policy_reason}. "
                f"Risk level: {risk_result['risk_level']}. "
                f"Factors: {factor_text}"
            )

        else:

            final_reason = (
                f"{policy_reason}. "
                f"Risk level: {risk_result['risk_level']}."
            )

        result = {
            "decision": final_decision,
            "risk": risk,
            "reason": final_reason,
        }

        # ====================================================
        # 8. AUDIT
        # ====================================================

        log_authorization_event(
            agent_id=agent_id,
            task_id=task_id,
            action=action,
            resource=resource,
            decision=final_decision,
            risk=risk,
            reason=final_reason,
        )

        return result