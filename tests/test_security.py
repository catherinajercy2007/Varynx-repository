import pytest

from app.security import (
    validate_agent_id,
    validate_task_id,
    validate_action,
    validate_resource,
    validate_api_key,
    validate_authorization_request,
)


# ============================================================
# AGENT ID TESTS
# ============================================================

def test_valid_agent_id():
    valid, message = validate_agent_id(
        "day11-security-agent"
    )

    assert valid is True
    assert message == "Valid agent ID"


def test_empty_agent_id():
    valid, message = validate_agent_id("")

    assert valid is False
    assert "empty" in message.lower()


def test_invalid_agent_id():
    valid, message = validate_agent_id(
        "../malicious-agent"
    )

    assert valid is False


# ============================================================
# TASK ID TESTS
# ============================================================

def test_valid_task_id():
    valid, message = validate_task_id(
        "day11-security-task-001"
    )

    assert valid is True
    assert message == "Valid task ID"


def test_invalid_task_id():
    valid, message = validate_task_id(
        "../task"
    )

    assert valid is False


# ============================================================
# ACTION TESTS
# ============================================================

def test_valid_action():
    valid, message = validate_action(
        "s3:GetObject"
    )

    assert valid is True
    assert message == "Valid action"


def test_empty_action():
    valid, message = validate_action("")

    assert valid is False


def test_invalid_action():
    valid, message = validate_action(
        "s3:GetObject;DROP DATABASE"
    )

    assert valid is False


# ============================================================
# RESOURCE TESTS
# ============================================================

def test_valid_resource():
    valid, message = validate_resource(
        "public/sales.csv"
    )

    assert valid is True
    assert message == "Valid resource"


def test_path_traversal():
    valid, message = validate_resource(
        "../secret.txt"
    )

    assert valid is False
    assert message == "Path traversal detected"


def test_nested_path_traversal():
    valid, message = validate_resource(
        "public/../../secret.txt"
    )

    assert valid is False
    assert message == "Path traversal detected"


def test_null_byte():
    valid, message = validate_resource(
        "public/file.txt\x00"
    )

    assert valid is False
    assert message == "Null byte detected"


def test_empty_resource():
    valid, message = validate_resource("")

    assert valid is False


# ============================================================
# API KEY TESTS
# ============================================================

def test_valid_api_key():
    valid, message = validate_api_key(
        "abcdefghijklmnopqrstuvwxyz123456"
    )

    assert valid is True
    assert message == "Valid API key"


def test_empty_api_key():
    valid, message = validate_api_key("")

    assert valid is False


def test_invalid_api_key():
    valid, message = validate_api_key(
        "short"
    )

    assert valid is False


# ============================================================
# COMPLETE REQUEST TESTS
# ============================================================

def test_valid_authorization_request():

    valid, message = validate_authorization_request(
        agent_id="day11-security-agent",
        api_key="abcdefghijklmnopqrstuvwxyz123456",
        task_id="day11-security-task-001",
        action="s3:GetObject",
        resource="public/sales.csv",
    )

    assert valid is True
    assert message == "Security validation passed"


def test_malicious_authorization_request():

    valid, message = validate_authorization_request(
        agent_id="../malicious-agent",
        api_key="abcdefghijklmnopqrstuvwxyz123456",
        task_id="day11-security-task-001",
        action="s3:GetObject",
        resource="public/sales.csv",
    )

    assert valid is False


def test_path_traversal_authorization_request():

    valid, message = validate_authorization_request(
        agent_id="day11-security-agent",
        api_key="abcdefghijklmnopqrstuvwxyz123456",
        task_id="day11-security-task-001",
        action="s3:GetObject",
        resource="../secret.txt",
    )

    assert valid is False


# ============================================================
# ATTACK PAYLOAD TESTS
# ============================================================

@pytest.mark.parametrize(
    "resource",
    [
        "../secret.txt",
        "../../etc/passwd",
        "public/../../private/data.csv",
        "..\\..\\secret.txt",
        "public/file.txt\x00",
    ],
)
def test_malicious_resource_payloads(resource):

    valid, message = validate_resource(resource)

    assert valid is False


@pytest.mark.parametrize(
    "agent_id",
    [
        "../admin",
        "../../root",
        "agent;DROP",
        "",
    ],
)
def test_malicious_agent_payloads(agent_id):

    valid, message = validate_agent_id(agent_id)

    assert valid is False


@pytest.mark.parametrize(
    "action",
    [
        "",
        "DROP DATABASE",
        "s3:GetObject;DROP",
        "action with spaces",
    ],
)
def test_malicious_action_payloads(action):

    valid, message = validate_action(action)

    assert valid is False