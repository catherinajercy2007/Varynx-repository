# Day 46 — Evaluation Framework Audit

## Objective

Audit the established Days 23–45 research/evaluation infrastructure
before adding experimental support for Dynamic Behavioral Trust.

The purpose of this task is **not** to rebuild the evaluation framework.
Existing quantitative evaluation, baseline comparison, ablation,
threshold sensitivity, robustness, statistical, and performance
components remain the established research foundation.

## Repository Findings

| Component | Status | Required action |
|---|---|---|
| Experimental dataset | Extension required | Add optional trust-aware evaluation data/adapter without breaking the existing schema. |
| Quantitative evaluation | Compatible | Reuse existing binary metric definitions and detector evaluation. |
| Baseline comparison | Extension required | Add a controlled Dynamic Behavioral Trust condition. |
| Ablation | Extension required | Add trust-enabled/trust-disabled experimental conditions. |
| Threshold sensitivity | Extension required | Later add controlled trust-boundary sensitivity; preserve existing defaults. |
| Robustness | Extension required | Add trust-state/drift perturbation conditions. |
| Statistical evaluation | Compatible | Reuse paired statistical procedures once trust/control outputs are paired. |
| Performance | Compatible | Benchmark trust updates through the existing callable benchmark interface. |
| Dynamic Behavioral Trust | Compatible | Consume the actual `TrustSnapshot` output; do not duplicate trust computation. |
| Evaluation regression tests | Compatible | Extend existing focused suites with trust-specific tests. |

## Important Architectural Finding

The existing research framework already provides reusable generic
machinery.

The primary missing capability is a **trust-aware evaluation adapter**
between `DynamicBehavioralTrust` and the established experimental
pipeline.

The current experimental dataset contains reproducible
scenario/event information such as seed, scenario, agent, action,
resource, ground truth, risk score, decision, and timestamp.

It does not currently carry a dynamic trust snapshot.

Therefore, Dynamic Behavioral Trust should be evaluated through an
explicit adapter/extension rather than by modifying the trust engine
or duplicating trust calculations inside `evaluation.py`.

## Existing Dynamic Trust Interface

`app/behavioral_trust.py` provides:

- bounded trust scores in `[0, 100]`
- trust bands
- weighted evidence aggregation
- neutral handling of missing evidence
- learning rate
- time decay
- immutable `TrustSnapshot` records
- per-agent state/history

These outputs are sufficient for a later evaluation adapter.

## Required Research Controls

Trust-enabled experiments must preserve:

1. identical scenario definitions
2. identical ground-truth labels
3. identical seeds
4. identical metric definitions
5. identical evaluation procedures
6. explicit trust-enabled/trust-disabled conditions

The experiment must measure incremental value rather than assume that
Dynamic Behavioral Trust improves security.

## Day 47 Dependency

The next task is to implement a trust-aware evaluation adapter that
consumes real `TrustSnapshot` values and exposes them to the existing
evaluation pipeline without duplicating the trust engine.