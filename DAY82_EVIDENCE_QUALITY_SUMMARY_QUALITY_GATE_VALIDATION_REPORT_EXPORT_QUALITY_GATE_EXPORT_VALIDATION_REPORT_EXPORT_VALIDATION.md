# Day 82 — Exported Validation Report Export Validation

## Objective

Day 82 validates the JSON-compatible validation report produced by Day 81.

The purpose is to ensure that an exported validation report has:

- the required fields
- valid field types
- supported status values
- internally consistent values
- a valid nested quality-gate record

## Validation Layers

The evaluation pipeline is:

Day 79
-> Exported quality-gate validation

Day 80
-> Exported quality-gate validation report

Day 81
-> Exported validation report JSON persistence

Day 82
-> Exported validation report export validation

## Required Fields

The exported validation report requires:

- `quality_gate`
- `valid`
- `status`
- `errors`

## Supported Status Values

The report status must be:

- `PASS`
- `FAIL`

## Consistency Rules

If `valid` is `True`:

- `status` must be `PASS`
- `errors` must be empty

If `valid` is `False`:

- `status` must be `FAIL`
- `errors` must contain at least one error

The nested quality gate must also have consistent:

- `valid`
- `status`

values.

## Important Semantic Distinction

Day 82 validates the exported validation report itself.

It does not mean that the underlying evidence is accepted.

For example, the following is a valid exported validation report:

```text
quality_gate:
    valid: False
    status: FAIL
    accepted: False

report:
    valid: True
    status: PASS
    errors: []s