"""
Varynx - Day 61
Unified Behavioral Intelligence Pipeline

Purpose
-------
Provides a single orchestration layer for the behavioral intelligence,
BCSE, predictive, and runtime components developed during Days 46-60.

Pipeline:

    Behavioral Evidence
            |
            v
    Dynamic Behavioral Trust
            |
            v
    Behavioral State
            |
            v
    Behavioral Deviation
            |
            v
    Adaptive Baseline
            |
            v
    BCSE Scenario
            |
            v
    Security Consequence
            |
            v
    Context-Aware Consequence
            |
            v
    Predictive Security Signal
            |
            v
    Behavioral Trajectory
            |
            v
    Predictive Forecast
            |
            v
    Predictive Control
            |
            v
    Predictive Runtime Envelope

Architectural boundaries
------------------------
This module:

- orchestrates existing Varynx components
- preserves component outputs
- provides a unified structured result
- records consistency observations
- maintains pipeline-level history

This module does NOT:

- replace authorization
- directly authorize an agent
- directly block an agent
- execute hypothetical actions
- infer malicious intent
- replace the existing risk engine
- replace adaptive_response.py
- create a universal Varynx security score
"""

from __future__ import annotations

from dataclasses import dataclass, field
from inspect import Parameter, signature
from math import isfinite
from typing import Any, Mapping, Optional, Sequence


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCORE_MIN = 0.0
SCORE_MAX = 100.0

PIPELINE_VERSION = "day61-v1"

# These are descriptive only. They are not used to override decisions.
TRUST_HIGH = "HIGH"
TRUST_MODERATE = "MODERATE"
TRUST_LOW = "LOW"
TRUST_CRITICAL = "CRITICAL"

STATE_STABLE = "STABLE"
STATE_MOSTLY_STABLE = "MOSTLY_STABLE"
STATE_VARIABLE = "VARIABLE"
STATE_UNSTABLE = "UNSTABLE"
STATE_HIGHLY_UNSTABLE = "HIGHLY_UNSTABLE"

DEVIATION_NONE = "NONE"
DEVIATION_LOW = "LOW"
DEVIATION_MODERATE = "MODERATE"
DEVIATION_HIGH = "HIGH"
DEVIATION_CRITICAL = "CRITICAL"

CONSEQUENCE_NONE = "NONE"
CONSEQUENCE_LOW = "LOW"
CONSEQUENCE_MODERATE = "MODERATE"
CONSEQUENCE_HIGH = "HIGH"
CONSEQUENCE_CRITICAL = "CRITICAL"

PREDICTIVE_LOW = "LOW"
PREDICTIVE_MODERATE = "MODERATE"
PREDICTIVE_HIGH = "HIGH"
PREDICTIVE_CRITICAL = "CRITICAL"

RUNTIME_READY = "RUNTIME_READY"
RUNTIME_ESCALATED = "RUNTIME_ESCALATED"
RUNTIME_PENDING = "RUNTIME_PENDING"


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_agent_id(agent_id: str) -> str:
    """Validate and return an agent identifier."""
    if not isinstance(agent_id, str):
        raise TypeError("agent_id must be a string")

    normalized = agent_id.strip()

    if not normalized:
        raise ValueError("agent_id must not be empty")

    return normalized


def _validate_score(value: float, field_name: str) -> float:
    """Validate a numeric score in the range 0-100."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be numeric")

    numeric = float(value)

    if not isfinite(numeric):
        raise ValueError(f"{field_name} must be finite")

    if not SCORE_MIN <= numeric <= SCORE_MAX:
        raise ValueError(
            f"{field_name} must be between "
            f"{SCORE_MIN} and {SCORE_MAX}"
        )

    return numeric


def _validate_text(value: str, field_name: str) -> str:
    """Validate a non-empty text value."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{field_name} must not be empty")

    return normalized


def _validate_mapping(
    value: Mapping[str, Any],
    field_name: str,
) -> dict[str, Any]:
    """Validate mapping-like input and make a defensive copy."""
    if value is None:
        return {}

    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")

    return dict(value)


def _validate_sequence(
    value: Sequence[Any] | None,
    field_name: str,
) -> tuple[Any, ...]:
    """Validate optional sequence input."""
    if value is None:
        return ()

    if isinstance(value, (str, bytes)):
        raise TypeError(f"{field_name} must be a sequence, not text")

    try:
        return tuple(value)
    except TypeError as exc:
        raise TypeError(
            f"{field_name} must be a sequence"
        ) from exc


def _extract_attribute(
    result: Any,
    names: Sequence[str],
    default: Any = None,
) -> Any:
    """
    Extract an attribute/key from a component result.

    Supports:
    - dataclass/object attributes
    - dictionaries
    """
    if result is None:
        return default

    if isinstance(result, Mapping):
        for name in names:
            if name in result:
                return result[name]

    for name in names:
        if hasattr(result, name):
            return getattr(result, name)

    return default


