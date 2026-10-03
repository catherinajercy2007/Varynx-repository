"""
Tests for Day77 Reproducible Experiment Harness.
"""

from app.experiment_reproducibility import (
    ExperimentConfig,
    ReproducibleExperimentHarness,
    REPRODUCIBILITY_NON_REPRODUCIBLE,
    REPRODUCIBILITY_REPRODUCIBLE,
    RUN_STATUS_FAILED,
    RUN_STATUS_SUCCESS,
    canonical_json,
    creates_universal_security_score,
    enforcement_is_executed_here,
    experiment_harness_is_deterministic,
    experiment_harness_is_read_only,
    fingerprint,
    malicious_intent_is_inferred_here,
    security_decision_is_modified_here,
)


def deterministic_experiment(seed: int):
    """
    Deterministic experiment.

    Different seeds intentionally produce different outputs.
    The same seed always produces the same output.
    """

    return {
        "seed": seed,
        "decision": "ALLOW",
        "score": seed % 100,
    }


def variable_experiment(seed: int):
    """
    Deliberately non-reproducible experiment.

    The counter changes on every execution even when the seed
    remains identical.
    """

    variable_experiment.counter += 1

    return {
        "seed": seed,
        "execution_counter": variable_experiment.counter,
    }


variable_experiment.counter = 0


def test_explicit_seeds_are_preserved():
    config = ExperimentConfig(
        experiment_id="day77-explicit",
        scenario="seeded",
        repetitions=4,
        seeds=(101, 202, 303, 404),
    )

    harness = ReproducibleExperimentHarness()

    assert harness.resolve_seeds(config) == (
        101,
        202,
        303,
        404,
    )


def test_generated_seeds_are_deterministic():
    config = ExperimentConfig(
        experiment_id="day77-generated",
        scenario="generated-seeds",
        repetitions=4,
    )

    harness = ReproducibleExperimentHarness()

    first = harness.resolve_seeds(config)
    second = harness.resolve_seeds(config)

    assert first == second
    assert len(first) == 4


def test_deterministic_experiment_is_reproducible():
    """
    Different seeds may produce different results.

    Reproducibility is established because each seed produces
    the same result across its repeated executions.
    """

    config = ExperimentConfig(
        experiment_id="day77-reproducible",
        scenario="stable-output",
        repetitions=4,
        seeds=(101, 202, 303, 404),
    )

    report = ReproducibleExperimentHarness().run(
        config,
        deterministic_experiment,
    )

    assert (
        report.reproducibility
        == REPRODUCIBILITY_REPRODUCIBLE
    )

    assert len(report.runs) == 8

    for seed in config.seeds:
        seed_runs = [
            run
            for run in report.runs
            if run.seed == seed
        ]

        assert len(seed_runs) == 2

        assert (
            seed_runs[0].output_fingerprint
            == seed_runs[1].output_fingerprint
        )


def test_same_experiment_produces_same_report_metadata():
    config = ExperimentConfig(
        experiment_id="day77-stable-metadata",
        scenario="stable-output",
        repetitions=3,
        seeds=(11, 22, 33),
    )

    harness = ReproducibleExperimentHarness()

    first = harness.run(
        config,
        deterministic_experiment,
    )

    second = harness.run(
        config,
        deterministic_experiment,
    )

    assert (
        first.configuration_fingerprint
        == second.configuration_fingerprint
    )

    assert (
        first.output_fingerprints
        == second.output_fingerprints
    )

    assert (
        first.reproducibility
        == second.reproducibility
    )


def test_different_seeds_are_allowed_to_produce_different_outputs():
    config = ExperimentConfig(
        experiment_id="day77-seed-variation",
        scenario="seed-dependent-output",
        repetitions=3,
        seeds=(101, 202, 303),
    )

    report = ReproducibleExperimentHarness().run(
        config,
        deterministic_experiment,
    )

    assert (
        report.reproducibility
        == REPRODUCIBILITY_REPRODUCIBLE
    )

    first_runs = [
        run
        for run in report.runs
        if run.repeat_index == 0
    ]

    fingerprints = {
        run.output_fingerprint
        for run in first_runs
    }

    assert len(fingerprints) == 3

    assert (
        report.evidence["outputs_identical"]
        is False
    )


def test_non_deterministic_output_is_detected():
    variable_experiment.counter = 0

    config = ExperimentConfig(
        experiment_id="day77-nondeterministic",
        scenario="changing-output",
        repetitions=3,
        seeds=(1, 2, 3),
    )

    report = ReproducibleExperimentHarness().run(
        config,
        variable_experiment,
    )

    assert (
        report.reproducibility
        == REPRODUCIBILITY_NON_REPRODUCIBLE
    )

    for seed in config.seeds:
        seed_runs = [
            run
            for run in report.runs
            if run.seed == seed
        ]

        assert len(seed_runs) == 2

        assert (
            seed_runs[0].output_fingerprint
            != seed_runs[1].output_fingerprint
        )


