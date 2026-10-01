# Day 70 — Evidence Quality Report Summary Validation

## Objective

Day 70 adds validation for the compact Evidence Quality Report Summary
introduced on Day 68 and exported on Day 69.

The validation layer ensures that summaries are structurally complete,
type-safe, and internally consistent before they are consumed as
evaluation evidence.

## Validation Flow

Evidence Quality Summary
          |
          v
   Structure Validation
          |
          v
     Value Validation
          |
          v
  Consistency Validation
          |
          v
       PASS / FAIL

## Required Fields

The summary must contain:

- overall_status
- accepted
- quality_gate_status
- integrity_verified
- artifact_count
- verified_artifact_count
- validation_error_count

## Main Functions

### validate_summary_structure()

Checks that all required summary fields are present.

### validate_summary_values()

Checks:

- allowed status values
- boolean fields
- non-negative integer counters

### validate_summary_consistency()

Checks that:

- ACCEPTED corresponds to accepted=True
- REJECTED corresponds to accepted=False
- PASS corresponds to accepted=True
- FAIL corresponds to accepted=False
- verified artifacts do not exceed total artifacts

### validate_evidence_quality_summary()

Runs all summary validation checks.

### generate_evidence_quality_summary_validation()

Produces a reusable validation result containing:

- valid
- status
- errors

## Consistency Rules

An accepted summary must contain:

```text
overall_status = ACCEPTED
accepted = True
quality_gate_status = PASS