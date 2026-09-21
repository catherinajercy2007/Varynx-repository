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

def test_allow_with_monitoring_records_security_event():
    service = RuntimeExecutionService()

    result = service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "executed",
        request={"resource": "sales.csv"},
    )

    assert result == "executed"
    assert len(service.gateway.security_events) == 1
    assert service.gateway.security_events[0]["decision"] == "ALLOW_WITH_MONITORING"
    assert service.gateway.security_events[0]["action"] == "executed_with_monitoring"
    assert service.gateway.security_events[0]["request"] == {
        "resource": "sales.csv"
    }

def test_runtime_security_events_are_preserved_across_executions():
    service = RuntimeExecutionService()

    first_result = service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "first-executed",
        request={"resource": "first.csv"},
    )

    second_result = service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "second-executed",
        request={"resource": "second.csv"},
    )

    assert first_result == "first-executed"
    assert second_result == "second-executed"

    events = service.gateway.security_events

    assert len(events) == 2
    assert events[0]["decision"] == "ALLOW_WITH_MONITORING"
    assert events[0]["action"] == "executed_with_monitoring"
    assert events[0]["request"] == {"resource": "first.csv"}

    assert events[1]["decision"] == "ALLOW_WITH_MONITORING"
    assert events[1]["action"] == "executed_with_monitoring"
    assert events[1]["request"] == {"resource": "second.csv"}

def test_runtime_security_events_can_be_filtered_by_action():
    service = RuntimeExecutionService()

    service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "executed",
        request={"resource": "sales.csv"},
    )

    with pytest.raises(RuntimeEnforcementError):
        service.execute(
            decision="DENY",
            tool=lambda request: "executed",
            request={"resource": "sensitive_data"},
        )

    monitoring_events = [
        event
        for event in service.gateway.security_events
        if event["action"] == "executed_with_monitoring"
    ]

    blocked_events = [
        event
        for event in service.gateway.security_events
        if event["action"] == "execution_blocked"
    ]

    assert len(monitoring_events) == 1
    assert monitoring_events[0]["request"] == {
        "resource": "sales.csv"
    }

    assert len(blocked_events) == 1
    assert blocked_events[0]["request"] == {
        "resource": "sensitive_data"
    }

def test_runtime_block_event_preserves_security_metadata():
    service = RuntimeExecutionService()

    with pytest.raises(RuntimeEnforcementError):
        service.execute(
            decision="DENY",
            tool=lambda request: "executed",
            request={"resource": "restricted.csv"},
            agent_id="agent-55",
            task_id="task-55",
            action="read",
            resource="restricted.csv",
            risk=95,
            reason="High risk runtime request",
        )

    event = service.gateway.security_events[0]

    assert event["decision"] == "BLOCK"
    assert event["action"] == "execution_blocked"
    assert event["request"] == {"resource": "restricted.csv"}

def test_previous_runtime_security_event_remains_unchanged():
    service = RuntimeExecutionService()

    service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "first-executed",
        request={"resource": "first.csv"},
    )

    first_event = service.gateway.security_events[0].copy()

    service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "second-executed",
        request={"resource": "second.csv"},
    )

    assert service.gateway.security_events[0] == first_event
    assert service.gateway.security_events[0]["request"] == {
        "resource": "first.csv"
    }

def test_runtime_security_events_preserve_execution_order():
    service = RuntimeExecutionService()

    service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "first-executed",
        request={"resource": "first.csv"},
    )

    with pytest.raises(RuntimeEnforcementError):
        service.execute(
            decision="DENY",
            tool=lambda request: "blocked",
            request={"resource": "blocked.csv"},
        )

    service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "third-executed",
        request={"resource": "third.csv"},
    )

    events = service.gateway.security_events

    assert len(events) == 3

    assert events[0]["action"] == "executed_with_monitoring"
    assert events[0]["request"] == {"resource": "first.csv"}

    assert events[1]["action"] == "execution_blocked"
    assert events[1]["request"] == {"resource": "blocked.csv"}

    assert events[2]["action"] == "executed_with_monitoring"
    assert events[2]["request"] == {"resource": "third.csv"}

