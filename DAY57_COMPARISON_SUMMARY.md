# Day 57 — Experimental Comparison Summary

## Objective

Day 57 extends the Phase III experimental evaluation framework with a
comparison summary layer.

The summary converts detailed baseline comparison measurements into a
compact result suitable for reporting and downstream processing.

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
10. Comparison summary

## Summary Measurements

The summary contains:

- Validation status
- Pass-rate difference
- ALLOW-count difference
- DENY-count difference
- Pass-rate baseline status
- ALLOW-count baseline status
- DENY-count baseline status
- Overall baseline alignment

## Summary Status

Three high-level statuses are supported:

### ALIGNED

The experiment is valid and all baseline conditions match.

### DIFFERS

The experiment is valid but at least one baseline condition differs.

### INVALID

The experiment or comparison result failed validation.

## Controlled Experiment

The default controlled experiment is expected to produce:

| Metric | Result |
|---|---:|
| Pass-rate difference | 0 |
| ALLOW-count difference | 0 |
| DENY-count difference | 0 |
| Pass-rate baseline | Met |
| ALLOW baseline | Match |
| DENY baseline | Match |
| Overall alignment | True |
| Status | ALIGNED |

## API

The implementation provides:

- `create_comparison_summary()`
- `generate_default_comparison_summary()`
- `comparison_summary_to_dict()`
- `comparison_summary_status()`
- `comparison_summary_details()`

It also provides:

- `ComparisonSummary`

## Testing

Run:

```powershell
python -m pytest tests/test_day57_comparison_summary.py -v