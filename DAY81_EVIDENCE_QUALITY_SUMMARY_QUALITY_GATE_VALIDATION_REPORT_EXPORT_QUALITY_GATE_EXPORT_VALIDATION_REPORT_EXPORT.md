# Day 81 — Exported Quality Gate Validation Report Export

## Objective

Day 81 adds JSON serialization and persistence for the Day 80 exported
quality-gate validation report.

## Scope

Day 80 creates a reusable validation report.

Day 81 provides:

- dictionary conversion
- JSON serialization
- file persistence
- JSON loading
- round-trip verification
- direct generation and export

## Report Structure

The exported report contains:

- `quality_gate`
- `valid`
- `status`
- `errors`

## API

### `validation_report_to_json_dict()`

Converts a validation report into a JSON-compatible dictionary.

### `validation_report_to_json()`

Serializes a validation report to JSON.

### `save_exported_quality_gate_validation_report()`

Persists the validation report to a JSON file.

### `load_exported_quality_gate_validation_report()`

Loads a previously saved JSON validation report.

### `generate_and_export_quality_gate_validation_report()`

Generates a Day 80 validation report and saves it directly.

### `export_quality_gate_validation_report_json()`

Generates the validation report and returns its JSON representation.

## Semantic Preservation

Day 81 preserves the distinction between:

1. validity of the exported quality-gate record
2. acceptance of the underlying evidence

For example, a failed underlying quality gate may be represented as:

```text
quality_gate:
    valid: False
    status: FAIL
    accepted: False