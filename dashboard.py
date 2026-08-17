from __future__ import annotations

import streamlit as st
import pandas as pd


# ============================================================
# CORE SECURITY ANALYTICS
# ============================================================

from app.analytics import (
    get_total_events,
    get_decision_counts,
    get_risk_summary,
    get_agent_activity,
    get_high_risk_events,
)


# ============================================================
# BEHAVIOR ANALYTICS
# ============================================================

from app.behavior import (
    get_suspicious_agents,
    get_repeated_denials,
)


# ============================================================
# INVESTIGATION
# ============================================================

from app.investigation import (
    get_investigation_events,
    get_investigation_filter_options,
)


# ============================================================
# BEHAVIORAL FEATURES
# ============================================================

from app.features import (
    get_behavioral_features,
    get_behavior_feature_names,
)


# ============================================================
# ANOMALY DETECTION
# ============================================================

from app.anomaly import (
    get_behavioral_anomalies,
    get_anomaly_summary,
)


# ============================================================
# DAY 21 — CONTROLLED SCENARIOS
# ============================================================

from app.scenarios import (
    BENIGN,
    SUSPICIOUS,
    MALICIOUS,
    get_scenario_catalog,
    get_scenarios,
    get_scenario_summary,
)


# ============================================================
# DAY 22 — ATTACK SCENARIOS
# ============================================================

from app.attack_scenarios import (
    ATTACK_SCENARIO_TYPES,
    get_attack_scenarios,
    get_attack_scenarios_by_type,
    get_attack_scenario_summary,
)


# ============================================================
# DAY 23 — EXPERIMENTAL DATASET
# ============================================================

