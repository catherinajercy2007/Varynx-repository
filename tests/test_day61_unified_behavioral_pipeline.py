"""
Varynx - Day 61
Unified Behavioral Intelligence Pipeline Tests

These tests validate the Day 61 orchestration layer independently from the
implementation details of the individual Day 46-60 engines.

The tests use deterministic stub components that expose the expected
semantic outputs of each layer.

Day 61 boundaries tested:

- orchestration
- input validation
- result validation
- evidence aggregation
- consistency analysis
- history management
- deterministic execution
- security boundaries

The tests do NOT test the mathematical correctness of the Day 46-60
algorithms themselves. Those algorithms have their own test suites.
"""

from dataclasses import dataclass

import pytest

from app.unified_behavioral_pipeline import (
    BehavioralPipelineInput,
    UnifiedBehavioralPipeline,
)


# ============================================================================
# Generic deterministic result helper
# ============================================================================


@dataclass(frozen=True)
class StubResult:
    """
    Generic deterministic component result.

    Different Day components expose different fields in the real project.
    This test object provides the fields required by Day 61.
    """

    evidence: tuple[str, ...] = ()


# ============================================================================
# Day 46 - Trust stub
# ============================================================================


@dataclass(frozen=True)
class TrustStubResult:
    trust_score: float
    trust_band: str
    evidence: tuple[str, ...] = ()


class StubTrustEngine:
    """Deterministic Day 46 trust engine."""

    def __init__(
        self,
        trust_score: float = 85.0,
        trust_band: str = "HIGH",
    ):
        self.trust_score = trust_score
        self.trust_band = trust_band
        self.calls = 0

    def update(
        self,
        agent_id,
        evidence=None,
        **kwargs,
    ):
        self.calls += 1

        return TrustStubResult(
            trust_score=self.trust_score,
            trust_band=self.trust_band,
            evidence=(
                "Trust evaluation completed",
            ),
        )


# ============================================================================
# Day 47 - State stub
# ============================================================================


@dataclass(frozen=True)
class StateStubResult:
    state_score: float
    state_level: str
    evidence: tuple[str, ...] = ()


class StubStateEngine:
    """Deterministic Day 47 behavioral-state engine."""

    def __init__(
        self,
        state_score: float = 85.0,
        state_level: str = "STABLE",
    ):
        self.state_score = state_score
        self.state_level = state_level
        self.calls = 0

    def evaluate(
        self,
        agent_id,
        dimensions=None,
        **kwargs,
    ):
        self.calls += 1

        return StateStubResult(
            state_score=self.state_score,
            state_level=self.state_level,
            evidence=(
                "Behavioral state evaluation completed",
            ),
        )


# ============================================================================
# Day 48 - Deviation stub
# ============================================================================


@dataclass(frozen=True)
class DeviationStubResult:
    deviation_score: float
    deviation_level: str
    evidence: tuple[str, ...] = ()


class StubDeviationEngine:
    """Deterministic Day 48 deviation engine."""

    def __init__(
        self,
        deviation_score: float = 10.0,
        deviation_level: str = "NONE",
    ):
        self.deviation_score = deviation_score
        self.deviation_level = deviation_level
        self.calls = 0

    def detect(
        self,
        agent_id,
        dimensions=None,
        **kwargs,
    ):
        self.calls += 1

        return DeviationStubResult(
            deviation_score=self.deviation_score,
            deviation_level=self.deviation_level,
            evidence=(
                "Behavioral deviation evaluation completed",
            ),
        )


# ============================================================================
# Day 49 - Baseline stub
# ============================================================================


@dataclass(frozen=True)
class BaselineStubResult:
    baseline_adapted: bool
    evidence: tuple[str, ...] = ()


class StubBaselineEngine:
    """Deterministic Day 49 baseline engine."""

    def __init__(self, baseline_adapted=True):
        self.baseline_adapted = baseline_adapted
        self.calls = 0

    def observe(
        self,
        agent_id,
        observation=None,
        **kwargs,
    ):
        self.calls += 1

        return BaselineStubResult(
            baseline_adapted=self.baseline_adapted,
            evidence=(
                "Behavioral baseline evaluated",
            ),
        )


# ============================================================================
# Day 51 - Scenario stub
# ============================================================================


@dataclass(frozen=True)
class ScenarioStubResult:
    scenario_id: str
    evidence: tuple[str, ...] = ()


class StubScenarioBuilder:
    """Deterministic Day 51 scenario builder."""

    def __init__(self):
        self.calls = 0

    def create_scenario(
        self,
        agent_id,
        current_context,
        hypothetical_context,
        changes,
        **kwargs,
    ):
        self.calls += 1

        return ScenarioStubResult(
            scenario_id=f"{agent_id}-cf-1",
            evidence=(
                "Counterfactual scenario constructed",
            ),
        )


# ============================================================================
# Day 52 - Consequence stub
# ============================================================================


@dataclass(frozen=True)
class ConsequenceStubResult:
    consequence_score: float
    consequence_level: str
    confidence: str
    evidence: tuple[str, ...] = ()


