
# Day 83 — Correlation ID and Evidence Binding

## Objective

Bind the security artifacts associated with one agent request into a
deterministic manifest. The manifest supports traceability across action,
behavioral analysis, BCSE, decision, and enforcement stages.

## Existing integration

Varynx already has a Day 73 security evidence timeline and Day 74
security evidence correlation module. Day 83 complements those modules
with a request-level binding manifest; it does not replace their
chronological reconstruction or correlation behavior.

## Files

- `app/security_evidence_binding.py`
- `tests/test_day83_security_evidence_binding.py`
- `DAY83_CORRELATION_ID_EVIDENCE_BINDING.md`

## Evidence reference

Each reference records:

- Correlation identifier.
- Artifact identifier.
- Lifecycle stage.
- Source.
- Optional SHA-256 digest of a canonical payload.

Supported stages:

- `AGENT_ACTION`
- `BEHAVIORAL`
- `BCSE`
- `DECISION`
- `ENFORCEMENT`

The source field identifies the claimed origin of an artifact. It does
not independently authenticate that source.

## Manifest states

- `BINDING_COMPLETE`: all configured required stages are represented.
- `BINDING_PARTIAL`: at least one required stage is missing.
- `BINDING_INVALID`: duplicate artifact identifiers were supplied.

References carrying a different correlation identifier are rejected.
Missing evidence is reported rather than invented.

## Integrity semantics

The manifest uses canonical JSON and SHA-256 for deterministic digesting.
Digest verification detects changes relative to the stored digest; it does
not establish authenticity, trusted timestamps, or truth of source data.
A trusted signature or separately protected storage would be required
for stronger authenticity guarantees.

## Security boundaries

- No authorization decision is made.
- No runtime enforcement is executed.
- No evidence is fabricated to fill missing stages.
- Evidence references are not proof that an artifact is trustworthy.
- Correlation identifiers are grouping keys, not secrets or credentials.
- Existing timeline, audit, and correlation implementations remain intact.

## Acceptance criteria

1. References with mismatched correlation IDs are rejected.
2. Missing required stages result in a partial manifest.
3. Duplicate artifact identifiers are flagged as invalid.
4. Input order does not affect deterministic output.
5. Optional payload digests are validated.
6. Manifest digest verification succeeds for unchanged content.
7. The module clearly distinguishes integrity checking from source authenticity.
8. Existing evidence timeline and correlation APIs remain unchanged.

## Limitations

The first version builds a manifest from caller-supplied references. It
does not automatically ingest live events, query a database, sign records,
or provide tamper-proof storage. Integration with the existing timeline
and audit path should be performed after this module passes tests and its
input contract is confirmed against the local repository.