from app.experimental_dataset import (
    DATASET_VERSION,
    generate_experimental_dataset,
    summarize_dataset,
    get_label_distribution,
    dataset_to_csv,
    dataset_to_jsonl,
    validate_dataset,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AegisGuard Research SOC",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SESSION STATE
# ============================================================

if "day23_dataset" not in st.session_state:
    st.session_state.day23_dataset = None

if "day23_summary" not in st.session_state:
    st.session_state.day23_summary = None

if "day23_validation" not in st.session_state:
    st.session_state.day23_validation = None

if "investigation_results" not in st.session_state:
    st.session_state.investigation_results = []

if "investigation_executed" not in st.session_state:
    st.session_state.investigation_executed = False


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_int(value, default=0):

    try:
        return int(value)

    except (TypeError, ValueError):
        return default


def safe_float(value, default=0.0):

    try:
        return float(value)

    except (TypeError, ValueError):
        return default


def calculate_binary_metrics(
    actual_positive,
    actual_negative,
    predicted_positive,
    predicted_negative,
):
    """
    Calculate standard binary classification metrics.

    Positive class:
        MALICIOUS

    Negative class:
        NON-MALICIOUS
        (BENIGN + SUSPICIOUS)
    """

    tp = sum(
        1
        for actual, predicted in zip(
            actual_positive,
            predicted_positive,
        )
        if actual and predicted
    )

    tn = sum(
        1
        for actual, predicted in zip(
            actual_negative,
            predicted_negative,
        )
        if actual and predicted
    )

    fp = sum(
        1
        for actual, predicted in zip(
            actual_negative,
            predicted_positive,
        )
        if actual and predicted
    )

    fn = sum(
        1
        for actual, predicted in zip(
            actual_positive,
            predicted_negative,
        )
        if actual and predicted
    )

    total = (
        tp + tn + fp + fn
    )

    accuracy = (
        (tp + tn) / total
        if total
        else 0.0
    )

    precision = (
        tp / (tp + fp)
        if (tp + fp)
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn)
        else 0.0
    )

    specificity = (
        tn / (tn + fp)
        if (tn + fp)
        else 0.0
    )

    f1 = (
        2
        * precision
        * recall
        / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    false_positive_rate = (
        fp / (fp + tn)
        if (fp + tn)
        else 0.0
    )

    false_negative_rate = (
        fn / (fn + tp)
        if (fn + tp)
        else 0.0
    )

    return {
        "true_positive": tp,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,
        "accuracy": round(
            accuracy,
            4,
        ),
        "precision": round(
            precision,
            4,
        ),
        "recall": round(
            recall,
            4,
        ),
        "specificity": round(
            specificity,
            4,
        ),
        "f1_score": round(
            f1,
            4,
        ),
        "false_positive_rate": round(
            false_positive_rate,
            4,
        ),
        "false_negative_rate": round(
            false_negative_rate,
            4,
        ),
    }


def evaluate_dataset(
    dataset,
    threshold,
    prediction_mode,
):
    """
    Evaluate AegisGuard's synthetic detection signal.

    Actual positive:
        ground_truth == MALICIOUS

    Predicted positive:
        depends on prediction_mode
    """

    actual_positive = []
    actual_negative = []
    predicted_positive = []
    predicted_negative = []

    for event in dataset:

        ground_truth = str(
            event.get(
                "ground_truth",
                "",
            )
        ).upper()

        risk_score = safe_float(
            event.get(
                "risk_score",
                0,
            )
        )

        decision = str(
            event.get(
                "decision",
                "",
            )
        ).upper()

        if prediction_mode == "Risk Threshold":

            predicted_attack = (
                risk_score >= threshold
            )

        elif prediction_mode == "Authorization Decision":

            predicted_attack = (
                decision == "DENY"
            )

        else:

            predicted_attack = (
                risk_score >= threshold
                or decision == "DENY"
            )

        actual_attack = (
            ground_truth == "MALICIOUS"
        )

        actual_positive.append(
            actual_attack
        )

        actual_negative.append(
            not actual_attack
        )

        predicted_positive.append(
            predicted_attack
        )

        predicted_negative.append(
            not predicted_attack
        )

    return calculate_binary_metrics(
        actual_positive,
        actual_negative,
        predicted_positive,
        predicted_negative,
    )


def build_threshold_evaluation(
    dataset,
    thresholds,
):
    """
    Evaluate detection performance across
    multiple risk thresholds.
    """

    rows = []

    for threshold in thresholds:

        metrics = evaluate_dataset(
            dataset,
            threshold,
            "Risk Threshold",
        )

        rows.append(
            {
                "Threshold":
                    threshold,

                "Accuracy":
                    metrics["accuracy"],

                "Precision":
                    metrics["precision"],

                "Recall":
                    metrics["recall"],

                "F1":
                    metrics["f1_score"],

                "Specificity":
                    metrics["specificity"],

                "FPR":
                    metrics["false_positive_rate"],

                "FNR":
                    metrics["false_negative_rate"],
            }
        )

    return pd.DataFrame(
        rows
    )


# ============================================================
# HEADER
# ============================================================

st.title(
    "🛡️ AegisGuard Security Research Center"
)

st.caption(
    "Behavior-aware authorization, security intelligence, "
    "controlled experimentation and quantitative evaluation"
)

st.divider()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "Research Control Plane"
    )

    st.success(
        "AegisGuard engine online"
    )

    st.divider()

    st.subheader(
        "Research Modules"
    )

    show_overview = st.checkbox(
        "Security Overview",
        value=True,
    )

    show_intelligence = st.checkbox(
        "Integrated Intelligence",
        value=True,
    )

    show_day21 = st.checkbox(
        "Day 21 Scenario Lab",
        value=True,
    )

    show_day22 = st.checkbox(
        "Day 22 Attack Research",
        value=True,
    )

    show_day23 = st.checkbox(
        "Day 23 Dataset Lab",
        value=True,
    )

    show_day24 = st.checkbox(
        "Day 24 Evaluation Lab",
        value=True,
    )

    show_anomalies = st.checkbox(
        "Anomaly Detection",
        value=True,
    )

    show_features = st.checkbox(
        "Behavioral Features",
        value=True,
    )

    show_investigation = st.checkbox(
        "Investigation",
        value=True,
    )

    show_agents = st.checkbox(
        "Agent Intelligence",
        value=True,
    )

    show_high_risk = st.checkbox(
        "High-Risk Events",
        value=True,
    )

    st.divider()

    st.subheader(
        "Research Progress"
    )

    st.markdown(
        """
        **Days 1–15**
        Security Foundation

        ↓

        **Day 16**
        Advanced SOC

        ↓

        **Day 17**
        Investigation

        ↓

        **Day 18**
        Behavioral Features

        ↓

        **Day 19**
        Anomaly Detection

        ↓

        **Day 20**
        Integrated Intelligence

        ↓

        **Day 21**
        Controlled Scenarios

        ↓

        **Day 22**
        Attack Taxonomy

        ↓

        **Day 23**
        Experimental Dataset

        ↓

        **Day 24**
        Quantitative Evaluation
        """
    )

    st.divider()

    st.caption(
        f"Dataset: {DATASET_VERSION}"
    )

    st.caption(
        "AegisGuard Research Prototype"
    )


# ============================================================
# LOAD SECURITY TELEMETRY
# ============================================================

try:

    total_events = (
        get_total_events()
    )

    decisions = (
        get_decision_counts()
    )

    risk = (
        get_risk_summary()
    )

    agents = (
        get_agent_activity()
    )

    high_risk_events = (
        get_high_risk_events()
    )

    suspicious_agents = (
        get_suspicious_agents()
    )

    repeated_denials = (
        get_repeated_denials()
    )

except Exception as error:

    st.error(
        f"Unable to load security data: {error}"
    )

    st.stop()


# ============================================================
# BEHAVIORAL FEATURES
# ============================================================

try:

    behavioral_features = (
        get_behavioral_features()
    )

except Exception:

    behavioral_features = []


# ============================================================
# ANOMALIES
# ============================================================

try:

    anomaly_results = (
        get_behavioral_anomalies()
    )

    anomaly_summary = (
        get_anomaly_summary()
    )

except Exception:

    anomaly_results = []

    anomaly_summary = {
        "agents_analyzed": 0,
        "high_anomaly_agents": 0,
        "medium_anomaly_agents": 0,
        "low_anomaly_agents": 0,
        "normal_agents": 0,
    }


# ============================================================
# SECURITY OVERVIEW
# ============================================================

