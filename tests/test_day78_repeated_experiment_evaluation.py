"""
Tests for Varynx Day78 - Repeated Experiment Evaluation.
"""

from app.repeated_experiment_evaluation import (
    AGGREGATION_COMPLETE,
    AGGREGATION_FAILED,
    AGGREGATION_PARTIAL,
    OUTCOME_FAILED,
    OUTCOME_SUCCESS,
    RepeatedExperimentConfig,
    RepeatedExperimentEvaluator,
    enforcement_is_executed_here,
    malicious_intent_is_inferred_here,
    repeated_evaluation_is_read_only,
    security_decision_is_modified_here,
    statistical_significance_is_claimed_here,
    universal_security_score_is_created,
)


def deterministic_experiment(seed: int):
    """
    Different seeds intentionally generate different values.
    """

    return {
        "seed": seed,
        "score": seed % 100,
        "latency": float(seed % 10) + 1.0,
        "decision": "ALLOW",
    }


def failing_experiment(seed: int):
    if seed == 202:
        raise RuntimeError(
            "intentional controlled failure"
        )

    return {
        "seed": seed,
        "score": 10,
    }


def non_mapping_experiment(seed: int):
    return f"result-{seed}"


def test_explicit_seed_configuration_is_preserved():
    config = RepeatedExperimentConfig(
        experiment_id="day78-config",
        scenario="controlled",
        seeds=(101, 202, 303),
    )

    assert config.seeds == (
        101,
        202,
        303,
    )


def test_repeated_experiment_executes_once_per_seed():
    calls = []

    def experiment(seed: int):
        calls.append(seed)

        return {
            "seed": seed,
            "score": seed % 10,
        }

    config = RepeatedExperimentConfig(
        experiment_id="day78-once",
        scenario="one-execution-per-seed",
        seeds=(10, 20, 30),
    )

    report = RepeatedExperimentEvaluator().run(
        config,
        experiment,
    )

    assert calls == [
        10,
        20,
        30,
    ]

    assert len(report.outcomes) == 3


def test_deterministic_experiment_aggregates_successfully():
    config = RepeatedExperimentConfig(
        experiment_id="day78-deterministic",
        scenario="stable",
        seeds=(101, 202, 303, 404),
    )

    report = RepeatedExperimentEvaluator().run(
        config,
        deterministic_experiment,
    )

    assert (
        report.aggregation_status
        == AGGREGATION_COMPLETE
    )

    assert report.successful_runs == 4
    assert report.failed_runs == 0

    assert all(
        outcome.status == OUTCOME_SUCCESS
        for outcome in report.outcomes
    )


def test_different_seeds_may_produce_different_outputs():
    config = RepeatedExperimentConfig(
        experiment_id="day78-seed-variation",
        scenario="different-seeds",
        seeds=(101, 202, 303),
    )

    report = RepeatedExperimentEvaluator().run(
        config,
        deterministic_experiment,
    )

    fingerprints = {
        outcome.output_fingerprint
        for outcome in report.outcomes
    }

    assert len(fingerprints) == 3

    assert (
        report.aggregation_status
        == AGGREGATION_COMPLETE
    )


def test_numeric_metrics_are_summarized():
    config = RepeatedExperimentConfig(
        experiment_id="day78-metrics",
        scenario="numeric-summary",
        seeds=(1, 2, 3),
    )

    report = RepeatedExperimentEvaluator().run(
        config,
        deterministic_experiment,
    )

    summaries = {
        summary.metric_name: summary
        for summary in report.numeric_summaries
    }

    assert "score" in summaries
    assert "latency" in summaries

    score = summaries["score"]

    assert score.count == 3
    assert score.minimum == 1.0
    assert score.maximum == 3.0
    assert score.total == 6.0
    assert score.mean == 2.0


def test_non_mapping_outputs_do_not_break_aggregation():
    config = RepeatedExperimentConfig(
        experiment_id="day78-non-mapping",
        scenario="string-output",
        seeds=(1, 2, 3),
    )

    report = RepeatedExperimentEvaluator().run(
        config,
        non_mapping_experiment,
    )

    assert (
        report.aggregation_status
        == AGGREGATION_COMPLETE
    )

    assert report.numeric_summaries == ()


def test_failure_is_preserved():
    config = RepeatedExperimentConfig(
        experiment_id="day78-failure",
        scenario="controlled-failure",
        seeds=(101, 202, 303),
    )

    report = RepeatedExperimentEvaluator().run(
        config,
        failing_experiment,
    )

    assert report.successful_runs == 2
    assert report.failed_runs == 1

    assert (
        report.aggregation_status
        == AGGREGATION_PARTIAL
    )

    failed = [
        outcome
        for outcome in report.outcomes
        if outcome.status == OUTCOME_FAILED
    ]

    assert len(failed) == 1
    assert failed[0].seed == 202


