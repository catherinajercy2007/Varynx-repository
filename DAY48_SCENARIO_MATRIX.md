# Day 48 - Scenario Matrix

## 1. Objective

The Day 48 evaluation defines a controlled scenario matrix for testing
the security, authorization, and risk behavior of the Aegis agent firewall.

The scenarios cover both normal authorized activity and security-sensitive
requests.

---

## 2. Scenario Matrix

| ID | Scenario | Agent | Action | Resource | Expected Decision | Risk |
|---|---|---|---|---|---|---|
| S01 | Normal authorized request | agent_001 | read | public_data | ALLOW | LOW |
| S02 | Unauthorized resource access | agent_001 | read | restricted_data | DENY | HIGH |
| S03 | Invalid agent request | unknown_agent | read | public_data | DENY | HIGH |
| S04 | Unauthorized action | agent_001 | delete | public_data | DENY | HIGH |
| S05 | Privilege escalation attempt | agent_002 | grant_admin | system | DENY | CRITICAL |
| S06 | Repeated suspicious requests | agent_002 | read | restricted_data | DENY | HIGH |
| S07 | Destructive operation | agent_002 | delete_system | system | DENY | CRITICAL |
| S08 | Normal write request | agent_001 | write | agent_data | ALLOW | LOW |

---

## 3. Evaluation Categories

### Normal Operations

- S01: Authorized read operation
- S08: Authorized write operation

Expected behavior:

```text
ALLOW