if show_overview:

    st.header(
        "📊 Security Overview"
    )

    c1, c2, c3, c4, c5 = (
        st.columns(5)
    )

    with c1:

        st.metric(
            "Total Events",
            total_events,
        )

    with c2:

        st.metric(
            "Allowed",
            decisions.get(
                "ALLOW",
                0,
            ),
        )

    with c3:

        st.metric(
            "Denied",
            decisions.get(
                "DENY",
                0,
            ),
        )

    with c4:

        st.metric(
            "Average Risk",
            risk.get(
                "average_risk",
                0,
            ),
        )

    with c5:

        st.metric(
            "Critical",
            risk.get(
                "critical_events",
                0,
            ),
        )

    r1, r2, r3, r4 = (
        st.columns(4)
    )

    with r1:

        st.metric(
            "Maximum Risk",
            risk.get(
                "maximum_risk",
                0,
            ),
        )

    with r2:

        st.metric(
            "High-Risk Events",
            risk.get(
                "high_risk_events",
                0,
            ),
        )

    with r3:

        st.metric(
            "Suspicious Agents",
            len(
                suspicious_agents
            ),
        )

    with r4:

        st.metric(
            "Repeated Denial Patterns",
            len(
                repeated_denials
            ),
        )

    decision_df = pd.DataFrame(
        {
            "Decision":
                list(
                    decisions.keys()
                ),

            "Count":
                list(
                    decisions.values()
                ),
        }
    )

    if not decision_df.empty:

        st.subheader(
            "Authorization Decisions"
        )

        st.bar_chart(
            decision_df.set_index(
                "Decision"
            ),
            width="stretch",
        )


# ============================================================
# INTEGRATED INTELLIGENCE
# ============================================================

if show_intelligence:

    st.divider()

    st.header(
        "🧠 Integrated Security Intelligence"
    )

    intelligence_records = []

    anomaly_lookup = {
        str(
            item.get(
                "agent_id",
                "",
            )
        ): item
        for item in anomaly_results
    }

    suspicious_lookup = {
        str(
            item.get(
                "agent_id",
                "",
            )
        )
        for item in suspicious_agents
    }

    for agent in agents:

        agent_id = str(
            agent.get(
                "agent_id",
                "",
            )
        )

        total = safe_int(
            agent.get(
                "total_requests",
                0,
            )
        )

        denied = safe_int(
            agent.get(
                "denied_requests",
                0,
            )
        )

        max_risk = safe_float(
            agent.get(
                "maximum_risk",
                0,
            )
        )

        denial_rate = (
            denied / total
            if total
            else 0
        )

        anomaly = (
            anomaly_lookup.get(
                agent_id,
                {},
            )
        )

        anomaly_score = safe_float(
            anomaly.get(
                "anomaly_score",
                0,
            )
        )

        suspicious_signal = (
            1
            if agent_id
            in suspicious_lookup
            else 0
        )

        intelligence_score = (
            max_risk * 0.40
            + denial_rate * 100 * 0.30
            + min(
                anomaly_score * 20,
                100,
            ) * 0.20
            + suspicious_signal * 100 * 0.10
        )

        intelligence_score = min(
            100,
            intelligence_score,
        )

        if intelligence_score >= 80:

            priority = "CRITICAL"

        elif intelligence_score >= 60:

            priority = "HIGH"

        elif intelligence_score >= 35:

            priority = "MEDIUM"

        else:

            priority = "LOW"

        intelligence_records.append(
            {
                "agent_id":
                    agent_id,

                "total_requests":
                    total,

                "denied_requests":
                    denied,

                "denial_rate":
                    round(
                        denial_rate * 100,
                        2,
                    ),

                "maximum_risk":
                    max_risk,

                "anomaly_score":
                    anomaly_score,

                "intelligence_score":
                    round(
                        intelligence_score,
                        2,
                    ),

                "priority":
                    priority,
            }
        )

    intelligence_df = pd.DataFrame(
        intelligence_records
    )

    if not intelligence_df.empty:

        st.dataframe(
            intelligence_df.sort_values(
                "intelligence_score",
                ascending=False,
            ),
            width="stretch",
            hide_index=True,
        )


# ============================================================
# DAY 21 — SCENARIO LAB
# ============================================================

if show_day21:

    st.divider()

    st.header(
        "🧪 Day 21 — Controlled Scenario Lab"
    )

    try:

        scenario_summary = (
            get_scenario_summary()
        )

    except Exception:

        scenario_summary = {}

    s1, s2, s3, s4 = (
        st.columns(4)
    )

    with s1:

        st.metric(
            "Total",
            scenario_summary.get(
                "total",
                0,
            ),
        )

    with s2:

        st.metric(
            "Benign",
            scenario_summary.get(
                "benign",
                0,
            ),
        )

    with s3:

        st.metric(
            "Suspicious",
            scenario_summary.get(
                "suspicious",
                0,
            ),
        )

    with s4:

        st.metric(
            "Malicious",
            scenario_summary.get(
                "malicious",
                0,
            ),
        )

    scenario_class = st.selectbox(
        "Scenario Class",
        [
            "ALL",
            BENIGN,
            SUSPICIOUS,
            MALICIOUS,
        ],
        key="day21_class",
    )

    try:

        if scenario_class == "ALL":

            scenarios = (
                get_scenario_catalog()
            )

        else:

            scenarios = (
                get_scenarios(
                    scenario_class
                )
            )

    except Exception:

        scenarios = []

    if scenarios:

        st.dataframe(
            pd.DataFrame(
                scenarios
            ),
            width="stretch",
            hide_index=True,
        )


