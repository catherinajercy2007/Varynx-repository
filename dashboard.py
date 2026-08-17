import streamlit as st
import pandas as pd


# ============================================================
# CORE ANALYTICS
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
    sample_scenarios,
)


# ============================================================
# DAY 22 — ATTACK SCENARIOS
# ============================================================

from app.attack_scenarios import (
    ATTACK_SCENARIO_TYPES,
    get_attack_scenarios,
    get_attack_scenario,
    get_attack_scenarios_by_type,
    get_attack_scenarios_by_severity,
    get_attack_scenario_summary,
    sample_attack_scenarios,
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
    page_title="AegisGuard Security Intelligence Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "investigation_results": [],
    "investigation_executed": False,
    "day21_sampled_scenarios": None,
    "day22_attack_experiment": None,
    "day23_dataset": None,
    "day23_dataset_summary": None,
    "day23_dataset_validation": None,
}

for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:
        st.session_state[key] = value


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


def clamp(
    value,
    minimum=0.0,
    maximum=100.0,
):

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def calculate_agent_intelligence(
    agent,
    anomaly_lookup,
    suspicious_lookup,
):

    agent_id = str(
        agent.get(
            "agent_id",
            "unknown-agent",
        )
    )

    total_requests = safe_int(
        agent.get(
            "total_requests",
            0,
        )
    )

    denied_requests = safe_int(
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
        denied_requests / total_requests
        if total_requests > 0
        else 0
    )

    anomaly = anomaly_lookup.get(
        agent_id,
        {},
    )

    anomaly_score = safe_float(
        anomaly.get(
            "anomaly_score",
            0,
        )
    )

    anomaly_severity = str(
        anomaly.get(
            "anomaly_severity",
            "NORMAL",
        )
    ).upper()

    risk_signal = clamp(
        maximum_risk
    )

    denial_signal = clamp(
        denial_rate * 100
    )

    anomaly_signal = clamp(
        anomaly_score / 3 * 100
    )

    suspicious_signal = (
        100
        if agent_id in suspicious_lookup
        else 0
    )

    severity_bonus = {
        "NORMAL": 0,
        "LOW": 5,
        "MEDIUM": 15,
        "HIGH": 25,
    }.get(
        anomaly_severity,
        0,
    )

    intelligence_score = (
        risk_signal * 0.35
        + denial_signal * 0.25
        + anomaly_signal * 0.25
        + suspicious_signal * 0.15
        + severity_bonus
    )

    intelligence_score = clamp(
        intelligence_score
    )

    if intelligence_score >= 80:
        priority = "CRITICAL"

    elif intelligence_score >= 60:
        priority = "HIGH"

    elif intelligence_score >= 35:
        priority = "MEDIUM"

    else:
        priority = "LOW"

    recommendation = {
        "CRITICAL":
            "Immediate investigation and containment review",

        "HIGH":
            "Prioritize analyst investigation",

        "MEDIUM":
            "Increase monitoring and review behavior",

        "LOW":
            "Continue normal monitoring",
    }[priority]

    return {
        "agent_id": agent_id,
        "total_requests": total_requests,
        "denied_requests": denied_requests,
        "denial_rate": round(
            denial_rate * 100,
            2,
        ),
        "maximum_risk": round(
            maximum_risk,
            2,
        ),
        "anomaly_score": round(
            anomaly_score,
            4,
        ),
        "anomaly_severity": anomaly_severity,
        "intelligence_score": round(
            intelligence_score,
            2,
        ),
        "priority": priority,
        "recommended_action": recommendation,
    }


# ============================================================
# HEADER
# ============================================================

st.title(
    "🛡️ AegisGuard Security Intelligence Center"
)

st.caption(
    "Behavior-aware security control plane for "
    "autonomous AI agent authorization, monitoring, "
    "investigation and reproducible research."
)

