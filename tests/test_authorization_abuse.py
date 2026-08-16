from app.authorization import AuthorizationService


def test_invalid_agent_is_denied(monkeypatch):

    monkeypatch.setattr(
        "app.authorization.verify_agent",
        lambda agent_id, api_key: False
    )

    result = AuthorizationService.authorize(
        agent_id="unknown-agent",
        api_key="abcdefghijklmnopqrstuvwxyz123456",
        task_id="day12-task-001",
        action="s3:GetObject",
        resource="public/sales.csv",
    )

    assert result["decision"] == "DENY"
    assert result["risk"] == 100
    assert "Invalid agent identity" in result["reason"]


def test_invalid_task_is_denied(monkeypatch):

    monkeypatch.setattr(
        "app.authorization.verify_agent",
        lambda agent_id, api_key: True
    )

    monkeypatch.setattr(
        "app.authorization.verify_task",
        lambda task_id, agent_id: False
    )

    result = AuthorizationService.authorize(
        agent_id="day12-security-agent",
        api_key="abcdefghijklmnopqrstuvwxyz123456",
        task_id="invalid-task",
        action="s3:GetObject",
        resource="public/sales.csv",
    )

    assert result["decision"] == "DENY"
    assert result["risk"] == 100
    assert "Invalid or expired task" in result["reason"]


def test_task_not_found_is_denied(monkeypatch):

    monkeypatch.setattr(
        "app.authorization.verify_agent",
        lambda agent_id, api_key: True
    )

    monkeypatch.setattr(
        "app.authorization.verify_task",
        lambda task_id, agent_id: True
    )

    monkeypatch.setattr(
        "app.authorization.get_task",
        lambda task_id, agent_id: None
    )

    result = AuthorizationService.authorize(
        agent_id="day12-security-agent",
        api_key="abcdefghijklmnopqrstuvwxyz123456",
        task_id="day12-task-001",
        action="s3:GetObject",
        resource="public/sales.csv",
    )

    assert result["decision"] == "DENY"
    assert result["risk"] == 100
    assert "Task not found" in result["reason"]


def test_unauthorized_action_is_denied(monkeypatch):

    monkeypatch.setattr(
        "app.authorization.verify_agent",
        lambda agent_id, api_key: True
    )

    monkeypatch.setattr(
        "app.authorization.verify_task",
        lambda task_id, agent_id: True
    )

    monkeypatch.setattr(
        "app.authorization.get_task",
        lambda task_id, agent_id: {
            "task_id": task_id,
            "agent_id": agent_id,
            "intent": "analyze_public_data",
        }
    )

    result = AuthorizationService.authorize(
        agent_id="data-analysis-agent",
        api_key="abcdefghijklmnopqrstuvwxyz123456",
        task_id="day12-task-001",
        action="s3:DeleteObject",
        resource="public/sales.csv",
    )

    assert result["decision"] == "DENY"
    assert result["risk"] >= 40
    assert "Action is not permitted" in result["reason"]


def test_unauthorized_resource_is_denied(monkeypatch):

    monkeypatch.setattr(
        "app.authorization.verify_agent",
        lambda agent_id, api_key: True
    )

    monkeypatch.setattr(
        "app.authorization.verify_task",
        lambda task_id, agent_id: True
    )

    monkeypatch.setattr(
        "app.authorization.get_task",
        lambda task_id, agent_id: {
            "task_id": task_id,
            "agent_id": agent_id,
            "intent": "analyze_public_data",
        }
    )

    result = AuthorizationService.authorize(
        agent_id="data-analysis-agent",
        api_key="abcdefghijklmnopqrstuvwxyz123456",
        task_id="day12-task-001",
        action="s3:GetObject",
        resource="private/customer.csv",
    )

    assert result["decision"] == "DENY"
    assert "Resource is outside the task scope" in result["reason"]


def test_privilege_escalation_is_denied(monkeypatch):

    monkeypatch.setattr(
        "app.authorization.verify_agent",
        lambda agent_id, api_key: True
    )

    monkeypatch.setattr(
        "app.authorization.verify_task",
        lambda task_id, agent_id: True
    )

    monkeypatch.setattr(
        "app.authorization.get_task",
        lambda task_id, agent_id: {
            "task_id": task_id,
            "agent_id": agent_id,
            "intent": "analyze_public_data",
        }
    )

    result = AuthorizationService.authorize(
        agent_id="data-analysis-agent",
        api_key="abcdefghijklmnopqrstuvwxyz123456",
        task_id="day12-task-001",
        action="iam:CreateUser",
        resource="public/users",
    )

    assert result["decision"] == "DENY"
    assert result["risk"] >= 40


def test_destructive_private_operation_is_denied(monkeypatch):

    monkeypatch.setattr(
        "app.authorization.verify_agent",
        lambda agent_id, api_key: True
    )

    monkeypatch.setattr(
        "app.authorization.verify_task",
        lambda task_id, agent_id: True
    )

    monkeypatch.setattr(
        "app.authorization.get_task",
        lambda task_id, agent_id: {
            "task_id": task_id,
            "agent_id": agent_id,
            "intent": "analyze_public_data",
        }
    )

    result = AuthorizationService.authorize(
        agent_id="data-analysis-agent",
        api_key="abcdefghijklmnopqrstuvwxyz123456",
        task_id="day12-task-001",
        action="s3:DeleteObject",
        resource="private/customer.csv",
    )

    assert result["decision"] == "DENY"
    assert result["risk"] == 100


def test_repeated_abuse_requests_remain_denied(monkeypatch):

    monkeypatch.setattr(
        "app.authorization.verify_agent",
        lambda agent_id, api_key: True
    )

    monkeypatch.setattr(
        "app.authorization.verify_task",
        lambda task_id, agent_id: True
    )

    monkeypatch.setattr(
        "app.authorization.get_task",
        lambda task_id, agent_id: {
            "task_id": task_id,
            "agent_id": agent_id,
            "intent": "analyze_public_data",
        }
    )

    for _ in range(5):

        result = AuthorizationService.authorize(
            agent_id="data-analysis-agent",
            api_key="abcdefghijklmnopqrstuvwxyz123456",
            task_id="day12-task-001",
            action="s3:DeleteObject",
            resource="private/customer.csv",
        )

        assert result["decision"] == "DENY"
        assert result["risk"] == 100