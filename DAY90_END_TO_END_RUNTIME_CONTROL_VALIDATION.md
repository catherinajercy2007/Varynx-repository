
# Varynx Day 90 — End-to-End Runtime Control & Evidence Validation

## Objective

Validate consistency among existing Varynx behavioral-security artifacts
before passing a response recommendation to the runtime enforcement layer.

Day 90 is an integration-validation layer. It is not a replacement for
behavioral analysis, adaptive response, or runtime enforcement.

## Files

- `app/runtime_control_validation.py`
- `tests/test_day90_runtime_control_validation.py`
- `DAY90_END_TO_END_RUNTIME_CONTROL_VALIDATION.md`

## Inputs

1. Agent identifier
2. Case identifier
3. Optional request correlation identifier
4. Day 83 evidence-binding manifest
5. Day 89 security trajectory graph
6. Day 88 security alert
7. Existing adaptive-response recommendation

Inputs must be supplied as serialized mappings compatible with the
corresponding module's `to_dict()` output.

## Validation responsibilities

- Check required artifact availability.
- Compare trajectory agent and case identifiers with the requested identity.
- Check correlation consistency when a correlation identifier is supplied.
- Inspect manifest status and missing evidence stages.
- Validate the basic structure of graph nodes and findings.
- Detect empty trajectories and reported omitted evidence.
- Check overlap between trajectory entry IDs and manifest artifact IDs.
- Check alert identity, severity, and evidence-reference consistency.
- Recognize supported adaptive-response actions.
- Reject unsupported claims that this validator authorizes or executes actions.
- Produce a deterministic validation report for identical supplied inputs.

## Result statuses

### VALIDATED_FOR_HANDOFF

The supplied artifacts passed the checks implemented by this validator.
This status does not prove that the proposed action is authorized or safe.

### REVIEW_REQUIRED

The validator detected missing artifacts, incomplete evidence, empty
trajectory data, or reference mappings that need human review.

### INVALID_HANDOFF

The validator detected identity mismatches, malformed artifact structures,
unknown manifest status, or unsupported claims of authorization or enforcement.

## Architecture boundaries

Day 90:

- Does not calculate a new risk score.
- Does not replace the Day 30 adaptive-response engine.
- Does not replace Day 73 evidence timeline or Day 74 correlation.
- Does not replace Day 83 evidence binding.
- Does not replace Day 84 audit-chain functionality.
- Does not replace Day 88 alert intelligence or Day 89 trajectory analysis.
- Does not mutate capability leases or policies.
- Does not execute runtime controls.
- Does not confirm that a kill switch, scope restriction, or other enforcement
  action succeeded.
- Does not establish that source evidence is authentic merely because a
  manifest references it.

## Evidence-reference limitation

Day 83 manifests use artifact IDs, while trajectory nodes use entry IDs.
The identifiers may belong to different namespaces. Day 90 checks for
overlap only as a consistency signal.

A production integration should provide an explicit mapping between source
artifact IDs and trajectory entry IDs. Lack of overlap requires review;
overlap alone does not prove that all evidence is complete or authentic.

## Validation report

The report includes:

- Validation ID
- Overall status
- Agent, case, and correlation identifiers
- Individual checks and their results
- Reason codes requiring review or invalidating the handoff
- Trajectory evidence entry IDs
- Existing response recommendation
- Alert severity
- Number of trajectory findings
- Explicit authorization and enforcement boundary flags

The report is returned in memory. Persistence to the existing audit database
or Day 84 hash-chain primitive must be integrated and tested separately.

## Verification commands

Run these from the repository root in PowerShell.

```powershell
& "D:\aegisguard-env\Scripts\python.exe" -m py_compile `
  app/runtime_control_validation.py `
  tests/test_day90_runtime_control_validation.py

& "D:\aegisguard-env\Scripts\python.exe" -m pytest -v `
  tests/test_day90_runtime_control_validation.py

& "D:\aegisguard-env\Scripts\python.exe" -m pytest -q

git diff --check
git status --short
```

## Completion criteria

- Focused tests pass.
- Compilation succeeds.
- The full existing test suite has been reviewed.
- Actual serialized outputs from Days 83, 88, and 89 are tested against
  the validator.
- Any differences in evidence-reference namespaces are explicitly mapped.
- Only intended Day 90 files are staged.
- The commit and remote push are verified.

A passing unit-test suite does not by itself establish production readiness.
