# Day 65 — Evidence Quality Report

## Objective

Day 65 packages the Day 64 evidence quality-gate decision into a structured evidence quality report.

The report provides a single machine-readable object containing:

- Evidence index
- Quality-gate result
- Overall evidence status
- Acceptance decision

## Evidence Flow

```text
Evidence Index
      |
      v
Evidence Validation
      |
      v
Evidence Quality Gate
      |
      v
Evidence Quality Report
      |
      +---- ACCEPTED
      |
      +---- REJECTED