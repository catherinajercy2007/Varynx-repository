from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from app.behavioral_capability_lease import (
    AUTHORITY_REVOKED,
    AUTHORITY_SUSPENDED,
    STATUS_BEHAVIORAL_CONDITION_FAILED,
    STATUS_CONTEXT_MISMATCH,
    STATUS_ELIGIBLE,
    STATUS_EXPIRED,
    STATUS_NOT_YET_VALID,
    STATUS_OUT_OF_SCOPE,
    STATUS_REVOKED,
    STATUS_SUSPENDED,
    BehavioralCapabilityLease,
    BehavioralCondition,
    evaluate_capability_lease,
    lease_evaluation_executes_enforcement,
    lease_evaluation_is_authorization,
)


NOW = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)


def make_lease(**overrides):
    values = {
        "lease_id": "lease-001",
        "agent_id": "analysis-agent",
        "task_id": "summarize-public-data",
        "capability": "object.read",
        "resource_scopes": ("s3://demo-bucket/public/",),
        "issued_at": NOW - timedelta(minutes=5),
        "not_before": NOW - timedelta(minutes=1),
        "expires_at": NOW + timedelta(minutes=30),
        "conditions": (),
        "authority_state": "ACTIVE",
    }
    values.update(overrides)
    return BehavioralCapabilityLease(**values)


def evaluate(lease=None, **overrides):
    request = {
        "agent_id": "analysis-agent",
        "task_id": "summarize-public-data",
        "capability": "object.read",
        "resource": "s3://demo-bucket/public/report.csv",
        "now": NOW,
        "behavioral_evidence": {},
    }
    request.update(overrides)
    return evaluate_capability_lease(lease or make_lease(), **request)


def test_valid_lease_is_eligible():
    result = evaluate()
    assert result.status == STATUS_ELIGIBLE
    assert result.eligible is True
    assert "LEASE_ACTIVE" in result.reason_codes


def test_agent_identity_mismatch():
    result = evaluate(agent_id="different-agent")
    assert result.status == STATUS_CONTEXT_MISMATCH
    assert "LEASE_AGENT_ID_MISMATCH" in result.reason_codes


def test_task_identity_mismatch():
    result = evaluate(task_id="different-task")
    assert result.status == STATUS_CONTEXT_MISMATCH
    assert "LEASE_TASK_ID_MISMATCH" in result.reason_codes


def test_capability_mismatch():
    result = evaluate(capability="object.delete")
    assert result.status == STATUS_CONTEXT_MISMATCH
    assert "LEASE_CAPABILITY_MISMATCH" in result.reason_codes


def test_resource_outside_scope():
    result = evaluate(resource="s3://demo-bucket/private/customer.csv")
    assert result.status == STATUS_OUT_OF_SCOPE


def test_scope_prefix_does_not_match_sibling_name():
    result = evaluate(resource="s3://demo-bucket/publicity/report.csv")
    assert result.status == STATUS_OUT_OF_SCOPE


def test_exact_resource_scope_is_supported():
    lease = make_lease(resource_scopes=("resource-1",))
    result = evaluate(lease, resource="resource-1")
    assert result.status == STATUS_ELIGIBLE


def test_not_yet_valid():
    lease = make_lease(not_before=NOW + timedelta(seconds=1))
    assert evaluate(lease).status == STATUS_NOT_YET_VALID


def test_expiry_is_exclusive():
    lease = make_lease(expires_at=NOW)
    assert evaluate(lease).status == STATUS_EXPIRED


def test_revoked_authority_is_not_eligible():
    lease = make_lease(authority_state=AUTHORITY_REVOKED)
    assert evaluate(lease).status == STATUS_REVOKED


def test_suspended_authority_is_not_eligible():
    lease = make_lease(authority_state=AUTHORITY_SUSPENDED)
    assert evaluate(lease).status == STATUS_SUSPENDED