class StubConsequenceEstimator:
    """Deterministic Day 52 consequence estimator."""

    def __init__(
        self,
        consequence_score=35.0,
        consequence_level="LOW",
        confidence="HIGH",
    ):
        self.consequence_score = consequence_score
        self.consequence_level = consequence_level
        self.confidence = confidence
        self.calls = 0

    def estimate(
        self,
        scenario,
        scenario_id,
        dimensions=None,
        **kwargs,
    ):
        self.calls += 1

        return ConsequenceStubResult(
            consequence_score=self.consequence_score,
            consequence_level=self.consequence_level,
            confidence=self.confidence,
            evidence=(
                "Security consequence estimated",
            ),
        )


# ============================================================================
# Day 53 - Context-aware consequence stub
# ============================================================================


@dataclass(frozen=True)
class ContextStubResult:
    adjusted_consequence_score: float
    consequence_level: str
    confidence: str
    evidence: tuple[str, ...] = ()


class StubContextModel:
    """
    Deterministic Day 53 context-aware model.

    Notice that this intentionally accepts the current Day 53 contract:

        scenario_id
        consequence_score
        context

    It does not require an unsupported evidence argument.
    """

    def __init__(
        self,
        adjusted_score=40.0,
        consequence_level="MODERATE",
        confidence="HIGH",
    ):
        self.adjusted_score = adjusted_score
        self.consequence_level = consequence_level
        self.confidence = confidence
        self.calls = 0

    def estimate(
        self,
        scenario_id,
        consequence_score,
        context,
    ):
        self.calls += 1

        return ContextStubResult(
            adjusted_consequence_score=self.adjusted_score,
            consequence_level=self.consequence_level,
            confidence=self.confidence,
            evidence=(
                "Security context applied",
            ),
        )


# ============================================================================
# Day 56 - Predictive security stub
# ============================================================================


@dataclass(frozen=True)
class PredictiveStubResult:
    predictive_score: float
    predictive_level: str
    predictive_direction: str
    predictive_confidence: str
    evidence: tuple[str, ...] = ()


class StubPredictiveEngine:
    """Deterministic Day 56 predictive security engine."""

    def __init__(
        self,
        predictive_score=25.0,
        predictive_level="MODERATE",
        predictive_direction="STABLE",
        predictive_confidence="HIGH",
    ):
        self.predictive_score = predictive_score
        self.predictive_level = predictive_level
        self.predictive_direction = predictive_direction
        self.predictive_confidence = predictive_confidence
        self.calls = 0

    def evaluate(
        self,
        agent_id,
        dimensions=None,
        historical_scores=None,
        consequence_exposure=None,
        **kwargs,
    ):
        self.calls += 1

        return PredictiveStubResult(
            predictive_score=self.predictive_score,
            predictive_level=self.predictive_level,
            predictive_direction=self.predictive_direction,
            predictive_confidence=self.predictive_confidence,
            evidence=(
                "Predictive security signal generated",
            ),
        )


# ============================================================================
# Day 57 - Trajectory stub
# ============================================================================


@dataclass(frozen=True)
class TrajectoryStubResult:
    slope: float
    mean_change: float
    volatility: float
    direction: str
    stability: str
    confidence: str
    evidence: tuple[str, ...] = ()


class StubTrajectoryEngine:
    """Deterministic Day 57 trajectory engine."""

    def __init__(
        self,
        slope=0.0,
        mean_change=0.0,
        volatility=0.0,
        direction="STABLE",
        stability="STABLE",
        confidence="HIGH",
    ):
        self.slope = slope
        self.mean_change = mean_change
        self.volatility = volatility
        self.direction = direction
        self.stability = stability
        self.confidence = confidence
        self.calls = 0

    def analyze(
        self,
        agent_id,
        scores=None,
        historical_scores=None,
        observations=None,
        current_score=None,
        **kwargs,
    ):
        self.calls += 1

        return TrajectoryStubResult(
            slope=self.slope,
            mean_change=self.mean_change,
            volatility=self.volatility,
            direction=self.direction,
            stability=self.stability,
            confidence=self.confidence,
            evidence=(
                "Behavioral trajectory analyzed",
            ),
        )


# ============================================================================
# Day 58 - Forecast stub
# ============================================================================


@dataclass(frozen=True)
class ForecastStubResult:
    forecast_score: float
    forecast_direction: str
    confidence: str
    evidence: tuple[str, ...] = ()


class StubForecastEngine:
    """Deterministic Day 58 forecast engine."""

    def __init__(
        self,
        forecast_score=30.0,
        forecast_direction="STABLE",
        confidence="HIGH",
    ):
        self.forecast_score = forecast_score
        self.forecast_direction = forecast_direction
        self.confidence = confidence
        self.calls = 0

    def forecast(
        self,
        agent_id,
        current_score=None,
        score=None,
        historical_scores=None,
        observations=None,
        slope=0.0,
        **kwargs,
    ):
        self.calls += 1

        return ForecastStubResult(
            forecast_score=self.forecast_score,
            forecast_direction=self.forecast_direction,
            confidence=self.confidence,
            evidence=(
                "Predictive forecast generated",
            ),
        )


# ============================================================================
# Day 59 - Control stub
# ============================================================================


@dataclass(frozen=True)
class ControlStubResult:
    recommendation: str
    evidence: tuple[str, ...] = ()


