from typing import Any, Callable

from app.runtime_enforcement import RuntimeSecurityGateway


class RuntimeExecutionService:
    """
    Connects an existing authorization decision
    to the runtime enforcement boundary.
    """

    def __init__(self, gateway=None):
        self.gateway = gateway or RuntimeSecurityGateway()

    def execute(
        self,
        decision: str,
        tool: Callable[[Any], Any],
        request: Any,
        agent_id: str | None = None,
        task_id: str | None = None,
        action: str | None = None,
        resource: str | None = None,
        risk: int = 0,
        reason: str = "",
    ) -> Any:

        if decision == "DENY":
            enforcement_decision = "BLOCK"
        else:
            enforcement_decision = decision

        return self.gateway.enforce(
            decision=enforcement_decision,
            tool=tool,
            request=request,
            agent_id=agent_id,
            task_id=task_id,
            action=action,
            resource=resource,
            risk=risk,
            reason=reason,
        )