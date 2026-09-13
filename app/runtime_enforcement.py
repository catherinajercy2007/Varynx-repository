from typing import Any, Callable

from app.adaptive_response import ResponseAction


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
    ) -> Any:

        # Convert Enum to string
        if isinstance(decision, ResponseAction):
            decision = decision.value

        # BLOCK
        if decision == ResponseAction.BLOCK.value:
            raise RuntimeEnforcementError(
                "Action blocked by runtime security policy"
            )

        # ALLOW
        if decision == ResponseAction.ALLOW.value:
            return tool(request)

        # ALLOW WITH MONITORING
        if decision == ResponseAction.ALLOW_WITH_MONITORING.value:
            event = {
                "decision": decision,
                "request": request,
                "action": "executed_with_monitoring",
            }

            self.security_events.append(event)

            print(
                "ALLOW_WITH_MONITORING: "
                "executing with enhanced monitoring"
            )

            return tool(request)

        # STEP UP VERIFICATION
        if decision == ResponseAction.STEP_UP_VERIFICATION.value:
            raise RuntimeEnforcementError(
                "Additional verification required before execution"
            )

        # REDUCE SCOPE
        if decision == ResponseAction.REDUCE_SCOPE.value:
            raise RuntimeEnforcementError(
                "Execution requires reduced scope"
            )

        # HUMAN REVIEW
        if decision == ResponseAction.HUMAN_REVIEW.value:
            raise RuntimeEnforcementError(
                "Execution paused pending human review"
            )

        # UNKNOWN DECISION
        raise RuntimeEnforcementError(
            f"Unknown security decision: {decision}"
        )