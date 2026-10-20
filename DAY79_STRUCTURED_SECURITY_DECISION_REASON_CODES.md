# Day 79 — Structured Security Decision Reason Codes

## Purpose

Produce deterministic, machine-readable explanations for an **already
existing** security decision and the evidence supplied with it.

This module is explanatory only. It does not recalculate the decision,
authorize an action, execute enforcement, infer malicious intent, or
create a universal security score.

## Interface

```python
from app.security_reason_codes import (
    generate_security_reason_codes,
    reason_codes_to_dicts,
)

reasons = generate_security_reason_codes(
    decision="BLOCK",
    evidence={
        "risk_score": 85,
        "anomaly_score": 0.72,
        "repeated_denial_score": 0.65,
    },
)

serialized_reasons = reason_codes_to_dicts(reasons)
```

The result is an ordered tuple of immutable `SecurityReasonCode`
records.

Each record includes:

- `code`: stable machine-readable reason identifier
- `message`: human-readable explanation
- `category`: decision or behavioral evidence
- `decision`: the supplied existing decision
- `source_key`: evidence key used, when applicable
- `observed_value`: normalized observed score, when applicable
- `threshold`: threshold that triggered the reason, when applicable

Missing signals are omitted rather than invented. Input evidence is
not mutated.

## Supported evidence

The implementation recognizes these signal families:

- Primary behavioral risk
- Behavioral anomaly
- Repeated authorization denials
- Cross-context correlation
- Multi-resolution analysis
- Context entropy
- Capability or resource spread

Aliases support existing evidence names, including `behavioral_risk_index`,
`behavioral_anomaly_score`, `denial_score`, `correlation_score`,
`resolution_risk`, `context_entropy`, and `behavioral_spread`.

## Validation and thresholds

Numeric evidence must be finite and within 0–100. Values between 0 and
1 inclusive are interpreted as normalized fractions and converted to
percentages.

Prototype thresholds are explicit and deterministic. They require
calibration and evaluation against Varynx experimental datasets before
being treated as production-ready thresholds.

## Architectural boundaries

- The decision must come from an existing decision layer.
- This module does not select or override a decision.
- This module does not execute runtime enforcement.
- This module does not infer malicious intent.
- This module does not duplicate evidence correlation.
- This module does not introduce a universal security score.
- The generated reason records can be serialized for audit or later
  platform integration.

## Testing

Run the focused tests:

```powershell
& "D:\aegisguard-env\Scripts\python.exe" -m pytest -q tests\test_day79_security_reason_codes.py
```

Then run the complete regression suite:

```powershell
& "D:\aegisguard-env\Scripts\python.exe" -m pytest -q
```

Day 79 should not be considered complete until the focused tests and
full regression suite have been run successfully in the actual Varynx
repository.