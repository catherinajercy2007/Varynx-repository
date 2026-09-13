# DAY 12 — AUTHORIZATION BYPASS AND ABUSE TESTING

## Objective

Day 12 extends Day 11 security testing by testing the authorization boundary itself.

The objective is to verify that an authenticated or apparently valid agent cannot bypass task, policy, or risk controls.

## Attack Surface

```text
Agent
  ↓
Security Validation
  ↓
Identity Verification
  ↓
Task Verification
  ↓
Intent
  ↓
Policy
  ↓
Risk Engine
  ↓
Decision
  ↓
Audit