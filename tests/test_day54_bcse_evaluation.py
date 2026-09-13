import json
from pathlib import Path

import pytest

from app.bcse_evaluation import (
    BASELINE_FULL_VARYNX_BCSE,
    BASELINE_RISK_ONLY,
    SUPPORTED_BASELINES,
    BCSEEvaluator,
    EvaluationCase,
    build_reproducibility_manifest,
    validate_baseline,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "day54_bcse_cases.json"
)


def load_cases():
    with FIXTURE_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return tuple(
        EvaluationCase(**item)
        for item in data
    )


def test_fixture_cases_load():
    cases = load_cases()

    assert len(cases) == 6


def test_fixture_case_ids_are_unique():
    cases = load_cases()

    ids = [case.case_id for case in cases]

    assert len(ids) == len(set(ids))


def test_supported_baselines_exist():
    assert BASELINE_FULL_VARYNX_BCSE in SUPPORTED_BASELINES
    assert BASELINE_RISK_ONLY in SUPPORTED_BASELINES


def test_validate_supported_baseline():
    assert (
        validate_baseline(BASELINE_FULL_VARYNX_BCSE)
        == BASELINE_FULL_VARYNX_BCSE
    )


def test_validate_invalid_baseline():
    with pytest.raises(ValueError):
        validate_baseline("INVALID")


def test_evaluate_single_case():
    evaluator = BCSEEvaluator()
    case = load_cases()[0]

    result = evaluator.evaluate_case(case)

    assert result.case_id == case.case_id
    assert result.baseline == BASELINE_FULL_VARYNX_BCSE
    assert 0 <= result.context_index <= 100
    assert 0 <= result.adjusted_consequence_score <= 100


def test_evaluate_all_cases():
    evaluator = BCSEEvaluator()
    cases = load_cases()

    results = evaluator.evaluate(cases)

    assert len(results) == len(cases)


def test_all_results_are_bounded():
    evaluator = BCSEEvaluator()
    results = evaluator.evaluate(load_cases())

    for result in results:
        assert 0 <= result.adjusted_consequence_score <= 100


def test_all_results_are_within_expected_bounds():
    evaluator = BCSEEvaluator()
    results = evaluator.evaluate(load_cases())

    assert all(
        result.within_bounds
        for result in results
    )


def test_evaluation_is_deterministic():
    evaluator = BCSEEvaluator()
    cases = load_cases()

    first = evaluator.evaluate(cases)
    second = evaluator.evaluate(cases)

    assert first == second


def test_compare_results_identical():
    evaluator = BCSEEvaluator()
    cases = load_cases()

    first = evaluator.evaluate(cases)
    second = evaluator.evaluate(cases)

    assert evaluator.compare_results(
        first,
        second,
    )


def test_reproducibility_evaluation():
    evaluator = BCSEEvaluator()
    cases = load_cases()

    first, second, rate = (
        evaluator.evaluate_reproducibility(
            cases
        )
    )

    assert first == second
    assert rate == 1.0


def test_metrics_for_empty_results():
    metrics = BCSEEvaluator.calculate_metrics([])

    assert metrics.total_cases == 0
    assert metrics.valid_cases == 0
    assert metrics.bounded_cases == 0
    assert metrics.adjustment_rate == 0.0


def test_metrics_for_results():
    evaluator = BCSEEvaluator()
    cases = load_cases()

    results = evaluator.evaluate(cases)

    metrics = evaluator.calculate_metrics(results)

    assert metrics.total_cases == 6
    assert metrics.valid_cases == 6
    assert 0 <= metrics.bounded_cases <= 6
    assert 0 <= metrics.adjustment_rate <= 1
    assert metrics.reproducibility_rate == 1.0


def test_metrics_record_context_index():
    evaluator = BCSEEvaluator()
    results = evaluator.evaluate(load_cases())

    metrics = evaluator.calculate_metrics(results)

    assert 0 <= metrics.mean_context_index <= 100


def test_metrics_record_consequence_values():
    evaluator = BCSEEvaluator()
    results = evaluator.evaluate(load_cases())

    metrics = evaluator.calculate_metrics(results)

    assert 0 <= metrics.mean_base_consequence <= 100
    assert 0 <= metrics.mean_adjusted_consequence <= 100


def test_manifest_contains_case_ids():
    cases = load_cases()

    manifest = build_reproducibility_manifest(
        cases,
        BASELINE_FULL_VARYNX_BCSE,
    )

    assert manifest.evaluation_version == "day54-v1"
    assert manifest.seed == 0
    assert manifest.case_count == 6
    assert len(manifest.case_ids) == 6