class StubControlEngine:
    """Deterministic Day 59 predictive-control engine."""

    def __init__(
        self,
        recommendation="MAINTAIN",
    ):
        self.recommendation = recommendation
        self.calls = 0

    def recommend(
        self,
        agent_id,
        predictive_score=None,
        score=None,
        direction=None,
        predictive_direction=None,
        confidence=None,
        predictive_confidence=None,
        slope=0.0,
        forecast_score=None,
        forecast_direction=None,
        **kwargs,
    ):
        self.calls += 1

        return ControlStubResult(
            recommendation=self.recommendation,
            evidence=(
                "Predictive control recommendation generated",
            ),
        )


# ============================================================================
# Day 60 - Runtime stub
# ============================================================================


@dataclass(frozen=True)
class RuntimeStubResult:
    runtime_state: str
    execution_required: bool
    evidence: tuple[str, ...] = ()


class StubRuntimeEngine:
    """Deterministic Day 60 runtime-envelope engine."""

    def __init__(
        self,
        runtime_state="RUNTIME_READY",
        execution_required=True,
    ):
        self.runtime_state = runtime_state
        self.execution_required = execution_required
        self.calls = 0

    def prepare_decision(
        self,
        agent_id,
        projected_score=None,
        predictive_score=None,
        direction=None,
        confidence=None,
        recommendation=None,
        control_recommendation=None,
        slope=0.0,
        **kwargs,
    ):
        self.calls += 1

        return RuntimeStubResult(
            runtime_state=self.runtime_state,
            execution_required=self.execution_required,
            evidence=(
                "Runtime decision envelope prepared",
            ),
        )


# ============================================================================
# Test fixture helpers
# ============================================================================


def make_components(
    *,
    trust_score=85.0,
    trust_band="HIGH",
    state_score=85.0,
    state_level="STABLE",
    deviation_score=10.0,
    deviation_level="NONE",
    baseline_adapted=True,
    consequence_score=35.0,
    consequence_level="LOW",
    consequence_confidence="HIGH",
    predictive_score=25.0,
    predictive_level="MODERATE",
    predictive_direction="STABLE",
    predictive_confidence="HIGH",
    forecast_score=30.0,
    forecast_direction="STABLE",
    control_recommendation="MAINTAIN",
    runtime_state="RUNTIME_READY",
):
    """
    Build a complete deterministic set of Day 46-60 stubs.
    """

    return {
        "trust_engine": StubTrustEngine(
            trust_score=trust_score,
            trust_band=trust_band,
        ),
        "state_engine": StubStateEngine(
            state_score=state_score,
            state_level=state_level,
        ),
        "deviation_engine": StubDeviationEngine(
            deviation_score=deviation_score,
            deviation_level=deviation_level,
        ),
        "baseline_engine": StubBaselineEngine(
            baseline_adapted=baseline_adapted,
        ),
        "scenario_builder": StubScenarioBuilder(),
        "consequence_estimator": StubConsequenceEstimator(
            consequence_score=consequence_score,
            consequence_level=consequence_level,
            confidence=consequence_confidence,
        ),
        "context_model": StubContextModel(
            adjusted_score=consequence_score,
            consequence_level=consequence_level,
            confidence=consequence_confidence,
        ),
        "predictive_engine": StubPredictiveEngine(
            predictive_score=predictive_score,
            predictive_level=predictive_level,
            predictive_direction=predictive_direction,
            predictive_confidence=predictive_confidence,
        ),
        "trajectory_engine": StubTrajectoryEngine(
            slope=0.0,
            direction=predictive_direction,
        ),
        "forecast_engine": StubForecastEngine(
            forecast_score=forecast_score,
            forecast_direction=forecast_direction,
        ),
        "control_engine": StubControlEngine(
            recommendation=control_recommendation,
        ),
        "runtime_engine": StubRuntimeEngine(
            runtime_state=runtime_state,
            execution_required=True,
        ),
    }


def make_pipeline(**kwargs):
    """Create a Day 61 pipeline with deterministic components."""
    components = make_components(**kwargs)

    return UnifiedBehavioralPipeline(
        **components
    )


def make_input(
    *,
    agent_id="agent-001",
    trust_evidence=None,
    state_dimensions=None,
    deviation_dimensions=None,
    baseline_observation=None,
    current_context=None,
    hypothetical_context=None,
    counterfactual_changes=None,
    consequence_dimensions=None,
    security_context=None,
    predictive_dimensions=None,
    historical_scores=None,
):
    """
    Create a deterministic BehavioralPipelineInput.
    """

    return BehavioralPipelineInput(
        agent_id=agent_id,
        trust_evidence=(
            trust_evidence
            if trust_evidence is not None
            else {
                "behavioral_consistency": 85.0,
                "anomaly_resistance": 90.0,
                "authorization_consistency": 85.0,
            }
        ),
        state_dimensions=(
            state_dimensions
            if state_dimensions is not None
            else {
                "action_consistency": 85.0,
                "resource_consistency": 80.0,
                "context_consistency": 90.0,
            }
        ),
        deviation_dimensions=(
            deviation_dimensions
            if deviation_dimensions is not None
            else {
                "action_deviation": 10.0,
                "resource_deviation": 5.0,
                "context_deviation": 10.0,
            }
        ),
        baseline_observation=(
            baseline_observation
            if baseline_observation is not None
            else {
                "action": 50.0,
                "resource": 50.0,
                "context": 50.0,
            }
        ),
        current_context=(
            current_context
            if current_context is not None
            else object()
        ),
        hypothetical_context=(
            hypothetical_context
            if hypothetical_context is not None
            else object()
        ),
        counterfactual_changes=(
            counterfactual_changes
            if counterfactual_changes is not None
            else ()
        ),
        consequence_dimensions=(
            consequence_dimensions
            if consequence_dimensions is not None
            else {
                "confidentiality": 20.0,
                "integrity": 20.0,
                "availability": 20.0,
                "scope": 20.0,
                "privilege": 20.0,
                "persistence": 20.0,
            }
        ),
        security_context=(
            security_context
            if security_context is not None
            else {
                "resource_sensitivity": 20.0,
                "privilege_context": 20.0,
                "scope_context": 20.0,
                "environment_context": 20.0,
                "persistence_context": 20.0,
            }
        ),
        predictive_dimensions=(
            predictive_dimensions
            if predictive_dimensions is not None
            else {
                "behavioral_deviation": 10.0,
                "trust_decline": 5.0,
                "state_instability": 10.0,
                "consequence_exposure": 20.0,
                "behavioral_acceleration": 0.0,
            }
        ),
        historical_scores=(
            historical_scores
            if historical_scores is not None
            else (20.0, 22.0, 24.0)
        ),
    )