def test_failed_experiment_is_recorded():
    def failing_experiment(seed: int):
        raise RuntimeError(
            f"intentional failure for seed {seed}"
        )

    config = ExperimentConfig(
        experiment_id="day77-failure",
        scenario="failure-recording",
        repetitions=2,
        seeds=(10, 20),
    )

    report = ReproducibleExperimentHarness().run(
        config,
        failing_experiment,
    )

    assert (
        report.reproducibility
        == REPRODUCIBILITY_NON_REPRODUCIBLE
    )

    assert len(report.runs) == 4

    assert all(
        run.status == RUN_STATUS_FAILED
        for run in report.runs
    )

    assert (
        report.evidence["failed_runs"] == 4
    )


def test_successful_runs_have_success_status():
    config = ExperimentConfig(
        experiment_id="day77-success-status",
        scenario="success",
        repetitions=2,
        seeds=(5, 6),
    )

    report = ReproducibleExperimentHarness().run(
        config,
        deterministic_experiment,
    )

    assert all(
        run.status == RUN_STATUS_SUCCESS
        for run in report.runs
    )


def test_canonical_json_is_stable():
    value_a = {
        "z": 1,
        "a": [
            3,
            2,
            1,
        ],
    }

    value_b = {
        "a": [
            3,
            2,
            1,
        ],
        "z": 1,
    }

    assert canonical_json(value_a) == canonical_json(value_b)


def test_fingerprint_is_stable():
    value = {
        "experiment": "day77",
        "seed": 101,
        "decision": "ALLOW",
    }

    assert fingerprint(value) == fingerprint(value)


def test_configuration_fingerprint_changes_when_seed_changes():
    config_a = ExperimentConfig(
        experiment_id="day77-config",
        scenario="configuration",
        repetitions=2,
        seeds=(1, 2),
    )

    config_b = ExperimentConfig(
        experiment_id="day77-config",
        scenario="configuration",
        repetitions=2,
        seeds=(1, 3),
    )

    harness = ReproducibleExperimentHarness()

    report_a = harness.run(
        config_a,
        deterministic_experiment,
    )

    report_b = harness.run(
        config_b,
        deterministic_experiment,
    )

    assert (
        report_a.configuration_fingerprint
        != report_b.configuration_fingerprint
    )


def test_run_indexes_are_sequential():
    config = ExperimentConfig(
        experiment_id="day77-indexes",
        scenario="run-indexes",
        repetitions=3,
        seeds=(10, 20, 30),
    )

    report = ReproducibleExperimentHarness().run(
        config,
        deterministic_experiment,
    )

    assert [
        run.run_index
        for run in report.runs
    ] == list(range(6))


def test_repeat_indexes_are_zero_and_one():
    config = ExperimentConfig(
        experiment_id="day77-repeat-index",
        scenario="repeat-index",
        repetitions=2,
        seeds=(10, 20),
    )

    report = ReproducibleExperimentHarness().run(
        config,
        deterministic_experiment,
    )

    for seed in config.seeds:
        seed_runs = [
            run
            for run in report.runs
            if run.seed == seed
        ]

        assert [
            run.repeat_index
            for run in seed_runs
        ] == [0, 1]


def test_report_evidence_contains_reproducibility_metadata():
    config = ExperimentConfig(
        experiment_id="day77-evidence",
        scenario="evidence",
        repetitions=2,
        seeds=(101, 202),
    )

    report = ReproducibleExperimentHarness().run(
        config,
        deterministic_experiment,
    )

    assert (
        report.evidence["harness_version"]
        == "DAY77-V2"
    )

    assert (
        report.evidence["seed_count"] == 2
    )

    assert (
        report.evidence["repeat_executions_per_seed"]
        == 2
    )

    assert (
        report.evidence["total_runs"] == 4
    )

    assert (
        report.evidence["successful_runs"] == 4
    )

    assert (
        report.evidence["failed_runs"] == 0
    )

    assert (
        report.evidence["outputs_identical"]
        is False
    )

    assert (
        report.evidence["seed_level_repeatability"]
        is True
    )

    assert (
        report.evidence["read_only"]
        is True
    )


def test_architectural_boundaries_are_explicit():
    assert (
        experiment_harness_is_deterministic()
        is True
    )

    assert (
        experiment_harness_is_read_only()
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
        creates_universal_security_score()
        is False
    )


def test_invalid_repetition_is_rejected():
    try:
        ExperimentConfig(
            experiment_id="invalid",
            scenario="invalid",
            repetitions=0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError for repetitions=0"
        )


def test_seed_count_mismatch_is_rejected():
    try:
        ExperimentConfig(
            experiment_id="invalid-seeds",
            scenario="invalid",
            repetitions=3,
            seeds=(1, 2),
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError for seed count mismatch"
        )


def test_invalid_callable_is_rejected():
    config = ExperimentConfig(
        experiment_id="invalid-callable",
        scenario="validation",
        repetitions=1,
        seeds=(1,),
    )

    try:
        ReproducibleExperimentHarness().run(
            config,
            "not-a-function",
        )
    except TypeError:
        pass
    else:
        raise AssertionError(
            "Expected TypeError for invalid experiment callable"
        )