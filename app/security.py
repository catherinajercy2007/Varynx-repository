import re
from typing import Tuple


class SecurityValidator:

    AGENT_ID_PATTERN = re.compile(
        r"^[a-zA-Z0-9][a-zA-Z0-9_-]{2,63}$"
    )

    TASK_ID_PATTERN = re.compile(
        r"^[a-zA-Z0-9][a-zA-Z0-9_-]{2,63}$"
    )

    ACTION_PATTERN = re.compile(
        r"^[a-zA-Z0-9:_-]{2,100}$"
    )

    API_KEY_PATTERN = re.compile(
        r"^[A-Za-z0-9_-]{20,200}$"
    )

    @staticmethod
    def validate_agent_id(
        agent_id: str
    ) -> Tuple[bool, str]:

        if not isinstance(agent_id, str):
            return False, "Agent ID must be a string"

        if not agent_id:
            return False, "Agent ID cannot be empty"

        if len(agent_id) > 64:
            return False, "Agent ID is too long"

        if not SecurityValidator.AGENT_ID_PATTERN.fullmatch(agent_id):
            return False, "Invalid agent ID format"

        return True, "Valid agent ID"

    @staticmethod
    def validate_task_id(
        task_id: str
    ) -> Tuple[bool, str]:

        if not isinstance(task_id, str):
            return False, "Task ID must be a string"

        if not task_id:
            return False, "Task ID cannot be empty"

        if len(task_id) > 64:
            return False, "Task ID is too long"

        if not SecurityValidator.TASK_ID_PATTERN.fullmatch(task_id):
            return False, "Invalid task ID format"

        return True, "Valid task ID"

    @staticmethod
    def validate_action(
        action: str
    ) -> Tuple[bool, str]:

        if not isinstance(action, str):
            return False, "Action must be a string"

        if not action:
            return False, "Action cannot be empty"

        if len(action) > 100:
            return False, "Action is too long"

        if not SecurityValidator.ACTION_PATTERN.fullmatch(action):
            return False, "Invalid action format"

        return True, "Valid action"

    @staticmethod
    def validate_resource(
        resource: str
    ) -> Tuple[bool, str]:

        if not isinstance(resource, str):
            return False, "Resource must be a string"

        if not resource:
            return False, "Resource cannot be empty"

        if len(resource) > 500:
            return False, "Resource is too long"

        if "\x00" in resource:
            return False, "Null byte detected"

        if ".." in resource:
            return False, "Path traversal detected"

        if any(
            ord(character) < 32
            for character in resource
            if character not in ("\t",)
        ):
            return False, "Invalid control character detected"

        return True, "Valid resource"

    @staticmethod
    def validate_api_key(
        api_key: str
    ) -> Tuple[bool, str]:

        if not isinstance(api_key, str):
            return False, "API key must be a string"

        if not api_key:
            return False, "API key cannot be empty"

        if not SecurityValidator.API_KEY_PATTERN.fullmatch(api_key):
            return False, "Invalid API key format"

        return True, "Valid API key"

    @staticmethod
    def validate_authorization_request(
        agent_id: str,
        api_key: str,
        task_id: str,
        action: str,
        resource: str
    ) -> Tuple[bool, str]:

        checks = [
            SecurityValidator.validate_agent_id(agent_id),
            SecurityValidator.validate_api_key(api_key),
            SecurityValidator.validate_task_id(task_id),
            SecurityValidator.validate_action(action),
            SecurityValidator.validate_resource(resource),
        ]

        for valid, message in checks:

            if not valid:
                return False, message

        return True, "Security validation passed"


def validate_authorization_request(
    agent_id: str,
    api_key: str,
    task_id: str,
    action: str,
    resource: str
) -> Tuple[bool, str]:

    return SecurityValidator.validate_authorization_request(
        agent_id=agent_id,
        api_key=api_key,
        task_id=task_id,
        action=action,
        resource=resource,
    )