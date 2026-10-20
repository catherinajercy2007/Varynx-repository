
# Varynx Day 87 — Runtime Kill Switch & Emergency Authority Revocation

## 1. Objective

Day 87 defines an emergency-control state model that signals when a
global kill switch, agent-level revocation, or capability-level
revocation is active.

The module supplies a control assessment for the runtime enforcement
layer. It does not directly stop agents or deny operations.

## 2. Supported controls

| Control target | Effect of an active control |
|---|---|
| GLOBAL | Matches every assessed agent and capability |
| AGENT | Matches the specified agent |
| CAPABILITY | Matches the specified capability |

Multiple active controls can match the same request. The assessment
returns the matching control IDs and corresponding reason codes.

## 3. State transitions

A control is created as ACTIVE. An explicit release operation changes
it to RELEASED.

Controls do not expire or automatically release based on elapsed time.
Release requires a non-empty operator identity, release reason, and
timezone-aware timestamp.

A released control remains in the registry as a historical record.
A later activation creates a new control ID.

## 4. Audit and handoff

Each activation and release generates an in-memory event containing:

- Event ID and control ID
- Target type and target identifier
- Actor identity
- Reason
- Timestamp

The enforcement signal reports whether an emergency control matches
the requested agent and capability.

The signal explicitly reports that enforcement has not been executed.
The consuming enforcement service must validate and act on this signal.

## 5. Security boundaries

Day 87 does not:

- terminate a process or stop a running agent by itself;
- modify Day 80 capability leases;
- replace authorization or adaptive response;
- authenticate or authorize operators;
- provide persistent, tamper-proof storage;
- guarantee immediate propagation across multiple processes;
- automatically restore previously revoked authority.

## 6. Production integration requirements

Before production use, add and validate:

1. Authenticated and authorized emergency-control operators.
2. Durable storage and atomic state transitions.
3. Concurrency protection and idempotency across processes.
4. Integration with Member 2's runtime enforcement layer.
5. Fail-safe behavior for unavailable or stale control state.
6. Integration with the existing audit/evidence pipeline.
7. Recovery approval and operational procedures.
8. Tests for concurrent activation, release, restart recovery, and
   enforcement propagation.

The existing SQLite audit API records authorization events, but it
does not automatically persist these new control events. Do not claim
durable emergency auditing until that integration exists.

## 7. Validation

Run the focused tests, compile the new module, and run the complete
repository test suite. Record the actual outputs and investigate any
regressions before merging.
