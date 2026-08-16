# 🛡️ AegisGuard — AI Agent Firewall & Behavioral Security System

AegisGuard is a security-focused authorization and monitoring system designed to protect AI agents and automated workloads from unauthorized actions, excessive privilege usage, suspicious behavior, and anomalous activity.

The project combines **deterministic authorization**, **risk scoring**, **security audit logging**, **behavioral analytics**, and **ML-assisted anomaly detection** into a single security architecture.

---

## 🚀 Project Overview

Modern AI agents can interact with files, databases, APIs, cloud services, and other resources. Traditional access-control systems are often insufficient when an agent begins behaving abnormally after receiving legitimate authorization.

AegisGuard addresses this problem by introducing multiple security layers:

```text
                    AI AGENT REQUEST
                           │
                           ▼
                 ┌───────────────────┐
                 │ Request Validation │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ Authorization     │
                 │ Policy Engine     │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ Risk Evaluation   │
                 └─────────┬─────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
                  ALLOW          DENY
                    │
                    ▼
                 ┌───────────────────┐
                 │ Audit Logging     │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ Behavioral        │
                 │ Analytics         │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ Anomaly Detection │
                 │ / ML Signal       │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ Security          │
                 │ Dashboard         │
                 └───────────────────┘
```

---

# 🎯 Objectives

AegisGuard is designed to:

* Control what AI agents are allowed to access.
* Enforce task-specific authorization.
* Prevent unauthorized actions and resources.
* Calculate security risk for requests.
* Record security decisions in an audit trail.
* Detect repeated authorization failures.
* Identify suspicious agent behavior.
* Analyze historical agent activity.
* Detect behavioral anomalies.
* Provide a centralized security monitoring dashboard.
* Provide ML-assisted security signals without replacing deterministic authorization.

---

# 🏗️ Architecture

```text
┌──────────────────────────────────────────────┐
│                 AI AGENT                     │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│          AEGISGUARD SECURITY LAYER           │
│                                              │
│  ┌──────────────┐    ┌───────────────────┐   │
│  │ Authorization│───▶│ Risk Evaluation   │   │
│  │ Engine       │    │ Engine            │   │
│  └──────────────┘    └───────────────────┘   │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │ Security Audit Logging                 │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │ Behavioral Security Analytics          │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │ ML-Assisted Anomaly Detection         │  │
│  └────────────────────────────────────────┘  │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
             ┌─────────────────────┐
             │ SQLite Audit Store  │
             └──────────┬──────────┘
                        │
                        ▼
             ┌─────────────────────┐
             │ Streamlit Dashboard │
             └─────────────────────┘
```

---

# 🔐 Core Security Concepts

## 1. Authorization

AegisGuard evaluates requests using security context such as:

* Agent identity
* Task identity
* Requested action
* Requested resource
* Authorization policy
* Risk level

The authorization layer produces a decision such as:

```text
ALLOW
DENY
```

---

## 2. Risk Scoring

Each request can receive a numerical risk score.

Risk scoring considers security-relevant characteristics of the request and helps prioritize potentially dangerous activity.

Example:

```text
Risk Score: 82
Decision: DENY
Reason: High-risk unauthorized resource access
```

Risk scoring is treated as a **security signal**, not absolute proof of malicious intent.

---

## 3. Audit Logging

Security decisions are recorded for later investigation.

Example audit information:

```text
timestamp
agent_id
task_id
action
resource
decision
risk
reason
```

The audit trail enables:

* Incident investigation
* Behavioral analysis
* Security reporting
* Anomaly detection
* Historical activity analysis

---

# 🧠 Behavioral Security

AegisGuard analyzes agent behavior over multiple requests rather than evaluating every request in isolation.

Behavioral indicators include:

* Request volume
* Authorization denials
* Denial rate
* Average risk
* Maximum risk
* High-risk events
* Resource diversity
* Action diversity
* Task activity

Agents can be classified using behavioral rules such as:

```text
NORMAL
ELEVATED
SUSPICIOUS
```