# ============================================================================
# Input model tests
# ============================================================================


def test_input_model_accepts_valid_data():
    data = make_input()

    assert data.agent_id == "agent-001"
    assert isinstance(data.trust_evidence, dict)
    assert isinstance(data.state_dimensions, dict)
    assert isinstance(data.deviation_dimensions, dict)
    assert isinstance(data.historical_scores, tuple)


def test_input_model_rejects_empty_agent_id():
    with pytest.raises(ValueError):
        make_input(agent_id="   ")


def test_input_model_rejects_non_string_agent_id():
    with pytest.raises(TypeError):
        BehavioralPipelineInput(
            agent_id=123
        )


def test_input_model_rejects_invalid_historical_score():
    with pytest.raises(ValueError):
        make_input(
            historical_scores=(20.0, 150.0)
        )


def test_input_model_rejects_negative_historical_score():
    with pytest.raises(ValueError):
        make_input(
            historical_scores=(20.0, -1.0)
        )


def test_input_model_rejects_invalid_mapping():
    with pytest.raises(TypeError):
        BehavioralPipelineInput(
            agent_id="agent-001",
            trust_evidence="invalid",
        )


def test_input_model_converts_historical_scores_to_tuple():
    data = BehavioralPipelineInput(
        agent_id="agent-001",
        historical_scores=[10.0, 20.0, 30.0],
    )

    assert data.historical_scores == (
        10.0,
        20.0,
        30.0,
    )


# ============================================================================
# Result model tests through pipeline
# ============================================================================


def test_pipeline_returns_unified_result():
    pipeline = make_pipeline()

    result = pipeline.evaluate(
        make_input()
    )

    assert result.agent_id == "agent-001"
    assert result.trust_score == 85.0
    assert result.state_score == 85.0
    assert result.deviation_score == 10.0
    assert result.consequence_score == 35.0
    assert result.predictive_score == 25.0
    assert result.forecast_score == 30.0
    assert result.control_recommendation == "MAINTAIN"
    assert result.runtime_state == "RUNTIME_READY"


def test_pipeline_result_is_immutable():
    pipeline = make_pipeline()

    result = pipeline.evaluate(
        make_input()
    )

    with pytest.raises(
        Exception
    ):
        result.trust_score = 10.0


def test_pipeline_result_contains_version():
    pipeline = make_pipeline()

    result = pipeline.evaluate(
        make_input()
    )

    assert result.pipeline_version == "day61-v1"


# ============================================================================
# Individual component orchestration tests
# ============================================================================


def test_day46_trust_engine_is_called():
    pipeline = make_pipeline()

    pipeline.evaluate(
        make_input()
    )

    assert pipeline.trust_engine.calls == 1


def test_day47_state_engine_is_called():
    pipeline = make_pipeline()

    pipeline.evaluate(
        make_input()
    )

    assert pipeline.state_engine.calls == 1


def test_day48_deviation_engine_is_called():
    pipeline = make_pipeline()

    pipeline.evaluate(
        make_input()
    )

    assert pipeline.deviation_engine.calls == 1


def test_day49_baseline_engine_is_called():
    pipeline = make_pipeline()

    pipeline.evaluate(
        make_input()
    )

    assert pipeline.baseline_engine.calls == 1


def test_day51_scenario_builder_is_called():
    pipeline = make_pipeline()

    pipeline.evaluate(
        make_input()
    )

    assert pipeline.scenario_builder.calls == 1


def test_day52_consequence_estimator_is_called():
    pipeline = make_pipeline()

    pipeline.evaluate(
        make_input()
    )

    assert pipeline.consequence_estimator.calls == 1


def test_day53_context_model_is_called():
    pipeline = make_pipeline()

    pipeline.evaluate(
        make_input()
    )

    assert pipeline.context_model.calls == 1


def test_day56_predictive_engine_is_called():
    pipeline = make_pipeline()

    pipeline.evaluate(
        make_input()
    )

    assert pipeline.predictive_engine.calls == 1


