from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
import csv
import io
import json
import random


# ============================================================
# DAY 23 — EXPERIMENTAL DATASET GENERATOR
# ============================================================

DATASET_VERSION = "day23-v1"

GROUND_TRUTH_LABELS = {
    "BENIGN",
    "SUSPICIOUS",
    "MALICIOUS",
}


# ============================================================
# RISK MODEL
# ============================================================

ACTION_RISK = {
    "s3:GetObject": 25,
    "s3:ListBucket": 30,
    "s3:DeleteObject": 80,
    "iam:CreateUser": 95,
    "iam:AttachRolePolicy": 100,
}


def calculate_risk_score(
    action: str,
    severity: str,
    ground_truth: str,
) -> int:
    """
    Generate a deterministic synthetic risk score.

    This is a research-data generator, not the production
    authorization engine.
    """

    base_score = ACTION_RISK.get(
        action,
        20,
    )

    severity_bonus = {
        "LOW": 0,
        "MEDIUM": 10,
        "HIGH": 15,
        "CRITICAL": 20,
    }.get(
        severity.upper(),
        0,
    )

    label_bonus = {
        "BENIGN": 0,
        "SUSPICIOUS": 5,
        "MALICIOUS": 10,
    }.get(
        ground_truth.upper(),
        0,
    )

    return min(
        100,
        base_score
        + severity_bonus
        + label_bonus,
    )


def is_denied(
    ground_truth: str,
    action: str,
    resource: str,
) -> bool:
    """
    Approximate authorization outcome for synthetic
    experimental events.
    """

    if ground_truth == "BENIGN":
        return False

    if action in {
        "iam:CreateUser",
        "iam:AttachRolePolicy",
        "s3:DeleteObject",
    }:
        return True

    if "private/" in resource:
        return True

    if ground_truth == "SUSPICIOUS":
        return True

    return False


# ============================================================
# EVENT GENERATION
# ============================================================

def generate_event(
    scenario: dict[str, Any],
    sequence_position: int,
    experiment_seed: int,
    event_index: int,
    timestamp: datetime,
) -> dict[str, Any]:
    """
    Convert one scenario action into one experimental event.
    """

    actions = scenario.get(
        "actions",
        [],
    )

    resources = scenario.get(
        "resources",
        [],
    )

    if not actions:
        raise ValueError(
            "Scenario contains no actions"
        )

    if not resources:
        raise ValueError(
            "Scenario contains no resources"
        )

    action = actions[
        sequence_position
        % len(actions)
    ]

    resource = resources[
        sequence_position
        % len(resources)
    ]

    ground_truth = str(
        scenario.get(
            "ground_truth",
            "SUSPICIOUS",
        )
    ).upper()

    severity = str(
        scenario.get(
            "severity",
            "MEDIUM",
        )
    ).upper()

    denied = is_denied(
        ground_truth,
        action,
        resource,
    )

    risk_score = calculate_risk_score(
        action,
        severity,
        ground_truth,
    )

    return {
        "event_id": (
            f"EXP-{experiment_seed:04d}-"
            f"{event_index:06d}"
        ),

        "dataset_version":
            DATASET_VERSION,

        "experiment_seed":
            experiment_seed,

        "scenario_id":
            scenario.get(
                "scenario_id",
                "",
            ),

        "scenario_type":
            scenario.get(
                "scenario_type",
                "",
            ),

        "agent_id":
            scenario.get(
                "agent_id",
                "",
            ),

        "task_id":
            scenario.get(
                "task_id",
                "",
            ),

        "action":
            action,

        "resource":
            resource,

        "severity":
            severity,

        "ground_truth":
            ground_truth,

        "expected_signal":
            scenario.get(
                "expected_signal",
                "",
            ),

        "sequence_position":
            sequence_position + 1,

        "risk_score":
            risk_score,

        "decision":
            "DENY"
            if denied
            else "ALLOW",

        "denied":
            denied,

        "timestamp":
            timestamp.isoformat(),
    }


# ============================================================
# DATASET GENERATION
# ============================================================

