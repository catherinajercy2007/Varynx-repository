cd "C:\Users\cathe\OneDrive\Desktop\aegis-agent-firewall"

@"
# DAY 5 — AUDIT LOGGING

## Objective

Implement audit logging for authorization decisions in AegisGuard.

Every authorization attempt is recorded as a security event.

## Authorization Flow

Agent
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
Audit Logging

## Logged Fields

Each authorization event contains:

- timestamp
- agent_id
- task_id
- action
- resource
- decision
- risk
- reason

## Storage

Audit events are stored locally in:

`audit_logs.jsonl`

The file uses JSON Lines format. Each line contains one JSON security event.

The audit log is excluded from Git using `.gitignore`.

## Authorization Events Tested

The following authorization scenarios were tested:

1. Valid authorization
2. Unauthorized resource
3. Unauthorized action
4. Invalid agent
5. Invalid task
6. Expired task
7. Audit log retrieval
8. Malformed JSON line handling

## Successful Authorization

A valid request produces an `ALLOW` audit event.

## Denied Authorization

Unauthorized requests produce `DENY` audit events.

Examples include:

- invalid agent identity
- invalid API key
- invalid or expired task
- unauthorized resource
- unauthorized action

## Audit Endpoint

Audit events can be retrieved using:

`GET /audit/logs`

If the audit file does not exist, the endpoint returns:

```json
{
  "events": []
}