# ============================================================
# DAY 22 — ATTACK RESEARCH
# ============================================================

if show_day22:

    st.divider()

    st.header(
        "⚔️ Day 22 — Attack Scenario Research"
    )

    attack_summary = (
        get_attack_scenario_summary()
    )

    a1, a2, a3, a4 = (
        st.columns(4)
    )

    with a1:

        st.metric(
            "Attack Scenarios",
            attack_summary.get(
                "total",
                0,
            ),
        )

    with a2:

        st.metric(
            "Malicious",
            attack_summary.get(
                "malicious",
                0,
            ),
        )

    with a3:

        st.metric(
            "Benign",
            attack_summary.get(
                "benign",
                0,
            ),
        )

    with a4:

        st.metric(
            "Critical",
            attack_summary.get(
                "critical",
                0,
            ),
        )

    attack_type = st.selectbox(
        "Attack Type",
        [
            "ALL"
        ]
        + list(
            ATTACK_SCENARIO_TYPES
        ),
        key="day22_attack_type",
    )

    if attack_type == "ALL":

        attacks = (
            get_attack_scenarios()
        )

    else:

        attacks = (
            get_attack_scenarios_by_type(
                attack_type
            )
        )

    if attacks:

        st.dataframe(
            pd.DataFrame(
                attacks
            ),
            width="stretch",
            hide_index=True,
        )


# ============================================================
# DAY 23 — DATASET LAB
# ============================================================

if show_day23:

    st.divider()

    st.header(
        "🧬 Day 23 — Experimental Dataset Lab"
    )

    st.caption(
        "Generate a reproducible dataset from the "
        "controlled security scenario catalog."
    )

    d1, d2, d3 = (
        st.columns(3)
    )

    with d1:

        events_per_scenario = st.number_input(
            "Events per Scenario",
            min_value=1,
            max_value=100,
            value=5,
            step=1,
            key="day23_events",
        )

    with d2:

        experiment_seed = st.number_input(
            "Experiment Seed",
            min_value=0,
            max_value=999999,
            value=42,
            step=1,
            key="day23_seed",
        )

    with d3:

        st.metric(
            "Dataset Version",
            DATASET_VERSION,
        )

    if st.button(
        "🧬 Generate Dataset",
        type="primary",
        key="generate_day23_dataset",
    ):

        try:

            source_scenarios = (
                get_attack_scenarios()
            )

            dataset = (
                generate_experimental_dataset(
                    scenarios=source_scenarios,
                    events_per_scenario=int(
                        events_per_scenario
                    ),
                    seed=int(
                        experiment_seed
                    ),
                )
            )

            st.session_state.day23_dataset = (
                dataset
            )

            st.session_state.day23_summary = (
                summarize_dataset(
                    dataset
                )
            )

            st.session_state.day23_validation = (
                validate_dataset(
                    dataset
                )
            )

            st.success(
                f"Generated {len(dataset)} events."
            )

        except Exception as error:

            st.error(
                f"Dataset generation failed: {error}"
            )

    dataset = (
        st.session_state.day23_dataset
    )

    if dataset:

        summary = (
            st.session_state.day23_summary
            or {}
        )

        validation = (
            st.session_state.day23_validation
            or {}
        )

        m1, m2, m3, m4, m5 = (
            st.columns(5)
        )

        with m1:

            st.metric(
                "Events",
                summary.get(
                    "total_events",
                    0,
                ),
            )

        with m2:

            st.metric(
                "Benign",
                summary.get(
                    "benign_events",
                    0,
                ),
            )

        with m3:

            st.metric(
                "Suspicious",
                summary.get(
                    "suspicious_events",
                    0,
                ),
            )

        with m4:

            st.metric(
                "Malicious",
                summary.get(
                    "malicious_events",
                    0,
                ),
            )

        with m5:

            st.metric(
                "Avg Risk",
                summary.get(
                    "average_risk",
                    0,
                ),
            )

        if validation.get(
            "valid",
            False,
        ):

            st.success(
                "Dataset integrity validation passed."
            )

        else:

            st.error(
                "Dataset integrity validation failed."
            )

        dataset_df = pd.DataFrame(
            dataset
        )

        st.subheader(
            "Dataset Preview"
        )

        st.dataframe(
            dataset_df.head(25),
            width="stretch",
            hide_index=True,
        )

        csv_data = dataset_to_csv(
            dataset
        )

        jsonl_data = dataset_to_jsonl(
            dataset
        )

        dc1, dc2 = (
            st.columns(2)
        )

        with dc1:

            st.download_button(
                "⬇️ Download CSV",
                data=csv_data,
                file_name=(
                    "aegisguard_day23_dataset.csv"
                ),
                mime="text/csv",
                use_container_width=True,
                key="download_day23_csv",
            )

        with dc2:

            st.download_button(
                "⬇️ Download JSONL",
                data=jsonl_data,
                file_name=(
                    "aegisguard_day23_dataset.jsonl"
                ),
                mime="application/json",
                use_container_width=True,
                key="download_day23_jsonl",
            )


