# Day 79 — Evidence Quality Summary Quality Gate Export Validation

## Objective

Day 79 validates the exported quality-gate JSON record produced by
Day 78.

The validation ensures that the exported quality-gate record has:

- all required fields
- correct field types
- supported status values
- internally consistent values
- meaningful validation-error semantics

## Scope

Day 79 validates the exported representation of the Day 77 quality gate.

It does not re-run evidence integrity verification.

It does not replace the Day 73 validation layer.

It verifies that the serialized quality-gate record remains structurally
and logically valid after export.

## Required Fields

The exported quality-gate record contains:

- `valid`
- `status`
- `validation_errors`
- `accepted`

## Validation Rules

### Structure

All required fields must exist.

### Values

- `valid` must be a boolean.
- `status` must be `PASS` or `FAIL`.
- `validation_errors` must be a list.
- `accepted` must be a boolean.

### Consistency

When `valid` is `True`, status must be `PASS`.

When `valid` is `False`, status must be `FAIL`.

When status is `PASS`, accepted must be `True`.

When status is `FAIL`, accepted must be `False`.

A valid record must not contain validation errors.

An invalid record must contain at least one validation error.

## Important Semantic Distinction

A rejected underlying quality gate can still be represented by a valid
exported record.

Example:

```text
valid: False
status: FAIL
accepted: False
validation_errors: [...]