def _extract_score(
    result: Any,
    names: Sequence[str],
    field_name: str,
    required: bool = True,
) -> Optional[float]:
    """Extract and validate a 0-100 score from a component result."""
    value = _extract_attribute(result, names)

    if value is None:
        if required:
            raise ValueError(
                f"Unable to extract {field_name} from component result"
            )
        return None

    return _validate_score(value, field_name)


def _extract_text(
    result: Any,
    names: Sequence[str],
    field_name: str,
    required: bool = True,
) -> Optional[str]:
    """Extract a text field from a component result."""
    value = _extract_attribute(result, names)

    if value is None:
        if required:
            raise ValueError(
                f"Unable to extract {field_name} from component result"
            )
        return None

    return _validate_text(str(value), field_name)


def _extract_evidence(result: Any) -> tuple[str, ...]:
    """
    Extract evidence from a component result.

    Evidence is treated as descriptive information and is never interpreted
    as proof of malicious intent.
    """
    value = _extract_attribute(
        result,
        (
            "evidence",
            "trust_evidence",
            "state_evidence",
            "deviation_evidence",
            "consequence_evidence",
            "predictive_evidence",
            "runtime_evidence",
        ),
        default=(),
    )

    if value is None:
        return ()

    if isinstance(value, str):
        return (value,)

    try:
        return tuple(str(item) for item in value)
    except TypeError:
        return (str(value),)


# ---------------------------------------------------------------------------
# Safe component invocation
# ---------------------------------------------------------------------------


def _call_supported(
    method: Any,
    kwargs: Mapping[str, Any],
) -> Any:
    """
    Call an existing component method using only supported keyword arguments.

    This is intentionally conservative.

    It prevents Day 61 from passing arguments that an existing Day 46-60
    component does not support.

    It does NOT invent missing required arguments. If the component requires
    an argument that is not supplied, Python's normal TypeError is allowed
    to surface so the integration problem is visible.
    """
    try:
        method_signature = signature(method)
    except (TypeError, ValueError):
        return method(**dict(kwargs))

    parameters = method_signature.parameters

    accepts_var_kwargs = any(
        parameter.kind == Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )

    if accepts_var_kwargs:
        return method(**dict(kwargs))

    supported_kwargs = {
        key: value
        for key, value in kwargs.items()
        if key in parameters
    }

    return method(**supported_kwargs)


def _find_method(
    component: Any,
    method_names: Sequence[str],
) -> Any:
    """Find the first callable method from a list of candidate names."""
    if component is None:
        raise ValueError("Component must not be None")

    for method_name in method_names:
        method = getattr(component, method_name, None)

        if callable(method):
            return method

    available = [
        name
        for name in dir(component)
        if not name.startswith("_")
        and callable(getattr(component, name, None))
    ]

    raise AttributeError(
        "No supported method found on component. "
        f"Expected one of: {', '.join(method_names)}. "
        f"Available callable methods: {', '.join(available)}"
    )


def _invoke_component(
    component: Any,
    method_names: Sequence[str],
    kwargs: Mapping[str, Any],
) -> Any:
    """Find and invoke a component method safely."""
    method = _find_method(component, method_names)
    return _call_supported(method, kwargs)


# ---------------------------------------------------------------------------
# Input Model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BehavioralPipelineInput:
    """
    Input supplied to the unified Day 61 pipeline.

    The object contains evidence/context required by the individual
    behavioral, BCSE, predictive, and runtime layers.

    It does not represent an authorization request.
    """

    agent_id: str

    # Day 46
    trust_evidence: Mapping[str, float] = field(default_factory=dict)

    # Day 47
    state_dimensions: Mapping[str, float] = field(default_factory=dict)

    # Day 48
    deviation_dimensions: Mapping[str, float] = field(
        default_factory=dict
    )

    # Day 49
    baseline_observation: Mapping[str, float] = field(
        default_factory=dict
    )

    # Day 51
    current_context: Any = None
    hypothetical_context: Any = None
    counterfactual_changes: Sequence[Any] = field(
        default_factory=tuple
    )

    # Day 52
    consequence_dimensions: Mapping[str, float] = field(
        default_factory=dict
    )

    # Day 53
    security_context: Mapping[str, float] = field(
        default_factory=dict
    )

    # Day 56
    predictive_dimensions: Mapping[str, float] = field(
        default_factory=dict
    )

    # Days 57-58
    historical_scores: Sequence[float] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        """Validate the immutable input model."""
        normalized_agent_id = _validate_agent_id(self.agent_id)

        object.__setattr__(
            self,
            "agent_id",
            normalized_agent_id,
        )

        object.__setattr__(
            self,
            "trust_evidence",
            _validate_mapping(
                self.trust_evidence,
                "trust_evidence",
            ),
        )

        object.__setattr__(
            self,
            "state_dimensions",
            _validate_mapping(
                self.state_dimensions,
                "state_dimensions",
            ),
        )

        object.__setattr__(
            self,
            "deviation_dimensions",
            _validate_mapping(
                self.deviation_dimensions,
                "deviation_dimensions",
            ),
        )

        object.__setattr__(
            self,
            "baseline_observation",
            _validate_mapping(
                self.baseline_observation,
                "baseline_observation",
            ),
        )

        object.__setattr__(
            self,
            "consequence_dimensions",
            _validate_mapping(
                self.consequence_dimensions,
                "consequence_dimensions",
            ),
        )

        object.__setattr__(
            self,
            "security_context",
            _validate_mapping(
                self.security_context,
                "security_context",
            ),
        )

        object.__setattr__(
            self,
            "predictive_dimensions",
            _validate_mapping(
                self.predictive_dimensions,
                "predictive_dimensions",
            ),
        )

        object.__setattr__(
            self,
            "counterfactual_changes",
            _validate_sequence(
                self.counterfactual_changes,
                "counterfactual_changes",
            ),
        )

        historical = _validate_sequence(
            self.historical_scores,
            "historical_scores",
        )

        validated_history = tuple(
            _validate_score(
                score,
                "historical_score",
            )
            for score in historical
        )

        object.__setattr__(
            self,
            "historical_scores",
            validated_history,
        )