# ============================================================
# DAY 24 — QUANTITATIVE EVALUATION LAB
# ============================================================

if show_day24:

    st.divider()

    st.header(
        "📈 Day 24 — Quantitative Detection Evaluation"
    )

    st.caption(
        "Controlled evaluation of AegisGuard detection "
        "performance against ground-truth experimental events."
    )

    # --------------------------------------------------------
    # RESEARCH DEFINITION
    # --------------------------------------------------------

    with st.expander(
        "🔬 Evaluation Methodology",
        expanded=True,
    ):

        st.markdown(
            """
            ### Evaluation target

            **Positive class:** `MALICIOUS`

            **Negative class:** `BENIGN + SUSPICIOUS`

            The evaluation compares AegisGuard's predicted
            security signal against the known ground-truth
            label in the synthetic experimental dataset.

            ### Metrics

            **Accuracy**

            Overall proportion of correctly classified events.

            **Precision**

            Proportion of predicted malicious events that
            were actually malicious.

            **Recall / Detection Rate**

            Proportion of actual malicious events detected.

            **Specificity**

            Proportion of non-malicious events correctly
            identified as non-malicious.

            **F1 Score**

            Harmonic mean of precision and recall.

            **False Positive Rate**

            Proportion of non-malicious events incorrectly
            classified as malicious.

            **False Negative Rate**

            Proportion of malicious events missed by the
            detector.
            """
        )

    # --------------------------------------------------------
    # DATASET CHECK
    # --------------------------------------------------------

    evaluation_dataset = (
        st.session_state.day23_dataset
    )

    if not evaluation_dataset:

        st.warning(
            "No Day 23 dataset is currently loaded."
        )

        st.info(
            "Generate the Day 23 experimental dataset "
            "above before running the Day 24 evaluation."
        )

    else:

        evaluation_df = pd.DataFrame(
            evaluation_dataset
        )

        st.success(
            f"Evaluation dataset loaded: "
            f"{len(evaluation_dataset)} events"
        )

        # ----------------------------------------------------
        # CLASS DISTRIBUTION
        # ----------------------------------------------------

        distribution = (
            get_label_distribution(
                evaluation_dataset
            )
        )

        st.subheader(
            "Ground-Truth Class Distribution"
        )

        class_df = pd.DataFrame(
            {
                "Class": [
                    "BENIGN",
                    "SUSPICIOUS",
                    "MALICIOUS",
                ],

                "Count": [
                    distribution.get(
                        "BENIGN",
                        0,
                    ),

                    distribution.get(
                        "SUSPICIOUS",
                        0,
                    ),

                    distribution.get(
                        "MALICIOUS",
                        0,
                    ),
                ],
            }
        )

        cc1, cc2 = (
            st.columns(2)
        )

        with cc1:

            st.bar_chart(
                class_df.set_index(
                    "Class"
                ),
                width="stretch",
            )

        with cc2:

            st.dataframe(
                class_df,
                width="stretch",
                hide_index=True,
            )

        # ----------------------------------------------------
        # RESEARCH WARNING
        # ----------------------------------------------------

        total_classes = sum(
            distribution.values()
        )

        if total_classes:

            malicious_ratio = (
                distribution.get(
                    "MALICIOUS",
                    0,
                )
                / total_classes
            )

            suspicious_ratio = (
                distribution.get(
                    "SUSPICIOUS",
                    0,
                )
                / total_classes
            )

            if (
                malicious_ratio > 0.70
                or suspicious_ratio == 0
            ):

                st.warning(
                    "Dataset imbalance detected. "
                    "Current results should be interpreted "
                    "as controlled prototype measurements, "
                    "not generalized production performance."
                )

        # ----------------------------------------------------
        # EVALUATION CONTROLS
        # ----------------------------------------------------

        st.subheader(
            "Evaluation Configuration"
        )

        e1, e2 = (
            st.columns(2)
        )

        with e1:

            prediction_mode = st.selectbox(
                "Prediction Signal",
                [
                    "Risk Threshold",
                    "Authorization Decision",
                    "Risk OR Authorization",
                ],
                key="day24_prediction_mode",
            )

        with e2:

            risk_threshold = st.slider(
                "Risk Detection Threshold",
                min_value=0,
                max_value=100,
                value=70,
                step=5,
                key="day24_risk_threshold",
            )

        # ----------------------------------------------------
        # CALCULATE METRICS
        # ----------------------------------------------------

        metrics = evaluate_dataset(
            evaluation_dataset,
            risk_threshold,
            prediction_mode,
        )

        st.subheader(
            "Detection Performance"
        )

        p1, p2, p3, p4, p5 = (
            st.columns(5)
        )

        with p1:

            st.metric(
                "Accuracy",
                f"{metrics['accuracy'] * 100:.2f}%",
            )

        with p2:

            st.metric(
                "Precision",
                f"{metrics['precision'] * 100:.2f}%",
            )

        with p3:

            st.metric(
                "Recall",
                f"{metrics['recall'] * 100:.2f}%",
            )

        with p4:

            st.metric(
                "F1 Score",
                f"{metrics['f1_score'] * 100:.2f}%",
            )

        with p5:

            st.metric(
                "Specificity",
                f"{metrics['specificity'] * 100:.2f}%",
            )

        # ----------------------------------------------------
        # ERROR METRICS
        # ----------------------------------------------------

        f1, f2, f3 = (
            st.columns(3)
        )

        with f1:

            st.metric(
                "False Positive Rate",
                f"{metrics['false_positive_rate'] * 100:.2f}%",
            )

        with f2:

            st.metric(
                "False Negative Rate",
                f"{metrics['false_negative_rate'] * 100:.2f}%",
            )

        with f3:

            st.metric(
                "Detection Rate",
                f"{metrics['recall'] * 100:.2f}%",
            )

        # ----------------------------------------------------
        # CONFUSION MATRIX
        # ----------------------------------------------------

        st.subheader(
            "Confusion Matrix"
        )

        cm_df = pd.DataFrame(
            [
                [
                    metrics["true_negative"],
                    metrics["false_positive"],
                ],

                [
                    metrics["false_negative"],
                    metrics["true_positive"],
                ],
            ],

            index=[
                "Actual Non-Malicious",
                "Actual Malicious",
            ],

            columns=[
                "Predicted Non-Malicious",
                "Predicted Malicious",
            ],
        )

        cm1, cm2 = (
            st.columns(2)
        )

        with cm1:

            st.dataframe(
                cm_df,
                width="stretch",
            )

        with cm2:

            st.metric(
                "True Positives",
                metrics["true_positive"],
            )

            st.metric(
                "True Negatives",
                metrics["true_negative"],
            )

            st.metric(
                "False Positives",
                metrics["false_positive"],
            )

            st.metric(
                "False Negatives",
                metrics["false_negative"],
            )

        # ----------------------------------------------------
        # THRESHOLD ANALYSIS
        # ----------------------------------------------------

        st.divider()

        st.subheader(
            "📐 Risk Threshold Sensitivity Analysis"
        )

        st.caption(
            "Measure how detection performance changes "
            "as the risk threshold changes."
        )

        thresholds = list(
            range(
                0,
                101,
                5,
            )
        )

        threshold_df = (
            build_threshold_evaluation(
                evaluation_dataset,
                thresholds,
            )
        )

        st.dataframe(
            threshold_df,
            width="stretch",
            hide_index=True,
        )

        threshold_chart_df = (
            threshold_df[
                [
                    "Threshold",
                    "Precision",
                    "Recall",
                    "F1",
                    "Specificity",
                ]
            ]
            .set_index(
                "Threshold"
            )
        )

        st.line_chart(
            threshold_chart_df,
            width="stretch",
        )

        # ----------------------------------------------------
        # BEST F1 THRESHOLD
        # ----------------------------------------------------

        if not threshold_df.empty:

            best_row = (
                threshold_df.sort_values(
                    "F1",
                    ascending=False,
                )
                .iloc[0]
            )

            st.subheader(
                "Recommended Experimental Threshold"
            )

            b1, b2, b3 = (
                st.columns(3)
            )

            with b1:

                st.metric(
                    "Best F1 Threshold",
                    int(
                        best_row[
                            "Threshold"
                        ]
                    ),
                )

            with b2:

                st.metric(
                    "Best F1",
                    f"{best_row['F1'] * 100:.2f}%",
                )

            with b3:

                st.metric(
                    "Recall at Best F1",
                    f"{best_row['Recall'] * 100:.2f}%",
                )

            st.info(
                "This threshold is selected only by maximum "
                "F1 on the current synthetic dataset. "
                "It must not be treated as a production "
                "security threshold without independent "
                "validation data."
            )

        # ----------------------------------------------------
        # EVENT-LEVEL PREDICTIONS
        # ----------------------------------------------------

        st.subheader(
            "Event-Level Evaluation"
        )

        evaluated_rows = []

        for event in evaluation_dataset:

            risk_score = safe_float(
                event.get(
                    "risk_score",
                    0,
                )
            )

            decision = str(
                event.get(
                    "decision",
                    "",
                )
            ).upper()

            ground_truth = str(
                event.get(
                    "ground_truth",
                    "",
                )
            ).upper()

            if prediction_mode == "Risk Threshold":

                predicted = (
                    risk_score
                    >= risk_threshold
                )

            elif prediction_mode == "Authorization Decision":

                predicted = (
                    decision == "DENY"
                )

            else:

                predicted = (
                    risk_score
                    >= risk_threshold
                    or decision == "DENY"
                )

            actual = (
                ground_truth == "MALICIOUS"
            )

            if actual and predicted:

                classification = "TP"

            elif actual and not predicted:

                classification = "FN"

            elif not actual and predicted:

                classification = "FP"

            else:

                classification = "TN"

            evaluated_rows.append(
                {
                    "event_id":
                        event.get(
                            "event_id",
                            "",
                        ),

                    "scenario_id":
                        event.get(
                            "scenario_id",
                            "",
                        ),

                    "ground_truth":
                        ground_truth,

                    "risk_score":
                        risk_score,

                    "decision":
                        decision,

                    "predicted_malicious":
                        predicted,

                    "classification":
                        classification,
                }
            )

        evaluated_df = pd.DataFrame(
            evaluated_rows
        )

        classification_filter = st.selectbox(
            "Evaluation Result",
            [
                "ALL",
                "TP",
                "TN",
                "FP",
                "FN",
            ],
            key="day24_result_filter",
        )

        display_df = (
            evaluated_df
        )

        if classification_filter != "ALL":

            display_df = evaluated_df[
                evaluated_df[
                    "classification"
                ]
                == classification_filter
            ]

        st.write(
            f"Matching events: "
            f"**{len(display_df)}**"
        )

        st.dataframe(
            display_df,
            width="stretch",
            hide_index=True,
        )

        # ----------------------------------------------------
        # EXPORT EVALUATION RESULTS
        # ----------------------------------------------------

        evaluation_csv = (
            evaluated_df.to_csv(
                index=False
            )
        )

        st.download_button(
            "⬇️ Download Evaluation Results",
            data=evaluation_csv,
            file_name=(
                "aegisguard_day24_evaluation_results.csv"
            ),
            mime="text/csv",
            use_container_width=True,
            key="day24_download",
        )

        # ----------------------------------------------------
        # RESEARCH METADATA
        # ----------------------------------------------------

        st.subheader(
            "🔬 Experimental Metadata"
        )

        metadata_df = pd.DataFrame(
            {
                "Parameter": [
                    "Dataset Version",
                    "Evaluation Target",
                    "Prediction Mode",
                    "Risk Threshold",
                    "Dataset Size",
                    "Positive Class",
                    "Negative Class",
                ],

                "Value": [
                    DATASET_VERSION,
                    "Malicious Detection",
                    prediction_mode,
                    risk_threshold,
                    len(
                        evaluation_dataset
                    ),
                    "MALICIOUS",
                    "BENIGN + SUSPICIOUS",
                ],
            }
        )

        st.dataframe(
            metadata_df,
            width="stretch",
            hide_index=True,
        )

        # ----------------------------------------------------
        # RESEARCH INTERPRETATION
        # ----------------------------------------------------

        st.subheader(
            "🧪 Interpretation"
        )

        if metrics["false_positive_rate"] > 0:

            st.warning(
                "False positives are present. This means "
                "the current detector is classifying at least "
                "some non-malicious events as malicious."
            )

        else:

            st.success(
                "No false positives were observed in this "
                "controlled experiment."
            )

        if metrics["false_negative_rate"] > 0:

            st.warning(
                "False negatives are present. Some malicious "
                "events were not detected by the current "
                "prediction rule."
            )

        else:

            st.success(
                "No false negatives were observed in this "
                "controlled experiment."
            )

        st.info(
            "These measurements describe this experimental "
            "dataset only. They are not evidence of real-world "
            "generalization."
        )


