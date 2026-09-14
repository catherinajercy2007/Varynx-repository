import pytest

from app.runtime_execution import RuntimeExecutionService
from app.runtime_enforcement import RuntimeEnforcementError


def test_block_stops_runtime_execution():
    executed = []

    def fake_tool(request):
        executed.append(request)
        return "executed"

    service = RuntimeExecutionService()

    with pytest.raises(RuntimeEnforcementError):
        service.execute(
            decision="BLOCK",
            tool=fake_tool,
            request={"resource": "sensitive_data"},
        )

    assert executed == []


def test_allow_reaches_runtime_execution():
    def fake_tool(request):
        return "executed"

    service = RuntimeExecutionService()

    result = service.execute(
        decision="ALLOW",
        tool=fake_tool,
        request={"resource": "sales.csv"},
    )

    assert result == "executed"

def test_blocked_runtime_execution_is_audited():
    executed = []

    def fake_tool(request):
        executed.append(request)
        return "executed"

    service = RuntimeExecutionService()

    with pytest.raises(RuntimeEnforcementError):
        service.execute(
            decision="DENY",
            tool=fake_tool,
            request={"resource": "sensitive_data"},
            agent_id="test-agent",
            task_id="test-task",
            action="read",
            resource="sensitive_data",
            risk=100,
            reason="Runtime security blocked execution",
        )

    assert executed == []