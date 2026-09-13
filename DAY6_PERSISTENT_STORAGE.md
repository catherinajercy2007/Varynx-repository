# DAY 6 — PERSISTENT STORAGE

## Objective

The objective of Day 6 is to replace temporary JSON Lines audit storage with persistent SQLite storage.

AegisGuard now stores authorization audit events in a local SQLite database.

---

## Day 5 Storage

During Day 5, audit events were stored in:

`audit_logs.jsonl`

JSON Lines provided a simple prototype storage mechanism.

However, JSONL is not a structured database and is not suitable for persistent querying as the project grows.

---

## Day 6 Storage

Day 6 introduces SQLite persistent storage.

Database file:

`aegisguard.db`

SQLite was selected because it:

- requires no separate database server
- is included with Python
- provides structured storage
- supports SQL queries
- is suitable for the current local prototype

---

## Database Structure

The database contains the following table:

`audit_events`

### Columns

| Column | Description |
|---|---|
| id | Unique audit event identifier |
| timestamp | UTC timestamp of the authorization event |
| agent_id | Identifier of the requesting AI agent |
| task_id | Identifier of the active task |
| action | Requested action |
| resource | Requested resource |
| decision | ALLOW or DENY |
| risk | Risk score associated with the decision |
| reason | Explanation for the authorization decision |

---

## Persistent Authorization Flow

The Day 6 architecture is:

```text
AI Agent
    ↓
AegisGuard
    ↓
Identity Verification
    ↓
Task Verification
    ↓
Trusted Task Intent
    ↓
Policy Evaluation
    ↓
ALLOW / DENY
    ↓
Audit Logger
    ↓
SQLite Database
    ↓
GET /audit/logs