def test_day57_trajectory_engine_is_called():
    pipeline = make_pipeline()

    pipeline.evaluate(
        make_input()
    )

    assert pipeline.trajectory_engine.calls == 1


def test_day58_forecast_engine_is_called():
    pipeline = make_pipeline()

    pipeline.evaluate(
        make_input()
    )

    assert pipeline.forecast_engine.calls == 1


def test_day59_control_engine_is_called():
    pipeline = make_pipeline()

    pipeline.evaluate(
        make_input()
    )

    assert pipeline.control_engine.calls == 1


def test_day60_runtime_engine_is_called():
    pipeline = make_pipeline()

    pipeline.evaluate(
        make_input()
    )

    assert pipeline.runtime_engine.calls == 1


# ============================================================================
# End-to-end pipeline tests
# ============================================================================


def test_complete_pipeline_executes():
    pipeline = make_pipeline()

    result = pipeline.evaluate(
        make_input()
    )

    assert result.agent_id == "agent-001"

    assert result.trust_score == 85.0
    assert result.state_score == 85.0
    assert result.deviation_score == 10.0

    assert result.consequence_score == 35.0

    assert result.predictive_score == 25.0
    assert result.forecast_score == 30.0

    assert result.control_recommendation == "MAINTAIN"
    assert result.runtime_state == "RUNTIME_READY"


def test_pipeline_preserves_component_outputs():
    pipeline = make_pipeline(
        trust_score=72.0,
        trust_band="MODERATE",
        state_score=65.0,
        state_level="MOSTLY_STABLE",
        deviation_score=35.0,
        deviation_level="LOW",
        consequence_score=45.0,
        consequence_level="MODERATE",
        predictive_score=50.0,
        predictive_level="HIGH",
        predictive_direction="DETERIORATING",
        predictive_confidence="HIGH",
        forecast_score=60.0,
        forecast_direction="DETERIORATING",
        control_recommendation="INCREASE_MONITORING",
        runtime_state="RUNTIME_READY",
    )

    result = pipeline.evaluate(
        make_input()
    )

    assert result.trust_score == 72.0
    assert result.trust_band == "MODERATE"

    assert result.state_score == 65.0
    assert result.state_level == "MOSTLY_STABLE"

    assert result.deviation_score == 35.0
    assert result.deviation_level == "LOW"

    assert result.consequence_score == 45.0
    assert result.consequence_level == "MODERATE"

    assert result.predictive_score == 50.0
    assert result.predictive_level == "HIGH"
    assert result.predictive_direction == "DETERIORATING"

    assert result.forecast_score == 60.0
    assert result.forecast_direction == "DETERIORATING"

    assert (
        result.control_recommendation
        == "INCREASE_MONITORING"
    )

    assert result.runtime_state == "RUNTIME_READY"


# ============================================================================
# Evidence tests
# ============================================================================


def test_pipeline_aggregates_evidence():
    pipeline = make_pipeline()

    result = pipeline.evaluate(
        make_input()
    )

    assert len(result.evidence) > 0

    assert (
        "Trust evaluation completed"
        in result.evidence
    )

    assert (
        "Behavioral state evaluation completed"
        in result.evidence
    )

    assert (
        "Behavioral deviation evaluation completed"
        in result.evidence
    )


def test_pipeline_removes_duplicate_evidence():
    pipeline = make_pipeline()

    result = pipeline.evaluate(
        make_input()
    )

    assert len(result.evidence) == len(
        set(result.evidence)
    )


# ============================================================================
# Consistency flag tests
# ============================================================================


def test_high_trust_with_high_deviation_flag():
    pipeline = make_pipeline(
        trust_score=90.0,
        trust_band="HIGH",
        deviation_score=85.0,
        deviation_level="CRITICAL",
    )

    result = pipeline.evaluate(
        make_input()
    )

    assert (
        "HIGH_TRUST_WITH_HIGH_DEVIATION"
        in result.consistency_flags
    )


def test_stable_state_with_high_deviation_flag():
    pipeline = make_pipeline(
        state_score=90.0,
        state_level="STABLE",
        deviation_score=85.0,
        deviation_level="CRITICAL",
    )

    result = pipeline.evaluate(
        make_input()
    )

    assert (
        "STABLE_STATE_WITH_HIGH_DEVIATION"
        in result.consistency_flags
    )


def test_high_trust_with_unstable_state_flag():
    pipeline = make_pipeline(
        trust_score=90.0,
        trust_band="HIGH",
        state_score=15.0,
        state_level="HIGHLY_UNSTABLE",
    )

    result = pipeline.evaluate(
        make_input()
    )

    assert (
        "HIGH_TRUST_WITH_UNSTABLE_STATE"
        in result.consistency_flags
    )


def test_critical_deviation_and_trust_flag():
    pipeline = make_pipeline(
        trust_score=20.0,
        trust_band="CRITICAL",
        deviation_score=90.0,
        deviation_level="CRITICAL",
    )

    result = pipeline.evaluate(
        make_input()
    )

    assert (
        "CRITICAL_DEVIATION_AND_TRUST"
        in result.consistency_flags
    )


