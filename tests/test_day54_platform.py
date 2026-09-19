import pytest

from app.bcse_evaluation import (
    BASELINE_FULL_VARYNX_BCSE,
    BCSEEvaluator,
    EvaluationResult,
    build_reproducibility_manifest,
)
from app.platform.bcse_evaluation import (
    BCSEEvaluationPlatformAdapter,
)


def build_result(case_index: int = 0) -> EvaluationResult:
    evaluator = BCSEEvaluator()

    from app.bcse_evaluation import EvaluationCase

    case = EvaluationCase(
        case_id=f"case-{case_index}",
        scenario_id=f"scenario-{case_index}",
        base_consequence_score=50.0 + case_index,
        context={
            "trust_score": 70.0,
            "state_score": 60.0,
            "deviation_score": 20.0,
        },
    )

    return evaluator.evaluate_case(
        case,
        baseline=BASELINE_FULL_VARYNX_BCSE,
    )


def test_record_evaluation():
    adapter = BCSEEvaluationPlatformAdapter()
    result = build_result()

    stored = adapter.record_evaluation(
        "agent-1",
        result,
    )

    assert stored["case_id"] == result.case_id
    assert stored["baseline"] == BASELINE_FULL_VARYNX_BCSE
    assert (
        stored["adjusted_consequence_score"]
        == result.adjusted_consequence_score
    )


def test_latest_evaluation_returns_latest_result():
    adapter = BCSEEvaluationPlatformAdapter()

    first = build_result(1)
    second = build_result(2)

    adapter.record_evaluation("agent-1", first)
    adapter.record_evaluation("agent-1", second)

    latest = adapter.latest_evaluation("agent-1")

    assert latest is not None
    assert latest["case_id"] == second.case_id


def test_latest_evaluation_returns_none_for_unknown_agent():
    adapter = BCSEEvaluationPlatformAdapter()

    assert adapter.latest_evaluation("missing-agent") is None


def test_evaluation_history_preserves_order():
    adapter = BCSEEvaluationPlatformAdapter()

    first = build_result(1)
    second = build_result(2)

    adapter.record_evaluation("agent-1", first)
    adapter.record_evaluation("agent-1", second)

    history = adapter.evaluation_history("agent-1")

    assert len(history) == 2
    assert history[0]["case_id"] == first.case_id
    assert history[1]["case_id"] == second.case_id


def test_history_count():
    adapter = BCSEEvaluationPlatformAdapter()

    assert adapter.history_count("agent-1") == 0

    adapter.record_evaluation(
        "agent-1",
        build_result(),
    )

    assert adapter.history_count("agent-1") == 1


def test_agent_histories_are_isolated():
    adapter = BCSEEvaluationPlatformAdapter()

    agent_a = build_result(1)
    agent_b = build_result(2)

    adapter.record_evaluation("agent-a", agent_a)
    adapter.record_evaluation("agent-b", agent_b)

    assert (
        adapter.latest_evaluation("agent-a")["case_id"]
        == agent_a.case_id
    )
    assert (
        adapter.latest_evaluation("agent-b")["case_id"]
        == agent_b.case_id
    )


def test_reset_single_agent():
    adapter = BCSEEvaluationPlatformAdapter()

    adapter.record_evaluation(
        "agent-a",
        build_result(1),
    )
    adapter.record_evaluation(
        "agent-b",
        build_result(2),
    )

    adapter.reset_evaluations("agent-a")

    assert adapter.history_count("agent-a") == 0
    assert adapter.history_count("agent-b") == 1


def test_reset_all_agents():
    adapter = BCSEEvaluationPlatformAdapter()

    adapter.record_evaluation(
        "agent-a",
        build_result(1),
    )
    adapter.record_evaluation(
        "agent-b",
        build_result(2),
    )

    adapter.reset_evaluations()

    assert adapter.history_count("agent-a") == 0
    assert adapter.history_count("agent-b") == 0


def test_result_serialization_is_fresh():
    adapter = BCSEEvaluationPlatformAdapter()
    result = build_result()

    stored = adapter.record_evaluation(
        "agent-1",
        result,
    )

    stored["case_id"] = "tampered"

    latest = adapter.latest_evaluation("agent-1")

    assert latest is not None
    assert latest["case_id"] == result.case_id


def test_history_serialization_is_fresh():
    adapter = BCSEEvaluationPlatformAdapter()
    result = build_result()

    adapter.record_evaluation(
        "agent-1",
        result,
    )

    history = adapter.evaluation_history("agent-1")
    history[0]["case_id"] = "tampered"

    latest = adapter.latest_evaluation("agent-1")

    assert latest is not None
    assert latest["case_id"] == result.case_id


def test_metrics_serialization():
    evaluator = BCSEEvaluator()

    result = build_result(1)
    metrics = evaluator.calculate_metrics((result,))

    serialized = BCSEEvaluationPlatformAdapter.serialize_metrics(
        metrics
    )

    assert serialized["total_cases"] == metrics.total_cases
    assert (
        serialized["mean_adjusted_consequence"]
        == metrics.mean_adjusted_consequence
    )
    assert (
        serialized["reproducibility_rate"]
        == metrics.reproducibility_rate
    )

def test_manifest_serialization():
    from app.bcse_evaluation import EvaluationCase

    cases = (
        EvaluationCase(
            case_id="case-1",
            scenario_id="scenario-1",
            base_consequence_score=50,
            context={},
        ),
    )

    manifest = build_reproducibility_manifest(
        cases,
        BASELINE_FULL_VARYNX_BCSE,
    )

    serialized = BCSEEvaluationPlatformAdapter.serialize_manifest(
        manifest
    )

    assert serialized["evaluation_version"] == "day54-v1"
    assert serialized["seed"] == 0
    assert serialized["case_ids"] == ["case-1"]
    assert serialized["case_count"] == 1


def test_invalid_agent_id_is_rejected():
    adapter = BCSEEvaluationPlatformAdapter()

    with pytest.raises(ValueError):
        adapter.history_count("")


def test_invalid_result_is_rejected():
    adapter = BCSEEvaluationPlatformAdapter()

    with pytest.raises(TypeError):
        adapter.record_evaluation(
            "agent-1",
            object(),
        )