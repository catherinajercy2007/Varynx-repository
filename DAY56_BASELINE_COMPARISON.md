# Day 56 — Experimental Baseline Comparison

## Objective

Day 56 extends the Phase III experimental evaluation framework with a
baseline comparison layer.

The comparison layer evaluates validated experiment results against
defined reference metrics.

## Evaluation Pipeline

The current evaluation pipeline is:

1. Scenario definition
2. Scenario execution
3. Comparative metric calculation
4. Reproducibility evaluation
5. Experiment result aggregation
6. JSON result export
7. Experiment result validation
8. Experiment quality gate
9. Baseline comparison

## Default Baseline

The controlled baseline contains:

| Metric | Baseline |
|---|---:|
| Pass rate | 100% |
| ALLOW count | 2 |
| DENY count | 6 |

These values correspond to the controlled eight-scenario evaluation matrix.

## Comparison Measurements

The implementation calculates:

- Pass-rate difference
- ALLOW-count difference
- DENY-count difference
- Pass-rate baseline compliance
- ALLOW-count baseline match
- DENY-count baseline match

## Validation Dependency

Baseline comparison only proceeds when the experiment report passes
the existing experiment validation checks.

Invalid reports therefore cannot be treated as valid baseline comparisons.

## API

The implementation provides:

- `compare_with_baseline()`
- `compare_experiment_report()`
- `generate_default_baseline_comparison()`
- `baseline_comparison_to_dict()`

It also provides:

- `BaselineMetrics`
- `BaselineComparison`
- `DEFAULT_BASELINE`

## Controlled Experiment

Expected controlled comparison:

| Metric | Experiment | Baseline | Difference |
|---|---:|---:|---:|
| Pass rate | 100% | 100% | 0 |
| ALLOW count | 2 | 2 | 0 |
| DENY count | 6 | 6 | 0 |

Expected status:

```text
Valid: True
Pass-rate baseline: Met
ALLOW baseline: Match
DENY baseline: Match