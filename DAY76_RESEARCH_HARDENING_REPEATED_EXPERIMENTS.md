\# Day 76 — Research Hardening: Repeated Experiments



\## Objective



Day 76 establishes a reproducible repeated-experiment protocol

using the existing Varynx research evaluation infrastructure.



\## Existing Infrastructure



\- app/experimental\_dataset.py

\- app/evaluation.py

\- app/repeated\_evaluation.py

\- tests/test\_repeated\_evaluation.py



\## Experiment Configuration



\- Scenarios: existing Varynx attack scenarios

\- Seeds: 42, 101, 202, 303, 404, 505, 606, 707, 808, 909

\- Events per scenario: 5

\- Threshold: 70

\- Repetitions: 10



\## Metrics



\- Accuracy

\- Precision

\- Recall

\- F1

\- Specificity

\- False-positive rate

\- False-negative rate



\## Baseline



Existing baseline detector.



\## Varynx Experimental Detector



Existing experimental AegisGuard/Varynx detector.



\## Results



\[PASTE ACTUAL RESULTS HERE]



\## Reproducibility



The same controlled scenario configuration and seed were

executed repeatedly to verify reproducibility.



\[INSERT ACTUAL OBSERVATION]



\## Consistency



\[INSERT ACTUAL CONSISTENCY RESULT]



\## Tests



\[INSERT ACTUAL TEST RESULT]



\## Limitations



These experiments use the project's synthetic experimental

dataset and controlled scenarios. Results should not be

interpreted as proof of universal real-world security

effectiveness.



\## Completion Status



Day 76 is complete after the repeated experiments,

reproducibility verification, tests, and full regression

validation have passed.

