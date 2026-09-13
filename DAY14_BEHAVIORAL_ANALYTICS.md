# DAY 14 — BEHAVIORAL ANALYTICS

## Objective

Day 14 adds behavioral security analytics to AegisGuard.

The system analyzes historical authorization audit events to identify suspicious agent behavior.

## Data Source

Behavioral analytics uses the persistent SQLite database:

```text
aegisguard.db