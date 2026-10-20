
# Day 81 — Behavioral Capability and Scope Assessment

## Objective

Day 81 adds a deterministic, explainable assessment layer that evaluates a
requested capability and resource against an explicit scope policy and the
Day 80 behavioral capability lease.

The component provides eligibility information and a recommendation for
downstream policy review. It does not independently authorize, execute,
or enforce an operation.

## Files

- `app/behavioral_capability_scope.py`
- `tests/test_day81_behavioral_capability_scope.py`
- `DAY81_BEHAVIORAL_CAPABILITY_SCOPE.md`

## Architecture

Request context
→ Explicit capability/scope policy
→ Restricted-resource check
→ Day 80 capability lease evaluation
→ Immutable assessment and reason codes
→ Existing authorization and runtime enforcement

## Scope matching

Resource scopes support exact resource identifiers and slash-delimited
path subtrees. For example, `public/` matches `public/report.csv` but
does not match `publicity/report.csv`.

Wildcards and glob patterns are not supported.

Explicitly restricted scopes take precedence over allowed scopes.

## Day 80 integration

The assessment reuses `BehavioralCapabilityLease` and
`evaluate_capability_lease`. It does not duplicate lease timing,
identity, task, resource, or behavioral-condition evaluation.

Missing evidence does not satisfy a lease condition.

## Security boundaries

- Assessment results are not authorization decisions.
- Recommendations do not execute enforcement.
- Existing policy and runtime controls remain authoritative.
- A positive assessment means only that the supplied scope and lease
  constraints passed.
- The component does not infer malicious intent.
- The component does not invent missing behavioral evidence.

## Verification

Run the focused Day 81 tests, then the full repository suite.

Acceptance criteria:

1. In-scope requests pass the assessment when the lease is eligible.
2. Out-of-scope resources are rejected.
3. Path-prefix boundary confusion is prevented.
4. Explicit restrictions override allowed parent scopes.
5. Capability, identity, task, timing, and behavioral-condition failures
   remain ineligible.
6. Results are deterministic for identical inputs.
7. Serialization explicitly states that the result is not an
   authorization decision and does not execute enforcement.
8. Day 80 behavior remains unchanged.

## Limitations

The initial implementation uses explicit scope rules rather than a
general-purpose policy language. It does not execute runtime controls.
Thresholds and behavioral conditions must be configured and evaluated
separately.

The assessment is a research prototype and must not be treated as a
replacement for an authoritative authorization and enforcement layer.
