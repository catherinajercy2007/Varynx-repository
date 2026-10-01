# Day 58 — Final Experimental Evaluation Report

## Objective

Day 58 combines the outputs of the Phase III experimental evaluation
pipeline into a single structured final evaluation report.

The report brings together:

- Experiment measurements
- Validation and quality-gate results
- Baseline comparison
- Overall evaluation status

## Evaluation Pipeline

The current pipeline is:

1. Scenario definition
2. Scenario execution
3. Comparative metric calculation
4. Reproducibility evaluation
5. Experiment result aggregation
6. JSON result export
7. Experiment result validation
8. Experiment quality gate
9. Baseline comparison
10. Comparison summary
11. Final evaluation report

## Report Structure

The final report contains four sections:

### Experiment

Contains the aggregated experiment measurements.

### Quality Gate

Contains validation status and validation errors.

### Comparison

Contains baseline differences and alignment information.

### Overall Status

The final status can be:

- `PASS`
- `DIFFERS`
- `INVALID`

## Overall Status Rules

### PASS

The experiment is valid and aligned with the baseline.

### DIFFERS

The experiment is valid, but one or more baseline measurements differ.

### INVALID

The experiment or its comparison failed validation.

## Controlled Experiment

The default five-run experiment is expected to produce:

| Metric | Expected |
|---|---:|
| Experiment runs | 5 |
| Scenarios per run | 8 |
| Average pass rate | 100% |
| Average ALLOW count | 2 |
| Average DENY count | 6 |
| Quality gate | PASS |
| Baseline alignment | True |
| Overall status | PASS |

## API

The implementation provides:

- `determine_overall_status()`
- `generate_final_report()`
- `generate_default_final_report()`
- `final_report_to_dict()`

It also provides:

- `FinalEvaluationReport`

## Example Structure

```text
FinalEvaluationReport
├── experiment
│   ├── total_runs
│   ├── scenarios_per_run
│   ├── average_pass_rate
│   ├── average_allow_count
│   └── average_deny_count
│
├── quality_gate
│   ├── valid
│   ├── status
│   ├── missing_fields
│   ├── value_errors
│   └── consistency_errors
│
├── comparison
│   ├── pass_rate_difference
│   ├── allow_count_difference
│   ├── deny_count_difference
│   └── baseline_aligned
│
└── overall_status