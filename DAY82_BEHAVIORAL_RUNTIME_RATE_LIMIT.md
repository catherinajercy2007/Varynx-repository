
# Day 82 — Behavioral Runtime Rate-Limit Assessment

## Objective

Provide deterministic, explainable rate-limit assessments for autonomous
agent actions using caller-supplied event history and configurable
rolling-window limits.

This module belongs to behavioral intelligence and recommendation.
It does not implement runtime throttling or replace authorization.

## Files

- `app/behavioral_runtime_rate_limit.py`
- `tests/test_day82_behavioral_runtime_rate_limit.py`
- `DAY82_BEHAVIORAL_RUNTIME_RATE_LIMIT.md`

## Design

A request is evaluated against a rolling time window using:

- Agent identity
- Requested capability
- Target resource
- Event timestamp
- Correlation identifier
- Configured maximum requests
- Configured window duration

The current proposed request is counted once. Historical events are counted
only when they match the same agent, capability, and resource and fall
within the defined interval.

Duplicate historical correlation IDs count once to avoid inflating the
recorded request count. The caller remains responsible for supplying
trustworthy event history and unique identifiers.

## Assessment statuses

- `WITHIN_LIMIT`: projected request count is below the configured maximum.
- `LIMIT_REACHED`: projected request count equals the maximum.
- `LIMIT_EXCEEDED`: projected request count exceeds the maximum.

## Recommendations

- `CONTINUE_MONITORING`
- `REVIEW_RATE_LIMIT`
- `RESTRICT_RATE`

These are recommendations only. They do not authorize or deny a request,
change an existing decision, or execute throttling.

## Security boundaries

- The module does not maintain live state.
- The module does not delay, reject, or throttle requests.
- It does not independently authorize actions.
- It does not infer malicious intent from request volume.
- It does not invent missing events.
- Results are based on the supplied history and configured policy.
- Timestamps must be timezone-aware.
- Only exact agent, capability, and resource matches are counted.

## Acceptance criteria

1. Requests below, at, and above the limit produce the correct status.
2. Events outside the time window are excluded.
3. Future events are excluded.
4. Different agents, capabilities, and resources are not mixed.
5. Duplicate correlation identifiers do not inflate counts.
6. Invalid configuration and event inputs are rejected.
7. Identical inputs produce identical results.
8. Serialization explicitly states that enforcement is not executed.
9. The existing authorization and enforcement layers remain authoritative.

## Limitations

The first version evaluates a supplied snapshot of historical events.
It does not provide distributed counters, concurrency control, persistent
storage, or production-grade live rate limiting. Those capabilities belong
in a separately designed runtime service and require additional testing.