def test_high_consequence_low_predictive_flag():
    pipeline = make_pipeline(
        consequence_score=90.0,
        consequence_level="CRITICAL",
        predictive_score=20.0,
        predictive_level="MODERATE",
    )

    result = pipeline.evaluate(
        make_input()
    )

    assert (
        "HIGH_CONSEQUENCE_WITH_LOW_PREDICTIVE_SIGNAL"
        in result.consistency_flags
    )


def test_predictive_deterioration_with_low_deviation_flag():
    pipeline = make_pipeline(
        deviation_score=10.0,
        deviation_level="NONE",
        predictive_direction="DETERIORATING",
    )

    result = pipeline.evaluate(
        make_input()
    )

    assert (
        "PREDICTIVE_DETERIORATION_WITH_LOW_CURRENT_DEVIATION"
        in result.consistency_flags
    )


def test_no_unnecessary_consistency_flags_for_normal_case():
    pipeline = make_pipeline()

    result = pipeline.evaluate(
        make_input()
    )

    assert result.consistency_flags == ()


# ============================================================================
# Runtime boundary tests
# ============================================================================


def test_runtime_state_is_preserved():
    pipeline = make_pipeline(
        runtime_state="RUNTIME_ESCALATED",
    )

    result = pipeline.evaluate(
        make_input()
    )

    assert (
        result.runtime_state
        == "RUNTIME_ESCALATED"
    )


def test_pipeline_does_not_execute_runtime_action():
    pipeline = make_pipeline()

    result = pipeline.evaluate(
        make_input()
    )

    # Day 61 only returns the runtime envelope state.
    # No action-execution API exists in the pipeline.
    assert hasattr(
        result,
        "runtime_state",
    )

    assert not hasattr(
        result,
        "execute",
    )

    assert not hasattr(
        result,
        "block_agent",
    )

    assert not hasattr(
        result,
        "authorize",
    )


def test_predictive_block_is_only_a_recommendation():
    pipeline = make_pipeline(
        predictive_score=95.0,
        predictive_level="CRITICAL",
        predictive_direction="DETERIORATING",
        predictive_confidence="HIGH",
        control_recommendation="PREEMPTIVE_BLOCK",
        runtime_state="RUNTIME_ESCALATED",
    )

    result = pipeline.evaluate(
        make_input()
    )

    assert (
        result.control_recommendation
        == "PREEMPTIVE_BLOCK"
    )

    assert (
        result.runtime_state
        == "RUNTIME_ESCALATED"
    )

    # No execution method is exposed.
    assert not hasattr(
        pipeline,
        "execute_action",
    )

    assert not hasattr(
        pipeline,
        "block_agent",
    )


# ============================================================================
# History tests
# ============================================================================


def test_history_starts_empty():
    pipeline = make_pipeline()

    assert pipeline.history(
        "agent-001"
    ) == ()


def test_latest_starts_empty():
    pipeline = make_pipeline()

    assert pipeline.latest(
        "agent-001"
    ) is None


def test_history_records_result():
    pipeline = make_pipeline()

    result = pipeline.evaluate(
        make_input()
    )

    history = pipeline.history(
        "agent-001"
    )

    assert len(history) == 1
    assert history[0] == result


def test_latest_returns_latest_result():
    pipeline = make_pipeline()

    result = pipeline.evaluate(
        make_input()
    )

    latest = pipeline.latest(
        "agent-001"
    )

    assert latest == result


def test_history_preserves_multiple_results():
    pipeline = make_pipeline()

    first = pipeline.evaluate(
        make_input()
    )

    second = pipeline.evaluate(
        make_input()
    )

    history = pipeline.history(
        "agent-001"
    )

    assert len(history) == 2
    assert history[0] == first
    assert history[1] == second


def test_snapshot_all_returns_latest_per_agent():
    pipeline = make_pipeline()

    pipeline.evaluate(
        make_input(
            agent_id="agent-001"
        )
    )

    pipeline.evaluate(
        make_input(
            agent_id="agent-002"
        )
    )

    snapshots = pipeline.snapshot_all()

    assert set(snapshots.keys()) == {
        "agent-001",
        "agent-002",
    }


def test_reset_single_agent():
    pipeline = make_pipeline()

    pipeline.evaluate(
        make_input(
            agent_id="agent-001"
        )
    )

    pipeline.evaluate(
        make_input(
            agent_id="agent-002"
        )
    )

    pipeline.reset(
        "agent-001"
    )

    assert pipeline.latest(
        "agent-001"
    ) is None

    assert pipeline.latest(
        "agent-002"
    ) is not None


def test_reset_all_agents():
    pipeline = make_pipeline()

    pipeline.evaluate(
        make_input(
            agent_id="agent-001"
        )
    )

    pipeline.evaluate(
        make_input(
            agent_id="agent-002"
        )
    )

    pipeline.reset()

    assert pipeline.snapshot_all() == {}


# ============================================================================
# Determinism tests
# ============================================================================


def test_same_input_produces_same_component_output():
    pipeline_one = make_pipeline()
    pipeline_two = make_pipeline()

    data = make_input()

    result_one = pipeline_one.evaluate(
        data
    )

    result_two = pipeline_two.evaluate(
        data
    )

    assert result_one == result_two


def test_pipeline_is_deterministic_for_repeated_evaluation():
    pipeline = make_pipeline()

    data = make_input()

    result_one = pipeline.evaluate(
        data
    )

    result_two = pipeline.evaluate(
        data
    )

    assert result_one == result_two