# ============================================================
# ANOMALY DETECTION
# ============================================================

if show_anomalies:

    st.divider()

    st.header(
        "🚨 Behavioral Anomaly Detection"
    )

    ac1, ac2, ac3, ac4 = (
        st.columns(4)
    )

    with ac1:

        st.metric(
            "Agents Analyzed",
            anomaly_summary.get(
                "agents_analyzed",
                0,
            ),
        )

    with ac2:

        st.metric(
            "High Anomaly",
            anomaly_summary.get(
                "high_anomaly_agents",
                0,
            ),
        )

    with ac3:

        st.metric(
            "Medium Anomaly",
            anomaly_summary.get(
                "medium_anomaly_agents",
                0,
            ),
        )

    with ac4:

        st.metric(
            "Normal",
            anomaly_summary.get(
                "normal_agents",
                0,
            ),
        )

    if anomaly_results:

        anomaly_df = pd.DataFrame(
            anomaly_results
        )

        st.dataframe(
            anomaly_df,
            width="stretch",
            hide_index=True,
        )

    else:

        st.info(
            "No anomaly records available."
        )


# ============================================================
# BEHAVIORAL FEATURES
# ============================================================

if show_features:

    st.divider()

    st.header(
        "🧠 Behavioral Feature Analytics"
    )

    if behavioral_features:

        behavior_df = pd.DataFrame(
            behavioral_features
        )

        st.dataframe(
            behavior_df,
            width="stretch",
            hide_index=True,
        )

        try:

            feature_names = (
                get_behavior_feature_names()
            )

        except Exception:

            feature_names = [
                column
                for column
                in behavior_df.columns
                if column != "agent_id"
            ]

        available_features = [
            feature
            for feature
            in feature_names
            if feature
            in behavior_df.columns
        ]

        if available_features:

            selected_feature = st.selectbox(
                "Feature",
                available_features,
                key="feature_selector",
            )

            if (
                "agent_id"
                in behavior_df.columns
            ):

                st.bar_chart(
                    behavior_df[
                        [
                            "agent_id",
                            selected_feature,
                        ]
                    ]
                    .set_index(
                        "agent_id"
                    ),
                    width="stretch",
                )

    else:

        st.info(
            "No behavioral features available."
        )


