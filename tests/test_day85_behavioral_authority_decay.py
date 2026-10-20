
from datetime import datetime, timedelta, timezone

import pytest

from app.behavioral_authority_decay import (
    AuthorityDecayPolicy,
    AUTHORITY_NORMAL,
    AUTHORITY_REDUCED,
    AUTHORITY_RESTRICTED,
    STATUS_DECAYED,
    STATUS_INVALID_EVIDENCE,
    STATUS_RECOVERY_INSUFFICIENT,
    STATUS_RECOVERY_QUALIFIED,
    STATUS_STABLE,
    RECOMMEND_KEEP_STATE,
    RECOMMEND_REDUCE_AUTHORITY,
    RECOMMEND_REVIEW_RECOVERY,
    assess_behavioral_authority,
)

NOW = datetime(2026, 10, 20, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def policy():
    return AuthorityDecayPolicy(
        policy_id="authority-policy-85",
        evidence_ttl_seconds=300,
        recovery_minimum_events=3,
        adverse_signal_threshold=70,
        recovery_signal_maximum=20,
    )


def assess(policy, **overrides):
    values = {
        "agent_id": "agent-a",
        "current_state": AUTHORITY_NORMAL,
        "policy": policy,
        "now": NOW,
        "last_qualifying_evidence_at": NOW - timedelta(seconds=30),
        "adverse_signal_score": 10,
    }
    values.update(overrides)
    return assess_behavioral_authority(**values)


def test_fresh_benign_evidence_keeps_normal_state(policy):
    result = assess(policy)

    assert result.status == STATUS_STABLE
    assert result.recommended_state == AUTHORITY_NORMAL


def test_stale_evidence_reduces_normal_authority(policy):
    result = assess(
        policy,
        last_qualifying_evidence_at=NOW - timedelta(seconds=301),
    )

    assert result.status == STATUS_DECAYED
    assert result.recommended_state == AUTHORITY_REDUCED


def test_missing_evidence_reduces_normal_authority(policy):
    result = assess(policy, last_qualifying_evidence_at=None)

    assert result.recommended_state == AUTHORITY_REDUCED


def test_adverse_signal_reduces_normal_authority(policy):
    result = assess(policy, adverse_signal_score=70)

    assert result.status == STATUS_DECAYED
    assert result.recommended_state == AUTHORITY_REDUCED


def test_adverse_signal_escalates_reduced_state(policy):
    result = assess(
        policy,
        current_state=AUTHORITY_REDUCED,
        adverse_signal_score=90,
    )

    assert result.recommended_state == AUTHORITY_RESTRICTED


def test_restricted_state_is_not_automatically_recovered(policy):
    result = assess(
        policy,
        current_state=AUTHORITY_RESTRICTED,
        recovery_signal_score=0,
        recovery_qualifying_events=100,
    )

    assert result.recommended_state == AUTHORITY_RESTRICTED


def test_reduced_state_recovers_with_qualifying_evidence(policy):
    result = assess(
        policy,
        current_state=AUTHORITY_REDUCED,
        recovery_signal_score=10,
        recovery_qualifying_events=3,
    )

    assert result.status == STATUS_RECOVERY_QUALIFIED
    assert result.recommended_state == AUTHORITY_NORMAL
    assert result.recommendation == RECOMMEND_REVIEW_RECOVERY


def test_recovery_fails_with_too_few_events(policy):
    result = assess(
        policy,
        current_state=AUTHORITY_REDUCED,
        recovery_signal_score=10,
        recovery_qualifying_events=2,
    )

    assert result.status == STATUS_RECOVERY_INSUFFICIENT
    assert result.recommended_state == AUTHORITY_REDUCED


def test_recovery_fails_when_signal_is_too_high(policy):
    result = assess(
        policy,
        current_state=AUTHORITY_REDUCED,
        recovery_signal_score=21,
        recovery_qualifying_events=3,
    )

    assert result.status == STATUS_RECOVERY_INSUFFICIENT


def test_stale_evidence_cannot_recover_authority(policy):
    result = assess(
        policy,
        current_state=AUTHORITY_REDUCED,
        last_qualifying_evidence_at=NOW - timedelta(seconds=301),
        recovery_signal_score=0,
        recovery_qualifying_events=10,
    )

    assert result.recommended_state == AUTHORITY_REDUCED
    assert result.recommendation == RECOMMEND_KEEP_STATE


def test_missing_recovery_signal_does_not_restore_authority(policy):
    result = assess(
        policy,
        current_state=AUTHORITY_REDUCED,
        recovery_signal_score=None,
        recovery_qualifying_events=10,
    )

    assert result.recommended_state == AUTHORITY_REDUCED


def test_invalid_adverse_signal_does_not_increase_authority(policy):
    result = assess(policy, adverse_signal_score=float("nan"))

    assert result.status == STATUS_INVALID_EVIDENCE
    assert result.recommended_state == AUTHORITY_NORMAL


def test_out_of_range_signal_is_invalid(policy):
    result = assess(policy, adverse_signal_score=101)

    assert result.status == STATUS_INVALID_EVIDENCE


def test_future_evidence_timestamp_is_rejected(policy):
    with pytest.raises(ValueError, match="future"):
        assess(
            policy,
            last_qualifying_evidence_at=NOW + timedelta(seconds=1),
        )


def test_naive_current_time_is_rejected(policy):
    with pytest.raises(ValueError, match="timezone-aware"):
        assess(policy, now=datetime(2026, 10, 20, 10, 0))


def test_negative_recovery_event_count_is_rejected(policy):
    with pytest.raises(ValueError):
        assess(policy, recovery_qualifying_events=-1)


def test_unknown_state_is_rejected(policy):
    with pytest.raises(ValueError, match="current_state"):
        assess(policy, current_state="UNLIMITED")


def test_policy_rejects_invalid_ttl():
    with pytest.raises(ValueError):
        AuthorityDecayPolicy("p", 0, 3, 70, 20)


def test_policy_rejects_out_of_range_threshold():
    with pytest.raises(ValueError):
        AuthorityDecayPolicy("p", 300, 3, 120, 20)


def test_assessment_is_deterministic(policy):
    kwargs = {
        "current_state": AUTHORITY_REDUCED,
        "recovery_signal_score": 10,
        "recovery_qualifying_events": 3,
    }

    first = assess(policy, **kwargs).to_dict()
    second = assess(policy, **kwargs).to_dict()

    assert first == second


def test_serialization_declares_recommendation_only(policy):
    result = assess(policy).to_dict()

    assert result["changes_authority_directly"] is False
    assert result["executes_enforcement"] is False
    assert result["is_authorization_decision"] is False


def test_policy_is_immutable(policy):
    with pytest.raises((AttributeError, TypeError)):
        policy.evidence_ttl_seconds = 1


def test_result_includes_reason_codes(policy):
    result = assess(policy)

    assert result.reason_codes
    assert all(isinstance(code, str) for code in result.reason_codes)
