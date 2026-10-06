# Day 75 — Evidence Quality Summary Quality Gate Validation Report Export

## Objective

Day 75 adds JSON export and persistence support for the validation report
created in Day 74.

The feature allows the evidence quality summary quality-gate validation
report to be:

- converted to a JSON-compatible dictionary
- serialized to JSON
- saved to disk
- loaded from disk
- exported directly from a quality-gate record

## Files

### Implementation

`evaluation/evidence_quality_summary_quality_gate_validation_report_export.py`

### Tests

`tests/test_day75_evidence_quality_summary_quality_gate_validation_report_export.py`

## Main Functions

### `validation_report_to_json_dict()`

Converts the Day 74 validation report into a JSON-compatible dictionary.

### `validation_report_to_json()`

Serializes the validation report into formatted JSON.

### `save_quality_gate_validation_report()`

Persists a validation report to a JSON file.

Parent directories are created automatically.

### `load_quality_gate_validation_report()`

Loads a previously saved validation report from JSON.

### `generate_and_export_quality_gate_validation_report()`

Generates the Day 74 validation report and saves it directly to disk.

### `export_quality_gate_validation_report_json()`

Generates the validation report and returns its JSON representation.

## Validation Semantics

Day 75 preserves the distinction introduced in Day 74.

A quality-gate record can represent a rejected quality gate while still being
a valid record.

For example:

- quality gate `valid = False`
- quality gate `status = FAIL`
- quality gate `accepted = False`

can still produce:

- validation report `valid = True`
- validation report `status = PASS`

because the record itself is structurally and logically valid.

## Evaluation Chain

Day 68
→ Evidence Quality Report Summary

Day 69
→ Summary Export

Day 70
→ Summary Validation

Day 71
→ Summary Quality Gate

Day 72
→ Quality Gate Export

Day 73
→ Quality Gate Validation

Day 74
→ Quality Gate Validation Report

Day 75
→ Quality Gate Validation Report Export

## Reproducibility

JSON serialization uses deterministic key ordering with `sort_keys=True`.

Saved reports can therefore be loaded and compared against their original
JSON-compatible representation.

## Testing

The Day 75 test suite verifies:

- dictionary conversion
- JSON serialization
- custom indentation
- file creation
- parent directory creation
- JSON loading
- round-trip preservation
- accepted quality-gate export
- rejected quality-gate export
- direct generation and export
- deterministic JSON output

## Expected Result

All Day 75 tests should pass without modifying the existing Days 68–74
implementation.