@pytest.mark.parametrize(
    ("operator", "observed", "threshold", "expected"),
    [
        ("lt", 20, 30, True),
        ("lte", 30, 30, True),
        ("gt", 31, 30, True),
        ("gte", 30, 30, True),
        ("eq", 30, 30, True),
        ("lt", 30, 30, False),
    ],
)
def test_behavior_condition_operators(
    operator, observed, threshold, expected
):
    condition = BehavioralCondition("risk_score", operator, threshold)
    passed, _ = condition.evaluate({"risk_score": observed})
    assert passed is expected


def test_behavior_condition_failure_prevents_eligibility():
    lease = make_lease(
        conditions=(BehavioralCondition("risk_score", "lte", 40),)
    )
    result = evaluate(lease, behavioral_evidence={"risk_score": 75})
    assert result.status == STATUS_BEHAVIORAL_CONDITION_FAILED


def test_missing_behavior_signal_fails_closed():
    lease = make_lease(
        conditions=(BehavioralCondition("risk_score", "lte", 40),)
    )
    result = evaluate(lease, behavioral_evidence={})
    assert result.status == STATUS_BEHAVIORAL_CONDITION_FAILED
    assert "MISSING_BEHAVIOR_SIGNAL:risk_score" in result.reason_codes


def test_multiple_conditions_must_all_pass():
    lease = make_lease(
        conditions=(
            BehavioralCondition("risk_score", "lte", 40),
            BehavioralCondition("anomaly_score", "lte", 30),
        )
    )
    result = evaluate(
        lease,
        behavioral_evidence={"risk_score": 20, "anomaly_score": 15},
    )
    assert result.status == STATUS_ELIGIBLE


def test_condition_invalid_signal_is_reported():
    condition = BehavioralCondition("risk_score", "lte", 40)
    passed, reason = condition.evaluate({"risk_score": float("nan")})
    assert passed is False
    assert reason == "INVALID_BEHAVIOR_SIGNAL:risk_score"


def test_lease_requires_scopes():
    with pytest.raises(ValueError):
        make_lease(resource_scopes=())


def test_expiry_must_follow_activation():
    with pytest.raises(ValueError):
        make_lease(
            not_before=NOW + timedelta(minutes=5),
            expires_at=NOW,
        )


def test_naive_datetime_is_rejected():
    with pytest.raises(ValueError):
        make_lease(issued_at=datetime(2026, 10, 19, 12, 0))


def test_unknown_authority_state_is_rejected():
    with pytest.raises(ValueError):
        make_lease(authority_state="UNKNOWN")


def test_condition_rejects_unknown_operator():
    with pytest.raises(ValueError):
        BehavioralCondition("risk_score", "approximately", 40)


def test_condition_rejects_non_finite_threshold():
    with pytest.raises(ValueError):
        BehavioralCondition("risk_score", "lte", float("inf"))


def test_evidence_must_be_a_mapping():
    with pytest.raises(TypeError):
        evaluate(behavioral_evidence=["risk_score", 10])


def test_lease_is_immutable():
    lease = make_lease()
    with pytest.raises(FrozenInstanceError):
        lease.agent_id = "other-agent"


def test_serialization_is_json_friendly():
    lease_data = make_lease().to_dict()
    assert lease_data["version"] == "DAY80-V1"
    assert lease_data["resource_scopes"] == [
        "s3://demo-bucket/public/"
    ]
    assert isinstance(lease_data["expires_at"], str)


def test_evaluation_serialization_marks_non_enforcement_boundary():
    result = evaluate()
    serialized = result.to_dict()
    assert serialized["is_authorization_decision"] is False
    assert serialized["executes_enforcement"] is False
    assert lease_evaluation_is_authorization(result) is False
    assert lease_evaluation_executes_enforcement(result) is False


def test_evaluation_is_deterministic_for_same_inputs():
    first = evaluate()
    second = evaluate()
    assert first == second


def test_lease_conditions_are_immutable_tuple():
    lease = make_lease(
        conditions=(BehavioralCondition("risk_score", "lte", 40),)
    )
    assert isinstance(lease.conditions, tuple)
