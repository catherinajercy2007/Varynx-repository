import copy
from typing import Any, Callable

from app.adaptive_response import ResponseAction
from app.audit import log_authorization_event


class RuntimeEnforcementError(Exception):
    """Raised when runtime security enforcement fails."""


class RuntimeSecurityGateway:
    """
    Runtime enforcement boundary.

    Consumes an already-computed security decision and decides
    whether the requested operation may execute.
    """

    def __init__(self):
        self.security_events = []

    def enforce(
        self,
        decision: str | ResponseAction,
        tool: Callable[[Any], Any],
        request: Any,
        agent_id: str | None = None,
        task_id: str | None = None,
        action: str | None = None,
        resource: str | None = None,
        risk: int = 0,
        reason: str = "",
    ) -> Any:

        if isinstance(decision, ResponseAction):
            decision = decision.value

        if decision == ResponseAction.BLOCK.value:
            if all(
                value is not None
                for value in (
                    agent_id,
                    task_id,
                    action,
                    resource,
                )
            ):
                log_authorization_event(
                    agent_id=agent_id,
                    task_id=task_id,
                    action=action,
                    resource=resource,
                    decision="BLOCK",
                    risk=risk,
                    reason=reason or "Runtime security blocked execution",
                )

            self.security_events.append(
                {
                    "decision": decision,
                    "request": copy.deepcopy(request),
                    "action": "execution_blocked",
                }
            )

            raise RuntimeEnforcementError(
                "Action blocked by runtime security policy"
            )

        if decision == ResponseAction.ALLOW.value:
            return tool(request)

        if decision == ResponseAction.ALLOW_WITH_MONITORING.value:
            event = {
                "decision": decision,
                "request": copy.deepcopy(request),
                "action": "executed_with_monitoring",
            }

            self.security_events.append(event)

            print(
                "ALLOW_WITH_MONITORING: "
                "executing with enhanced monitoring"
            )

            return tool(request)

        if decision == ResponseAction.STEP_UP_VERIFICATION.value:
            raise RuntimeEnforcementError(
                "Additional verification required before execution"
            )

        if decision == ResponseAction.REDUCE_SCOPE.value:
            raise RuntimeEnforcementError(
                "Execution requires reduced scope"
            )

        if decision == ResponseAction.HUMAN_REVIEW.value:
            raise RuntimeEnforcementError(
                "Execution paused pending human review"
            )

        raise RuntimeEnforcementError(
            f"Unknown security decision: {decision}"
        )