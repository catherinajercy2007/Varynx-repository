
from dataclasses import dataclass

import pytest

from app.counterfactual_capability_gate import (
    OUTCOME_ELIGIBLE,
    OUTCOME_HUMAN_REVIEW,
    OUTCOME_REJECT,
    OUTCOME_RESTRICT,
    REASON_AUTHORITY_RESTRICTED,
    REASON_CRITICAL_CONSEQUENCE,
    REASON_INSUFFICIENT_EVIDENCE,
    REASON_LOW_CONFIDENCE,
    REASON_RESTRICTED_RESOURCE,
    REASON_SCOPE_EXPANSION,
    CounterfactualGatePolicy,
    assess_counterfactual_capability,
)


@dataclass(frozen=True)
class FakeConsequenceEstimate:
    scenario_id: str = "scenario-1"
    consequence_score: float = 25.0
    consequence_level: str = "LOW"
    confidence: str = "HIGH"
    evidence: tuple[str, ...] = ("supplied evidence",)


@dataclass(frozen=True)
class FakeIntegrationResult:
    consequence: FakeConsequenceEstimate


@pytest.fixture
def policy():
    return CounterfactualGatePolicy(
        policy_id="gate-policy-1",
        allowed_scopes=("public-data", "reports"),
        restricted_scopes=("public-data/private",),
        maximum_review_consequence=59.99,
        critical_consequence_threshold=80.0,
        minimum_evidence_items=1,
    )


def assess(policy, estimate=None, **overrides):
    values = {
        "agent_id": "agent-1",
        "scenario_id": "scenario-1",
        "capability": "read",
        "requested_resource": "public-data/report.csv",
        "authority_state": "NORMAL",
        "policy": policy,
        "bcse_result": estimate or FakeConsequenceEstimate(),
        "scope_expansion": False,
    }
    values.update(overrides)
    return assess_counterfactual_capability(**values)


def test_low_consequence_with_high_confidence_is_eligible(policy):
    result = assess(policy)
    assert result.outcome == OUTCOME_ELIGIBLE
    assert result.consequence_score == 25.0
    assert result.confidence == "HIGH"


def test_day55_integration_result_is_supported(policy):
    result = assess(
        policy,
        estimate=FakeIntegrationResult(FakeConsequenceEstimate()),
    )
    assert result.outcome == OUTCOME_ELIGIBLE


def test_scope_outside_allowed_scope_is_restricted(policy):
    result = assess(
        policy,
        requested_resource="private-vault/customer.csv",
    )
    assert result.outcome == OUTCOME_RESTRICT
    assert REASON_SCOPE_EXPANSION in result.reason_codes


def test_explicit_restriction_overrides_allowed_parent_scope(policy):
    result = assess(
        policy,
        requested_resource="public-data/private/customer.csv",
    )
    assert result.outcome == OUTCOME_REJECT
    assert REASON_RESTRICTED_RESOURCE in result.reason_codes


def test_restricted_authority_cannot_pass_gate(policy):
    result = assess(policy, authority_state="RESTRICTED")
    assert result.outcome == OUTCOME_REJECT
    assert REASON_AUTHORITY_RESTRICTED in result.reason_codes


def test_critical_consequence_is_rejected(policy):
    estimate = FakeConsequenceEstimate(
        consequence_score=85.0,
        consequence_level="CRITICAL",
        confidence="HIGH",
    )
    result = assess(policy, estimate=estimate)
    assert result.outcome == OUTCOME_REJECT
    assert REASON_CRITICAL_CONSEQUENCE in result.reason_codes


def test_high_consequence_requires_review(policy):
    estimate = FakeConsequenceEstimate(
        consequence_score=65.0,
        consequence_level="HIGH",
        confidence="HIGH",
    )
    result = assess(policy, estimate=estimate)
    assert result.outcome == OUTCOME_HUMAN_REVIEW


