import pytest

from app.runtime_execution import RuntimeExecutionService
from app.runtime_enforcement import RuntimeEnforcementError
from app.authorization import AuthorizationService
def test_deny_is_enforced_as_block():
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
        )

    assert executed == []

from app.authorization import AuthorizationService
def test_authorization_deny_reaches_runtime_as_block(monkeypatch):
    executed = []

    def fake_tool(request):
        executed.append(request)
        return "executed"

    def fake_authorize(*args, **kwargs):
        return {
            "decision": "DENY",
            "risk": 100,
            "reason": "Test authorization denial",
        }

    monkeypatch.setattr(
        AuthorizationService,
        "authorize",
        staticmethod(fake_authorize),
    )

    authorization_result = AuthorizationService.authorize(
        agent_id="test-agent",
        api_key="test-key",
        task_id="test-task",
        action="read",
        resource="sensitive_data",
    )

    service = RuntimeExecutionService()

    with pytest.raises(RuntimeEnforcementError):
        service.execute(
            decision=authorization_result["decision"],
            tool=fake_tool,
            request={"resource": "sensitive_data"},
        )

    assert executed == []

def test_authorization_allow_reaches_runtime(monkeypatch):
    executed = []

    def fake_tool(request):
        executed.append(request)
        return "executed"

    def fake_authorize(*args, **kwargs):
        return {
            "decision": "ALLOW",
            "risk": 10,
            "reason": "Test authorization allowed",
        }

    monkeypatch.setattr(
        AuthorizationService,
        "authorize",
        staticmethod(fake_authorize),
    )

    authorization_result = AuthorizationService.authorize(
        agent_id="test-agent",
        api_key="test-key",
        task_id="test-task",
        action="read",
        resource="sales.csv",
    )

    service = RuntimeExecutionService()

    result = service.execute(
        decision=authorization_result["decision"],
        tool=fake_tool,
        request={"resource": "sales.csv"},
    )

    assert result == "executed"
    assert executed == [{"resource": "sales.csv"}]

def test_blocked_runtime_event_can_be_retrieved(monkeypatch, tmp_path):
    from app import database

    database_file = tmp_path / "runtime_audit.db"
    monkeypatch.setattr(database, "DATABASE_FILE", database_file)

    database.initialize_database()

    service = RuntimeExecutionService()

    with pytest.raises(RuntimeEnforcementError):
        service.execute(
            decision="DENY",
            tool=lambda request: "executed",
            request={"resource": "sensitive_data"},
            agent_id="test-agent",
            task_id="test-task",
            action="read",
            resource="sensitive_data",
            risk=100,
            reason="Runtime security blocked execution",
        )

    events = database.get_audit_events()

    assert len(events) == 1
    assert events[0]["agent_id"] == "test-agent"
    assert events[0]["task_id"] == "test-task"
    assert events[0]["action"] == "read"
    assert events[0]["resource"] == "sensitive_data"
    assert events[0]["decision"] == "BLOCK"
    assert events[0]["risk"] == 100
    assert events[0]["reason"] == "Runtime security blocked execution"

def test_allow_with_monitoring_reaches_runtime():
    executed = []

    def fake_tool(request):
        executed.append(request)
        return "executed"

    service = RuntimeExecutionService()

    result = service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=fake_tool,
        request={"resource": "sales.csv"},
    )

    assert result == "executed"
    assert executed == [{"resource": "sales.csv"}]

def test_unknown_runtime_decision_is_rejected():
    executed = []

    def fake_tool(request):
        executed.append(request)
        return "executed"

    service = RuntimeExecutionService()

    with pytest.raises(RuntimeEnforcementError):
        service.execute(
            decision="UNKNOWN_DECISION",
            tool=fake_tool,
            request={"resource": "sensitive_data"},
        )

    assert executed == []