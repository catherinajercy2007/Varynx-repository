
# Day 84 — Tamper-Evident Audit Chain

## Objective

Provide sequential audit records linked through SHA-256 hashes. Each record
contains a canonicalized payload digest through its record hash and the
hash of the preceding record.

The chain is designed to detect record modification, broken links, sequence
changes, and deletion that leaves a detectable linkage gap.

## Existing Varynx architecture

Varynx already contains an audit entry point (`app/audit.py`), a persistent
audit database path, a Day 73 evidence timeline, and a Day 74 evidence
correlation layer.

This module defines the chain primitive and verification contract. It does
not replace those components or silently change the existing database
schema. A separate integration change must connect the chain to the
authoritative audit-write path after the actual persistence contract is
reviewed.

## Files

- `app/tamper_evident_audit_chain.py`
- `tests/test_day84_tamper_evident_audit_chain.py`
- `DAY84_TAMPER_EVIDENT_AUDIT_CHAIN.md`

## Record structure

Each record includes:

- Record identifier.
- Monotonic sequence number.
- Timezone-aware timestamp.
- Event type.
- Correlation identifier.
- Actor identifier.
- JSON-compatible payload.
- Previous record hash.
- Current record hash.

The first record references a fixed genesis hash.

## Integrity verification

Verification recomputes each record hash and checks:

1. Sequence continuity.
2. Previous-hash linkage.
3. Record identifier uniqueness.
4. Canonical payload integrity.

A failed check returns an invalid-chain status and identifies the first
record where verification failed.

## Security limitations

A hash chain is tamper-evident, not inherently tamper-proof.

An attacker who can rewrite every record and recompute every hash may
produce a different internally valid chain. Stronger protection requires
independent trusted checkpoints, restricted storage permissions, external
signatures, or a separately protected append-only storage system.

The in-memory implementation is a prototype. It does not provide durable
persistence, multi-process concurrency control, digital signatures,
trusted timestamps, or external checkpoint management.

## Acceptance criteria

1. A correctly linked chain verifies successfully.
2. Payload modifications are detected.
3. Previous-hash modifications are detected.
4. Reordering and deletion that break sequence/linkage are detected.
5. Invalid timestamps, sequence numbers, and payloads are rejected.
6. Exported records can be verified.
7. Identical records produce deterministic hashes.
8. Existing audit, timeline, and correlation interfaces remain unchanged.
9. Verification results do not make authorization or enforcement decisions.

## Integration plan

After the chain primitive passes testing:

1. Inspect the actual audit database schema and write path.
2. Decide how chain records will be persisted transactionally.
3. Establish concurrency and recovery behavior.
4. Protect chain checkpoints independently.
5. Add integration tests proving that each accepted audit event is linked.
6. Verify compatibility with the existing evidence timeline and correlation APIs.

Do not claim the persistent audit path is protected until these integration
steps are implemented and verified.
