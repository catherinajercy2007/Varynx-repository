# Day 67 — Evidence Quality Report Validation

## Objective

Day 67 adds validation for the Evidence Quality Report created on Day 65
and exported on Day 66.

The validation layer ensures that persisted evidence-quality reports have:

- the required structure,
- valid field types,
- valid status values,
- a valid quality-gate structure,
- consistent acceptance decisions.

## Validation Flow

Evidence Quality Report
          |
          v
   Structure Validation
          |
          v
     Value Validation
          |
          v
 Quality Gate Validation
          |
          v
   Consistency Validation
          |
          v
      PASS / FAIL

## Main Functions

### validate_report_structure()

Checks that the report contains:

- evidence_index
- quality_gate
- overall_status
- accepted

### validate_report_values()

Checks field types and allowed status values.

### validate_quality_gate()

Validates the nested quality-gate result.

### validate_report_consistency()

Ensures that report status and acceptance values agree.

### validate_evidence_quality_report()

Runs all validation checks and returns a consolidated result.

### generate_evidence_quality_report_validation()

Produces a reusable validation report containing:

- valid
- status
- errors

## Consistency Rules

An `ACCEPTED` report must have:

```text
accepted = True