def test_all_failures_produce_failed_aggregation():
    def always_fail(seed: int):
        raise RuntimeError(
            "controlled failure"
        )

    config = RepeatedExperimentConfig(
        experiment_id="day78-all-fail",
        scenario="failure",
        seeds=(1, 2, 3),
    )

    report = RepeatedExperimentEvaluator().run(
        config,
        always_fail,
    )

    assert (
        report.aggregation_status
        == AGGREGATION_FAILED
    )

    assert report.successful_runs == 0
    assert report.failed_runs == 3


def test_minimum_successful_runs_can_define_partial_result():
    config = RepeatedExperimentConfig(
        experiment_id="day78-minimum",
        scenario="minimum-success",
        seeds=(101, 202, 303),
        minimum_successful_runs=2,
    )

    report = RepeatedExperimentEvaluator().run(
        config,
        failing_experiment,
    )

    assert (
        report.aggregation_status
        == AGGREGATION_PARTIAL
    )

    assert report.successful_runs == 2


def test_configuration_fingerprint_is_deterministic():
    config = RepeatedExperimentConfig(
        experiment_id="day78-fingerprint",
        scenario="stable",
        seeds=(11, 22, 33),
    )

    evaluator = RepeatedExperimentEvaluator()

    first = evaluator.run(
        config,
        deterministic_experiment,
    )

    second = evaluator.run(
        config,
        deterministic_experiment,
    )

    assert (
        first.configuration_fingerprint
        == second.configuration_fingerprint
    )


def test_configuration_fingerprint_changes_when_seed_changes():
    evaluator = RepeatedExperimentEvaluator()

    config_a = RepeatedExperimentConfig(
        experiment_id="day78-fingerprint",
        scenario="stable",
        seeds=(11, 22, 33),
    )

    config_b = RepeatedExperimentConfig(
        experiment_id="day78-fingerprint",
        scenario="stable",
        seeds=(11, 22, 44),
    )

    report_a = evaluator.run(
        config_a,
        deterministic_experiment,
    )

    report_b = evaluator.run(
        config_b,
        deterministic_experiment,
    )

    assert (
        report_a.configuration_fingerprint
        != report_b.configuration_fingerprint
    )


def test_output_fingerprints_are_recorded():
    config = RepeatedExperimentConfig(
        experiment_id="day78-output-fingerprint",
        scenario="fingerprint",
        seeds=(1, 2),
    )

    report = RepeatedExperimentEvaluator().run(
        config,
        deterministic_experiment,
    )

    assert len(
        report.outcome_fingerprints
    ) == 2

    assert all(
        isinstance(fingerprint, str)
        and len(fingerprint) == 64
        for fingerprint
        in report.outcome_fingerprints
    )


def test_evidence_records_research_boundaries():
    config = RepeatedExperimentConfig(
        experiment_id="day78-evidence",
        scenario="boundaries",
        seeds=(1, 2),
    )

    report = RepeatedExperimentEvaluator().run(
        config,
        deterministic_experiment,
    )

    assert (
        report.evidence["read_only"]
        is True
    )

    assert (
        report.evidence[
            "security_decision_modified"
        ]
        is False
    )

    assert (
        report.evidence[
            "enforcement_executed"
        ]
        is False
    )

    assert (
        report.evidence[
            "malicious_intent_inferred"
        ]
        is False
    )

    assert (
        report.evidence[
            "universal_security_score_created"
        ]
        is False
    )

    assert (
        report.evidence[
            "statistical_significance_claimed"
        ]
        is False
    )


def test_architectural_boundary_helpers():
    assert (
        repeated_evaluation_is_read_only()
        is True
    )

    assert (
        security_decision_is_modified_here()
        is False
    )

    assert (
        enforcement_is_executed_here()
        is False
    )

    assert (
        malicious_intent_is_inferred_here()
        is False
    )

    assert (
        universal_security_score_is_created()
        is False
    )

    assert (
        statistical_significance_is_claimed_here()
        is False
    )


def test_empty_seed_list_is_rejected():
    try:
        RepeatedExperimentConfig(
            experiment_id="day78-invalid",
            scenario="invalid",
            seeds=(),
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError for empty seeds"
        )


def test_invalid_seed_type_is_rejected():
    try:
        RepeatedExperimentConfig(
            experiment_id="day78-invalid-seed",
            scenario="invalid",
            seeds=(1, "bad"),
        )
    except TypeError:
        pass
    else:
        raise AssertionError(
            "Expected TypeError for invalid seed"
        )


def test_invalid_minimum_successful_runs_is_rejected():
    try:
        RepeatedExperimentConfig(
            experiment_id="day78-invalid-minimum",
            scenario="invalid",
            seeds=(1, 2),
            minimum_successful_runs=3,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError for invalid minimum"
        )


def test_invalid_experiment_callable_is_rejected():
    config = RepeatedExperimentConfig(
        experiment_id="day78-invalid-callable",
        scenario="invalid",
        seeds=(1,),
    )

    try:
        RepeatedExperimentEvaluator().run(
            config,
            "not-callable",
        )
    except TypeError:
        pass
    else:
        raise AssertionError(
            "Expected TypeError for invalid callable"
        )