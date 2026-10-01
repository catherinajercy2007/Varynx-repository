"""
Day 47
Dynamic Behavioral Trust Evaluation Adapter Tests
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.behavioral_trust import DynamicBehavioralTrust
from app.trust_evaluation import (
    TrustEvaluationResult,
    evaluate_trust_sequence,
    records_to_dicts,
    snapshots_from_result,
)


BASE_TIME = datetime(
    2026,
    1,
    1,
    tzinfo=timezone.utc,
)


def make_event(
    agent_id="agent-a",
    ground_truth="BENIGN",
    evidence=None,
    offset_hours=0,
):
    return {
        "agent_id": agent_id,
        "ground_truth": ground_truth,
        "timestamp": (
            BASE_TIME
            + timedelta(hours=offset_hours)
        ),
        "evidence": evidence or {},
    }


def evidence_provider(event):
    return event.get("evidence", {})


def test_empty_sequence_returns_empty_metrics():
    engine = DynamicBehavioralTrust()

    result = evaluate_trust_sequence(
        [],
        engine,
        evidence_provider,
    )

    assert isinstance(
        result,
        TrustEvaluationResult,
    )

    assert result.records == ()

    assert result.metrics["TP"] == 0
    assert result.metrics["TN"] == 0
    assert result.metrics["FP"] == 0
    assert result.metrics["FN"] == 0


def test_single_event_creates_trust_record():
    engine = DynamicBehavioralTrust()

    events = [
        make_event(
            evidence={
                "behavioral_consistency": 100,
            }
        )
    ]

    result = evaluate_trust_sequence(
        events,
        engine,
        evidence_provider,
    )

    assert len(result.records) == 1

    record = result.records[0]

    assert record.agent_id == "agent-a"
    assert record.trust_score >= 50
    assert record.evidence_score == 100
    assert record.update_index == 1
    assert record.ground_truth == "BENIGN"


def test_multiple_events_preserve_update_order():
    engine = DynamicBehavioralTrust(
        learning_rate=1.0,
    )

    events = [
        make_event(
            evidence={
                "behavioral_consistency": 90,
            },
            offset_hours=0,
        ),
        make_event(
            evidence={
                "behavioral_consistency": 20,
            },
            offset_hours=1,
        ),
        make_event(
            evidence={
                "behavioral_consistency": 80,
            },
            offset_hours=2,
        ),
    ]

    result = evaluate_trust_sequence(
        events,
        engine,
        evidence_provider,
    )

    assert [
        record.update_index
        for record in result.records
    ] == [1, 2, 3]


def test_low_trust_prediction_uses_explicit_threshold():
    engine = DynamicBehavioralTrust(
        learning_rate=1.0,
    )

    events = [
        make_event(
            ground_truth="MALICIOUS",
            evidence={
                "behavioral_consistency": 20,
            }
        )
    ]

    result = evaluate_trust_sequence(
        events,
        engine,
        evidence_provider,
        trust_threshold=40,
    )

    assert result.records[0].trust_score == 20
    assert result.records[0].predicted_low_trust is True
    assert result.metrics["TP"] == 1


def test_high_trust_prediction_is_not_low_trust():
    engine = DynamicBehavioralTrust(
        learning_rate=1.0,
    )

    events = [
        make_event(
            ground_truth="BENIGN",
            evidence={
                "behavioral_consistency": 90,
            }
        )
    ]

    result = evaluate_trust_sequence(
        events,
        engine,
        evidence_provider,
        trust_threshold=40,
    )

    assert result.records[0].trust_score == 90
    assert result.records[0].predicted_low_trust is False
    assert result.metrics["TN"] == 1


def test_ground_truth_is_case_insensitive():
    engine = DynamicBehavioralTrust(
        learning_rate=1.0,
    )

    events = [
        make_event(
            ground_truth="malicious",
            evidence={
                "behavioral_consistency": 10,
            }
        )
    ]

    result = evaluate_trust_sequence(
        events,
        engine,
        evidence_provider,
    )

    assert result.records[0].ground_truth == "MALICIOUS"
    assert result.metrics["TP"] == 1


def test_evidence_provider_receives_original_event():
    engine = DynamicBehavioralTrust()

    received = []

    def provider(event):
        received.append(event)
        return event["evidence"]

    event = make_event(
        evidence={
            "behavioral_consistency": 75,
        }
    )

    evaluate_trust_sequence(
        [event],
        engine,
        provider,
    )

    assert received == [event]


def test_none_evidence_is_supported():
    engine = DynamicBehavioralTrust()

    events = [
        make_event(
            evidence={}
        )
    ]

    result = evaluate_trust_sequence(
        events,
        engine,
        lambda event: None,
    )

    assert len(result.records) == 1
    assert result.records[0].evidence_score == 50


def test_result_preserves_trust_threshold():
    engine = DynamicBehavioralTrust()

    result = evaluate_trust_sequence(
        [
            make_event(
                evidence={
                    "behavioral_consistency": 80,
                }
            )
        ],
        engine,
        evidence_provider,
        trust_threshold=55,
    )

    assert result.trust_threshold == 55


def test_records_can_be_serialized():
    engine = DynamicBehavioralTrust()

    result = evaluate_trust_sequence(
        [
            make_event(
                evidence={
                    "behavioral_consistency": 80,
                }
            )
        ],
        engine,
        evidence_provider,
    )

    records = records_to_dicts(
        result.records
    )

    assert isinstance(records, list)
    assert len(records) == 1

    assert records[0]["agent_id"] == "agent-a"
    assert "trust_score" in records[0]
    assert "trust_band" in records[0]
    assert "evidence_score" in records[0]
    assert "predicted_low_trust" in records[0]


def test_snapshot_alias_returns_records():
    engine = DynamicBehavioralTrust()

    result = evaluate_trust_sequence(
        [
            make_event(
                evidence={
                    "behavioral_consistency": 80,
                }
            )
        ],
        engine,
        evidence_provider,
    )

    assert result.snapshots == result.records


def test_snapshots_from_result_returns_records():
    engine = DynamicBehavioralTrust()

    result = evaluate_trust_sequence(
        [
            make_event(
                evidence={
                    "behavioral_consistency": 80,
                }
            )
        ],
        engine,
        evidence_provider,
    )

    records = snapshots_from_result(result)

    assert records == result.records


def test_invalid_threshold_below_zero_is_rejected():
    engine = DynamicBehavioralTrust()

    with pytest.raises(ValueError):
        evaluate_trust_sequence(
            [],
            engine,
            evidence_provider,
            trust_threshold=-1,
        )


def test_invalid_threshold_above_100_is_rejected():
    engine = DynamicBehavioralTrust()

    with pytest.raises(ValueError):
        evaluate_trust_sequence(
            [],
            engine,
            evidence_provider,
            trust_threshold=101,
        )


def test_boolean_threshold_is_rejected():
    engine = DynamicBehavioralTrust()

    with pytest.raises(TypeError):
        evaluate_trust_sequence(
            [],
            engine,
            evidence_provider,
            trust_threshold=True,
        )


def test_invalid_engine_is_rejected():
    with pytest.raises(TypeError):
        evaluate_trust_sequence(
            [],
            object(),
            evidence_provider,
        )


def test_invalid_evidence_provider_is_rejected():
    engine = DynamicBehavioralTrust()

    with pytest.raises(TypeError):
        evaluate_trust_sequence(
            [],
            engine,
            None,
        )


def test_invalid_event_type_is_rejected():
    engine = DynamicBehavioralTrust()

    with pytest.raises(TypeError):
        evaluate_trust_sequence(
            [[]],
            engine,
            evidence_provider,
        )


def test_missing_agent_id_is_rejected():
    engine = DynamicBehavioralTrust()

    event = {
        "ground_truth": "BENIGN",
        "evidence": {
            "behavioral_consistency": 80,
        },
    }

    with pytest.raises(ValueError):
        evaluate_trust_sequence(
            [event],
            engine,
            evidence_provider,
        )


def test_invalid_evidence_provider_result_is_rejected():
    engine = DynamicBehavioralTrust()

    def invalid_provider(event):
        return ["not", "a", "mapping"]

    with pytest.raises(TypeError):
        evaluate_trust_sequence(
            [
                make_event()
            ],
            engine,
            invalid_provider,
        )


def test_invalid_timestamp_is_rejected():
    engine = DynamicBehavioralTrust()

    event = make_event()
    event["timestamp"] = "2026-01-01"

    with pytest.raises(TypeError):
        evaluate_trust_sequence(
            [event],
            engine,
            evidence_provider,
        )


def test_multiple_agents_keep_independent_trust_state():
    engine = DynamicBehavioralTrust(
        learning_rate=1.0,
    )

    events = [
        make_event(
            agent_id="agent-a",
            evidence={
                "behavioral_consistency": 90,
            },
            offset_hours=0,
        ),
        make_event(
            agent_id="agent-b",
            evidence={
                "behavioral_consistency": 20,
            },
            offset_hours=0,
        ),
    ]

    result = evaluate_trust_sequence(
        events,
        engine,
        evidence_provider,
    )

    assert result.records[0].trust_score == 90
    assert result.records[1].trust_score == 20


def test_same_inputs_and_timestamps_are_reproducible():
    events = [
        make_event(
            ground_truth="BENIGN",
            evidence={
                "behavioral_consistency": 90,
                "context_consistency": 80,
            },
            offset_hours=0,
        ),
        make_event(
            ground_truth="MALICIOUS",
            evidence={
                "behavioral_consistency": 20,
                "context_consistency": 30,
            },
            offset_hours=1,
        ),
    ]

    first = evaluate_trust_sequence(
        events,
        DynamicBehavioralTrust(
            learning_rate=0.25,
        ),
        evidence_provider,
    )

    second = evaluate_trust_sequence(
        events,
        DynamicBehavioralTrust(
            learning_rate=0.25,
        ),
        evidence_provider,
    )

    assert first.to_dict() == second.to_dict()