# ---------------------------------------------------------------------------
# Output / Data Model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class UnifiedBehavioralPipelineResult:
    """
    Unified Day 61 pipeline result.

    This is a structured representation of independent security-intelligence
    dimensions. It intentionally does NOT contain a universal Varynx score.
    """

    agent_id: str

    # Day 46
    trust_score: float
    trust_band: str

    # Day 47
    state_score: float
    state_level: str

    # Day 48
    deviation_score: float
    deviation_level: str

    # Day 49
    baseline_adapted: bool

    # Days 52-53
    consequence_score: float
    consequence_level: str
    consequence_confidence: str

    # Day 56
    predictive_score: float
    predictive_level: str
    predictive_direction: str
    predictive_confidence: str

    # Day 58
    forecast_score: float
    forecast_direction: str

    # Day 59
    control_recommendation: str

    # Day 60
    runtime_state: str

    # Evidence / consistency
    evidence: tuple[str, ...] = ()
    consistency_flags: tuple[str, ...] = ()

    # Additional metadata
    pipeline_version: str = PIPELINE_VERSION

    def __post_init__(self) -> None:
        """Validate immutable output data."""
        object.__setattr__(
            self,
            "agent_id",
            _validate_agent_id(self.agent_id),
        )

        for field_name in (
            "trust_score",
            "state_score",
            "deviation_score",
            "consequence_score",
            "predictive_score",
            "forecast_score",
        ):
            _validate_score(
                getattr(self, field_name),
                field_name,
            )

        for field_name in (
            "trust_band",
            "state_level",
            "deviation_level",
            "consequence_level",
            "consequence_confidence",
            "predictive_level",
            "predictive_direction",
            "predictive_confidence",
            "forecast_direction",
            "control_recommendation",
            "runtime_state",
            "pipeline_version",
        ):
            _validate_text(
                getattr(self, field_name),
                field_name,
            )

        if not isinstance(self.baseline_adapted, bool):
            raise TypeError(
                "baseline_adapted must be a boolean"
            )

        object.__setattr__(
            self,
            "evidence",
            tuple(str(item) for item in self.evidence),
        )

        object.__setattr__(
            self,
            "consistency_flags",
            tuple(
                str(item)
                for item in self.consistency_flags
            ),
        )


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class UnifiedBehavioralPipeline:
    """
    Day 61 unified behavioral intelligence orchestration layer.

    Existing component engines can be injected through the constructor.

    Example:

        pipeline = UnifiedBehavioralPipeline(
            trust_engine=trust_engine,
            state_engine=state_engine,
            deviation_engine=deviation_engine,
            baseline_engine=baseline_engine,
            scenario_builder=scenario_builder,
            consequence_estimator=consequence_estimator,
            context_model=context_model,
            predictive_engine=predictive_engine,
            trajectory_engine=trajectory_engine,
            forecast_engine=forecast_engine,
            control_engine=control_engine,
            runtime_engine=runtime_engine,
        )

    The pipeline does not create a replacement implementation of these
    engines.
    """

    def __init__(
        self,
        *,
        trust_engine: Any = None,
        state_engine: Any = None,
        deviation_engine: Any = None,
        baseline_engine: Any = None,
        scenario_builder: Any = None,
        consequence_estimator: Any = None,
        context_model: Any = None,
        predictive_engine: Any = None,
        trajectory_engine: Any = None,
        forecast_engine: Any = None,
        control_engine: Any = None,
        runtime_engine: Any = None,
    ) -> None:
        self.trust_engine = trust_engine
        self.state_engine = state_engine
        self.deviation_engine = deviation_engine
        self.baseline_engine = baseline_engine
        self.scenario_builder = scenario_builder
        self.consequence_estimator = consequence_estimator
        self.context_model = context_model
        self.predictive_engine = predictive_engine
        self.trajectory_engine = trajectory_engine
        self.forecast_engine = forecast_engine
        self.control_engine = control_engine
        self.runtime_engine = runtime_engine

        self._history: dict[
            str,
            list[UnifiedBehavioralPipelineResult],
        ] = {}

        self._latest: dict[
            str,
            UnifiedBehavioralPipelineResult,
        ] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_component(
        self,
        component: Any,
        component_name: str,
    ) -> Any:
        if component is None:
            raise RuntimeError(
                f"{component_name} has not been configured. "
                "Pass the existing Day component into "
                "UnifiedBehavioralPipeline."
            )

        return component

    def _record_result(
        self,
        result: UnifiedBehavioralPipelineResult,
    ) -> None:
        agent_id = result.agent_id

        self._history.setdefault(
            agent_id,
            [],
        ).append(result)

        self._latest[agent_id] = result

    # ------------------------------------------------------------------
    # Day 46 - Trust
    # ------------------------------------------------------------------

    def _evaluate_trust(
        self,
        data: BehavioralPipelineInput,
    ) -> Any:
        component = self._require_component(
            self.trust_engine,
            "Day 46 behavioral trust engine",
        )

        kwargs = {
            "agent_id": data.agent_id,
            "evidence": dict(data.trust_evidence),
            "trust_evidence": dict(data.trust_evidence),
            "dimensions": dict(data.trust_evidence),
        }

        return _invoke_component(
            component,
            (
                "update",
                "evaluate",
                "calculate",
                "compute",
                "assess",
            ),
            kwargs,
        )

    # ------------------------------------------------------------------
    # Day 47 - State
    # ------------------------------------------------------------------

    def _evaluate_state(
        self,
        data: BehavioralPipelineInput,
    ) -> Any:
        component = self._require_component(
            self.state_engine,
            "Day 47 behavioral state engine",
        )

        kwargs = {
            "agent_id": data.agent_id,
            "dimensions": dict(data.state_dimensions),
            "state_dimensions": dict(data.state_dimensions),
            "scores": dict(data.state_dimensions),
        }

        return _invoke_component(
            component,
            (
                "evaluate",
                "calculate_state",
                "calculate",
                "assess",
                "observe",
                "update",
            ),
            kwargs,
        )

    # ------------------------------------------------------------------
    # Day 48 - Deviation
    # ------------------------------------------------------------------

    def _evaluate_deviation(
        self,
        data: BehavioralPipelineInput,
    ) -> Any:
        component = self._require_component(
            self.deviation_engine,
            "Day 48 behavioral deviation engine",
        )

        kwargs = {
            "agent_id": data.agent_id,
            "dimensions": dict(data.deviation_dimensions),
            "deviation_dimensions": dict(
                data.deviation_dimensions
            ),
            "observations": dict(data.deviation_dimensions),
        }

        return _invoke_component(
            component,
            (
                "detect",
                "evaluate",
                "calculate_deviation",
                "calculate",
                "assess",
                "observe",
            ),
            kwargs,
        )

    # ------------------------------------------------------------------
    # Day 49 - Adaptive baseline
    # ------------------------------------------------------------------

    def _evaluate_baseline(
        self,
        data: BehavioralPipelineInput,
    ) -> Any:
        component = self._require_component(
            self.baseline_engine,
            "Day 49 adaptive behavioral baseline engine",
        )

        kwargs = {
            "agent_id": data.agent_id,
            "observation": dict(data.baseline_observation),
            "baseline_observation": dict(
                data.baseline_observation
            ),
            "dimensions": dict(data.baseline_observation),
        }

        return _invoke_component(
            component,
            (
                "observe",
                "update",
                "adapt",
                "evaluate",
            ),
            kwargs,
        )

    # ------------------------------------------------------------------
    # Day 51 - Counterfactual scenario
    # ------------------------------------------------------------------

    def _build_scenario(
        self,
        data: BehavioralPipelineInput,
    ) -> Any:
        component = self._require_component(
            self.scenario_builder,
            "Day 51 counterfactual scenario builder",
        )

        kwargs = {
            "agent_id": data.agent_id,
            "current_context": data.current_context,
            "hypothetical_context": data.hypothetical_context,
            "changes": tuple(data.counterfactual_changes),
            "counterfactual_changes": tuple(
                data.counterfactual_changes
            ),
        }

        return _invoke_component(
            component,
            (
                "create_scenario",
                "build_scenario",
                "build",
                "create",
            ),
            kwargs,
        )

    # ------------------------------------------------------------------
    # Day 52 - Consequence estimation
    # ------------------------------------------------------------------

    def _estimate_consequence(
        self,
        data: BehavioralPipelineInput,
        scenario: Any,
    ) -> Any:
        component = self._require_component(
            self.consequence_estimator,
            "Day 52 security consequence estimator",
        )

        scenario_id = _extract_attribute(
            scenario,
            ("scenario_id", "id"),
        )

        if scenario_id is None:
            raise ValueError(
                "Day 51 scenario result does not contain scenario_id"
            )

        kwargs = {
            "scenario": scenario,
            "scenario_id": scenario_id,
            "dimensions": dict(
                data.consequence_dimensions
            ),
            "consequence_dimensions": dict(
                data.consequence_dimensions
            ),
        }

        return _invoke_component(
            component,
            (
                "estimate",
                "evaluate",
                "calculate",
                "assess",
            ),
            kwargs,
        )

    # ------------------------------------------------------------------
    # Day 53 - Context-aware consequence
    # ------------------------------------------------------------------

    def _estimate_context(
        self,
        data: BehavioralPipelineInput,
        scenario: Any,
        consequence: Any,
    ) -> Any:
        component = self._require_component(
            self.context_model,
            "Day 53 context-aware consequence model",
        )

        scenario_id = _extract_attribute(
            scenario,
            ("scenario_id", "id"),
        )

        if scenario_id is None:
            raise ValueError(
                "Day 51 scenario result does not contain scenario_id"
            )

        consequence_score = _extract_score(
            consequence,
            (
                "consequence_score",
                "score",
                "base_consequence_score",
            ),
            "consequence_score",
        )

        # IMPORTANT:
        # The current known Day 53 API accepts:
        #
        # scenario_id
        # consequence_score
        # context
        #
        # Do not pass unsupported "evidence".
        kwargs = {
            "scenario_id": scenario_id,
            "consequence_score": consequence_score,
            "context": dict(data.security_context),
        }

        return _invoke_component(
            component,
            (
                "estimate",
                "evaluate",
                "calculate",
                "assess",
            ),
            kwargs,
        )

    # ------------------------------------------------------------------
    # Day 56 - Predictive security
    # ------------------------------------------------------------------

    def _evaluate_predictive(
        self,
        data: BehavioralPipelineInput,
        context_consequence: Any,
    ) -> Any:
        component = self._require_component(
            self.predictive_engine,
            "Day 56 predictive security engine",
        )

        consequence_score = _extract_score(
            context_consequence,
            (
                "adjusted_consequence_score",
                "consequence_score",
                "score",
            ),
            "consequence_score",
            required=False,
        )

        kwargs = {
            "agent_id": data.agent_id,
            "dimensions": dict(
                data.predictive_dimensions
            ),
            "predictive_dimensions": dict(
                data.predictive_dimensions
            ),
            "historical_scores": tuple(
                data.historical_scores
            ),
            "consequence_exposure": (
                consequence_score
            ),
        }

        return _invoke_component(
            component,
            (
                "evaluate",
                "predict",
                "calculate",
                "assess",
                "update",
            ),
            kwargs,
        )

    # ------------------------------------------------------------------
    # Day 57 - Trajectory
    # ------------------------------------------------------------------

    def _evaluate_trajectory(
        self,
        data: BehavioralPipelineInput,
        predictive: Any,
    ) -> Any:
        component = self._require_component(
            self.trajectory_engine,
            "Day 57 predictive trajectory engine",
        )

        predictive_score = _extract_score(
            predictive,
            (
                "predictive_score",
                "score",
                "security_score",
            ),
            "predictive_score",
        )

        historical_scores = tuple(
            data.historical_scores
        )

        if not historical_scores:
            historical_scores = (
                predictive_score,
            )

        kwargs = {
            "agent_id": data.agent_id,
            "scores": historical_scores,
            "historical_scores": historical_scores,
            "observations": historical_scores,
            "current_score": predictive_score,
        }

        return _invoke_component(
            component,
            (
                "analyze",
                "evaluate",
                "calculate",
                "predict",
                "observe",
                "update",
            ),
            kwargs,
        )

    # ------------------------------------------------------------------
    # Day 58 - Forecast
    # ------------------------------------------------------------------

    def _evaluate_forecast(
        self,
        data: BehavioralPipelineInput,
        predictive: Any,
        trajectory: Any,
    ) -> Any:
        component = self._require_component(
            self.forecast_engine,
            "Day 58 predictive forecast engine",
        )

        predictive_score = _extract_score(
            predictive,
            (
                "predictive_score",
                "score",
                "security_score",
            ),
            "predictive_score",
        )

        slope = _extract_attribute(
            trajectory,
            (
                "slope",
                "trend_slope",
            ),
            default=0.0,
        )

        historical_scores = tuple(
            data.historical_scores
        )

        if not historical_scores:
            historical_scores = (
                predictive_score,
            )

        kwargs = {
            "agent_id": data.agent_id,
            "current_score": predictive_score,
            "score": predictive_score,
            "historical_scores": historical_scores,
            "observations": historical_scores,
            "slope": slope,
        }

        return _invoke_component(
            component,
            (
                "forecast",
                "predict",
                "evaluate",
                "calculate",
                "update",
            ),
            kwargs,
        )

    # ------------------------------------------------------------------
    # Day 59 - Predictive control
    # ------------------------------------------------------------------

    def _evaluate_control(
        self,
        data: BehavioralPipelineInput,
        predictive: Any,
        trajectory: Any,
        forecast: Any,
    ) -> Any:
        component = self._require_component(
            self.control_engine,
            "Day 59 predictive control engine",
        )

        predictive_score = _extract_score(
            predictive,
            (
                "predictive_score",
                "score",
                "security_score",
            ),
            "predictive_score",
        )

        predictive_direction = _extract_text(
            predictive,
            (
                "predictive_direction",
                "direction",
            ),
            "predictive_direction",
            required=False,
        )

        predictive_confidence = _extract_text(
            predictive,
            (
                "predictive_confidence",
                "confidence",
            ),
            "predictive_confidence",
            required=False,
        )

        trajectory_slope = _extract_attribute(
            trajectory,
            (
                "slope",
                "trend_slope",
            ),
            default=0.0,
        )

        forecast_score = _extract_score(
            forecast,
            (
                "forecast_score",
                "predicted_score",
                "score",
            ),
            "forecast_score",
            required=False,
        )

        forecast_direction = _extract_text(
            forecast,
            (
                "forecast_direction",
                "direction",
            ),
            "forecast_direction",
            required=False,
        )

        kwargs = {
            "agent_id": data.agent_id,
            "predictive_score": predictive_score,
            "score": predictive_score,
            "direction": predictive_direction,
            "predictive_direction": predictive_direction,
            "confidence": predictive_confidence,
            "predictive_confidence": predictive_confidence,
            "slope": trajectory_slope,
            "forecast_score": forecast_score,
            "forecast_direction": forecast_direction,
        }

        return _invoke_component(
            component,
            (
                "recommend",
                "evaluate",
                "calculate",
                "decide",
                "assess",
            ),
            kwargs,
        )

    # ------------------------------------------------------------------
    # Day 60 - Runtime envelope
    # ------------------------------------------------------------------

    def _evaluate_runtime(
        self,
        data: BehavioralPipelineInput,
        predictive: Any,
        trajectory: Any,
        forecast: Any,
        control: Any,
    ) -> Any:
        component = self._require_component(
            self.runtime_engine,
            "Day 60 predictive runtime engine",
        )

        predictive_score = _extract_score(
            predictive,
            (
                "predictive_score",
                "score",
                "security_score",
            ),
            "predictive_score",
        )

        direction = _extract_text(
            predictive,
            (
                "predictive_direction",
                "direction",
            ),
            "direction",
        )

        confidence = _extract_text(
            predictive,
            (
                "predictive_confidence",
                "confidence",
            ),
            "confidence",
        )

        recommendation = _extract_text(
            control,
            (
                "control_recommendation",
                "recommendation",
                "control",
                "action",
            ),
            "control_recommendation",
        )

        slope = _extract_attribute(
            trajectory,
            (
                "slope",
                "trend_slope",
            ),
            default=0.0,
        )

        kwargs = {
            "agent_id": data.agent_id,
            "projected_score": predictive_score,
            "predictive_score": predictive_score,
            "direction": direction,
            "confidence": confidence,
            "recommendation": recommendation,
            "control_recommendation": recommendation,
            "slope": slope,
        }

        return _invoke_component(
            component,
            (
                "prepare_decision",
                "prepare",
                "evaluate",
                "create_decision",
                "build_decision",
            ),
            kwargs,
        )

    # ------------------------------------------------------------------
    # Consistency analysis
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_consistency_flags(
        trust_score: float,
        trust_band: str,
        state_score: float,
        state_level: str,
        deviation_score: float,
        deviation_level: str,
        consequence_score: float,
        predictive_score: float,
        predictive_direction: str,
    ) -> tuple[str, ...]:
        """
        Detect notable combinations of independent signals.

        These flags are descriptive.

        They do not override authorization or adaptive response.
        """
        flags: list[str] = []

        if (
            trust_band == TRUST_HIGH
            and deviation_level in {
                DEVIATION_HIGH,
                DEVIATION_CRITICAL,
            }
        ):
            flags.append(
                "HIGH_TRUST_WITH_HIGH_DEVIATION"
            )

        if (
            trust_band == TRUST_LOW
            and deviation_level == DEVIATION_LOW
        ):
            flags.append(
                "LOW_TRUST_WITH_LOW_DEVIATION"
            )

        if (
            state_level in {
                STATE_STABLE,
                STATE_MOSTLY_STABLE,
            }
            and deviation_level
            in {
                DEVIATION_HIGH,
                DEVIATION_CRITICAL,
            }
        ):
            flags.append(
                "STABLE_STATE_WITH_HIGH_DEVIATION"
            )

        if (
            state_level
            in {
                STATE_UNSTABLE,
                STATE_HIGHLY_UNSTABLE,
            }
            and deviation_level
            in {
                DEVIATION_NONE,
                DEVIATION_LOW,
            }
        ):
            flags.append(
                "UNSTABLE_STATE_WITH_LOW_DEVIATION"
            )

        if (
            trust_band == TRUST_HIGH
            and state_level
            in {
                STATE_UNSTABLE,
                STATE_HIGHLY_UNSTABLE,
            }
        ):
            flags.append(
                "HIGH_TRUST_WITH_UNSTABLE_STATE"
            )

        if (
            trust_band == TRUST_CRITICAL
            and deviation_level == DEVIATION_CRITICAL
        ):
            flags.append(
                "CRITICAL_DEVIATION_AND_TRUST"
            )

        if (
            consequence_score >= 70.0
            and predictive_score < 40.0
        ):
            flags.append(
                "HIGH_CONSEQUENCE_WITH_LOW_PREDICTIVE_SIGNAL"
            )

        if (
            predictive_direction == "DETERIORATING"
            and deviation_score < 20.0
        ):
            flags.append(
                "PREDICTIVE_DETERIORATION_WITH_LOW_CURRENT_DEVIATION"
            )

        return tuple(flags)

    # ------------------------------------------------------------------
    # Main execution
    # ------------------------------------------------------------------

    def evaluate(
        self,
        data: BehavioralPipelineInput,
    ) -> UnifiedBehavioralPipelineResult:
        """
        Execute the complete Day 61 orchestration pipeline.

        Raises
        ------
        RuntimeError
            When a required Day 46-60 component is not configured.

        TypeError / ValueError
            When an existing component exposes an incompatible contract.

        The method intentionally does not catch and suppress component
        failures. Integration errors must remain visible.
        """
        if not isinstance(
            data,
            BehavioralPipelineInput,
        ):
            raise TypeError(
                "data must be a BehavioralPipelineInput"
            )

        # --------------------------------------------------------------
        # Day 46
        # --------------------------------------------------------------

        trust_result = self._evaluate_trust(data)

        trust_score = _extract_score(
            trust_result,
            (
                "trust_score",
                "score",
            ),
            "trust_score",
        )

        trust_band = _extract_text(
            trust_result,
            (
                "trust_band",
                "band",
                "trust_level",
            ),
            "trust_band",
        )

        # --------------------------------------------------------------
        # Day 47
        # --------------------------------------------------------------

        state_result = self._evaluate_state(data)

        state_score = _extract_score(
            state_result,
            (
                "state_score",
                "stability_score",
                "score",
            ),
            "state_score",
        )

        state_level = _extract_text(
            state_result,
            (
                "state_level",
                "stability_level",
                "level",
            ),
            "state_level",
        )

        # --------------------------------------------------------------
        # Day 48
        # --------------------------------------------------------------

        deviation_result = self._evaluate_deviation(data)

        deviation_score = _extract_score(
            deviation_result,
            (
                "deviation_score",
                "score",
            ),
            "deviation_score",
        )

        deviation_level = _extract_text(
            deviation_result,
            (
                "deviation_level",
                "level",
            ),
            "deviation_level",
        )

        # --------------------------------------------------------------
        # Day 49
        # --------------------------------------------------------------

        baseline_result = self._evaluate_baseline(data)

        baseline_adapted_value = _extract_attribute(
            baseline_result,
            (
                "baseline_adapted",
                "adapted",
                "accepted",
                "updated",
            ),
            default=False,
        )

        baseline_adapted = bool(
            baseline_adapted_value
        )

        # --------------------------------------------------------------
        # Day 51
        # --------------------------------------------------------------

        scenario_result = self._build_scenario(data)

        # --------------------------------------------------------------
        # Day 52
        # --------------------------------------------------------------

        consequence_result = self._estimate_consequence(
            data,
            scenario_result,
        )

        # --------------------------------------------------------------
        # Day 53
        # --------------------------------------------------------------

        context_result = self._estimate_context(
            data,
            scenario_result,
            consequence_result,
        )

        consequence_score = _extract_score(
            context_result,
            (
                "adjusted_consequence_score",
                "consequence_score",
                "score",
            ),
            "consequence_score",
        )

        consequence_level = _extract_text(
            context_result,
            (
                "consequence_level",
                "adjusted_consequence_level",
                "level",
            ),
            "consequence_level",
        )

        consequence_confidence = _extract_text(
            context_result,
            (
                "confidence",
                "consequence_confidence",
            ),
            "consequence_confidence",
        )

        # --------------------------------------------------------------
        # Day 56
        # --------------------------------------------------------------

        predictive_result = self._evaluate_predictive(
            data,
            context_result,
        )

        predictive_score = _extract_score(
            predictive_result,
            (
                "predictive_score",
                "score",
                "security_score",
            ),
            "predictive_score",
        )

        predictive_level = _extract_text(
            predictive_result,
            (
                "predictive_level",
                "level",
            ),
            "predictive_level",
        )

        predictive_direction = _extract_text(
            predictive_result,
            (
                "predictive_direction",
                "direction",
            ),
            "predictive_direction",
        )

        predictive_confidence = _extract_text(
            predictive_result,
            (
                "predictive_confidence",
                "confidence",
            ),
            "predictive_confidence",
        )

        # --------------------------------------------------------------
        # Day 57
        # --------------------------------------------------------------

        trajectory_result = self._evaluate_trajectory(
            data,
            predictive_result,
        )

        # --------------------------------------------------------------
        # Day 58
        # --------------------------------------------------------------

        forecast_result = self._evaluate_forecast(
            data,
            predictive_result,
            trajectory_result,
        )

        forecast_score = _extract_score(
            forecast_result,
            (
                "forecast_score",
                "predicted_score",
                "score",
            ),
            "forecast_score",
        )

        forecast_direction = _extract_text(
            forecast_result,
            (
                "forecast_direction",
                "direction",
            ),
            "forecast_direction",
        )

        # --------------------------------------------------------------
        # Day 59
        # --------------------------------------------------------------

        control_result = self._evaluate_control(
            data,
            predictive_result,
            trajectory_result,
            forecast_result,
        )

        control_recommendation = _extract_text(
            control_result,
            (
                "control_recommendation",
                "recommendation",
                "control",
                "action",
            ),
            "control_recommendation",
        )

        # --------------------------------------------------------------
        # Day 60
        # --------------------------------------------------------------

        runtime_result = self._evaluate_runtime(
            data,
            predictive_result,
            trajectory_result,
            forecast_result,
            control_result,
        )

        runtime_state = _extract_text(
            runtime_result,
            (
                "runtime_state",
                "state",
            ),
            "runtime_state",
        )

        # --------------------------------------------------------------
        # Evidence aggregation
        # --------------------------------------------------------------

        evidence_parts: list[str] = []

        for component_result in (
            trust_result,
            state_result,
            deviation_result,
            baseline_result,
            scenario_result,
            consequence_result,
            context_result,
            predictive_result,
            trajectory_result,
            forecast_result,
            control_result,
            runtime_result,
        ):
            evidence_parts.extend(
                _extract_evidence(
                    component_result
                )
            )

        # Remove duplicates while preserving order.
        evidence = tuple(
            dict.fromkeys(evidence_parts)
        )

        # --------------------------------------------------------------
        # Consistency analysis
        # --------------------------------------------------------------

        consistency_flags = (
            self._detect_consistency_flags(
                trust_score=trust_score,
                trust_band=trust_band,
                state_score=state_score,
                state_level=state_level,
                deviation_score=deviation_score,
                deviation_level=deviation_level,
                consequence_score=consequence_score,
                predictive_score=predictive_score,
                predictive_direction=predictive_direction,
            )
        )

        # Add consistency observations to evidence.
        if consistency_flags:
            evidence = tuple(
                dict.fromkeys(
                    evidence
                    + tuple(
                        f"Consistency flag: {flag}"
                        for flag in consistency_flags
                    )
                )
            )

        # --------------------------------------------------------------
        # Unified result
        # --------------------------------------------------------------

        result = UnifiedBehavioralPipelineResult(
            agent_id=data.agent_id,
            trust_score=trust_score,
            trust_band=trust_band,
            state_score=state_score,
            state_level=state_level,
            deviation_score=deviation_score,
            deviation_level=deviation_level,
            baseline_adapted=baseline_adapted,
            consequence_score=consequence_score,
            consequence_level=consequence_level,
            consequence_confidence=consequence_confidence,
            predictive_score=predictive_score,
            predictive_level=predictive_level,
            predictive_direction=predictive_direction,
            predictive_confidence=predictive_confidence,
            forecast_score=forecast_score,
            forecast_direction=forecast_direction,
            control_recommendation=control_recommendation,
            runtime_state=runtime_state,
            evidence=evidence,
            consistency_flags=consistency_flags,
        )

        self._record_result(result)

        return result

    # ------------------------------------------------------------------
    # History API
    # ------------------------------------------------------------------

    def history(
        self,
        agent_id: str,
    ) -> tuple[UnifiedBehavioralPipelineResult, ...]:
        """Return immutable pipeline history for an agent."""
        agent_id = _validate_agent_id(agent_id)

        return tuple(
            self._history.get(
                agent_id,
                [],
            )
        )

    def latest(
        self,
        agent_id: str,
    ) -> Optional[UnifiedBehavioralPipelineResult]:
        """Return the latest pipeline result for an agent."""
        agent_id = _validate_agent_id(agent_id)

        return self._latest.get(agent_id)

    def snapshot_all(
        self,
    ) -> dict[
        str,
        UnifiedBehavioralPipelineResult,
    ]:
        """
        Return the latest result for every known agent.

        A defensive dictionary copy is returned.
        """
        return dict(self._latest)

    def reset(
        self,
        agent_id: Optional[str] = None,
    ) -> None:
        """
        Reset pipeline-level history.

        If agent_id is supplied, only that agent is reset.

        If agent_id is None, all pipeline-level history is cleared.

        This does not automatically reset the underlying Day 46-60
        component engines.
        """
        if agent_id is None:
            self._history.clear()
            self._latest.clear()
            return

        agent_id = _validate_agent_id(agent_id)

        self._history.pop(agent_id, None)
        self._latest.pop(agent_id, None)


# ---------------------------------------------------------------------------
# Public exports
# ---------------------------------------------------------------------------

__all__ = [
    "SCORE_MIN",
    "SCORE_MAX",
    "PIPELINE_VERSION",
    "BehavioralPipelineInput",
    "UnifiedBehavioralPipelineResult",
    "UnifiedBehavioralPipeline",
]