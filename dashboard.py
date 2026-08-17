from __future__ import annotations

import streamlit as st
import pandas as pd


# ============================================================
# AEGISGUARD CORE ANALYTICS
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
# INVESTIGATION ENGINE
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
# CONTROLLED SCENARIOS
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
# ATTACK SCENARIOS
# ============================================================

from app.attack_scenarios import (
    ATTACK_SCENARIO_TYPES,
    get_attack_scenarios,
    get_attack_scenarios_by_type,
    get_attack_scenario_summary,
)


# ============================================================
# EXPERIMENTAL DATASET
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
# DAY 25 — RESEARCH EVALUATION ENGINE
# ============================================================

from app.evaluation import (
    compare_detectors,
    build_baseline_sweep,
    build_aegisguard_sweep,
    get_best_threshold,
    get_confusion_matrix,
    generate_comparison_summary,
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

DEFAULT_STATE = {
    "day23_dataset": None,
    "day23_summary": None,
    "day23_validation": None,
    "investigation_results": [],
    "investigation_executed": False,
    "day25_baseline": None,
    "day25_aegisguard": None,
    "day25_comparison": None,
}


for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# HELPERS
# ============================================================

def safe_int(
    value,
    default=0,
):

    try:
        return int(value)

    except (TypeError, ValueError):

        return default


def safe_float(
    value,
    default=0.0,
):

    try:
        return float(value)

    except (TypeError, ValueError):

        return default


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
        "Security Modules"
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
        "Controlled Scenarios",
        value=True,
    )

    show_day22 = st.checkbox(
        "Attack Research",
        value=True,
    )

    show_day23 = st.checkbox(
        "Experimental Dataset",
        value=True,
    )

    show_day25 = st.checkbox(
        "Baseline Comparison",
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
        "Research Roadmap"
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

        ↓

        **Day 25**

        Baseline Comparison
        """
    )

    st.divider()

    st.caption(
        f"Dataset Version: {DATASET_VERSION}"
    )

    st.caption(
        "AegisGuard Research Prototype"
    )


# ============================================================
# LOAD CORE SECURITY DATA
# ============================================================

try:

    total_events = get_total_events()

    decisions = get_decision_counts()

    risk = get_risk_summary()

    agents = get_agent_activity()

    high_risk_events = get_high_risk_events()

    suspicious_agents = get_suspicious_agents()

    repeated_denials = get_repeated_denials()

except Exception as error:

    st.error(
        f"Unable to load security data: {error}"
    )

    st.stop()


# ============================================================
# LOAD BEHAVIORAL FEATURES
# ============================================================

try:

    behavioral_features = (
        get_behavioral_features()
    )

except Exception:

    behavioral_features = []


# ============================================================
# LOAD ANOMALIES
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
# DAY 16 — SECURITY OVERVIEW
# ============================================================

if show_overview:

    st.header(
        "📊 Security Operations Overview"
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
            "Critical Events",
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

    st.subheader(
        "Authorization Decisions"
    )

    decision_df = pd.DataFrame(
        {
            "Decision": list(
                decisions.keys()
            ),

            "Count": list(
                decisions.values()
            ),
        }
    )

    if not decision_df.empty:

        st.bar_chart(
            decision_df.set_index(
                "Decision"
            ),
            width="stretch",
        )

    else:

        st.info(
            "No authorization decisions available."
        )


# ============================================================
# INTEGRATED SECURITY INTELLIGENCE
# ============================================================

if show_intelligence:

    st.divider()

    st.header(
        "🧠 Integrated Security Intelligence"
    )

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

    intelligence_records = []

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

        maximum_risk = safe_float(
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
            maximum_risk * 0.40
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
                "agent_id": agent_id,
                "total_requests": total,
                "denied_requests": denied,
                "denial_rate": round(
                    denial_rate * 100,
                    2,
                ),
                "maximum_risk": maximum_risk,
                "anomaly_score": anomaly_score,
                "intelligence_score": round(
                    intelligence_score,
                    2,
                ),
                "priority": priority,
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

    else:

        st.info(
            "No integrated intelligence records available."
        )


# ============================================================
# DAY 21 — CONTROLLED SECURITY SCENARIOS
# ============================================================

if show_day21:

    st.divider()

    st.header(
        "🧪 Controlled Security Scenario Lab"
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
        key="day21_scenario_class",
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

    else:

        st.info(
            "No scenarios available."
        )


# ============================================================
# DAY 22 — ATTACK SCENARIO RESEARCH
# ============================================================

if show_day22:

    st.divider()

    st.header(
        "⚔️ Attack Scenario Research"
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

    else:

        st.info(
            "No attack scenarios available."
        )


# ============================================================
# DAY 23 — EXPERIMENTAL DATASET
# ============================================================

if show_day23:

    st.divider()

    st.header(
        "🧬 Experimental Dataset Laboratory"
    )

    st.caption(
        "Generate a reproducible dataset for controlled research experiments."
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
            key="day23_events_per_scenario",
        )

    with d2:

        experiment_seed = st.number_input(
            "Experiment Seed",
            min_value=0,
            max_value=999999,
            value=42,
            step=1,
            key="day23_experiment_seed",
        )

    with d3:

        st.metric(
            "Dataset Version",
            DATASET_VERSION,
        )

    if st.button(
        "🧬 Generate Experimental Dataset",
        type="primary",
        key="day23_generate",
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

            # Reset Day 25 results because
            # the underlying dataset changed.
            st.session_state.day25_baseline = None
            st.session_state.day25_aegisguard = None
            st.session_state.day25_comparison = None

            st.success(
                f"Generated {len(dataset)} experimental events."
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
                    len(dataset),
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
                "Average Risk",
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

        st.subheader(
            "Ground-Truth Distribution"
        )

        distribution = (
            get_label_distribution(
                dataset
            )
        )

        distribution_df = pd.DataFrame(
            {
                "Class": list(
                    distribution.keys()
                ),

                "Count": list(
                    distribution.values()
                ),
            }
        )

        if not distribution_df.empty:

            st.bar_chart(
                distribution_df.set_index(
                    "Class"
                ),
                width="stretch",
            )

        download_col1, download_col2 = (
            st.columns(2)
        )

        with download_col1:

            st.download_button(
                "⬇️ Download CSV",
                data=dataset_to_csv(
                    dataset
                ),
                file_name=(
                    "aegisguard_day23_dataset.csv"
                ),
                mime="text/csv",
                width="stretch",
                key="day23_download_csv",
            )

        with download_col2:

            st.download_button(
                "⬇️ Download JSONL",
                data=dataset_to_jsonl(
                    dataset
                ),
                file_name=(
                    "aegisguard_day23_dataset.jsonl"
                ),
                mime="application/json",
                width="stretch",
                key="day23_download_jsonl",
            )


# ============================================================
# DAY 25 — BASELINE VS AEGISGUARD
# ============================================================

if show_day25:

    st.divider()

    st.header(
        "🔬 Day 25 — Baseline vs AegisGuard"
    )

    st.caption(
        "Controlled quantitative comparison using the same "
        "experimental dataset and ground-truth labels."
    )

    # --------------------------------------------------------
    # METHODOLOGY
    # --------------------------------------------------------

    with st.expander(
        "📖 Experimental Methodology",
        expanded=True,
    ):

        st.markdown(
            """
            ### Research Question

            **Does the current AegisGuard detection approach
            produce different detection performance from a
            transparent baseline under identical experimental
            conditions?**

            ### Positive Class

            `MALICIOUS`

            ### Negative Class

            `BENIGN + SUSPICIOUS`

            ### Baseline

            A transparent rule-based detector:

            **DENY OR risk ≥ threshold → MALICIOUS**

            ### AegisGuard

            The current experimental AegisGuard rule:

            **DENY OR risk ≥ threshold → MALICIOUS**

            Both detectors are evaluated on exactly the same
            experimental dataset.

            The purpose of Day 25 is to establish a reproducible
            baseline comparison framework.

            **A single experiment does not establish statistical
            superiority or real-world generalization.**
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
            "No experimental dataset is currently loaded."
        )

        st.info(
            "Generate a dataset in the Day 23 section first."
        )

    else:

        dataset_size = len(
            evaluation_dataset
        )

        distribution = (
            get_label_distribution(
                evaluation_dataset
            )
        )

        st.success(
            f"Evaluation dataset loaded: {dataset_size} events."
        )

        total_labels = sum(
            distribution.values()
        )

        if total_labels:

            malicious_ratio = (
                distribution.get(
                    "MALICIOUS",
                    0,
                )
                / total_labels
            )

            if malicious_ratio > 0.70:

                st.warning(
                    f"Class imbalance warning: "
                    f"MALICIOUS represents "
                    f"{malicious_ratio * 100:.1f}% "
                    "of the dataset."
                )

        # ----------------------------------------------------
        # EXPERIMENT CONTROLS
        # ----------------------------------------------------

        st.subheader(
            "Experimental Controls"
        )

        threshold_col1, threshold_col2 = (
            st.columns(2)
        )

        with threshold_col1:

            baseline_threshold = st.slider(
                "Baseline Risk Threshold",
                min_value=0,
                max_value=100,
                value=70,
                step=5,
                key="day25_baseline_threshold",
            )

        with threshold_col2:

            aegisguard_threshold = st.slider(
                "AegisGuard Risk Threshold",
                min_value=0,
                max_value=100,
                value=70,
                step=5,
                key="day25_aegisguard_threshold",
            )

        # ----------------------------------------------------
        # RUN EXPERIMENT
        # ----------------------------------------------------

        if st.button(
            "▶️ Run Baseline Comparison",
            type="primary",
            key="day25_run",
        ):

            (
                baseline_metrics,
                aegisguard_metrics,
                comparison_df,
            ) = compare_detectors(
                evaluation_dataset,
                baseline_threshold=baseline_threshold,
                aegisguard_threshold=aegisguard_threshold,
            )

            st.session_state.day25_baseline = (
                baseline_metrics
            )

            st.session_state.day25_aegisguard = (
                aegisguard_metrics
            )

            st.session_state.day25_comparison = (
                comparison_df
            )

            st.success(
                "Baseline comparison completed."
            )

        # ----------------------------------------------------
        # DISPLAY RESULTS
        # ----------------------------------------------------

        baseline_metrics = (
            st.session_state.day25_baseline
        )

        aegisguard_metrics = (
            st.session_state.day25_aegisguard
        )

        comparison_df = (
            st.session_state.day25_comparison
        )

        if (
            baseline_metrics is not None
            and aegisguard_metrics is not None
            and comparison_df is not None
        ):

            st.divider()

            st.subheader(
                "🏁 Quantitative Comparison"
            )

            display_df = (
                comparison_df.copy()
            )

            for column in [
                "Baseline",
                "AegisGuard",
            ]:

                display_df[column] = (
                    display_df[column] * 100
                ).round(2)

            display_df["Difference"] = (
                display_df["Difference"] * 100
            ).round(2)

            display_df = display_df.rename(
                columns={
                    "Baseline":
                        "Baseline (%)",

                    "AegisGuard":
                        "AegisGuard (%)",

                    "Difference":
                        "Difference (pp)",
                }
            )

            st.dataframe(
                display_df,
                width="stretch",
                hide_index=True,
            )

            # ------------------------------------------------
            # KPI CARDS
            # ------------------------------------------------

            st.subheader(
                "Performance Indicators"
            )

            baseline_col, aegisguard_col = (
                st.columns(2)
            )

            with baseline_col:

                st.markdown(
                    "### 🔹 Baseline"
                )

                b1, b2, b3, b4 = (
                    st.columns(4)
                )

                with b1:

                    st.metric(
                        "Accuracy",
                        f"{baseline_metrics['Accuracy'] * 100:.2f}%",
                    )

                with b2:

                    st.metric(
                        "Precision",
                        f"{baseline_metrics['Precision'] * 100:.2f}%",
                    )

                with b3:

                    st.metric(
                        "Recall",
                        f"{baseline_metrics['Recall'] * 100:.2f}%",
                    )

                with b4:

                    st.metric(
                        "F1",
                        f"{baseline_metrics['F1'] * 100:.2f}%",
                    )

            with aegisguard_col:

                st.markdown(
                    "### 🛡️ AegisGuard"
                )

                a1, a2, a3, a4 = (
                    st.columns(4)
                )

                with a1:

                    st.metric(
                        "Accuracy",
                        f"{aegisguard_metrics['Accuracy'] * 100:.2f}%",
                    )

                with a2:

                    st.metric(
                        "Precision",
                        f"{aegisguard_metrics['Precision'] * 100:.2f}%",
                    )

                with a3:

                    st.metric(
                        "Recall",
                        f"{aegisguard_metrics['Recall'] * 100:.2f}%",
                    )

                with a4:

                    st.metric(
                        "F1",
                        f"{aegisguard_metrics['F1'] * 100:.2f}%",
                    )

            # ------------------------------------------------
            # CONFUSION MATRICES
            # ------------------------------------------------

            st.subheader(
                "Confusion Matrices"
            )

            cm1, cm2 = (
                st.columns(2)
            )

            with cm1:

                st.markdown(
                    "### Baseline"
                )

                st.dataframe(
                    get_confusion_matrix(
                        baseline_metrics
                    ),
                    width="stretch",
                )

            with cm2:

                st.markdown(
                    "### AegisGuard"
                )

                st.dataframe(
                    get_confusion_matrix(
                        aegisguard_metrics
                    ),
                    width="stretch",
                )

            # ------------------------------------------------
            # RESEARCH SUMMARY
            # ------------------------------------------------

            summary = (
                generate_comparison_summary(
                    baseline_metrics,
                    aegisguard_metrics,
                )
            )

            st.subheader(
                "🔬 Research Interpretation"
            )

            f1_difference = (
                summary["f1_difference"]
            )

            precision_difference = (
                summary["precision_difference"]
            )

            recall_difference = (
                summary["recall_difference"]
            )

            if summary["outcome"] == (
                "AEGISGUARD_HIGHER_F1"
            ):

                st.info(
                    f"AegisGuard achieved a higher F1 "
                    f"score than the baseline by "
                    f"{f1_difference * 100:.2f} "
                    "percentage points in this experiment."
                )

            elif summary["outcome"] == (
                "BASELINE_HIGHER_F1"
            ):

                st.warning(
                    f"The baseline achieved a higher F1 "
                    f"score than AegisGuard by "
                    f"{abs(f1_difference) * 100:.2f} "
                    "percentage points in this experiment."
                )

            else:

                st.info(
                    "Both approaches produced the same "
                    "F1 score in this experiment."
                )

            i1, i2, i3 = (
                st.columns(3)
            )

            with i1:

                st.metric(
                    "F1 Difference",
                    f"{f1_difference * 100:.2f} pp",
                )

            with i2:

                st.metric(
                    "Precision Difference",
                    f"{precision_difference * 100:.2f} pp",
                )

            with i3:

                st.metric(
                    "Recall Difference",
                    f"{recall_difference * 100:.2f} pp",
                )

            st.warning(
                "These results represent one controlled "
                "experiment. They must not be presented as "
                "proof of statistical superiority."
            )

            # ------------------------------------------------
            # THRESHOLD SENSITIVITY
            # ------------------------------------------------

            st.divider()

            st.subheader(
                "📐 Threshold Sensitivity Analysis"
            )

            thresholds = list(
                range(
                    0,
                    101,
                    5,
                )
            )

            baseline_sweep = (
                build_baseline_sweep(
                    evaluation_dataset,
                    thresholds,
                )
            )

            aegisguard_sweep = (
                build_aegisguard_sweep(
                    evaluation_dataset,
                    thresholds,
                )
            )

            f1_df = pd.DataFrame(
                {
                    "Baseline F1":
                        baseline_sweep["F1"],

                    "AegisGuard F1":
                        aegisguard_sweep["F1"],
                },
                index=thresholds,
            )

            f1_df.index.name = (
                "Risk Threshold"
            )

            st.markdown(
                "#### F1 Score vs Risk Threshold"
            )

            st.line_chart(
                f1_df,
                width="stretch",
            )

            recall_df = pd.DataFrame(
                {
                    "Baseline Recall":
                        baseline_sweep["Recall"],

                    "AegisGuard Recall":
                        aegisguard_sweep["Recall"],
                },
                index=thresholds,
            )

            recall_df.index.name = (
                "Risk Threshold"
            )

            st.markdown(
                "#### Recall vs Risk Threshold"
            )

            st.line_chart(
                recall_df,
                width="stretch",
            )

            precision_df = pd.DataFrame(
                {
                    "Baseline Precision":
                        baseline_sweep["Precision"],

                    "AegisGuard Precision":
                        aegisguard_sweep["Precision"],
                },
                index=thresholds,
            )

            precision_df.index.name = (
                "Risk Threshold"
            )

            st.markdown(
                "#### Precision vs Risk Threshold"
            )

            st.line_chart(
                precision_df,
                width="stretch",
            )

            # ------------------------------------------------
            # OPTIMAL THRESHOLDS
            # ------------------------------------------------

            st.subheader(
                "🎯 Best Experimental Threshold"
            )

            best_baseline = (
                get_best_threshold(
                    baseline_sweep,
                    metric="F1",
                )
            )

            best_aegisguard = (
                get_best_threshold(
                    aegisguard_sweep,
                    metric="F1",
                )
            )

            bt1, bt2 = (
                st.columns(2)
            )

            with bt1:

                st.metric(
                    "Baseline",
                    f"Threshold {best_baseline['Threshold']:.0f}",
                    f"F1 {best_baseline['F1'] * 100:.2f}%",
                )

            with bt2:

                st.metric(
                    "AegisGuard",
                    f"Threshold {best_aegisguard['Threshold']:.0f}",
                    f"F1 {best_aegisguard['F1'] * 100:.2f}%",
                )

            # ------------------------------------------------
            # EXPORT
            # ------------------------------------------------

            st.subheader(
                "📥 Research Export"
            )

            export_df = (
                comparison_df.copy()
            )

            st.download_button(
                "⬇️ Download Comparison CSV",
                data=export_df.to_csv(
                    index=False
                ),
                file_name=(
                    "aegisguard_day25_baseline_comparison.csv"
                ),
                mime="text/csv",
                width="stretch",
                key="day25_download_comparison",
            )

            metadata_df = pd.DataFrame(
                {
                    "Parameter": [
                        "Dataset Version",
                        "Dataset Size",
                        "Positive Class",
                        "Negative Class",
                        "Baseline Threshold",
                        "AegisGuard Threshold",
                    ],

                    "Value": [
                        DATASET_VERSION,
                        dataset_size,
                        "MALICIOUS",
                        "BENIGN + SUSPICIOUS",
                        baseline_threshold,
                        aegisguard_threshold,
                    ],
                }
            )

            st.subheader(
                "🧾 Experiment Metadata"
            )

            st.dataframe(
                metadata_df,
                width="stretch",
                hide_index=True,
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

        st.dataframe(
            pd.DataFrame(
                anomaly_results
            ),
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
                "Feature to Visualize",
                available_features,
                key="behavior_feature",
            )

            if (
                "agent_id"
                in behavior_df.columns
            ):

                feature_chart = (
                    behavior_df[
                        [
                            "agent_id",
                            selected_feature,
                        ]
                    ]
                    .set_index(
                        "agent_id"
                    )
                )

                st.bar_chart(
                    feature_chart,
                    width="stretch",
                )

    else:

        st.info(
            "No behavioral feature data available."
        )


# ============================================================
# SECURITY INVESTIGATION
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
        "🔍 Run Investigation",
        type="primary",
        key="run_investigation",
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
        "👤 Agent Activity Intelligence"
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

            st.subheader(
                "Request Activity"
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
# SUSPICIOUS AGENTS
# ============================================================

st.divider()

st.header(
    "⚠️ Suspicious Agents"
)

if suspicious_agents:

    suspicious_df = pd.DataFrame(
        suspicious_agents
    )

    st.dataframe(
        suspicious_df,
        width="stretch",
        hide_index=True,
    )

else:

    st.success(
        "No suspicious agents detected."
    )


# ============================================================
# REPEATED DENIALS
# ============================================================

st.divider()

st.header(
    "🚫 Repeated Denial Patterns"
)

if repeated_denials:

    denial_df = pd.DataFrame(
        repeated_denials
    )

    st.dataframe(
        denial_df,
        width="stretch",
        hide_index=True,
    )

else:

    st.info(
        "No repeated denial patterns detected."
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

        st.dataframe(
            pd.DataFrame(
                high_risk_events
            ),
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
    "🏗️ AegisGuard Research Architecture"
)

architecture_col1, architecture_col2 = (
    st.columns(2)
)

with architecture_col1:

    st.markdown(
        """
        ### Security Control Plane

        Agent Request

        ↓

        Identity / Context

        ↓

        Authorization

        ↓

        Risk Assessment

        ↓

        Behavioral Analysis

        ↓

        ALLOW / DENY

        ↓

        Security Telemetry
        """
    )

with architecture_col2:

    st.markdown(
        """
        ### Experimental Research Plane

        Security Telemetry

        ↓

        Feature Engineering

        ↓

        Anomaly Detection

        ↓

        Controlled Scenarios

        ↓

        Attack Taxonomy

        ↓

        Experimental Dataset

        ↓

        Baseline

        ↘

        AegisGuard

        ↓

        Quantitative Comparison

        ↓

        Repeated Experiments

        ↓

        Statistical Validation
        """
    )


# ============================================================
# DAY 25 MILESTONE
# ============================================================

st.divider()

st.header(
    "🔬 Day 25 Research Milestone"
)

st.markdown(
    """
    ### Baseline Detection Comparison Framework

    Day 25 establishes a reproducible experimental framework
    for comparing AegisGuard against a transparent baseline.

    **Measured metrics**

    - Accuracy
    - Precision
    - Recall
    - F1-score
    - Specificity
    - False-positive rate
    - False-negative rate
    - True positives
    - True negatives
    - False positives
    - False negatives

    **Experimental capabilities**

    - Controlled dataset
    - Fixed ground truth
    - Reproducible thresholds
    - Baseline comparison
    - Confusion matrices
    - Threshold sensitivity
    - Best-threshold analysis
    - Research metadata
    - CSV experiment export

    This forms the methodological foundation for the later
    repeated experiments, ablation studies and statistical
    validation required for a research-level evaluation.
    """
)

st.warning(
    "Do not claim that AegisGuard is superior based on one "
    "synthetic experiment. Later research stages must use "
    "repeated trials, independent datasets and appropriate "
    "statistical analysis."
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "AegisGuard — Behavior-Aware Security Control Plane "
    "for Autonomous AI Agents"
)

st.caption(
    "Research Prototype • Day 25 • Baseline Detection Comparison"
)