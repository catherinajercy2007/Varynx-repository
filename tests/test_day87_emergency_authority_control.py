
from datetime import datetime, timedelta, timezone

import pytest

from app.emergency_authority_control import (
    ControlState,
    ControlTarget,
    EmergencyAuthorityControl,
    EmergencyEventType,
)


NOW = datetime(2026, 10, 20, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def registry():
    return EmergencyAuthorityControl()


def activate(registry, target_type, target_id, reason="incident detected"):
    return registry.activate(
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        actor_id="security-operator",
        now=NOW,
    )


def test_global_kill_switch_matches_every_agent_and_capability(registry):
    control = activate(registry, ControlTarget.GLOBAL, "*")
    result = registry.assess(
        agent_id="agent-42",
        capability="read",
        now=NOW,
    )
    assert result.blocked_by_emergency_control is True
    assert control.control_id in result.matching_control_ids
    assert "GLOBAL_KILL_SWITCH_ACTIVE" in result.reason_codes


def test_agent_revocation_matches_only_the_named_agent(registry):
    control = activate(registry, ControlTarget.AGENT, "agent-1")

    affected = registry.assess(
        agent_id="agent-1", capability="read", now=NOW
    )
    unaffected = registry.assess(
        agent_id="agent-2", capability="read", now=NOW
    )

    assert affected.blocked_by_emergency_control is True
    assert control.control_id in affected.matching_control_ids
    assert unaffected.blocked_by_emergency_control is False


def test_capability_revocation_matches_only_that_capability(registry):
    activate(registry, ControlTarget.CAPABILITY, "delete")

    assert registry.assess(
        agent_id="agent-1", capability="delete", now=NOW
    ).blocked_by_emergency_control is True

    assert registry.assess(
        agent_id="agent-1", capability="read", now=NOW
    ).blocked_by_emergency_control is False


def test_multiple_controls_are_reported(registry):
    activate(registry, ControlTarget.AGENT, "agent-1")
    activate(registry, ControlTarget.CAPABILITY, "delete")

    result = registry.assess(
        agent_id="agent-1", capability="delete", now=NOW
    )
    assert result.blocked_by_emergency_control is True
    assert len(result.matching_control_ids) == 2
    assert len(result.reason_codes) == 2


def test_duplicate_active_activation_is_idempotent(registry):
    first = activate(registry, ControlTarget.AGENT, "agent-1")
    second = registry.activate(
        target_type=ControlTarget.AGENT,
        target_id="agent-1",
        reason="duplicate event",
        actor_id="another-operator",
        now=NOW + timedelta(seconds=5),
    )
    assert first.control_id == second.control_id
    assert len(registry.events) == 1


def test_release_requires_explicit_actor_and_reason(registry):
    control = activate(registry, ControlTarget.AGENT, "agent-1")

    with pytest.raises(ValueError):
        registry.release(
            control_id=control.control_id,
            actor_id="operator",
            reason=" ",
            now=NOW + timedelta(seconds=1),
        )


def test_release_removes_control_from_active_assessment(registry):
    control = activate(registry, ControlTarget.AGENT, "agent-1")
    released = registry.release(
        control_id=control.control_id,
        actor_id="authorized-reviewer",
        reason="incident reviewed and cleared",
        now=NOW + timedelta(minutes=5),
    )

    assert released.state == ControlState.RELEASED
    result = registry.assess(
        agent_id="agent-1",
        capability="read",
        now=NOW + timedelta(minutes=6),
    )
    assert result.blocked_by_emergency_control is False


def test_released_control_is_not_silently_reactivated(registry):
    control = activate(registry, ControlTarget.AGENT, "agent-1")
    registry.release(
        control_id=control.control_id,
        actor_id="reviewer",
        reason="review complete",
        now=NOW + timedelta(seconds=1),
    )

    new_control = activate(
        registry, ControlTarget.AGENT, "agent-1", "new incident"
    )
    assert new_control.control_id != control.control_id
    assert new_control.state == ControlState.ACTIVE


def test_unknown_control_cannot_be_released(registry):
    with pytest.raises(KeyError):
        registry.release(
            control_id="missing",
            actor_id="operator",
            reason="review",
            now=NOW,
        )


def test_control_cannot_be_released_twice(registry):
    control = activate(registry, ControlTarget.AGENT, "agent-1")
    registry.release(
        control_id=control.control_id,
        actor_id="reviewer",
        reason="cleared",
        now=NOW + timedelta(seconds=1),
    )
    with pytest.raises(ValueError, match="already been released"):
        registry.release(
            control_id=control.control_id,
            actor_id="reviewer",
            reason="second release",
            now=NOW + timedelta(seconds=2),
        )


def test_release_cannot_precede_activation(registry):
    control = activate(registry, ControlTarget.AGENT, "agent-1")
    with pytest.raises(ValueError, match="precede activation"):
        registry.release(
            control_id=control.control_id,
            actor_id="reviewer",
            reason="reviewed",
            now=NOW - timedelta(seconds=1),
        )


def test_future_control_does_not_match_before_activation(registry):
    registry.activate(
        target_type=ControlTarget.GLOBAL,
        target_id="*",
        reason="scheduled test",
        actor_id="operator",
        now=NOW + timedelta(minutes=10),
    )
    result = registry.assess(
        agent_id="agent-1",
        capability="read",
        now=NOW,
    )
    assert result.blocked_by_emergency_control is False


@pytest.mark.parametrize(
    "target_type,target_id",
    [
        (ControlTarget.GLOBAL, "agent-1"),
        (ControlTarget.AGENT, "*"),
        (ControlTarget.CAPABILITY, "*"),
    ],
)
def test_target_identifiers_are_validated(registry, target_type, target_id):
    with pytest.raises(ValueError):
        activate(registry, target_type, target_id)


def test_invalid_target_type_is_rejected(registry):
    with pytest.raises(TypeError):
        registry.activate(
            target_type="GLOBAL",
            target_id="*",
            reason="incident",
            actor_id="operator",
            now=NOW,
        )


def test_naive_timestamps_are_rejected(registry):
    with pytest.raises(ValueError, match="timezone-aware"):
        registry.activate(
            target_type=ControlTarget.GLOBAL,
            target_id="*",
            reason="incident",
            actor_id="operator",
            now=datetime(2026, 10, 20, 10, 0),
        )


def test_event_history_records_activation_and_release(registry):
    control = activate(registry, ControlTarget.AGENT, "agent-1")
    registry.release(
        control_id=control.control_id,
        actor_id="reviewer",
        reason="approved recovery",
        now=NOW + timedelta(minutes=1),
    )

    assert len(registry.events) == 2
    assert registry.events[0].event_type == (
        EmergencyEventType.AGENT_AUTHORITY_REVOKED
    )
    assert registry.events[1].event_type == (
        EmergencyEventType.CONTROL_RELEASED
    )


def test_enforcement_signal_is_explicitly_handoff_only(registry):
    activate(registry, ControlTarget.GLOBAL, "*")
    signal = registry.enforcement_signal(
        agent_id="agent-1",
        capability="read",
        now=NOW,
    )

    assert signal["blocked_by_emergency_control"] is True
    assert signal["enforcement_executed"] is False
    assert signal["authorization_decision_made"] is False


def test_serialized_control_marks_boundary(registry):
    control = activate(registry, ControlTarget.GLOBAL, "*")
    result = control.to_dict()
    assert result["is_authorization_decision"] is False
    assert result["executes_enforcement"] is False


def test_unknown_agent_and_capability_are_rejected(registry):
    with pytest.raises(ValueError):
        registry.assess(agent_id=" ", capability="read", now=NOW)
    with pytest.raises(ValueError):
        registry.assess(agent_id="agent-1", capability="", now=NOW)


def test_activation_preserves_original_reason(registry):
    control = activate(
        registry, ControlTarget.AGENT, "agent-1", "critical anomaly"
    )
    assert control.reason == "critical anomaly"
    assert registry.events[0].reason == "critical anomaly"