This provides a second layer of security beyond individual authorization decisions.

---

# 📊 Security Dashboard

AegisGuard includes a Streamlit-based security monitoring dashboard.

Run the dashboard with:

```powershell
python -m streamlit run dashboard.py
```

Then open:

```text
http://localhost:8501
```

## Current Dashboard Features

### Security Metrics

* Total Events
* Allowed Requests
* Denied Requests
* Average Risk
* Critical Events
* Maximum Risk
* High-Risk Events
* Suspicious Agents

### Authorization Monitoring

* ALLOW vs DENY activity
* Authorization decision statistics

### Agent Monitoring

* Agent activity
* Suspicious agents
* Repeated authorization denials

### Risk Monitoring

* High-risk events
* Critical events
* Maximum risk
* Average risk

---

# 🗂️ Project Structure

```text
aegis-agent-firewall/
│
├── app/
│   ├── __init__.py
│   ├── authorization.py
│   ├── risk.py
│   ├── analytics.py
│   ├── behavior.py
│   └── ...
│
├── tests/
│   ├── ...
│   └── security tests
│
├── dashboard.py
│
├── README.md
├── requirements.txt
├── .gitignore
│
└── runtime files
    ├── aegisguard.db
    └── audit_logs.jsonl
```

Runtime-generated files such as databases, logs, environment files, Python cache files, and local development configuration should not be committed to the repository.

---

# 🧪 Security Testing

AegisGuard includes automated security tests covering multiple attack and abuse scenarios.

The test suite can be executed with:

```powershell
python -m pytest -q
```

Current Day 15 baseline:

```text
52 passed
```

The tests cover areas including:

* Authorization validation
* Unauthorized resource access
* Invalid actions
* Policy enforcement
* Risk evaluation
* Abuse scenarios
* Audit logging
* Security analytics
* Behavioral analysis

---

# 🛡️ Security Testing Philosophy

The project follows a defense-in-depth approach.

Instead of relying on a single security mechanism:

```text
Authorization
      +
Risk Scoring
      +
Audit Logging
      +
Behavioral Analytics
      +
Anomaly Detection
```

Each layer provides an additional security signal.

A machine-learning model is not treated as the final authority for authorization decisions.

---

# 📅 Development Progress

## Day 1 — Project Foundation

* Project initialized
* Security architecture defined
* Initial project structure created

## Day 2 — Authorization Foundation

* Basic authorization logic
* Agent/task security context
* Initial policy enforcement

## Day 3 — Policy and Resource Controls

* Action/resource authorization
* Policy-based access control
* Security validation

## Day 4–10 — Security Engine Development

* Authorization improvements
* Risk evaluation
* Security validation
* Attack-oriented testing
* Documentation and project hardening

## Day 11 — Attack & Abuse Security Tests

Implemented security tests for:

* Unauthorized actions
* Unauthorized resources
* Abuse scenarios
* Security boundary validation

## Day 12 — Authorization Abuse Testing

Extended authorization abuse testing and validated security behavior against additional misuse scenarios.

## Day 13 — Security Analytics

Implemented security analytics for:

* Total security events
* Authorization decisions
* Risk statistics
* Agent activity
* High-risk activity

## Day 14 — Behavioral Security Analytics

Implemented behavioral analysis including:

* Suspicious-agent detection
* Repeated-denial detection
* Behavioral classification
* Agent-level security analysis

## Day 15 — Security Monitoring Dashboard

Implemented a Streamlit security dashboard providing:

* Security KPIs
* Authorization monitoring
* Risk monitoring
* Agent activity
* Suspicious-agent monitoring
* Repeated-denial monitoring
* High-risk event monitoring

Baseline verification:

```text
52 tests passed
```

---

# 🔭 Day 16–20 Roadmap

## Day 16 — Advanced Security Monitoring

Planned improvements:

* Advanced security metrics
* Risk distribution
* Agent risk ranking
* Resource risk analysis
* Recent security event monitoring

