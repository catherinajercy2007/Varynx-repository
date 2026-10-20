
# Varynx Day 89 — Security Trajectory & Action-Sequence Risk Graph

## Objective

Construct a deterministic, explainable graph from existing security evidence
to identify observed action-sequence patterns and preserve traceability to
the evidence that produced each finding.

## Files

- `app/security_trajectory_graph.py`
- `tests/test_day89_security_trajectory_graph.py`
- `DAY89_SECURITY_TRAJECTORY.md`

## Architecture

The module accepts existing Day 73 `SecurityEvidenceEntry` records or
compatible mappings. It does not query the database or fabricate missing
events.

Each graph node represents one observed evidence entry. Edges describe
chronological succession or a detected relationship. Findings retain the
source entry IDs and graph node IDs.

## Supported patterns

1. Chronological succession between adjacent events.
2. Consecutive denied or restricted decisions.
3. Expansion across distinct observed resources.
4. Explicit changes in context identifiers.
5. Increases in an explicitly supplied risk signal.
6. Changes in recorded security decisions.

Thresholds are configuration inputs, not empirically validated universal
security boundaries.

## Determinism

Graph, edge, and finding identifiers use SHA-256 digests over canonical
JSON payloads. Identical normalized evidence and configuration should
produce identical output identifiers.

## Integration boundaries

- Day 73 remains the source of normalized evidence timeline entries.
- Day 74 remains responsible for evidence correlation.
- Day 79 remains responsible for structured decision reason codes.
- Day 88 remains responsible for alert and escalation recommendations.
- Day 89 does not replace BCSE or calculate a new universal risk score.
- Day 89 does not authorize actions, execute enforcement, modify leases,
  or infer malicious intent.

## Limitations

- The graph covers only the supplied case and supplied entries.
- Missing events cannot be reconstructed by this module.
- Resource expansion may be legitimate for a task; policy context is needed
  to determine whether it is concerning.
- A context change or rising risk signal is an observation, not proof of an
  attack.
- The graph is an in-memory analysis result, not a durable graph database.
- `evidence_complete` is caller-supplied metadata, not a cryptographic
  completeness guarantee.
- Hash-based IDs provide deterministic identification, not evidence
  authenticity or tamper-proof storage.

## Verification

Run the focused tests, compile checks, and complete project test suite
before committing the implementation.
