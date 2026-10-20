# Day 47 — Dynamic Behavioral Trust Evaluation Adapter

## Objective

Connect the existing `DynamicBehavioralTrust` engine to the established
Varynx research evaluation pipeline.

The adapter provides a reproducible experimental interface without
duplicating trust calculations or modifying the trust engine.

## Problem

The Dynamic Behavioral Trust engine produces stateful `TrustSnapshot`
objects, while the existing research evaluation engine operates on
binary actual/predicted observations.

A research adapter is therefore required to translate:

    experimental event
            ↓
    trust evidence
            ↓
    DynamicBehavioralTrust
            ↓
    TrustSnapshot
            ↓
    low-trust prediction
            ↓
    existing classification metrics

## Scope

This task provides:

- trust sequence evaluation
- trust snapshot preservation
- explicit trust thresholding
- binary ground-truth conversion
- reuse of existing `calculate_metrics()`
- deterministic serialization
- validation of adapter inputs

## Architecture

```text
Experimental Event
       |
       v
Evidence Provider
       |
       v
DynamicBehavioralTrust.update()
       |
       v
TrustSnapshot
       |
       v
TrustEvaluationRecord
       |
       +----> Ground Truth
       |
       +----> Low Trust Prediction
       |
       v
app.evaluation.calculate_metrics()
       |
       v
Research Metrics