## Day 17 — Security Investigation

Planned features:

* Agent filtering
* Decision filtering
* Risk filtering
* Action/resource filtering
* Event investigation
* Historical agent activity

## Day 18 — Behavioral Feature Engineering

Planned behavioral features:

```text
request_count
allow_count
deny_count
deny_rate
average_risk
maximum_risk
high_risk_count
unique_resources
unique_actions
unique_tasks
```

These features will form the foundation for anomaly detection.

## Day 19 — Anomaly Detection

Planned implementation:

```text
Behavioral Features
        ↓
Feature Matrix
        ↓
Anomaly Detection
        ↓
Anomaly Score
        ↓
Behavioral Classification
```

An unsupervised anomaly-detection approach such as Isolation Forest may be used where appropriate.

## Day 20 — ML-Assisted Security Monitoring

Planned integration:

```text
Authorization
      +
Risk Score
      +
Behavioral Rules
      +
ML Anomaly Signal
      ↓
Security Monitoring
```

The ML component will provide an additional security signal rather than replacing the deterministic authorization engine.

---

# 🧰 Technology Stack

| Technology   | Purpose                     |
| ------------ | --------------------------- |
| Python       | Core implementation         |
| SQLite       | Security audit data storage |
| Streamlit    | Security dashboard          |
| Pandas       | Data analysis               |
| Pytest       | Automated security testing  |
| Git          | Version control             |
| GitHub       | Source-code hosting         |
| Scikit-learn | Planned anomaly detection   |

---

# ▶️ Installation

## 1. Clone the repository

```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd aegis-agent-firewall
```

## 2. Create a virtual environment

```powershell
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```powershell
pip install -r requirements.txt
```

## 4. Run the test suite

```powershell
python -m pytest -q
```

## 5. Start the dashboard

```powershell
python -m streamlit run dashboard.py
```

---

# 🧪 Development Workflow

Each development day follows:

```text
Implement
   ↓
Run tests
   ↓
Verify application
   ↓
Inspect Git diff
   ↓
Commit
   ↓
Push to GitHub
```

Example:

```powershell
python -m pytest -q
python -m streamlit run dashboard.py

git status
git diff

git add .
git commit -m "Day XX: description"
git push
```

---

# 🔒 Files Excluded From Version Control

The following files should remain local:

```text
.env
aegisguard.db
audit_logs.jsonl
__pycache__/
.agents/
```

These may contain runtime data, environment-specific configuration, generated files, or local development artifacts.

---

# 📈 Future Development

Potential future extensions include:

* Real-time security monitoring
* Agent trust scoring
* Temporal behavior analysis
* Advanced anomaly detection
* Explainable anomaly scoring
* Alert generation
* Security event correlation
* SIEM integration
* Splunk integration
* Cloud security integration
* Containerized deployment
* API-based security gateway
* Multi-agent security policies
* Threat intelligence integration

---

# ⚠️ Security Design Principle

AegisGuard follows a defense-in-depth philosophy.

A high risk score or anomaly score does **not automatically prove malicious intent**.

The system should combine:

```text
Policy
  +
Authorization
  +
Risk
  +
Behavior
  +
Audit Evidence
  +
Anomaly Signals
```

to support security decisions and investigation.

---

# 📌 Project Status

**Current Stage:** Active Development

**Completed:** Days 1–15

**Current Focus:** Days 16–20

**Current Day 15 Test Baseline:**

```text
52 tests passed
```

**Dashboard:** Streamlit

**Database:** SQLite

**Primary Goal:**

> Build a practical security layer capable of enforcing authorization, recording security decisions, analyzing AI-agent behavior, and identifying potentially anomalous activity.

---

# 👩‍💻 Author

**Catherina Jercy**

Cyber Security Engineering Student

GitHub:

```text
https://github.com/catherinajercy2007
```

---

# 📜 Disclaimer

AegisGuard is an educational and research-oriented cybersecurity project.

It should be tested and reviewed carefully before being used to protect production systems or sensitive environments.
