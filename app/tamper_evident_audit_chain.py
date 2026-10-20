
"""Day 84: Tamper-Evident Audit Chain for Varynx.

A deterministic hash-chain implementation for audit records.
This module detects content and linkage inconsistencies; it does not
provide authenticated storage, trusted timestamps, or protection against
an attacker who can rewrite the entire chain and its trusted checkpoint.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
import json
from typing import Any, Mapping


VERSION = "DAY84-V1"
GENESIS_HASH = "0" * 64

CHAIN_VALID = "CHAIN_VALID"
CHAIN_INVALID = "CHAIN_INVALID"

REASON_RECORD_HASH_MISMATCH = "RECORD_HASH_MISMATCH"
REASON_PREVIOUS_HASH_MISMATCH = "PREVIOUS_HASH_MISMATCH"
REASON_SEQUENCE_MISMATCH = "SEQUENCE_MISMATCH"
REASON_DUPLICATE_RECORD_ID = "DUPLICATE_RECORD_ID"


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _canonical_json(payload: Any) -> str:
    try:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Audit payload must contain finite JSON-compatible values"
        ) from exc


def _digest(payload: Any) -> str:
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _aware_timestamp(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("timestamp must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value


@dataclass(frozen=True)
class AuditRecord:
    """One immutable record in a hash-linked audit sequence."""

    record_id: str
    sequence: int
    timestamp: str
    event_type: str
    correlation_id: str
    actor_id: str
    payload: Mapping[str, Any]
    previous_hash: str
    record_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": VERSION,
            "record_id": self.record_id,
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "correlation_id": self.correlation_id,
            "actor_id": self.actor_id,
            "payload": deepcopy(dict(self.payload)),
            "previous_hash": self.previous_hash,
            "record_hash": self.record_hash,
        }


@dataclass(frozen=True)
class ChainVerification:
    status: str
    checked_records: int
    valid_records: int
    failure_index: int | None
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["version"] = VERSION
        return result


def _record_hash_payload(
    *,
    record_id: str,
    sequence: int,
    timestamp: str,
    event_type: str,
    correlation_id: str,
    actor_id: str,
    payload: Mapping[str, Any],
    previous_hash: str,
) -> dict[str, Any]:
    return {
        "version": VERSION,
        "record_id": record_id,
        "sequence": sequence,
        "timestamp": timestamp,
        "event_type": event_type,
        "correlation_id": correlation_id,
        "actor_id": actor_id,
        "payload": dict(payload),
        "previous_hash": previous_hash,
    }


def create_audit_record(
    *,
    record_id: str,
    sequence: int,
    timestamp: datetime,
    event_type: str,
    correlation_id: str,
    actor_id: str,
    payload: Mapping[str, Any],
    previous_hash: str,
) -> AuditRecord:
    """Create one record linked to a previous record hash."""
    record_id = _text(record_id, "record_id")
    event_type = _text(event_type, "event_type")
    correlation_id = _text(correlation_id, "correlation_id")
    actor_id = _text(actor_id, "actor_id")

    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise TypeError("sequence must be an integer")
    if sequence < 1:
        raise ValueError("sequence must be >= 1")

    timestamp = _aware_timestamp(timestamp).isoformat()
    previous_hash = _text(previous_hash, "previous_hash").lower()

    if len(previous_hash) != 64 or any(
        char not in "0123456789abcdef" for char in previous_hash
    ):
        raise ValueError("previous_hash must be a 64-character SHA-256 digest")

    if not isinstance(payload, Mapping):
        raise TypeError("payload must be a mapping")

    # Validate and deep-copy payload before hashing.
    safe_payload = deepcopy(dict(payload))
    _canonical_json(safe_payload)

    hash_payload = _record_hash_payload(
        record_id=record_id,
        sequence=sequence,
        timestamp=timestamp,
        event_type=event_type,
        correlation_id=correlation_id,
        actor_id=actor_id,
        payload=safe_payload,
        previous_hash=previous_hash,
    )

    return AuditRecord(
        record_id=record_id,
        sequence=sequence,
        timestamp=timestamp,
        event_type=event_type,
        correlation_id=correlation_id,
        actor_id=actor_id,
        payload=safe_payload,
        previous_hash=previous_hash,
        record_hash=_digest(hash_payload),
    )


class TamperEvidentAuditChain:
    """Append-only interface over an in-memory audit chain.

    Persistence and external checkpoint protection must be supplied by
    an integration layer. Verification does not establish authenticity
    if an attacker can rewrite the entire chain.
    """

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    @property
    def records(self) -> tuple[AuditRecord, ...]:
        # Records are immutable dataclasses; return a tuple snapshot.
        return tuple(self._records)

    def append(
        self,
        *,
        record_id: str,
        timestamp: datetime,
        event_type: str,
        correlation_id: str,
        actor_id: str,
        payload: Mapping[str, Any],
    ) -> AuditRecord:
        """Append a record using the current chain head."""
        if any(item.record_id == record_id for item in self._records):
            raise ValueError(f"Duplicate record_id: {record_id}")

        previous_hash = (
            self._records[-1].record_hash
            if self._records
            else GENESIS_HASH
        )

        record = create_audit_record(
            record_id=record_id,
            sequence=len(self._records) + 1,
            timestamp=timestamp,
            event_type=event_type,
            correlation_id=correlation_id,
            actor_id=actor_id,
            payload=payload,
            previous_hash=previous_hash,
        )
        self._records.append(record)
        return record

    def verify(self) -> ChainVerification:
        """Verify sequence continuity, links, unique IDs, and record hashes."""
        seen_ids: set[str] = set()
        expected_previous_hash = GENESIS_HASH

        for index, record in enumerate(self._records):
            reasons: list[str] = []

            if record.sequence != index + 1:
                reasons.append(REASON_SEQUENCE_MISMATCH)

            if record.previous_hash != expected_previous_hash:
                reasons.append(REASON_PREVIOUS_HASH_MISMATCH)

            if record.record_id in seen_ids:
                reasons.append(REASON_DUPLICATE_RECORD_ID)
            seen_ids.add(record.record_id)

            try:
                expected_record = _digest(
                    _record_hash_payload(
                        record_id=record.record_id,
                        sequence=record.sequence,
                        timestamp=record.timestamp,
                        event_type=record.event_type,
                        correlation_id=record.correlation_id,
                        actor_id=record.actor_id,
                        payload=record.payload,
                        previous_hash=record.previous_hash,
                    )
                )
            except (TypeError, ValueError):
                expected_record = None

            if expected_record != record.record_hash:
                reasons.append(REASON_RECORD_HASH_MISMATCH)

            if reasons:
                return ChainVerification(
                    status=CHAIN_INVALID,
                    checked_records=len(self._records),
                    valid_records=index,
                    failure_index=index,
                    reason_codes=tuple(dict.fromkeys(reasons)),
                )

            expected_previous_hash = record.record_hash

        return ChainVerification(
            status=CHAIN_VALID,
            checked_records=len(self._records),
            valid_records=len(self._records),
            failure_index=None,
            reason_codes=(),
        )

    def export(self) -> dict[str, Any]:
        """Export the chain in a deterministic, serializable structure."""
        records = [record.to_dict() for record in self._records]
        return {
            "version": VERSION,
            "genesis_hash": GENESIS_HASH,
            "record_count": len(records),
            "head_hash": (
                self._records[-1].record_hash
                if self._records
                else GENESIS_HASH
            ),
            "records": records,
        }


def verify_exported_chain(exported: Mapping[str, Any]) -> ChainVerification:
    """Verify a serialized chain export without trusting its record hashes."""
    if not isinstance(exported, Mapping):
        raise TypeError("exported must be a mapping")

    raw_records = exported.get("records")
    if not isinstance(raw_records, list):
        raise ValueError("exported records must be a list")

    chain = TamperEvidentAuditChain()

    # Reconstruct records exactly as exported. This intentionally preserves
    # stored hashes so verify() can detect altered content or linkage.
    records: list[AuditRecord] = []
    for raw in raw_records:
        if not isinstance(raw, Mapping):
            raise ValueError("Each exported record must be a mapping")
        payload = raw.get("payload")
        if not isinstance(payload, Mapping):
            raise ValueError("Exported record payload must be a mapping")

        records.append(
            AuditRecord(
                record_id=raw["record_id"],
                sequence=raw["sequence"],
                timestamp=raw["timestamp"],
                event_type=raw["event_type"],
                correlation_id=raw["correlation_id"],
                actor_id=raw["actor_id"],
                payload=deepcopy(dict(payload)),
                previous_hash=raw["previous_hash"],
                record_hash=raw["record_hash"],
            )
        )

    chain._records = records
    return chain.verify()


__all__ = [
    "VERSION",
    "GENESIS_HASH",
    "AuditRecord",
    "ChainVerification",
    "TamperEvidentAuditChain",
    "create_audit_record",
    "verify_exported_chain",
    "CHAIN_VALID",
    "CHAIN_INVALID",
]