def generate_experimental_dataset(
    scenarios: list[dict[str, Any]],
    events_per_scenario: int = 5,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """
    Generate a reproducible synthetic security dataset.

    The same scenarios + event count + seed produce the
    same dataset.
    """

    if events_per_scenario < 1:
        raise ValueError(
            "events_per_scenario must be greater than zero"
        )

    if not scenarios:
        raise ValueError(
            "At least one scenario is required"
        )

    rng = random.Random(
        seed
    )

    base_time = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    dataset = []

    event_index = 1

    for scenario in scenarios:

        for sequence_position in range(
            events_per_scenario
        ):

            jitter_seconds = rng.randint(
                0,
                30,
            )

            timestamp = (
                base_time
                + timedelta(
                    seconds=(
                        event_index * 10
                        + jitter_seconds
                    )
                )
            )

            event = generate_event(
                scenario=scenario,
                sequence_position=(
                    sequence_position
                ),
                experiment_seed=seed,
                event_index=event_index,
                timestamp=timestamp,
            )

            dataset.append(
                event
            )

            event_index += 1

    return dataset


# ============================================================
# DATASET SUMMARY
# ============================================================

def summarize_dataset(
    dataset: list[dict[str, Any]],
) -> dict[str, Any]:

    total = len(
        dataset
    )

    benign = sum(
        event.get(
            "ground_truth"
        ) == "BENIGN"
        for event in dataset
    )

    suspicious = sum(
        event.get(
            "ground_truth"
        ) == "SUSPICIOUS"
        for event in dataset
    )

    malicious = sum(
        event.get(
            "ground_truth"
        ) == "MALICIOUS"
        for event in dataset
    )

    allowed = sum(
        event.get(
            "decision"
        ) == "ALLOW"
        for event in dataset
    )

    denied = sum(
        event.get(
            "decision"
        ) == "DENY"
        for event in dataset
    )

    average_risk = (
        sum(
            event.get(
                "risk_score",
                0,
            )
            for event in dataset
        )
        / total
        if total
        else 0
    )

    return {
        "dataset_version":
            DATASET_VERSION,

        "total_events":
            total,

        "benign_events":
            benign,

        "suspicious_events":
            suspicious,

        "malicious_events":
            malicious,

        "allowed_events":
            allowed,

        "denied_events":
            denied,

        "average_risk":
            round(
                average_risk,
                2,
            ),
    }


# ============================================================
# LABEL DISTRIBUTION
# ============================================================

def get_label_distribution(
    dataset: list[dict[str, Any]],
) -> dict[str, int]:

    distribution = {
        "BENIGN": 0,
        "SUSPICIOUS": 0,
        "MALICIOUS": 0,
    }

    for event in dataset:

        label = str(
            event.get(
                "ground_truth",
                "",
            )
        ).upper()

        if label in distribution:
            distribution[label] += 1

    return distribution


# ============================================================
# CSV EXPORT
# ============================================================

def dataset_to_csv(
    dataset: list[dict[str, Any]],
) -> str:

    if not dataset:
        return ""

    output = io.StringIO()

    fieldnames = list(
        dataset[0].keys()
    )

    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
    )

    writer.writeheader()

    writer.writerows(
        dataset
    )

    return output.getvalue()


# ============================================================
# JSONL EXPORT
# ============================================================

def dataset_to_jsonl(
    dataset: list[dict[str, Any]],
) -> str:

    return "\n".join(
        json.dumps(
            event,
            sort_keys=True,
        )
        for event in dataset
    )


# ============================================================
# DATASET VALIDATION
# ============================================================

def validate_dataset(
    dataset: list[dict[str, Any]],
) -> dict[str, Any]:

    required_fields = {
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

    missing_fields = []

    for index, event in enumerate(
        dataset
    ):

        missing = (
            required_fields
            - set(event.keys())
        )

        if missing:

            missing_fields.append(
                {
                    "row":
                        index,

                    "missing":
                        sorted(
                            missing
                        ),
                }
            )

    labels_valid = all(
        event.get(
            "ground_truth"
        ) in GROUND_TRUTH_LABELS
        for event in dataset
    )

    risk_valid = all(
        0
        <= int(
            event.get(
                "risk_score",
                -1,
            )
        )
        <= 100
        for event in dataset
    )

    decisions_valid = all(
        event.get(
            "decision"
        ) in {
            "ALLOW",
            "DENY",
        }
        for event in dataset
    )

    return {
        "valid":
            (
                not missing_fields
                and labels_valid
                and risk_valid
                and decisions_valid
            ),

        "total_rows":
            len(dataset),

        "missing_fields":
            missing_fields,

        "labels_valid":
            labels_valid,

        "risk_scores_valid":
            risk_valid,

        "decisions_valid":
            decisions_valid,
    }