# ============================================================
# INVESTIGATION
# ============================================================

if show_investigation:

    st.divider()

    st.header(
        "🔎 Security Investigation Engine"
    )

    try:

        filter_options = (
            get_investigation_filter_options()
        )

    except Exception:

        filter_options = {
            "agents": [],
            "actions": [],
        }

    ic1, ic2, ic3 = (
        st.columns(3)
    )

    with ic1:

        selected_agent = st.selectbox(
            "Agent",
            [
                "ALL"
            ]
            + filter_options.get(
                "agents",
                [],
            ),
            key="investigation_agent",
        )

    with ic2:

        selected_action = st.selectbox(
            "Action",
            [
                "ALL"
            ]
            + filter_options.get(
                "actions",
                [],
            ),
            key="investigation_action",
        )

    with ic3:

        selected_decision = st.selectbox(
            "Decision",
            [
                "ALL",
                "ALLOW",
                "DENY",
            ],
            key="investigation_decision",
        )

    if st.button(
        "🔍 Investigate",
        type="primary",
        key="investigate",
    ):

        try:

            results = (
                get_investigation_events(
                    agent_id=(
                        None
                        if selected_agent
                        == "ALL"
                        else selected_agent
                    ),

                    action=(
                        None
                        if selected_action
                        == "ALL"
                        else selected_action
                    ),

                    decision=(
                        None
                        if selected_decision
                        == "ALL"
                        else selected_decision
                    ),

                    limit=100,
                )
            )

            st.session_state.investigation_results = (
                results
            )

            st.session_state.investigation_executed = (
                True
            )

        except Exception as error:

            st.error(
                f"Investigation failed: {error}"
            )

    if st.session_state.investigation_executed:

        results = (
            st.session_state.investigation_results
        )

        if results:

            investigation_df = pd.DataFrame(
                results
            )

            st.metric(
                "Matching Events",
                len(results),
            )

            st.dataframe(
                investigation_df,
                width="stretch",
                hide_index=True,
            )

        else:

            st.info(
                "No matching events found."
            )


