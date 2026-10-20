
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from app.tamper_evident_audit_chain import (
    CHAIN_INVALID,
    CHAIN_VALID,
    GENESIS_HASH,
    TamperEvidentAuditChain,
    create_audit_record,
    verify_exported_chain,
)

NOW = datetime(2026, 10, 20, 10, 0, tzinfo=timezone.utc)


def append(chain, number=1, payload=None):
    return chain.append(
        record_id=f"record-{number}",
        timestamp=NOW + timedelta(seconds=number),
        event_type="SECURITY_DECISION",
        correlation_id=f"request-{number}",
        actor_id="agent-a",
        payload=payload if payload is not None else {"decision": "review"},
    )


def test_empty_chain_is_valid():
    chain = TamperEvidentAuditChain()

    result = chain.verify()

    assert result.status == CHAIN_VALID
    assert result.checked_records == 0


def test_single_record_chain_is_valid():
    chain = TamperEvidentAuditChain()
    append(chain)

    assert chain.verify().status == CHAIN_VALID


def test_multiple_linked_records_are_valid():
    chain = TamperEvidentAuditChain()
    append(chain, 1)
    append(chain, 2)
    append(chain, 3)

    result = chain.verify()

    assert result.status == CHAIN_VALID
    assert result.valid_records == 3


def test_first_record_uses_genesis_hash():
    chain = TamperEvidentAuditChain()
    record = append(chain)

    assert record.previous_hash == GENESIS_HASH


def test_next_record_links_to_previous_hash():
    chain = TamperEvidentAuditChain()
    first = append(chain, 1)
    second = append(chain, 2)

    assert second.previous_hash == first.record_hash


def test_payload_tampering_is_detected():
    chain = TamperEvidentAuditChain()
    append(chain, 1)
    append(chain, 2)

    original = chain._records[1]
    altered = replace(original, payload={"decision": "allow"})
    chain._records[1] = altered

    result = chain.verify()

    assert result.status == CHAIN_INVALID
    assert result.failure_index == 1


def test_previous_hash_tampering_is_detected():
    chain = TamperEvidentAuditChain()
    append(chain, 1)
    append(chain, 2)

    original = chain._records[1]
    chain._records[1] = replace(original, previous_hash="f" * 64)

    result = chain.verify()

    assert result.status == CHAIN_INVALID


def test_sequence_reordering_is_detected():
    chain = TamperEvidentAuditChain()
    append(chain, 1)
    append(chain, 2)

    chain._records.reverse()
    result = chain.verify()

    assert result.status == CHAIN_INVALID


def test_record_hash_tampering_is_detected():
    chain = TamperEvidentAuditChain()
    append(chain)

    chain._records[0] = replace(
        chain._records[0],
        record_hash="a" * 64,
    )

    assert chain.verify().status == CHAIN_INVALID


def test_duplicate_record_id_is_rejected_on_append():
    chain = TamperEvidentAuditChain()
    append(chain, 1)

    with pytest.raises(ValueError, match="Duplicate"):
        chain.append(
            record_id="record-1",
            timestamp=NOW,
            event_type="OTHER",
            correlation_id="request-x",
            actor_id="agent-a",
            payload={},
        )


def test_naive_timestamp_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        create_audit_record(
            record_id="r1",
            sequence=1,
            timestamp=datetime(2026, 10, 20, 10, 0),
            event_type="EVENT",
            correlation_id="c1",
            actor_id="agent",
            payload={},
            previous_hash=GENESIS_HASH,
        )


def test_invalid_sequence_is_rejected():
    with pytest.raises(ValueError, match="sequence"):
        create_audit_record(
            record_id="r1",
            sequence=0,
            timestamp=NOW,
            event_type="EVENT",
            correlation_id="c1",
            actor_id="agent",
            payload={},
            previous_hash=GENESIS_HASH,
        )


def test_non_json_payload_is_rejected():
    chain = TamperEvidentAuditChain()

    with pytest.raises(ValueError, match="JSON-compatible"):
        append(chain, payload={"unsupported": object()})


def test_non_finite_float_is_rejected():
    chain = TamperEvidentAuditChain()

    with pytest.raises(ValueError, match="JSON-compatible"):
        append(chain, payload={"score": float("nan")})


def test_export_can_be_verified():
    chain = TamperEvidentAuditChain()
    append(chain, 1)
    append(chain, 2)

    result = verify_exported_chain(chain.export())

    assert result.status == CHAIN_VALID
    assert result.checked_records == 2


def test_export_payload_modification_is_detected():
    chain = TamperEvidentAuditChain()
    append(chain)

    exported = chain.export()
    exported["records"][0]["payload"]["decision"] = "modified"

    result = verify_exported_chain(exported)

    assert result.status == CHAIN_INVALID


def test_exported_record_deletion_is_detected():
    chain = TamperEvidentAuditChain()
    append(chain, 1)
    append(chain, 2)
    append(chain, 3)

    exported = chain.export()
    del exported["records"][1]

    result = verify_exported_chain(exported)

    assert result.status == CHAIN_INVALID


def test_identical_inputs_produce_identical_hashes():
    first = TamperEvidentAuditChain()
    second = TamperEvidentAuditChain()

    append(first, 1)
    append(second, 1)

    assert first.records[0].record_hash == second.records[0].record_hash


def test_export_is_json_serializable():
    chain = TamperEvidentAuditChain()
    append(chain)

    import json
    serialized = json.dumps(chain.export(), sort_keys=True)

    assert '"record_hash"' in serialized


def test_records_property_returns_tuple():
    chain = TamperEvidentAuditChain()
    append(chain)

    assert isinstance(chain.records, tuple)


def test_payload_is_copied_on_append():
    chain = TamperEvidentAuditChain()
    payload = {"details": {"count": 1}}

    append(chain, payload=payload)
    payload["details"]["count"] = 99

    assert chain.records[0].payload["details"]["count"] == 1
    assert chain.verify().status == CHAIN_VALID