def test_runtime_security_event_decision_matches_action():
    service = RuntimeExecutionService()

    service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "executed",
        request={"resource": "monitored.csv"},
    )

    with pytest.raises(RuntimeEnforcementError):
        service.execute(
            decision="DENY",
            tool=lambda request: "executed",
            request={"resource": "blocked.csv"},
        )

    events = service.gateway.security_events

    assert events[0]["decision"] == "ALLOW_WITH_MONITORING"
    assert events[0]["action"] == "executed_with_monitoring"

    assert events[1]["decision"] == "BLOCK"
    assert events[1]["action"] == "execution_blocked"

def test_runtime_security_events_contain_required_fields():
    service = RuntimeExecutionService()

    service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "executed",
        request={"resource": "monitored.csv"},
    )

    with pytest.raises(RuntimeEnforcementError):
        service.execute(
            decision="DENY",
            tool=lambda request: "executed",
            request={"resource": "blocked.csv"},
        )

    required_fields = {"decision", "request", "action"}

    for event in service.gateway.security_events:
        assert required_fields.issubset(event.keys())

def test_runtime_security_event_schema_is_stable():
    service = RuntimeExecutionService()

    service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "executed",
        request={"resource": "monitored.csv"},
    )

    with pytest.raises(RuntimeEnforcementError):
        service.execute(
            decision="DENY",
            tool=lambda request: "executed",
            request={"resource": "blocked.csv"},
        )

    events = service.gateway.security_events

    assert len(events) == 2

    for event in events:
        assert isinstance(event, dict)
        assert set(["decision", "request", "action"]).issubset(event.keys())
        assert isinstance(event["decision"], str)
        assert isinstance(event["action"], str)
        assert isinstance(event["request"], dict)

    assert events[0]["decision"] == "ALLOW_WITH_MONITORING"
    assert events[0]["action"] == "executed_with_monitoring"

    assert events[1]["decision"] == "BLOCK"
    assert events[1]["action"] == "execution_blocked"

def test_runtime_security_event_schema_values_are_valid():
    service = RuntimeExecutionService()

    service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "executed",
        request={"resource": "monitored.csv"},
    )

    with pytest.raises(RuntimeEnforcementError):
        service.execute(
            decision="DENY",
            tool=lambda request: "executed",
            request={"resource": "blocked.csv"},
        )

    events = service.gateway.security_events

    assert events[0]["decision"] == "ALLOW_WITH_MONITORING"
    assert events[0]["action"] == "executed_with_monitoring"
    assert events[0]["request"] == {
        "resource": "monitored.csv"
    }

    assert events[1]["decision"] == "BLOCK"
    assert events[1]["action"] == "execution_blocked"
    assert events[1]["request"] == {
        "resource": "blocked.csv"
    }

def test_runtime_security_event_request_isolation():
    service = RuntimeExecutionService()

    first_request = {"resource": "first.csv"}

    service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "executed",
        request=first_request,
    )

    first_event = service.gateway.security_events[0]

    first_request["resource"] = "modified.csv"

    assert first_event["request"] == {
        "resource": "first.csv"
    }

def test_runtime_security_event_request_snapshot_is_independent():
    service = RuntimeExecutionService()

    service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "executed",
        request={"resource": "first.csv"},
    )

    event = service.gateway.security_events[0]

    event["request"]["resource"] = "modified.csv"

    assert event["request"] == {
        "resource": "modified.csv"
    }

def test_runtime_security_event_nested_request_isolation():
    service = RuntimeExecutionService()

    request = {
        "resource": "sensitive.csv",
        "metadata": {
            "scope": ["read", "export"],
        },
    }

    service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "executed",
        request=request,
    )

    request["metadata"]["scope"].append("admin")

    event = service.gateway.security_events[0]

    assert event["request"] == {
        "resource": "sensitive.csv",
        "metadata": {
            "scope": ["read", "export"],
        },
    }