st.divider()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "Security Intelligence Controls"
    )

    st.success(
        "AegisGuard security engine online"
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
        "Research Pipeline"
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
        """
    )

    st.divider()

    st.caption(
        "AegisGuard Research Prototype"
    )

    st.caption(
        f"Dataset Version: {DATASET_VERSION}"
    )


# ============================================================
# LOAD SECURITY DATA
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
        "Unable to load security data: "
        f"{error}"
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
# ANOMALY DATA
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
# LOOKUPS
# ============================================================

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


# ============================================================
# AGENT INTELLIGENCE
# ============================================================

intelligence_records = []

for agent in agents:

    intelligence_records.append(
        calculate_agent_intelligence(
            agent,
            anomaly_lookup,
            suspicious_lookup,
        )
    )


intelligence_df = pd.DataFrame(
    intelligence_records
)


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
            "Repeated Denials",
            len(
                repeated_denials
            ),
        )

    chart1, chart2 = (
        st.columns(2)
    )

    with chart1:

        st.subheader(
            "Authorization Decisions"
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

            st.bar_chart(
                decision_df.set_index(
                    "Decision"
                ),
                width="stretch",
            )

    with chart2:

        st.subheader(
            "Risk Indicators"
        )

        risk_df = pd.DataFrame(
            {
                "Indicator": [
                    "Average Risk",
                    "Maximum Risk",
                    "High-Risk Events",
                    "Critical Events",
                ],

                "Value": [
                    risk.get(
                        "average_risk",
                        0,
                    ),

                    risk.get(
                        "maximum_risk",
                        0,
                    ),

                    risk.get(
                        "high_risk_events",
                        0,
                    ),

                    risk.get(
                        "critical_events",
                        0,
                    ),
                ],
            }
        )

        st.bar_chart(
            risk_df.set_index(
                "Indicator"
            ),
            width="stretch",
        )


# ============================================================
# DAY 20 — INTEGRATED INTELLIGENCE
# ============================================================

if show_intelligence:

    st.divider()

    st.header(
        "🧠 Integrated Security Intelligence"
    )

    st.caption(
        "Combined authorization, behavioral, risk and "
        "anomaly signals."
    )

    if not intelligence_df.empty:

        priority_counts = (
            intelligence_df[
                "priority"
            ].value_counts()
        )

        avg_score = round(
            float(
                intelligence_df[
                    "intelligence_score"
                ].mean()
            ),
            2,
        )

        i1, i2, i3, i4, i5 = (
            st.columns(5)
        )

        with i1:

            st.metric(
                "Average Score",
                avg_score,
            )

        with i2:

            st.metric(
                "Critical",
                int(
                    priority_counts.get(
                        "CRITICAL",
                        0,
                    )
                ),
            )

        with i3:

            st.metric(
                "High",
                int(
                    priority_counts.get(
                        "HIGH",
                        0,
                    )
                ),
            )

        with i4:

            st.metric(
                "Medium",
                int(
                    priority_counts.get(
                        "MEDIUM",
                        0,
                    )
                ),
            )

        with i5:

            st.metric(
                "Low",
                int(
                    priority_counts.get(
                        "LOW",
                        0,
                    )
                ),
            )

        st.dataframe(
            intelligence_df.sort_values(
                "intelligence_score",
                ascending=False,
            ),
            width="stretch",
            hide_index=True,
        )


# ============================================================
# DAY 21 — CONTROLLED SCENARIO LAB
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

        scenario_summary = {
            "total": 0,
            "benign": 0,
            "suspicious": 0,
            "malicious": 0,
        }

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
        key="day21_class_filter",
    )

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

    if scenarios:

        scenario_df = pd.DataFrame(
            scenarios
        )

        st.dataframe(
            scenario_df,
            width="stretch",
            hide_index=True,
        )


# ============================================================
# DAY 22 — ATTACK RESEARCH LAB
# ============================================================

if show_day22:

    st.divider()

    st.header(
        "⚔️ Day 22 — Controlled Attack Research Lab"
    )

    st.caption(
        "Structured attack taxonomy used as the source "
        "for reproducible research experiments."
    )

    attack_summary = (
        get_attack_scenario_summary()
    )

    a1, a2, a3, a4, a5 = (
        st.columns(5)
    )

    with a1:

        st.metric(
            "Scenarios",
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

    with a5:

        st.metric(
            "High",
            attack_summary.get(
                "high",
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
        key="day22_type",
    )

    attack_severity = st.selectbox(
        "Severity",
        [
            "ALL",
            "CRITICAL",
            "HIGH",
            "MEDIUM",
            "LOW",
        ],
        key="day22_severity",
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

    if attack_severity != "ALL":

        attacks = [
            attack
            for attack
            in attacks
            if attack[
                "severity"
            ]
            == attack_severity
        ]

    if attacks:

        attack_df = pd.DataFrame(
            attacks
        )

        columns = [
            "scenario_id",
            "name",
            "scenario_type",
            "agent_id",
            "severity",
            "ground_truth",
            "expected_signal",
        ]

        st.dataframe(
            attack_df[
                [
                    column
                    for column
                    in columns
                    if column
                    in attack_df.columns
                ]
            ],
            width="stretch",
            hide_index=True,
        )


# ============================================================
# DAY 23 — EXPERIMENTAL DATASET RESEARCH LAB
# ============================================================

if show_day23:

    st.divider()

    st.header(
        "🧬 Day 23 — Experimental Dataset Research Lab"
    )

    st.caption(
        "Generate, validate, inspect and export reproducible "
        "security experiments from the controlled attack catalog."
    )

    # --------------------------------------------------------
    # RESEARCH OBJECTIVE
    # --------------------------------------------------------

    with st.expander(
        "🔬 What is Day 23 doing?",
        expanded=True,
    ):

        st.markdown(
            """
            Day 23 transforms the controlled security
            scenarios into a machine-readable experimental
            dataset.

            Each generated event contains:

            **Scenario → Agent → Task → Action → Resource →
            Severity → Ground Truth → Risk → Decision →
            Sequence Position → Timestamp → Experiment Seed**

            The dataset is synthetic and reproducible.
            It is intended for controlled research evaluation,
            not as evidence of real-world attack prevalence.
            """
        )

    # --------------------------------------------------------
    # DATASET CONTROLS
    # --------------------------------------------------------

    st.subheader(
        "Experimental Configuration"
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
            key="day23_seed",
        )

    with d3:

        dataset_version_display = st.text_input(
            "Dataset Version",
            value=DATASET_VERSION,
            disabled=True,
            key="day23_version",
        )

    # --------------------------------------------------------
    # SOURCE SCENARIOS
    # --------------------------------------------------------

    source_scenarios = (
        get_attack_scenarios()
    )

    st.metric(
        "Source Attack Scenarios",
        len(
            source_scenarios
        ),
    )

    # --------------------------------------------------------
    # GENERATE DATASET
    # --------------------------------------------------------

    generate_col, validate_col = (
        st.columns(2)
    )

    with generate_col:

        generate_dataset = st.button(
            "🧬 Generate Experimental Dataset",
            type="primary",
            use_container_width=True,
            key="day23_generate",
        )

    with validate_col:

        validate_existing = st.button(
            "🔎 Validate Current Dataset",
            use_container_width=True,
            key="day23_validate",
        )

    if generate_dataset:

        try:

            generated_dataset = (
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

            st.session_state[
                "day23_dataset"
            ] = generated_dataset

            st.session_state[
                "day23_dataset_summary"
            ] = summarize_dataset(
                generated_dataset
            )

            st.session_state[
                "day23_dataset_validation"
            ] = validate_dataset(
                generated_dataset
            )

            st.success(
                f"Generated {len(generated_dataset)} "
                "experimental events successfully."
            )

        except Exception as error:

            st.error(
                "Dataset generation failed: "
                f"{error}"
            )

    # --------------------------------------------------------
    # CURRENT DATASET
    # --------------------------------------------------------

    current_dataset = (
        st.session_state.get(
            "day23_dataset"
        )
    )

    if current_dataset:

        dataset_summary = (
            st.session_state.get(
                "day23_dataset_summary",
                {},
            )
        )

        dataset_validation = (
            st.session_state.get(
                "day23_dataset_validation",
                {},
            )
        )

        st.divider()

        st.subheader(
            "Dataset Overview"
        )

        m1, m2, m3, m4, m5 = (
            st.columns(5)
        )

        with m1:

            st.metric(
                "Events",
                dataset_summary.get(
                    "total_events",
                    len(
                        current_dataset
                    ),
                ),
            )

        with m2:

            st.metric(
                "Benign",
                dataset_summary.get(
                    "benign_events",
                    0,
                ),
            )

        with m3:

            st.metric(
                "Suspicious",
                dataset_summary.get(
                    "suspicious_events",
                    0,
                ),
            )

        with m4:

            st.metric(
                "Malicious",
                dataset_summary.get(
                    "malicious_events",
                    0,
                ),
            )

        with m5:

            st.metric(
                "Average Risk",
                dataset_summary.get(
                    "average_risk",
                    0,
                ),
            )

        # ----------------------------------------------------
        # VALIDATION STATUS
        # ----------------------------------------------------

        st.subheader(
            "Dataset Integrity"
        )

        validation_col1, validation_col2 = (
            st.columns(2)
        )

        with validation_col1:

            if dataset_validation.get(
                "valid",
                False,
            ):

                st.success(
                    "✅ Dataset validation passed"
                )

            else:

                st.error(
                    "❌ Dataset validation failed"
                )

        with validation_col2:

            st.write(
                "**Rows:** "
                f"{dataset_validation.get('total_rows', 0)}"
            )

            st.write(
                "**Labels valid:** "
                f"{dataset_validation.get('labels_valid', False)}"
            )

            st.write(
                "**Risk scores valid:** "
                f"{dataset_validation.get('risk_scores_valid', False)}"
            )

            st.write(
                "**Decisions valid:** "
                f"{dataset_validation.get('decisions_valid', False)}"
            )

        # ----------------------------------------------------
        # LABEL DISTRIBUTION
        # ----------------------------------------------------

        st.subheader(
            "Ground-Truth Distribution"
        )

        label_distribution = (
            get_label_distribution(
                current_dataset
            )
        )

        label_df = pd.DataFrame(
            {
                "Ground Truth": [
                    "BENIGN",
                    "SUSPICIOUS",
                    "MALICIOUS",
                ],

                "Count": [
                    label_distribution.get(
                        "BENIGN",
                        0,
                    ),

                    label_distribution.get(
                        "SUSPICIOUS",
                        0,
                    ),

                    label_distribution.get(
                        "MALICIOUS",
                        0,
                    ),
                ],
            }
        )

        chart_col, distribution_col = (
            st.columns(2)
        )

        with chart_col:

            st.bar_chart(
                label_df.set_index(
                    "Ground Truth"
                ),
                width="stretch",
            )

        with distribution_col:

            st.dataframe(
                label_df,
                width="stretch",
                hide_index=True,
            )

            total_labels = sum(
                label_distribution.values()
            )

            if total_labels:

                benign_ratio = (
                    label_distribution[
                        "BENIGN"
                    ]
                    / total_labels
                    * 100
                )

                suspicious_ratio = (
                    label_distribution[
                        "SUSPICIOUS"
                    ]
                    / total_labels
                    * 100
                )

                malicious_ratio = (
                    label_distribution[
                        "MALICIOUS"
                    ]
                    / total_labels
                    * 100
                )

                st.write(
                    f"Benign: **{benign_ratio:.1f}%**"
                )

                st.write(
                    f"Suspicious: **{suspicious_ratio:.1f}%**"
                )

                st.write(
                    f"Malicious: **{malicious_ratio:.1f}%**"
                )

        # ----------------------------------------------------
        # DATASET PREVIEW
        # ----------------------------------------------------

        st.subheader(
            "Experimental Dataset Preview"
        )

        dataset_df = pd.DataFrame(
            current_dataset
        )

        preview_count = st.slider(
            "Preview Rows",
            min_value=5,
            max_value=min(
                100,
                len(
                    dataset_df
                ),
            ),
            value=min(
                20,
                len(
                    dataset_df
                ),
            ),
            key="day23_preview_rows",
        )

        st.dataframe(
            dataset_df.head(
                preview_count
            ),
            width="stretch",
            hide_index=True,
        )

        # ----------------------------------------------------
        # DATASET FILTER
        # ----------------------------------------------------

        st.subheader(
            "Research Dataset Explorer"
        )

        filter_col1, filter_col2, filter_col3 = (
            st.columns(3)
        )

        with filter_col1:

            selected_label = st.selectbox(
                "Ground Truth",
                [
                    "ALL",
                    "BENIGN",
                    "SUSPICIOUS",
                    "MALICIOUS",
                ],
                key="day23_label_filter",
            )

        with filter_col2:

            selected_decision = st.selectbox(
                "Decision",
                [
                    "ALL",
                    "ALLOW",
                    "DENY",
                ],
                key="day23_decision_filter",
            )

        with filter_col3:

            min_risk = st.slider(
                "Minimum Risk",
                min_value=0,
                max_value=100,
                value=0,
                step=5,
                key="day23_min_risk",
            )

        filtered_df = dataset_df.copy()

        if selected_label != "ALL":

            filtered_df = filtered_df[
                filtered_df[
                    "ground_truth"
                ]
                == selected_label
            ]

        if selected_decision != "ALL":

            filtered_df = filtered_df[
                filtered_df[
                    "decision"
                ]
                == selected_decision
            ]

        if "risk_score" in filtered_df.columns:

            filtered_df = filtered_df[
                filtered_df[
                    "risk_score"
                ]
                >= min_risk
            ]

        st.write(
            f"Matching events: **{len(filtered_df)}**"
        )

        st.dataframe(
            filtered_df,
            width="stretch",
            hide_index=True,
        )

        # ----------------------------------------------------
        # EXPORT
        # ----------------------------------------------------

        st.subheader(
            "Research Dataset Export"
        )

        export_col1, export_col2 = (
            st.columns(2)
        )

        with export_col1:

            csv_data = dataset_to_csv(
                current_dataset
            )

            st.download_button(
                "⬇️ Download CSV Dataset",
                data=csv_data,
                file_name=(
                    "aegisguard_day23_experimental_dataset.csv"
                ),
                mime="text/csv",
                use_container_width=True,
                key="day23_csv_download",
            )

        with export_col2:

            jsonl_data = dataset_to_jsonl(
                current_dataset
            )

            st.download_button(
                "⬇️ Download JSONL Dataset",
                data=jsonl_data,
                file_name=(
                    "aegisguard_day23_experimental_dataset.jsonl"
                ),
                mime="application/json",
                use_container_width=True,
                key="day23_jsonl_download",
            )

        # ----------------------------------------------------
        # REPRODUCIBILITY
        # ----------------------------------------------------

        st.subheader(
            "🔁 Reproducibility Metadata"
        )

        reproducibility_df = pd.DataFrame(
            {
                "Parameter": [
                    "Dataset Version",
                    "Experiment Seed",
                    "Events per Scenario",
                    "Scenario Count",
                    "Total Events",
                ],

                "Value": [
                    DATASET_VERSION,
                    experiment_seed,
                    events_per_scenario,
                    len(
                        source_scenarios
                    ),
                    len(
                        current_dataset
                    ),
                ],
            }
        )

        st.dataframe(
            reproducibility_df,
            width="stretch",
            hide_index=True,
        )

        st.info(
            "Using the same scenario catalog, events-per-scenario "
            "value and experiment seed should reproduce the "
            "same synthetic dataset."
        )

        # ----------------------------------------------------
        # RESEARCH LIMITATION
        # ----------------------------------------------------

        st.warning(
            "Research limitation: this dataset is synthetic "
            "and controlled. It should not be presented as "
            "evidence of real-world attack prevalence or "
            "production detection performance."
        )

    else:

        st.info(
            "No experimental dataset has been generated yet. "
            "Configure the experiment above and click "
            "'Generate Experimental Dataset'."
        )


# ============================================================
# ANOMALY DETECTION
# ============================================================

if show_anomalies:

    st.divider()

    st.header(
        "🚨 Behavioral Anomaly Detection"
    )

    a1, a2, a3, a4 = (
        st.columns(4)
    )

    with a1:

        st.metric(
            "Agents Analyzed",
            anomaly_summary.get(
                "agents_analyzed",
                0,
            ),
        )

    with a2:

        st.metric(
            "High Anomaly",
            anomaly_summary.get(
                "high_anomaly_agents",
                0,
            ),
        )

    with a3:

        st.metric(
            "Medium Anomaly",
            anomaly_summary.get(
                "medium_anomaly_agents",
                0,
            ),
        )

    with a4:

        st.metric(
            "Normal",
            anomaly_summary.get(
                "normal_agents",
                0,
            ),
        )

    if anomaly_results:

        anomaly_rows = []

        for item in anomaly_results:

            anomaly_rows.append(
                {
                    "Agent":
                        item.get(
                            "agent_id",
                            "",
                        ),

                    "Anomaly Score":
                        safe_float(
                            item.get(
                                "anomaly_score",
                                0,
                            )
                        ),

                    "Severity":
                        item.get(
                            "anomaly_severity",
                            "NORMAL",
                        ),

                    "Average Risk":
                        safe_float(
                            item.get(
                                "average_risk",
                                0,
                            )
                        ),
                }
            )

        anomaly_df = pd.DataFrame(
            anomaly_rows
        )

        st.dataframe(
            anomaly_df,
            width="stretch",
            hide_index=True,
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

        st.metric(
            "Agents Profiled",
            len(
                behavior_df
            ),
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
                "Explore Feature",
                available_features,
                key="day18_feature",
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

    inv1, inv2, inv3 = (
        st.columns(3)
    )

    with inv1:

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

    with inv2:

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

    with inv3:

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
        "🔍 Investigate Events",
        type="primary",
        key="investigate_events",
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

            st.session_state[
                "investigation_results"
            ] = results

            st.session_state[
                "investigation_executed"
            ] = True

        except Exception as error:

            st.error(
                "Investigation failed: "
                f"{error}"
            )

    if st.session_state[
        "investigation_executed"
    ]:

        results = st.session_state[
            "investigation_results"
        ]

        if results:

            investigation_df = pd.DataFrame(
                results
            )

            st.metric(
                "Matching Events",
                len(
                    results
                ),
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
            "total_requests",
            "denied_requests",
        }

        if required_columns.issubset(
            agent_df.columns
        ):

            st.subheader(
                "Request Activity"
            )

            st.bar_chart(
                agent_df[
                    [
                        "agent_id",
                        "total_requests",
                        "denied_requests",
                    ]
                ]
                .set_index(
                    "agent_id"
                ),
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
        "🔥 High-Risk Security Events"
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
    "🏗️ AegisGuard Research Architecture"
)

architecture1, architecture2 = (
    st.columns(2)
)

with architecture1:

    st.markdown(
        """
        ### Security Control Plane

        Agent Request

        ↓

        Identity / Authorization

        ↓

        Policy Evaluation

        ↓

        Risk Assessment

        ↓

        ALLOW / DENY

        ↓

        Security Telemetry
        """
    )

with architecture2:

    st.markdown(
        """
        ### Research Intelligence Pipeline

        Security Telemetry

        ↓

        Behavioral Features

        ↓

        Anomaly Detection

        ↓

        Integrated Intelligence

        ↓

        Controlled Scenarios

        ↓

        Attack Taxonomy

        ↓

        Experimental Dataset

        ↓

        Quantitative Evaluation
        """
    )


# ============================================================
# DAY 23 MILESTONE
# ============================================================

st.divider()

st.header(
    "🔬 Day 23 Research Milestone"
)

st.markdown(
    """
    ### Reproducible Experimental Dataset

    AegisGuard can now transform controlled security
    scenarios into structured experimental events.

    Each event records:

    **Scenario → Agent → Action → Resource → Severity →
    Ground Truth → Risk → Decision → Sequence →
    Timestamp → Experiment Seed**

    This establishes the data foundation required for
    quantitative evaluation in the next research phase.

    The generated dataset supports:

    - Reproducible experiments
    - Ground-truth classification
    - Risk analysis
    - Authorization outcome analysis
    - Behavioral evaluation
    - CSV export
    - JSONL export
    - Dataset integrity validation
    """
)

st.caption(
    "AegisGuard — Behavior-Aware Security Control Plane "
    "for Autonomous AI Agents"
)

st.caption(
    "Day 23 • Experimental Dataset Generation"
)