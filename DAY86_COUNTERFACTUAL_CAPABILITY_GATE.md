
# Varynx Day 86 — Counterfactual Capability Gate

## 1. Objective

Day 86 introduces a deterministic gate that evaluates a proposed
capability or scope change using the existing Behavioral Counterfactual
Security Engine (BCSE).

The gate consumes existing BCSE consequence estimates. It does not
recalculate consequence magnitude or duplicate the scenario builder.

## 2. Pipeline

1. A proposed capability or scope change is described.
2. The existing Day 51–55 BCSE pipeline provides a scenario and
   consequence estimate.
3. Day 86 checks scenario identity, consequence score, confidence,
   evidence sufficiency, configured resource scopes, and current
   authority state.
4. Day 86 returns a reason-coded recommendation for the existing
   policy and runtime review workflow.

## 3. Outcomes

| Outcome | Meaning |
|---|---|
| ELIGIBLE_FOR_REVIEW | The supplied evidence passed this gate's configured checks. |
| REQUIRE_HUMAN_REVIEW | Evidence, confidence, consequence, or authority state requires review. |
| RESTRICT | The proposal falls outside configured allowed scopes. |
| REJECT | The resource is explicitly restricted, authority is already restricted, or the consequence is critical. |

An eligible result does not grant a capability or authorize a request.

## 4. Decision inputs

- Existing BCSE scenario identifier
- Potential consequence magnitude (0–100)
- BCSE confidence: LOW, MODERATE, or HIGH
- Supplied BCSE evidence
- Requested resource and configured scope rules
- Current authority state
- Explicitly configured thresholds

Thresholds are prototype configuration parameters and must be evaluated
empirically before any production use.

## 5. Safety and architecture boundaries

Day 86 does not:

- execute counterfactual actions;
- grant, extend, or modify a capability lease;
- replace the existing authorization policy;
- enforce runtime controls;
- infer malicious intent;
- interpret consequence magnitude as attack probability;
- duplicate the Day 51 scenario builder or Day 52 consequence estimator.

Member 2's runtime enforcement remains authoritative.

## 6. Validation

Run the focused tests first, then compile the module and run the
repository's full test suite. Record actual test output; do not infer
integration success from focused unit tests alone.

## 7. Research interpretation

The gate is a deterministic integration prototype. Its thresholds,
false-positive rate, false-negative rate, latency, robustness, and
impact on legitimate capability changes require evaluation against
defined baselines before claiming security improvement.
