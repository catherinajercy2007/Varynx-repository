from app.attack_scenarios import get_attack_scenarios
from app.repeated_evaluation import run_repeated_experiments


def test_day78_same_seed_and_configuration_is_reproducible():
    scenarios = get_attack_scenarios()

    first = run_repeated_experiments(
        scenarios=scenarios,
        seeds=[42],
        events_per_scenario=2,
        threshold=70.0,
    )

    second = run_repeated_experiments(
        scenarios=scenarios,
        seeds=[42],
        events_per_scenario=2,
        threshold=70.0,
    )

    assert first == second


def test_day78_experiment_configuration_controls_dataset_size():
    scenarios = get_attack_scenarios()

    results = run_repeated_experiments(
        scenarios=scenarios,
        seeds=[42],
        events_per_scenario=3,
        threshold=70.0,
    )

    assert len(results) == 1
    assert results[0]["seed"] == 42
    assert results[0]["dataset_size"] == len(scenarios) * 3


def test_day78_seed_configuration_is_preserved_per_experiment():
    scenarios = get_attack_scenarios()
    seeds = [42, 101, 202]

    results = run_repeated_experiments(
        scenarios=scenarios,
        seeds=seeds,
        events_per_scenario=2,
        threshold=70.0,
    )

    assert [result["seed"] for result in results] == seeds
    assert all(
        result["dataset_size"] == len(scenarios) * 2
        for result in results
    )