# ============================================================================
# Defensive-copy tests
# ============================================================================


def test_input_mapping_is_copied():
    evidence = {
        "behavioral_consistency": 80.0
    }

    data = BehavioralPipelineInput(
        agent_id="agent-001",
        trust_evidence=evidence,
    )

    evidence["new_dimension"] = 100.0

    assert (
        "new_dimension"
        not in data.trust_evidence
    )


def test_snapshot_all_returns_defensive_copy():
    pipeline = make_pipeline()

    pipeline.evaluate(
        make_input()
    )

    snapshots = pipeline.snapshot_all()

    snapshots.clear()

    assert (
        pipeline.latest("agent-001")
        is not None
    )


# ============================================================================
# Missing component tests
# ============================================================================


def test_missing_trust_engine_raises_error():
    pipeline = make_pipeline()
    pipeline.trust_engine = None

    with pytest.raises(RuntimeError):
        pipeline.evaluate(
            make_input()
        )


def test_missing_state_engine_raises_error():
    pipeline = make_pipeline()
    pipeline.state_engine = None

    with pytest.raises(RuntimeError):
        pipeline.evaluate(
            make_input()
        )


def test_missing_deviation_engine_raises_error():
    pipeline = make_pipeline()
    pipeline.deviation_engine = None

    with pytest.raises(RuntimeError):
        pipeline.evaluate(
            make_input()
        )


def test_missing_baseline_engine_raises_error():
    pipeline = make_pipeline()
    pipeline.baseline_engine = None

    with pytest.raises(RuntimeError):
        pipeline.evaluate(
            make_input()
        )


def test_missing_scenario_builder_raises_error():
    pipeline = make_pipeline()
    pipeline.scenario_builder = None

    with pytest.raises(RuntimeError):
        pipeline.evaluate(
            make_input()
        )


def test_missing_consequence_estimator_raises_error():
    pipeline = make_pipeline()
    pipeline.consequence_estimator = None

    with pytest.raises(RuntimeError):
        pipeline.evaluate(
            make_input()
        )


def test_missing_context_model_raises_error():
    pipeline = make_pipeline()
    pipeline.context_model = None

    with pytest.raises(RuntimeError):
        pipeline.evaluate(
            make_input()
        )


def test_missing_predictive_engine_raises_error():
    pipeline = make_pipeline()
    pipeline.predictive_engine = None

    with pytest.raises(RuntimeError):
        pipeline.evaluate(
            make_input()
        )


def test_missing_trajectory_engine_raises_error():
    pipeline = make_pipeline()
    pipeline.trajectory_engine = None

    with pytest.raises(RuntimeError):
        pipeline.evaluate(
            make_input()
        )


def test_missing_forecast_engine_raises_error():
    pipeline = make_pipeline()
    pipeline.forecast_engine = None

    with pytest.raises(RuntimeError):
        pipeline.evaluate(
            make_input()
        )


def test_missing_control_engine_raises_error():
    pipeline = make_pipeline()
    pipeline.control_engine = None

    with pytest.raises(RuntimeError):
        pipeline.evaluate(
            make_input()
        )


def test_missing_runtime_engine_raises_error():
    pipeline = make_pipeline()
    pipeline.runtime_engine = None

    with pytest.raises(RuntimeError):
        pipeline.evaluate(
            make_input()
        )


# ============================================================================
# Invalid evaluate input tests
# ============================================================================


def test_evaluate_rejects_non_pipeline_input():
    pipeline = make_pipeline()

    with pytest.raises(TypeError):
        pipeline.evaluate(
            {
                "agent_id": "agent-001"
            }
        )


# ============================================================================
# Agent isolation tests
# ============================================================================


def test_agents_have_independent_history():
    pipeline = make_pipeline()

    pipeline.evaluate(
        make_input(
            agent_id="agent-a"
        )
    )

    pipeline.evaluate(
        make_input(
            agent_id="agent-b"
        )
    )

    assert len(
        pipeline.history("agent-a")
    ) == 1

    assert len(
        pipeline.history("agent-b")
    ) == 1


def test_agent_history_does_not_cross_contaminate():
    pipeline = make_pipeline()

    pipeline.evaluate(
        make_input(
            agent_id="agent-a"
        )
    )

    assert (
        pipeline.history("agent-b")
        == ()
    )


# ============================================================================
# Boundary and architecture tests
# ============================================================================


def test_result_does_not_create_universal_varynx_score():
    pipeline = make_pipeline()

    result = pipeline.evaluate(
        make_input()
    )

    assert not hasattr(
        result,
        "overall_varynx_score",
    )

    assert not hasattr(
        result,
        "universal_security_score",
    )


def test_pipeline_does_not_expose_authorization_method():
    pipeline = make_pipeline()

    assert not hasattr(
        pipeline,
        "authorize",
    )

    assert not hasattr(
        pipeline,
        "authorize_action",
    )


def test_pipeline_does_not_expose_blocking_method():
    pipeline = make_pipeline()

    assert not hasattr(
        pipeline,
        "block",
    )

    assert not hasattr(
        pipeline,
        "block_agent",
    )


def test_pipeline_does_not_expose_hypothetical_execution_method():
    pipeline = make_pipeline()

    assert not hasattr(
        pipeline,
        "execute_counterfactual",
    )

    assert not hasattr(
        pipeline,
        "execute_hypothetical",
    )