def test_runtime_security_events_are_isolated_from_each_other():
    service = RuntimeExecutionService()

    service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "first",
        request={
            "resource": "first.csv",
            "metadata": {"scope": ["read"]},
        },
    )

    service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "second",
        request={
            "resource": "second.csv",
            "metadata": {"scope": ["write"]},
        },
    )

    first_event = service.gateway.security_events[0]
    second_event = service.gateway.security_events[1]

    first_event["request"]["metadata"]["scope"].append("export")

    assert first_event["request"] == {
        "resource": "first.csv",
        "metadata": {"scope": ["read", "export"]},
    }

    assert second_event["request"] == {
        "resource": "second.csv",
        "metadata": {"scope": ["write"]},
    }

def test_runtime_security_events_preserve_nested_request_order():
    service = RuntimeExecutionService()

    service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "first",
        request={
            "resource": "first.csv",
            "metadata": {"scope": ["read"]},
        },
    )

    with pytest.raises(RuntimeEnforcementError):
        service.execute(
            decision="DENY",
            tool=lambda request: "blocked",
            request={
                "resource": "blocked.csv",
                "metadata": {"scope": ["deny"]},
            },
        )

    service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "third",
        request={
            "resource": "third.csv",
            "metadata": {"scope": ["write"]},
        },
    )

    events = service.gateway.security_events

    assert len(events) == 3

    assert events[0]["action"] == "executed_with_monitoring"
    assert events[0]["request"] == {
        "resource": "first.csv",
        "metadata": {"scope": ["read"]},
    }

    assert events[1]["action"] == "execution_blocked"
    assert events[1]["request"] == {
        "resource": "blocked.csv",
        "metadata": {"scope": ["deny"]},
    }

    assert events[2]["action"] == "executed_with_monitoring"
    assert events[2]["request"] == {
        "resource": "third.csv",
        "metadata": {"scope": ["write"]},
    }

def test_runtime_security_event_mutation_does_not_affect_other_events():
    service = RuntimeExecutionService()

    service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "first",
        request={"resource": "first.csv"},
    )

    service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "second",
        request={"resource": "second.csv"},
    )

    events = service.gateway.security_events

    events[0]["action"] = "modified_action"

    assert len(events) == 2

    assert events[0]["decision"] == "ALLOW_WITH_MONITORING"
    assert events[0]["action"] == "modified_action"
    assert events[0]["request"] == {
        "resource": "first.csv"
    }

    assert events[1]["decision"] == "ALLOW_WITH_MONITORING"
    assert events[1]["action"] == "executed_with_monitoring"
    assert events[1]["request"] == {
        "resource": "second.csv"
    }

def test_runtime_security_event_collection_integrity_after_event_mutation():
    service = RuntimeExecutionService()

    service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "first",
        request={"resource": "first.csv"},
    )

    with pytest.raises(RuntimeEnforcementError):
        service.execute(
            decision="DENY",
            tool=lambda request: "blocked",
            request={"resource": "blocked.csv"},
        )

    service.execute(
        decision="ALLOW_WITH_MONITORING",
        tool=lambda request: "third",
        request={"resource": "third.csv"},
    )

    events = service.gateway.security_events

    events[0]["request"]["resource"] = "modified-first.csv"

    assert len(events) == 3

    assert events[0]["action"] == "executed_with_monitoring"
    assert events[0]["request"] == {
        "resource": "modified-first.csv"
    }

    assert events[1]["action"] == "execution_blocked"
    assert events[1]["request"] == {
        "resource": "blocked.csv"
    }

    assert events[2]["action"] == "executed_with_monitoring"
    assert events[2]["request"] == {
        "resource": "third.csv"
    }