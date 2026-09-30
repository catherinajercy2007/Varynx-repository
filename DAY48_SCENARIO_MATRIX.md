# Day 48 — Experimental Scenario Matrix

## Objective

Create a controlled and reproducible scenario matrix for
evaluating the incremental contribution of Varynx security
components.

The scenarios are evaluation inputs only. They do not implement
or replace the existing Varynx security engine.

## Scenario Categories

### Normal

Represents expected agent behavior.

Examples:

- normal agent activity
- normal resource access

Expected label:

`0`

### Suspicious

Represents behavior that deviates from established expectations
and should be useful for evaluating behavioral intelligence.

Examples:

- unusual resource access
- repeated denial pattern
- behavioral drift

Expected label:

`1`

### Malicious

Represents clearly security-relevant behavior.

Examples:

- privilege escalation attempt
- tool abuse attempt
- cross-context attack chain

Expected label:

`1`

## Scenario Matrix

| ID | Scenario | Category | Expected Risk | Label |
|---|---|---|---|---|
| S01 | Normal Agent Activity | normal | low | 0 |
| S02 | Normal Resource Access | normal | low | 0 |
| S03 | Unusual Resource Access | suspicious | medium | 1 |
| S04 | Repeated Denial Pattern | suspicious | medium | 1 |
| S05 | Behavioral Drift | suspicious | medium | 1 |
| S06 | Privilege Escalation Attempt | malicious | high | 1 |
| S07 | Tool Abuse Attempt | malicious | high | 1 |
| S08 | Cross-Context Attack Chain | malicious | high | 1 |

## Research Use

The matrix provides common evaluation inputs for controlled
comparisons across:

1. Policy-only
2. Risk
3. Risk + behavior
4. Risk + behavior + dynamic trust
5. Full Varynx with BCSE

The goal is to determine whether additional components provide
measurable incremental value.

## Reproducibility

Scenario identifiers are stable.

The scenario definitions should remain unchanged during a
controlled experiment unless a new dataset version is explicitly
created.

## Limitations

This matrix is a controlled research fixture and is not a
complete representation of real-world autonomous-agent behavior.

Future experiments should include larger datasets, repeated
trials, behavioral drift, adversarial conditions, and realistic
workload distributions.