# ============================================================================
# Multiple behavioral scenarios
# ============================================================================


def test_normal_behavioral_scenario():
    pipeline = make_pipeline(
        trust_score=90.0,
        trust_band="HIGH",
        state_score=90.0,
        state_level="STABLE",
        deviation_score=5.0,
        deviation_level="NONE",
        consequence_score=15.0,
        consequence_level="NONE",
        predictive_score=10.0,
        predictive_level="LOW",
        predictive_direction="STABLE",
        predictive_confidence="HIGH",
        forecast_score=10.0,
        forecast_direction="STABLE",
        control_recommendation="MAINTAIN",
        runtime_state="RUNTIME_READY",
    )

    result = pipeline.evaluate(
        make_input()
    )

    assert result.trust_band == "HIGH"
    assert result.state_level == "STABLE"
    assert result.deviation_level == "NONE"
    assert result.predictive_level == "LOW"
    assert result.control_recommendation == "MAINTAIN"


def test_deteriorating_behavioral_scenario():
    pipeline = make_pipeline(
        trust_score=55.0,
        trust_band="LOW",
        state_score=45.0,
        state_level="VARIABLE",
        deviation_score=65.0,
        deviation_level="HIGH",
        consequence_score=60.0,
        consequence_level="HIGH",
        predictive_score=75.0,
        predictive_level="CRITICAL",
        predictive_direction="DETERIORATING",
        predictive_confidence="HIGH",
        forecast_score=85.0,
        forecast_direction="DETERIORATING",
        control_recommendation="PREEMPTIVE_BLOCK",
        runtime_state="RUNTIME_ESCALATED",
    )

    result = pipeline.evaluate(
        make_input()
    )

    assert result.trust_score == 55.0
    assert result.deviation_score == 65.0
    assert result.predictive_score == 75.0
    assert (
        result.predictive_direction
        == "DETERIORATING"
    )
    assert (
        result.control_recommendation
        == "PREEMPTIVE_BLOCK"
    )
    assert (
        result.runtime_state
        == "RUNTIME_ESCALATED"
    )


def test_improving_behavioral_scenario():
    pipeline = make_pipeline(
        trust_score=75.0,
        trust_band="MODERATE",
        state_score=70.0,
        state_level="MOSTLY_STABLE",
        deviation_score=30.0,
        deviation_level="LOW",
        consequence_score=35.0,
        consequence_level="LOW",
        predictive_score=30.0,
        predictive_level="MODERATE",
        predictive_direction="IMPROVING",
        predictive_confidence="HIGH",
        forecast_score=20.0,
        forecast_direction="IMPROVING",
        control_recommendation="MAINTAIN",
        runtime_state="RUNTIME_READY",
    )

    result = pipeline.evaluate(
        make_input()
    )

    assert (
        result.predictive_direction
        == "IMPROVING"
    )

    assert (
        result.forecast_direction
        == "IMPROVING"
    )

    assert (
        result.runtime_state
        == "RUNTIME_READY"
    )


# ============================================================================
# Evidence + consistency integration
# ============================================================================


def test_consistency_flag_is_added_to_evidence():
    pipeline = make_pipeline(
        trust_score=90.0,
        trust_band="HIGH",
        deviation_score=90.0,
        deviation_level="CRITICAL",
    )

    result = pipeline.evaluate(
        make_input()
    )

    expected_flag = (
        "HIGH_TRUST_WITH_HIGH_DEVIATION"
    )

    assert expected_flag in result.consistency_flags

    assert any(
        expected_flag in item
        for item in result.evidence
    )


# ============================================================================
# Final integration test
# ============================================================================


def test_full_day46_to_day60_orchestration_path():
    """
    This is the primary Day 61 integration test.

    It verifies that all major stages can participate in one unified
    pipeline execution.
    """

    pipeline = make_pipeline()

    result = pipeline.evaluate(
        make_input(
            agent_id="integration-agent"
        )
    )

    assert result.agent_id == (
        "integration-agent"
    )

    # Day 46
    assert result.trust_score == 85.0
    assert result.trust_band == "HIGH"

    # Day 47
    assert result.state_score == 85.0
    assert result.state_level == "STABLE"

    # Day 48
    assert result.deviation_score == 10.0
    assert result.deviation_level == "NONE"

    # Day 49
    assert result.baseline_adapted is True

    # Days 52-53
    assert result.consequence_score == 35.0
    assert result.consequence_level == "LOW"
    assert (
        result.consequence_confidence
        == "HIGH"
    )

    # Day 56
    assert result.predictive_score == 25.0
    assert result.predictive_level == "MODERATE"
    assert (
        result.predictive_direction
        == "STABLE"
    )
    assert (
        result.predictive_confidence
        == "HIGH"
    )

    # Day 58
    assert result.forecast_score == 30.0
    assert (
        result.forecast_direction
        == "STABLE"
    )

    # Day 59
    assert (
        result.control_recommendation
        == "MAINTAIN"
    )

    # Day 60
    assert (
        result.runtime_state
        == "RUNTIME_READY"
    )

    # Evidence must survive the full pipeline.
    assert len(result.evidence) > 0

    # Normal scenario should not create contradictions.
    assert result.consistency_flags == ()