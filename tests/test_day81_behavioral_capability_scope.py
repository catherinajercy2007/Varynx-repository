
from datetime import datetime, timedelta, timezone

import pytest

from app.behavioral_capability_lease import (
    BehavioralCapabilityLease,
    BehavioralCondition,
)
from app.behavioral_capability_scope import (
    BehavioralScopePolicy,
    STATUS_CAPABILITY_MISMATCH,
    STATUS_EXPLICITLY_RESTRICTED,
    STATUS_LEASE_INELIGIBLE,
    STATUS_OUT_OF_SCOPE,
    STATUS_WITHIN_SCOPE,
    RECOMMEND_ALLOW_FOR_POLICY_REVIEW,
    RECOMMEND_DENY_FOR_POLICY_REVIEW,
    RECOMMEND_RESTRICT_SCOPE,
    assess_behavioral_capability_scope,
)

NOW = datetime(2026, 10, 20, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def lease():
    return BehavioralCapabilityLease(
        lease_id="lease-81",
        agent_id="analysis-agent",
        task_id="analyze-public-data",
        capability="s3:GetObject",
        resource_scopes=("public/",),
        issued_at=NOW - timedelta(minutes=10),
        not_before=NOW - timedelta(minutes=5),
        expires_at=NOW + timedelta(hours=1),
    )


@pytest.fixture
def policy():
    return BehavioralScopePolicy(
        policy_id="scope-policy-81",
        capability="s3:GetObject",
        allowed_scopes=("public/",),
        restricted_scopes=("public/restricted/",),
    )


def assess(lease, policy, **overrides):
    values = {
        "lease": lease,
        "policy": policy,
        "agent_id": "analysis-agent",
        "task_id": "analyze-public-data",
        "capability": "s3:GetObject",
        "resource": "public/report.csv",
        "now": NOW,
        "behavioral_evidence": {},
    }
    values.update(overrides)
    return assess_behavioral_capability_scope(**values)


def test_valid_request_is_eligible_for_policy_review(lease, policy):
    result = assess(lease, policy)

    assert result.status == STATUS_WITHIN_SCOPE
    assert result.eligible_for_policy_review is True
    assert result.recommendation == RECOMMEND_ALLOW_FOR_POLICY_REVIEW


def test_resource_outside_scope_is_restricted(lease, policy):
    result = assess(lease, policy, resource="private/customer.csv")

    assert result.status == STATUS_OUT_OF_SCOPE
    assert result.eligible_for_policy_review is False
    assert result.recommendation == RECOMMEND_RESTRICT_SCOPE


def test_path_prefix_boundary_is_enforced(lease, policy):
    result = assess(lease, policy, resource="publicity/report.csv")

    assert result.status == STATUS_OUT_OF_SCOPE


def test_explicit_restriction_overrides_allowed_parent_scope(lease, policy):
    result = assess(
        lease, policy, resource="public/restricted/customer.csv"
    )

    assert result.status == STATUS_EXPLICITLY_RESTRICTED
    assert result.recommendation == RECOMMEND_RESTRICT_SCOPE


def test_wrong_capability_is_rejected(lease, policy):
    result = assess(lease, policy, capability="s3:DeleteObject")

    assert result.status == STATUS_CAPABILITY_MISMATCH
    assert result.recommendation == RECOMMEND_DENY_FOR_POLICY_REVIEW


def test_wrong_agent_fails_lease_check(lease, policy):
    result = assess(lease, policy, agent_id="different-agent")

    assert result.status == STATUS_LEASE_INELIGIBLE
    assert result.eligible_for_policy_review is False


def test_wrong_task_fails_lease_check(lease, policy):
    result = assess(lease, policy, task_id="different-task")

    assert result.status == STATUS_LEASE_INELIGIBLE


def test_expired_lease_fails(lease, policy):
    result = assess(
        lease, policy, now=NOW + timedelta(hours=2)
    )

    assert result.status == STATUS_LEASE_INELIGIBLE


def test_missing_required_behavioral_signal_fails_condition():
    conditioned_lease = BehavioralCapabilityLease(
        lease_id="lease-conditioned",
        agent_id="analysis-agent",
        task_id="analyze-public-data",
        capability="s3:GetObject",
        resource_scopes=("public/",),
        issued_at=NOW - timedelta(minutes=10),
        not_before=NOW - timedelta(minutes=5),
        expires_at=NOW + timedelta(hours=1),
        conditions=(
            BehavioralCondition(
                signal="anomaly_score",
                operator="lte",
                threshold=30,
            ),
        ),
    )
    policy = BehavioralScopePolicy(
        policy_id="condition-policy",
        capability="s3:GetObject",
        allowed_scopes=("public/",),
    )

    result = assess(conditioned_lease, policy, behavioral_evidence={})

    assert result.status == STATUS_LEASE_INELIGIBLE


def test_behavior_condition_can_pass():
    conditioned_lease = BehavioralCapabilityLease(
        lease_id="lease-conditioned",
        agent_id="analysis-agent",
        task_id="analyze-public-data",
        capability="s3:GetObject",
        resource_scopes=("public/",),
        issued_at=NOW - timedelta(minutes=10),
        not_before=NOW - timedelta(minutes=5),
        expires_at=NOW + timedelta(hours=1),
        conditions=(
            BehavioralCondition(
                signal="anomaly_score",
                operator="lte",
                threshold=30,
            ),
        ),
    )
    policy = BehavioralScopePolicy(
        policy_id="condition-policy",
        capability="s3:GetObject",
        allowed_scopes=("public/",),
    )

    result = assess(
        conditioned_lease,
        policy,
        behavioral_evidence={"anomaly_score": 10},
    )

    assert result.status == STATUS_WITHIN_SCOPE


def test_policy_rejects_empty_allowed_scopes():
    with pytest.raises(ValueError):
        BehavioralScopePolicy(
            policy_id="invalid",
            capability="s3:GetObject",
            allowed_scopes=(),
        )


def test_policy_rejects_duplicate_scopes():
    with pytest.raises(ValueError):
        BehavioralScopePolicy(
            policy_id="invalid",
            capability="s3:GetObject",
            allowed_scopes=("public/", "public/"),
        )


def test_naive_datetime_is_rejected(lease, policy):
    with pytest.raises(ValueError):
        assess(lease, policy, now=datetime(2026, 10, 20, 10, 0))


def test_empty_resource_is_rejected(lease, policy):
    with pytest.raises(ValueError):
        assess(lease, policy, resource=" ")


def test_invalid_lease_type_is_rejected(policy):
    with pytest.raises(TypeError):
        assess(None, policy)


def test_invalid_policy_type_is_rejected(lease):
    with pytest.raises(TypeError):
        assess(lease, None)


def test_assessment_is_deterministic(lease, policy):
    first = assess(lease, policy).to_dict()
    second = assess(lease, policy).to_dict()

    assert first == second


def test_serialization_discloses_no_enforcement(lease, policy):
    result = assess(lease, policy).to_dict()

    assert result["version"] == "DAY81-V1"
    assert result["is_authorization_decision"] is False
    assert result["executes_enforcement"] is False


def test_result_contains_explanation(lease, policy):
    result = assess(lease, policy)

    assert result.reason_codes
    assert all(isinstance(code, str) for code in result.reason_codes)


def test_scope_assessment_does_not_mutate_evidence(lease, policy):
    evidence = {"anomaly_score": 10}
    original = evidence.copy()

    assess(lease, policy, behavioral_evidence=evidence)

    assert evidence == original