def test_low_confidence_requires_review_even_when_score_is_low(policy):
    estimate = FakeConsequenceEstimate(confidence="LOW")
    result = assess(policy, estimate=estimate)
    assert result.outcome == OUTCOME_HUMAN_REVIEW
    assert REASON_LOW_CONFIDENCE in result.reason_codes


def test_insufficient_evidence_requires_review(policy):
    estimate = FakeConsequenceEstimate(evidence=())
    result = assess(policy, estimate=estimate)
    assert result.outcome == OUTCOME_HUMAN_REVIEW
    assert REASON_INSUFFICIENT_EVIDENCE in result.reason_codes


def test_scope_expansion_requires_high_confidence_by_default(policy):
    estimate = FakeConsequenceEstimate(confidence="MODERATE")
    result = assess(
        policy,
        estimate=estimate,
        scope_expansion=True,
    )
    assert result.outcome == OUTCOME_HUMAN_REVIEW
    assert REASON_LOW_CONFIDENCE in result.reason_codes


def test_reduced_authority_does_not_get_restored(policy):
    result = assess(policy, authority_state="REDUCED")
    assert result.outcome == OUTCOME_HUMAN_REVIEW


def test_scenario_mismatch_is_rejected(policy):
    estimate = FakeConsequenceEstimate(scenario_id="different-scenario")
    with pytest.raises(ValueError, match="does not match"):
        assess(policy, estimate=estimate)


@pytest.mark.parametrize("score", [-0.1, 100.1, float("nan"), float("inf")])
def test_invalid_consequence_score_is_rejected(policy, score):
    estimate = FakeConsequenceEstimate(consequence_score=score)
    with pytest.raises(ValueError):
        assess(policy, estimate=estimate)


def test_unknown_confidence_is_rejected(policy):
    estimate = FakeConsequenceEstimate(confidence="CERTAIN")
    with pytest.raises(ValueError, match="confidence"):
        assess(policy, estimate=estimate)


def test_policy_requires_allowed_scopes():
    with pytest.raises(ValueError, match="must not be empty"):
        CounterfactualGatePolicy(
            policy_id="empty",
            allowed_scopes=(),
        )


def test_policy_thresholds_must_be_ordered():
    with pytest.raises(ValueError, match="must be below"):
        CounterfactualGatePolicy(
            policy_id="bad-thresholds",
            allowed_scopes=("reports",),
            maximum_review_consequence=80,
            critical_consequence_threshold=80,
        )


def test_scope_matching_does_not_use_prefix_collision(policy):
    result = assess(
        policy,
        requested_resource="public-database/report.csv",
    )
    assert result.outcome == OUTCOME_RESTRICT


def test_result_marks_itself_as_recommendation_only(policy):
    result = assess(policy).to_dict()
    assert result["is_authorization_decision"] is False
    assert result["executes_enforcement"] is False
    assert result["modifies_capability_lease"] is False


def test_assessment_does_not_mutate_bcse_estimate(policy):
    estimate = FakeConsequenceEstimate()
    before = (
        estimate.scenario_id,
        estimate.consequence_score,
        estimate.confidence,
        estimate.evidence,
    )
    assess(policy, estimate=estimate)
    after = (
        estimate.scenario_id,
        estimate.consequence_score,
        estimate.confidence,
        estimate.evidence,
    )
    assert after == before


def test_scope_expansion_with_high_confidence_can_be_eligible(policy):
    estimate = FakeConsequenceEstimate(
        consequence_score=20.0,
        confidence="HIGH",
    )
    result = assess(
        policy,
        estimate=estimate,
        scope_expansion=True,
    )
    assert result.outcome == OUTCOME_ELIGIBLE
    assert REASON_SCOPE_EXPANSION in result.reason_codes


def test_scope_policy_must_be_the_expected_type():
    with pytest.raises(TypeError):
        assess_counterfactual_capability(
            agent_id="agent-1",
            scenario_id="scenario-1",
            capability="read",
            requested_resource="reports/report.csv",
            authority_state="NORMAL",
            policy=object(),
            bcse_result=FakeConsequenceEstimate(),
        )
