
# Day 85 — Behavioral Authority Decay and Recovery

## Objective

Define an explainable state assessment for behavioral authority based on
evidence freshness, adverse behavioral signals, and qualifying recovery
evidence.

The module produces recommendations only. It does not modify capability
leases, grant privileges, authorize actions, or enforce restrictions.

## Files

- `app/behavioral_authority_decay.py`
- `tests/test_day85_behavioral_authority_decay.py`
- `DAY85_BEHAVIORAL_AUTHORITY_DECAY_RECOVERY.md`

## Authority states

- `NORMAL`: no configured decay condition is currently met.
- `REDUCED`: authority reduction is recommended.
- `RESTRICTED`: a stronger restriction is recommended or retained.

These are behavioral authority assessment states, not actual permissions.

## Decay rules

A configured adverse signal at or above its threshold reduces the
recommended authority state by one level. Missing or stale qualifying
evidence reduces NORMAL to REDUCED.

Thresholds and evidence freshness are configurable assumptions that must
be validated experimentally.

## Recovery rules

A REDUCED state can be recommended for recovery only when:

1. Qualifying evidence is present and fresh.
2. A recovery signal is present and within its configured threshold.
3. The required number of qualifying recovery events has been reached.

RESTRICTED authority is not automatically restored by this module. It
requires a separately designed review process.

## Security boundaries

- The module never grants permissions.
- It does not modify an existing capability lease.
- It does not execute runtime enforcement.
- Missing or invalid evidence never increases authority.
- Recovery requires explicit evidence; elapsed time alone is insufficient.
- Recommendations must be checked against authoritative policy.

## Acceptance criteria

1. Fresh benign evidence keeps the current normal state.
2. Missing or stale evidence reduces normal authority.
3. Strong adverse evidence recommends a lower state.
4. Recovery requires fresh evidence and qualifying recovery signals.
5. Restricted authority cannot be automatically restored.
6. Invalid signals are rejected or produce an explicit invalid status.
7. Identical inputs produce identical outputs.
8. Results clearly indicate that they are not authorization decisions.

## Limitations

This is a deterministic research model, not an empirically validated
authority algorithm. The thresholds, evidence TTL, and recovery event
count are configurable parameters, not established optimal values.
Evaluation should measure false restrictions, delayed recovery, and
sensitivity to stale or manipulated evidence.

## Integration plan

Integrate the assessment with the existing behavioral evidence and lease
lifecycle only after confirming their current interfaces. Keep actual
lease revocation, scope reduction, and enforcement in the authoritative
runtime security layer.
