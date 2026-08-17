from app.attack_scenarios import (
    get_attack_scenarios,
)

from app.experimental_dataset import (
    dataset_to_csv,
    dataset_to_jsonl,
    generate_experimental_dataset,
    get_label_distribution,
    summarize_dataset,
    validate_dataset,
)


def test_dataset_generation():

    scenarios = get_attack_scenarios()

    dataset = generate_experimental_dataset(
        scenarios,
        events_per_scenario=5,
        seed=42,
    )

    assert len(dataset) == 40


def test_dataset_is_reproducible():

    scenarios = get_attack_scenarios()

    first = generate_experimental_dataset(
        scenarios,
        events_per_scenario=5,
        seed=42,
    )

    second = generate_experimental_dataset(
        scenarios,
        events_per_scenario=5,
        seed=42,
    )

    assert first == second


def test_different_seed_changes_dataset():

    scenarios = get_attack_scenarios()

    first = generate_experimental_dataset(
        scenarios,
        events_per_scenario=5,
        seed=42,
    )

    second = generate_experimental_dataset(
        scenarios,
        events_per_scenario=5,
        seed=99,
    )

    assert first != second


def test_required_fields_exist():

    scenarios = get_attack_scenarios()

    dataset = generate_experimental_dataset(
        scenarios,
        events_per_scenario=1,
        seed=42,
    )

    required = {
        "event_id",
        "dataset_version",
        "experiment_seed",
        "scenario_id",
        "scenario_type",
        "agent_id",
        "task_id",
        "action",
        "resource",
        "severity",
        "ground_truth",
        "expected_signal",
        "sequence_position",
        "risk_score",
        "decision",
        "denied",
        "timestamp",
    }

    assert required.issubset(
        dataset[0].keys()
    )


def test_dataset_validation():

    scenarios = get_attack_scenarios()

    dataset = generate_experimental_dataset(
        scenarios,
        events_per_scenario=2,
        seed=42,
    )

    validation = validate_dataset(
        dataset
    )

    assert validation["valid"] is True


def test_label_distribution():

    scenarios = get_attack_scenarios()

    dataset = generate_experimental_dataset(
        scenarios,
        events_per_scenario=2,
        seed=42,
    )

    distribution = (
        get_label_distribution(
            dataset
        )
    )

    assert distribution["BENIGN"] == 2

    assert distribution["MALICIOUS"] == 14

    assert distribution["SUSPICIOUS"] == 0


def test_dataset_summary():

    scenarios = get_attack_scenarios()

    dataset = generate_experimental_dataset(
        scenarios,
        events_per_scenario=2,
        seed=42,
    )

    summary = summarize_dataset(
        dataset
    )

    assert summary["total_events"] == 16

    assert (
        summary["benign_events"]
        == 2
    )

    assert (
        summary["malicious_events"]
        == 14
    )


def test_csv_export():

    scenarios = get_attack_scenarios()

    dataset = generate_experimental_dataset(
        scenarios,
        events_per_scenario=1,
        seed=42,
    )

    csv_output = dataset_to_csv(
        dataset
    )

    assert "event_id" in csv_output

    assert "ground_truth" in csv_output


def test_jsonl_export():

    scenarios = get_attack_scenarios()

    dataset = generate_experimental_dataset(
        scenarios,
        events_per_scenario=1,
        seed=42,
    )

    jsonl_output = dataset_to_jsonl(
        dataset
    )

    assert "event_id" in jsonl_output

    assert "\n" in jsonl_output