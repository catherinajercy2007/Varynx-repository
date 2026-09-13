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