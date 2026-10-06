# Day 77 — Export Validation Quality Gate

## Objective

Day 77 adds a reusable quality gate on top of the validation report export
validation implemented in Day 76.

The quality gate converts the validation result into an explicit PASS or FAIL
acceptance decision.

## Implementation

File:

`evaluation/evidence_quality_summary_quality_gate_validation_report_export_quality_gate.py`

## Tests

File:

`tests/test_day77_evidence_quality_summary_quality_gate_validation_report_export_quality_gate.py`

## Result Model

`ExportedValidationReportQualityGateResult`

Fields:

- `valid`
- `status`
- `validation_errors`
- `accepted`

## Main Functions

### evaluate_exported_validation_report_quality_gate()

Validates the exported validation report and creates a quality-gate result.

### generate_exported_validation_report_quality_gate()

Convenience wrapper around the evaluator.

### exported_validation_report_quality_gate_to_dict()

Converts the result into a dictionary.

### exported_validation_report_quality_gate_status()

Returns the PASS or FAIL status.

## Acceptance Rule

The Day 77 quality gate accepts the report when Day 76 validation succeeds.

Therefore:

- valid validation report → PASS
- invalid validation report → FAIL

## Important Semantic Rule

The quality gate evaluates the validity of the exported validation report.

It does not directly decide whether the original evidence was accepted.

For example, an embedded quality gate may contain:

- valid = False
- status = FAIL
- accepted = False

If that record is internally consistent, the exported validation report can
still be valid.

In that situation Day 77 correctly returns:

- valid = True
- status = PASS
- accepted = True

## Evaluation Chain

Day 68 → Evidence Quality Report Summary

Day 69 → Summary Export

Day 70 → Summary Validation

Day 71 → Summary Quality Gate

Day 72 → Quality Gate Export

Day 73 → Quality Gate Validation

Day 74 → Validation Report

Day 75 → Validation Report Export

Day 76 → Export Validation

Day 77 → Export Validation Quality Gate

## Testing

The Day 77 test suite covers:

- valid report acceptance
- rejected underlying quality-gate records
- invalid status
- missing fields
- invalid data types
- consistency failures
- dataclass creation
- dictionary conversion
- status helpers
- generation helpers
- invalid input handling

## Expected Result

20 Day 77 tests should pass without modifying Days 68–76.