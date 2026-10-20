
# Day 80 — Behavioral Capability Lease

## Objective

Define time-limited behavioral authority for an autonomous AI agent,
bound to its identity, task, capability, resource scope, and behavioral
conditions.

## Implementation

- `app/behavioral_capability_lease.py`
- `tests/test_day80_behavioral_capability_lease.py`

## Lease evaluation

The evaluation checks:

1. Authority state: active, suspended, or revoked.
2. Validity window: not-before and expiry.
3. Agent identity and task identity.
4. Requested capability.
5. Resource scope.
6. Supplied behavioral conditions.

Missing behavioral evidence must not satisfy a required condition.
Expiry is exclusive: a lease is expired when the evaluation time is
equal to or later than its expiry time.

## Security boundary

Lease eligibility is not a replacement for the existing authorization
policy. This module does not execute runtime enforcement, issue cloud
credentials, or infer malicious intent.

Member 2 remains responsible for runtime enforcement integration.

## Validation

Run focused tests:

```powershell
& "D:\aegisguard-env\Scripts\python.exe" -m pytest -v tests/test_day80_behavioral_capability_lease.py
```

Run the full regression suite:

```powershell
& "D:\aegisguard-env\Scripts\python.exe" -m pytest -q
```

Do not mark Day 80 complete until the actual implementation passes
focused tests and the full project regression suite.
