"""
Day 70 - Security Audit Integrity & Chain Verification.

Provides deterministic, tamper-evident verification for audit events.

Security boundaries:
- Does not create security decisions.
- Does not modify decisions.
- Does not execute enforcement.
- Does not infer malicious intent.
- Does not calculate a universal security score.
- Does not replace persistent audit storage.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INTEGRITY_VALID = "INTEGRITY_VALID"
INTEGRITY_INVALID = "INTEGRITY_INVALID"
INTEGRITY_PARTIAL = "INTEGRITY_PARTIAL"

GENESIS_FINGERPRINT = "GENESIS"


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _validate_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    value = value.strip()

    if not value:
        raise ValueError(f"{field_name} must not be empty")

    return value


def _validate_sequence_number(value: int) -> int:
    if not isinstance(value, int):
        raise TypeError("sequence_number must be an integer")

    if value < 1:
        raise ValueError("sequence_number must be >= 1")

    return value


def _validate_mapping(
    value: Mapping[str, Any],
    field_name: str,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")

    return dict(value)


def _validate_events(
    events: Iterable[Any],
) -> tuple[Any, ...]:
    if isinstance(events, (str, bytes)):
        raise TypeError("events must be an iterable of audit events")

    materialized = tuple(events)

    if not materialized:
        raise ValueError("events must not be empty")

    return materialized


# ---------------------------------------------------------------------------
# Event helpers
# ---------------------------------------------------------------------------

def _event_value(event: Any, field_name: str) -> Any:
    if not hasattr(event, field_name):
        raise AttributeError(
            f"audit event is missing required field: {field_name}"
        )

    return getattr(event, field_name)


# ---------------------------------------------------------------------------
# Canonicalization
# ---------------------------------------------------------------------------

def canonicalize_evidence(
    evidence: Mapping[str, Any],
) -> str:
    """
    Produce deterministic JSON for audit evidence.
    """
    evidence = _validate_mapping(
        evidence,
        "evidence",
    )

    try:
        return json.dumps(
            evidence,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            default=str,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "evidence cannot be canonicalized"
        ) from exc


def canonicalize_event(
    event: Any,
) -> str:
    """
    Convert security-relevant audit event fields into a deterministic
    canonical representation.
    """
    payload = {
        "agent_id": _validate_text(
            _event_value(event, "agent_id"),
            "event.agent_id",
        ),
        "request_id": _validate_text(
            _event_value(event, "request_id"),
            "event.request_id",
        ),
        "sequence_number": _validate_sequence_number(
            _event_value(event, "sequence_number"),
        ),
        "event_type": _validate_text(
            _event_value(event, "event_type"),
            "event.event_type",
        ),
        "decision": getattr(event, "decision", None),
        "status": getattr(event, "status", None),
        "evidence": json.loads(
            canonicalize_evidence(
                _event_value(event, "evidence")
            )
        ),
        "execution_performed_here": bool(
            _event_value(
                event,
                "execution_performed_here",
            )
        ),
    }

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )


# ---------------------------------------------------------------------------
# Fingerprinting
# ---------------------------------------------------------------------------

def calculate_event_fingerprint(
    event: Any,
) -> str:
    """
    Calculate a deterministic SHA-256 fingerprint for one audit event.
    """
    canonical = canonicalize_event(event)

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def calculate_chain_fingerprint(
    event_fingerprint: str,
    previous_fingerprint: str = GENESIS_FINGERPRINT,
) -> str:
    """
    Calculate the chained fingerprint for an event.
    """
    event_fingerprint = _validate_text(
        event_fingerprint,
        "event_fingerprint",
    )

    previous_fingerprint = _validate_text(
        previous_fingerprint,
        "previous_fingerprint",
    )

    payload = (
        previous_fingerprint
        + ":"
        + event_fingerprint
    )

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------------------
# Integrity records
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AuditIntegrityRecord:
    agent_id: str
    request_id: str
    sequence_number: int
    event_fingerprint: str
    previous_fingerprint: str
    chain_fingerprint: str


@dataclass(frozen=True)
class AuditIntegrityResult:
    agent_id: str
    status: str
    event_count: int
    verified_events: int
    invalid_events: tuple[int, ...]
    sequence_valid: bool
    chain_valid: bool
    execution_boundary_valid: bool
    records: tuple[AuditIntegrityRecord, ...]


# ---------------------------------------------------------------------------
# Integrity engine
# ---------------------------------------------------------------------------

class SecurityAuditIntegrity:
    """
    Deterministic audit integrity verifier.

    The engine never mutates the supplied audit events.
    """

    def __init__(self) -> None:
        self._results: dict[str, AuditIntegrityResult] = {}

    def build_records(
        self,
        events: Iterable[Any],
    ) -> tuple[AuditIntegrityRecord, ...]:
        materialized = _validate_events(events)

        records: list[AuditIntegrityRecord] = []

        previous_fingerprint = GENESIS_FINGERPRINT

        for event in materialized:
            agent_id = _validate_text(
                _event_value(event, "agent_id"),
                "event.agent_id",
            )

            request_id = _validate_text(
                _event_value(event, "request_id"),
                "event.request_id",
            )

            sequence_number = _validate_sequence_number(
                _event_value(event, "sequence_number"),
            )

            event_fingerprint = calculate_event_fingerprint(
                event
            )

            chain_fingerprint = calculate_chain_fingerprint(
                event_fingerprint,
                previous_fingerprint,
            )

            records.append(
                AuditIntegrityRecord(
                    agent_id=agent_id,
                    request_id=request_id,
                    sequence_number=sequence_number,
                    event_fingerprint=event_fingerprint,
                    previous_fingerprint=previous_fingerprint,
                    chain_fingerprint=chain_fingerprint,
                )
            )

            previous_fingerprint = chain_fingerprint

        return tuple(records)

    def verify(
        self,
        agent_id: str,
        events: Iterable[Any],
        expected_records: (
            Iterable[AuditIntegrityRecord] | None
        ) = None,
    ) -> AuditIntegrityResult:
        """
        Verify event sequence, fingerprints, chain continuity,
        expected historical records, and execution boundary.

        A mismatch in expected-record length invalidates the chain,
        but does not cause unsafe indexing into the shorter sequence.
        """
        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        materialized = _validate_events(events)

        records = self.build_records(materialized)

        invalid_events: list[int] = []

        sequence_valid = True
        chain_valid = True
        execution_boundary_valid = True

        previous_sequence = 0
        previous_fingerprint = GENESIS_FINGERPRINT

        expected = (
            tuple(expected_records)
            if expected_records is not None
            else None
        )

        # ---------------------------------------------------------------
        # Expected-record structural validation
        # ---------------------------------------------------------------

        if expected is not None:
            if len(expected) != len(records):
                chain_valid = False

                # Record the sequence numbers that do not have
                # corresponding expected integrity records.
                if len(expected) < len(records):
                    for record in records[len(expected):]:
                        invalid_events.append(
                            record.sequence_number
                        )

        # ---------------------------------------------------------------
        # Event-by-event verification
        # ---------------------------------------------------------------

        for index, (event, record) in enumerate(
            zip(materialized, records)
        ):
            event_agent = _validate_text(
                _event_value(event, "agent_id"),
                "event.agent_id",
            )

            if event_agent != agent_id:
                raise ValueError(
                    "all events must belong to the requested agent"
                )

            sequence_number = record.sequence_number

            # -----------------------------------------------------------
            # Sequence verification
            # -----------------------------------------------------------

            if sequence_number != previous_sequence + 1:
                sequence_valid = False
                invalid_events.append(sequence_number)

            previous_sequence = sequence_number

            # -----------------------------------------------------------
            # Chain continuity
            # -----------------------------------------------------------

            if (
                record.previous_fingerprint
                != previous_fingerprint
            ):
                chain_valid = False
                invalid_events.append(sequence_number)

            # -----------------------------------------------------------
            # Current event fingerprint
            # -----------------------------------------------------------

            recalculated_event = calculate_event_fingerprint(
                event
            )

            if (
                recalculated_event
                != record.event_fingerprint
            ):
                chain_valid = False
                invalid_events.append(sequence_number)

            # -----------------------------------------------------------
            # Current chain fingerprint
            # -----------------------------------------------------------

            recalculated_chain = calculate_chain_fingerprint(
                recalculated_event,
                previous_fingerprint,
            )

            if (
                recalculated_chain
                != record.chain_fingerprint
            ):
                chain_valid = False
                invalid_events.append(sequence_number)

            # -----------------------------------------------------------
            # Execution boundary
            # -----------------------------------------------------------

            if bool(
                _event_value(
                    event,
                    "execution_performed_here",
                )
            ):
                execution_boundary_valid = False

            # -----------------------------------------------------------
            # Historical expected-record comparison
            # -----------------------------------------------------------
            #
            # IMPORTANT:
            # If expected has fewer records than current records,
            # the length mismatch has already invalidated the chain.
            #
            # Therefore we only access expected[index] when the index
            # actually exists.
            # -----------------------------------------------------------

            if (
                expected is not None
                and index < len(expected)
            ):
                expected_record = expected[index]

                if not isinstance(
                    expected_record,
                    AuditIntegrityRecord,
                ):
                    raise TypeError(
                        "expected_records must contain "
                        "AuditIntegrityRecord objects"
                    )

                if (
                    expected_record.agent_id
                    != record.agent_id
                    or expected_record.request_id
                    != record.request_id
                    or expected_record.sequence_number
                    != record.sequence_number
                    or expected_record.event_fingerprint
                    != record.event_fingerprint
                    or expected_record.previous_fingerprint
                    != record.previous_fingerprint
                    or expected_record.chain_fingerprint
                    != record.chain_fingerprint
                ):
                    chain_valid = False
                    invalid_events.append(sequence_number)

            previous_fingerprint = (
                record.chain_fingerprint
            )

        # ---------------------------------------------------------------
        # Remove duplicate invalid sequence numbers
        # ---------------------------------------------------------------

        invalid_events = sorted(
            set(invalid_events)
        )

        # ---------------------------------------------------------------
        # Determine status
        # ---------------------------------------------------------------

        if (
            sequence_valid
            and chain_valid
            and execution_boundary_valid
        ):
            status = INTEGRITY_VALID

        elif not execution_boundary_valid:
            status = INTEGRITY_PARTIAL

        else:
            status = INTEGRITY_INVALID

        verified_events = max(
            0,
            len(materialized) - len(invalid_events),
        )

        result = AuditIntegrityResult(
            agent_id=agent_id,
            status=status,
            event_count=len(materialized),
            verified_events=verified_events,
            invalid_events=tuple(invalid_events),
            sequence_valid=sequence_valid,
            chain_valid=chain_valid,
            execution_boundary_valid=execution_boundary_valid,
            records=records,
        )

        self._results[agent_id] = result

        return result

    def latest(
        self,
        agent_id: str,
    ) -> AuditIntegrityResult | None:
        agent_id = _validate_text(
            agent_id,
            "agent_id",
        )

        return self._results.get(agent_id)

    def snapshot_all(
        self,
    ) -> dict[str, AuditIntegrityResult]:
        return dict(self._results)

    def reset(self) -> None:
        self._results.clear()


# ---------------------------------------------------------------------------
# Standalone verification helpers
# ---------------------------------------------------------------------------

def verify_sequence(
    events: Iterable[Any],
) -> bool:
    materialized = _validate_events(events)

    expected = 1

    for event in materialized:
        sequence_number = _validate_sequence_number(
            _event_value(
                event,
                "sequence_number",
            )
        )

        if sequence_number != expected:
            return False

        expected += 1

    return True


def verify_execution_boundary(
    events: Iterable[Any],
) -> bool:
    materialized = _validate_events(events)

    return all(
        not bool(
            _event_value(
                event,
                "execution_performed_here",
            )
        )
        for event in materialized
    )


def integrity_is_deterministic() -> bool:
    return True


def decision_is_modified_here() -> bool:
    return False


def enforcement_is_executed_here() -> bool:
    return False


__all__ = [
    "INTEGRITY_VALID",
    "INTEGRITY_INVALID",
    "INTEGRITY_PARTIAL",
    "GENESIS_FINGERPRINT",
    "AuditIntegrityRecord",
    "AuditIntegrityResult",
    "SecurityAuditIntegrity",
    "canonicalize_evidence",
    "canonicalize_event",
    "calculate_event_fingerprint",
    "calculate_chain_fingerprint",
    "verify_sequence",
    "verify_execution_boundary",
    "integrity_is_deterministic",
    "decision_is_modified_here",
    "enforcement_is_executed_here",
]