# DAY 9 — RISK-ADAPTIVE AUTHORIZATION

## Objective

Day 9 extends the Day 8 deterministic risk engine into a risk-adaptive authorization layer.

The risk engine now produces:

- risk score
- risk level
- risk factors
- final risk-aware decision

## Authorization Architecture

```text
AI Agent
    ↓
Agent Identity
    ↓
Task Verification
    ↓
Trusted Task Intent
    ↓
Policy Evaluation
    ↓
Risk Engine
    ↓
Risk Score
    ↓
Risk Level
    ↓
Risk-Adaptive Decision
    ↓
Audit
    ↓
SQLite