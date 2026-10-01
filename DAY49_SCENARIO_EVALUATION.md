# Day 49 — Scenario Evaluation Runner

## Objective

Day 49 extends the Phase III experimental evaluation framework by executing
the controlled scenario matrix defined in Day 48.

The goal is to provide a reproducible mechanism for evaluating each security
scenario and collecting its expected decision, risk level, and pass status.

## Evaluation Input

The Day 48 scenario matrix contains eight controlled scenarios:

| ID | Scenario | Expected Decision | Risk |
|---|---|---|---|
| S01 | Normal authorized request | ALLOW | LOW |
| S02 | Unauthorized resource access | DENY | HIGH |
| S03 | Invalid agent request | DENY | HIGH |
| S04 | Unauthorized action | DENY | HIGH |
| S05 | Privilege escalation attempt | DENY | CRITICAL |
| S06 | Repeated suspicious requests | DENY | HIGH |
| S07 | Destructive operation | DENY | CRITICAL |
| S08 | Normal write request | ALLOW | LOW |

## Implementation

Day 49 introduces:

- `evaluation/scenario_runner.py`
- `tests/test_day49_scenario_runner.py`

The runner:

1. Loads the controlled scenario matrix.
2. Evaluates each scenario.
3. Records the expected decision.
4. Records the expected risk level.
5. Marks the scenario as passed or failed.
6. Produces aggregate evaluation statistics.

## Metrics

The runner reports:

- Total scenarios
- Passed scenarios
- Failed scenarios
- Pass rate
- ALLOW count
- DENY count

## Expected Evaluation

For the controlled Day 48 matrix:

- Total scenarios: 8
- Expected ALLOW: 2
- Expected DENY: 6
- Expected HIGH-risk scenarios: 4
- Expected CRITICAL-risk scenarios: 2
- Expected pass rate: 100%

## Testing

Run:

```powershell
python -m pytest tests/test_day49_scenario_runner.py -v