# ============================================================
# AGENT ACTIVITY
# ============================================================

if show_agents:

    st.divider()

    st.header(
        "👤 Agent Activity"
    )

    if agents:

        agent_df = pd.DataFrame(
            agents
        )

        st.dataframe(
            agent_df,
            width="stretch",
            hide_index=True,
        )

        required_columns = {
            "agent_id",
            "total_requests",
            "denied_requests",
        }

        if required_columns.issubset(
            agent_df.columns
        ):

            activity_df = (
                agent_df[
                    [
                        "agent_id",
                        "total_requests",
                        "denied_requests",
                    ]
                ]
                .set_index(
                    "agent_id"
                )
            )

            st.bar_chart(
                activity_df,
                width="stretch",
            )

    else:

        st.info(
            "No agent activity available."
        )


# ============================================================
# HIGH-RISK EVENTS
# ============================================================

if show_high_risk:

    st.divider()

    st.header(
        "🔥 High-Risk Events"
    )

    if high_risk_events:

        high_risk_df = pd.DataFrame(
            high_risk_events
        )

        st.dataframe(
            high_risk_df,
            width="stretch",
            hide_index=True,
        )

    else:

        st.success(
            "No high-risk events detected."
        )


# ============================================================
# RESEARCH ARCHITECTURE
# ============================================================

st.divider()

st.header(
    "🏗️ AegisGuard Research Pipeline"
)

arch1, arch2 = (
    st.columns(2)
)

with arch1:

    st.markdown(
        """
        ### Security Control Plane

        Agent Request

        ↓

        Identity

        ↓

        Authorization

        ↓

        Risk Assessment

        ↓

        ALLOW / DENY

        ↓

        Security Telemetry
        """
    )

with arch2:

    st.markdown(
        """
        ### Research Evaluation Plane

        Telemetry

        ↓

        Behavioral Features

        ↓

        Anomaly Detection

        ↓

        Controlled Scenarios

        ↓

        Attack Taxonomy

        ↓

        Experimental Dataset

        ↓

        Quantitative Metrics

        ↓

        Threshold Analysis
        """
    )


# ============================================================
# DAY 24 RESEARCH MILESTONE
# ============================================================

st.divider()

st.header(
    "🔬 Day 24 Research Milestone"
)

st.markdown(
    """
    ### Quantitative Detection Evaluation

    AegisGuard now supports controlled measurement of
    detection performance against known ground-truth events.

    The evaluation layer measures:

    - Accuracy
    - Precision
    - Recall
    - F1-score
    - Specificity
    - False-positive rate
    - False-negative rate
    - Confusion matrix
    - Risk-threshold sensitivity
    - Event-level classification
    - Reproducibility metadata

    This establishes the foundation for the next stage:
    **baseline comparison and statistically defensible
    experiments.**
    """
)

st.warning(
    "Current measurements are controlled prototype "
    "experiments using synthetic data. They must not be "
    "reported as real-world production performance."
)

st.caption(
    "AegisGuard — Behavior-Aware Security Control Plane "
    "for Autonomous AI Agents"
)

st.caption(
    "Day 24 • Quantitative Detection Evaluation"
)