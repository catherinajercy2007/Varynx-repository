# Day 90 — Exported Quality Gate Validation Report Verification

## Objective
Validate the JSON validation report exported in Day 89.

## Scope
- Validate the report's required fields.
- Check field types and allowed status values.
- Verify consistency between validity, status, and errors.
- Validate reports loaded from JSON files.
- Handle missing files and malformed JSON safely.
- Preserve the distinction between an invalid underlying quality gate
  and a structurally valid outer validation report.

## Implementation
- Added structure validation.
- Added field-value validation.
- Added consistency validation.
- Added combined validation.
- Added JSON file loading and validation.
- Added automated tests.

## Test command
python -m pytest tests/test_day90_evidence_quality_summary_quality_gate_validation_report_export_quality_gate_export_validation_report_export_validation_report_export_quality_gate_export_validation_report_export_validation.py -v

## Expected outcome
All Day 90 tests pass.