def test_manifest_rejects_duplicate_ids():
    cases = load_cases()

    duplicate_cases = (
        cases[0],
        cases[0],
    )

    with pytest.raises(ValueError):
        build_reproducibility_manifest(
            duplicate_cases,
            BASELINE_FULL_VARYNX_BCSE,
        )


def test_manifest_rejects_invalid_baseline():
    cases = load_cases()

    with pytest.raises(ValueError):
        build_reproducibility_manifest(
            cases,
            "INVALID",
        )


def test_manifest_accepts_custom_seed():
    cases = load_cases()

    manifest = build_reproducibility_manifest(
        cases,
        BASELINE_FULL_VARYNX_BCSE,
        seed=42,
    )

    assert manifest.seed == 42


def test_case_rejects_empty_id():
    with pytest.raises(ValueError):
        EvaluationCase(
            case_id="",
            scenario_id="scenario-1",
            base_consequence_score=50,
            context={},
        )


def test_case_rejects_invalid_score():
    with pytest.raises(ValueError):
        EvaluationCase(
            case_id="case-1",
            scenario_id="scenario-1",
            base_consequence_score=101,
            context={},
        )


def test_case_rejects_invalid_expected_range():
    with pytest.raises(ValueError):
        EvaluationCase(
            case_id="case-1",
            scenario_id="scenario-1",
            base_consequence_score=50,
            context={},
            expected_min=90,
            expected_max=10,
        )


def test_case_rejects_non_mapping_context():
    with pytest.raises(TypeError):
        EvaluationCase(
            case_id="case-1",
            scenario_id="scenario-1",
            base_consequence_score=50,
            context=None,
        )


def test_evaluator_rejects_duplicate_case_ids():
    evaluator = BCSEEvaluator()
    cases = load_cases()

    duplicate_cases = (
        cases[0],
        cases[0],
    )

    with pytest.raises(ValueError):
        evaluator.evaluate(duplicate_cases)


def test_evaluator_supports_baseline_labels():
    evaluator = BCSEEvaluator()
    case = load_cases()[0]

    result = evaluator.evaluate_case(
        case,
        baseline=BASELINE_RISK_ONLY,
    )

    assert result.baseline == BASELINE_RISK_ONLY


def test_custom_evaluation_version():
    evaluator = BCSEEvaluator(
        evaluation_version="custom-v1"
    )

    assert evaluator.evaluation_version == "custom-v1"


def test_evaluator_rejects_empty_version():
    with pytest.raises(ValueError):
        BCSEEvaluator(evaluation_version="")


def test_evaluator_rejects_non_string_version():
    with pytest.raises(TypeError):
        BCSEEvaluator(evaluation_version=None)


def test_metrics_reject_invalid_reproducibility_rate():
    with pytest.raises(ValueError):
        BCSEEvaluator.calculate_metrics(
            [],
            reproducibility_rate=1.5,
        )


def test_metrics_reject_negative_reproducibility_rate():
    with pytest.raises(ValueError):
        BCSEEvaluator.calculate_metrics(
            [],
            reproducibility_rate=-0.1,
        )


def test_case_result_preserves_base_score():
    evaluator = BCSEEvaluator()
    case = load_cases()[2]

    result = evaluator.evaluate_case(case)

    assert (
        result.base_consequence_score
        == case.base_consequence_score
    )


def test_context_can_change_adjusted_result():
    evaluator = BCSEEvaluator()
    cases = load_cases()

    low_context = evaluator.evaluate_case(
        cases[5]
    )

    high_context = evaluator.evaluate_case(
        cases[4]
    )

    assert (
        high_context.adjusted_consequence_score
        >= low_context.adjusted_consequence_score
    )


def test_reproducibility_manifest_is_immutable():
    cases = load_cases()

    manifest = build_reproducibility_manifest(
        cases,
        BASELINE_FULL_VARYNX_BCSE,
    )

    with pytest.raises(Exception):
        manifest.seed = 100


def test_evaluation_result_is_immutable():
    evaluator = BCSEEvaluator()
    result = evaluator.evaluate(
        load_cases()
    )[0]

    with pytest.raises(Exception):
        result.adjusted_consequence_score = 0


def test_evaluation_metrics_are_immutable():
    evaluator = BCSEEvaluator()
    results = evaluator.evaluate(
        load_cases()
    )

    metrics = evaluator.calculate_metrics(results)

    with pytest.raises(Exception):
        metrics.total_cases = 0