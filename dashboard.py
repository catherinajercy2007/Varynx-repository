import streamlit as st
import pandas as pd


# ============================================================
# AEGISGUARD — CORE SECURITY ANALYTICS
# ============================================================

from app.analytics import (
    get_total_events,
    get_decision_counts,
    get_risk_summary,
    get_agent_activity,
    get_high_risk_events,
)


# ============================================================
# AEGISGUARD — BEHAVIOR ANALYTICS
# ============================================================

from app.behavior import (
    get_suspicious_agents,
    get_repeated_denials,
)


# ============================================================
# AEGISGUARD — INVESTIGATION ENGINE
# ============================================================

from app.investigation import (
    get_investigation_events,
    get_investigation_event,
    get_investigation_filter_options,
)


# ============================================================
# AEGISGUARD — BEHAVIORAL FEATURES
# ============================================================

from app.features import (
    get_behavioral_features,
    get_behavior_feature_names,
)


# ============================================================
# AEGISGUARD — ANOMALY DETECTION
# ============================================================

from app.anomaly import (
    get_behavioral_anomalies,
    get_anomaly_summary,
)


# ============================================================
# AEGISGUARD — DAY 21 SCENARIO FRAMEWORK
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

if "investigation_results" not in st.session_state:
    st.session_state.investigation_results = []

if "investigation_executed" not in st.session_state:
    st.session_state.investigation_executed = False

if "day21_sampled_scenarios" not in st.session_state:
    st.session_state.day21_sampled_scenarios = None


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    try:
        return int(value)
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
    """
    Build an explainable agent-level security
    intelligence record from existing signals.
    """

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

    if total_requests > 0:
        denial_rate = (
            denied_requests
            / total_requests
        )
    else:
        denial_rate = 0.0

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

    anomaly_signal = clamp(
        anomaly_score / 3.0 * 100.0
    )

    denial_signal = clamp(
        denial_rate * 100.0
    )

    risk_signal = clamp(
        maximum_risk
    )

    suspicious_signal = (
        100.0
        if agent_id in suspicious_lookup
        else 0.0
    )

    severity_bonus = {
        "NORMAL": 0.0,
        "LOW": 5.0,
        "MEDIUM": 15.0,
        "HIGH": 25.0,
    }.get(
        anomaly_severity,
        0.0,
    )

    intelligence_score = (
        (risk_signal * 0.35)
        + (denial_signal * 0.25)
        + (anomaly_signal * 0.25)
        + (suspicious_signal * 0.15)
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

    if priority == "CRITICAL":
        recommended_action = (
            "Immediate investigation and containment review"
        )
    elif priority == "HIGH":
        recommended_action = (
            "Prioritize analyst investigation"
        )
    elif priority == "MEDIUM":
        recommended_action = (
            "Increase monitoring and review behavior"
        )
    else:
        recommended_action = (
            "Continue normal monitoring"
        )

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
        "recommended_action": recommended_action,
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
    "investigation and controlled experimentation."
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
        "Dashboard Layers"
    )

    show_overview = st.checkbox(
        "Security Overview",
        value=True,
    )

    show_intelligence = st.checkbox(
        "Integrated Intelligence",
        value=True,
    )

    show_scenarios = st.checkbox(
        "Day 21 Scenario Lab",
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
        """
    )

    st.divider()

    st.caption(
        "AegisGuard Research Prototype"
    )

    st.caption(
        "Day 21 • Experimental Security Scenarios"
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
        "Unable to load core security data: "
        f"{error}"
    )

    st.stop()


# ============================================================
# LOAD BEHAVIORAL FEATURES
# ============================================================

try:

    behavioral_features = (
        get_behavioral_features()
    )

except Exception as error:

    behavioral_features = []

    st.warning(
        "Behavioral feature layer unavailable: "
        f"{error}"
    )


# ============================================================
# LOAD ANOMALY DATA
# ============================================================

try:

    anomaly_results = (
        get_behavioral_anomalies()
    )

    anomaly_summary = (
        get_anomaly_summary()
    )

except Exception as error:

    anomaly_results = []

    anomaly_summary = {
        "agents_analyzed": 0,
        "high_anomaly_agents": 0,
        "medium_anomaly_agents": 0,
        "low_anomaly_agents": 0,
        "normal_agents": 0,
    }

    st.warning(
        "Anomaly detection layer unavailable: "
        f"{error}"
    )


# ============================================================
# BUILD LOOKUPS
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
# BUILD AGENT INTELLIGENCE
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
# DAY 16 — SECURITY OVERVIEW
# ============================================================

if show_overview:

    st.header(
        "📊 Security Overview"
    )

    col1, col2, col3, col4, col5 = (
        st.columns(5)
    )

    with col1:
        st.metric(
            "Total Events",
            total_events,
        )

    with col2:
        st.metric(
            "Allowed",
            decisions.get(
                "ALLOW",
                0,
            ),
        )

    with col3:
        st.metric(
            "Denied",
            decisions.get(
                "DENY",
                0,
            ),
        )

    with col4:
        st.metric(
            "Average Risk",
            risk.get(
                "average_risk",
                0,
            ),
        )

    with col5:
        st.metric(
            "Critical Events",
            risk.get(
                "critical_events",
                0,
            ),
        )

    st.divider()

    risk1, risk2, risk3, risk4 = (
        st.columns(4)
    )

    with risk1:
        st.metric(
            "Maximum Risk",
            risk.get(
                "maximum_risk",
                0,
            ),
        )

    with risk2:
        st.metric(
            "High-Risk Events",
            risk.get(
                "high_risk_events",
                0,
            ),
        )

    with risk3:
        st.metric(
            "Suspicious Agents",
            len(
                suspicious_agents
            ),
        )

    with risk4:
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
# DAY 20 — INTEGRATED SECURITY INTELLIGENCE
# ============================================================

if show_intelligence:

    st.divider()

    st.header(
        "🧠 Integrated Security Intelligence"
    )

    st.caption(
        "Unified prioritization using authorization, "
        "risk, behavioral and anomaly signals."
    )

    if not intelligence_df.empty:

        critical_count = int(
            (
                intelligence_df[
                    "priority"
                ]
                == "CRITICAL"
            ).sum()
        )

        high_count = int(
            (
                intelligence_df[
                    "priority"
                ]
                == "HIGH"
            ).sum()
        )

        medium_count = int(
            (
                intelligence_df[
                    "priority"
                ]
                == "MEDIUM"
            ).sum()
        )

        low_count = int(
            (
                intelligence_df[
                    "priority"
                ]
                == "LOW"
            ).sum()
        )

        avg_intelligence = round(
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
                "Avg Intelligence",
                avg_intelligence,
            )

        with i2:
            st.metric(
                "Critical",
                critical_count,
            )

        with i3:
            st.metric(
                "High",
                high_count,
            )

        with i4:
            st.metric(
                "Medium",
                medium_count,
            )

        with i5:
            st.metric(
                "Low",
                low_count,
            )

        st.subheader(
            "Agent Security Prioritization"
        )

        prioritization_columns = [
            "agent_id",
            "intelligence_score",
            "priority",
            "maximum_risk",
            "denial_rate",
            "anomaly_score",
            "anomaly_severity",
            "total_requests",
            "recommended_action",
        ]

        prioritization_df = (
            intelligence_df[
                [
                    column
                    for column
                    in prioritization_columns
                    if column
                    in intelligence_df.columns
                ]
            ]
            .sort_values(
                by="intelligence_score",
                ascending=False,
            )
        )

        st.dataframe(
            prioritization_df,
            width="stretch",
            hide_index=True,
        )

        st.subheader(
            "Unified Intelligence Score"
        )

        score_chart = (
            intelligence_df[
                [
                    "agent_id",
                    "intelligence_score",
                ]
            ]
            .set_index(
                "agent_id"
            )
            .sort_values(
                by="intelligence_score",
                ascending=False,
            )
        )

        st.bar_chart(
            score_chart,
            width="stretch",
        )

        st.subheader(
            "Priority Investigation Queue"
        )

        selected_priority = st.selectbox(
            "Priority",
            [
                "ALL",
                "CRITICAL",
                "HIGH",
                "MEDIUM",
                "LOW",
            ],
            key="day20_priority",
        )

        if selected_priority == "ALL":

            priority_df = (
                prioritization_df
            )

        else:

            priority_df = (
                prioritization_df[
                    prioritization_df[
                        "priority"
                    ]
                    == selected_priority
                ]
            )

        if not priority_df.empty:

            st.dataframe(
                priority_df,
                width="stretch",
                hide_index=True,
            )

        else:

            st.info(
                "No agents match the selected priority."
            )

        if critical_count > 0:

            st.error(
                f"{critical_count} critical agent(s) "
                "require immediate investigation."
            )

        elif high_count > 0:

            st.warning(
                f"{high_count} high-priority agent(s) "
                "require analyst investigation."
            )

        else:

            st.success(
                "No critical or high-priority agent behavior "
                "is currently identified."
            )


# ============================================================
# DAY 21 — CONTROLLED SECURITY SCENARIO LAB
# ============================================================

if show_scenarios:

    st.divider()

    st.header(
        "🧪 Controlled Security Scenario Lab"
    )

    st.caption(
        "Reproducible benign, suspicious and malicious "
        "scenarios for controlled security experiments."
    )

    # --------------------------------------------------------
    # SCENARIO SUMMARY
    # --------------------------------------------------------

    try:

        scenario_summary = (
            get_scenario_summary()
        )

    except Exception as error:

        st.error(
            "Unable to load scenario framework: "
            f"{error}"
        )

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
            "Total Scenarios",
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

    # --------------------------------------------------------
    # SCENARIO CLASSIFICATION
    # --------------------------------------------------------

    st.subheader(
        "Scenario Catalog"
    )

    scenario_filter = st.selectbox(
        "Scenario Class",
        [
            "ALL",
            BENIGN,
            SUSPICIOUS,
            MALICIOUS,
        ],
        key="day21_scenario_filter",
    )

    if scenario_filter == "ALL":

        scenarios = (
            get_scenario_catalog()
        )

    else:

        scenarios = (
            get_scenarios(
                scenario_filter
            )
        )

    if scenarios:

        scenario_df = pd.DataFrame(
            scenarios
        )

        display_columns = [
            "scenario_id",
            "scenario_type",
            "agent_id",
            "task_id",
            "action",
            "resource",
            "expected_behavior",
        ]

        display_columns = [
            column
            for column
            in display_columns
            if column
            in scenario_df.columns
        ]

        st.dataframe(
            scenario_df[
                display_columns
            ],
            width="stretch",
            hide_index=True,
        )

    else:

        st.info(
            "No scenarios match the selected class."
        )

    # --------------------------------------------------------
    # SCENARIO INVESTIGATION
    # --------------------------------------------------------

    if scenarios:

        st.subheader(
            "Scenario Investigation"
        )

        scenario_ids = [
            scenario[
                "scenario_id"
            ]
            for scenario
            in scenarios
        ]

        selected_scenario_id = (
            st.selectbox(
                "Select Scenario",
                scenario_ids,
                key="day21_selected_scenario",
            )
        )

        selected_scenario = next(
            (
                scenario
                for scenario
                in scenarios
                if scenario[
                    "scenario_id"
                ]
                == selected_scenario_id
            ),
            None,
        )

        if selected_scenario:

            detail1, detail2 = (
                st.columns(2)
            )

            with detail1:

                st.markdown(
                    "### Scenario Definition"
                )

                st.write(
                    "**Scenario ID:** "
                    f"`{selected_scenario['scenario_id']}`"
                )

                st.write(
                    "**Class:** "
                    f"`{selected_scenario['scenario_type']}`"
                )

                st.write(
                    "**Agent:** "
                    f"`{selected_scenario['agent_id']}`"
                )

                st.write(
                    "**Task:** "
                    f"`{selected_scenario['task_id']}`"
                )

            with detail2:

                st.markdown(
                    "### Requested Operation"
                )

                st.write(
                    "**Action:** "
                    f"`{selected_scenario['action']}`"
                )

                st.write(
                    "**Resource:** "
                    f"`{selected_scenario['resource']}`"
                )

                st.write(
                    "**Expected Decision:** "
                    f"`{selected_scenario['expected_behavior']}`"
                )

            st.info(
                selected_scenario.get(
                    "description",
                    "No description available.",
                )
            )

    # --------------------------------------------------------
    # REPRODUCIBLE EXPERIMENT SAMPLER
    # --------------------------------------------------------

    st.subheader(
        "Reproducible Experiment Sampler"
    )

    sampler1, sampler2 = (
        st.columns(2)
    )

    with sampler1:

        sample_count = st.number_input(
            "Number of Scenarios",
            min_value=1,
            max_value=50,
            value=9,
            step=1,
            key="day21_sample_count",
        )

    with sampler2:

        random_seed = st.number_input(
            "Experiment Seed",
            min_value=0,
            max_value=999999,
            value=42,
            step=1,
            key="day21_seed",
        )

    if st.button(
        "🎲 Generate Reproducible Scenario Set",
        key="day21_generate_scenarios",
        type="primary",
    ):

        try:

            sampled = sample_scenarios(
                count=int(
                    sample_count
                ),
                seed=int(
                    random_seed
                ),
            )

            sampled_df = pd.DataFrame(
                sampled
            )

            st.session_state[
                "day21_sampled_scenarios"
            ] = sampled_df

            st.success(
                "Reproducible scenario set generated."
            )

        except Exception as error:

            st.error(
                "Unable to generate scenario set: "
                f"{error}"
            )

    if (
        st.session_state[
            "day21_sampled_scenarios"
        ]
        is not None
    ):

        st.subheader(
            "Generated Experimental Dataset"
        )

        st.dataframe(
            st.session_state[
                "day21_sampled_scenarios"
            ],
            width="stretch",
            hide_index=True,
        )

        csv_data = (
            st.session_state[
                "day21_sampled_scenarios"
            ]
            .to_csv(
                index=False
            )
            .encode(
                "utf-8"
            )
        )

        st.download_button(
            "⬇️ Export Scenario Dataset",
            data=csv_data,
            file_name=(
                "aegisguard_day21_scenarios.csv"
            ),
            mime="text/csv",
        )

    # --------------------------------------------------------
    # SCENARIO DISTRIBUTION
    # --------------------------------------------------------

    st.subheader(
        "Scenario Distribution"
    )

    distribution_df = pd.DataFrame(
        {
            "Scenario Type": [
                "Benign",
                "Suspicious",
                "Malicious",
            ],
            "Count": [
                scenario_summary.get(
                    "benign",
                    0,
                ),
                scenario_summary.get(
                    "suspicious",
                    0,
                ),
                scenario_summary.get(
                    "malicious",
                    0,
                ),
            ],
        }
    )

    st.bar_chart(
        distribution_df.set_index(
            "Scenario Type"
        ),
        width="stretch",
    )

    # --------------------------------------------------------
    # RESEARCH METHODOLOGY
    # --------------------------------------------------------

    st.subheader(
        "Experimental Methodology"
    )

    st.markdown(
        """
        **Benign scenarios**

        Represent expected and authorized agent behavior.

        **Suspicious scenarios**

        Represent behavior that violates normal access
        expectations or behavioral patterns.

        **Malicious scenarios**

        Represent controlled unauthorized actions used
        to evaluate AegisGuard's security controls.

        **Reproducibility**

        Every generated scenario set uses an explicit
        random seed. The same seed produces the same
        scenario selection.

        **Research purpose**

        The controlled scenario framework establishes
        labeled experimental cases for the evaluation
        phase beginning with Days 22–30.
        """
    )


# ============================================================
# DAY 19 — BEHAVIORAL ANOMALY DETECTION
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
                    "Agent": item.get(
                        "agent_id",
                        "",
                    ),
                    "Anomaly Score": safe_float(
                        item.get(
                            "anomaly_score",
                            0,
                        )
                    ),
                    "Severity": item.get(
                        "anomaly_severity",
                        "NORMAL",
                    ),
                    "Denial Rate": round(
                        safe_float(
                            item.get(
                                "denial_rate",
                                0,
                            )
                        ) * 100,
                        2,
                    ),
                    "Average Risk": safe_float(
                        item.get(
                            "average_risk",
                            0,
                        )
                    ),
                    "Critical Requests": safe_int(
                        item.get(
                            "critical_requests",
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

        st.subheader(
            "Anomaly Score Distribution"
        )

        st.bar_chart(
            anomaly_df[
                [
                    "Agent",
                    "Anomaly Score",
                ]
            ].set_index(
                "Agent"
            ),
            width="stretch",
        )


# ============================================================
# DAY 18 — BEHAVIORAL FEATURE ANALYTICS
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

        f1, f2, f3 = (
            st.columns(3)
        )

        with f1:

            st.metric(
                "Agents Profiled",
                len(
                    behavior_df
                ),
            )

        with f2:

            if (
                "average_risk"
                in behavior_df.columns
            ):

                st.metric(
                    "Mean Agent Risk",
                    round(
                        float(
                            behavior_df[
                                "average_risk"
                            ].mean()
                        ),
                        2,
                    ),
                )

        with f3:

            if (
                "denial_rate"
                in behavior_df.columns
            ):

                high_denial = int(
                    (
                        behavior_df[
                            "denial_rate"
                        ]
                        >= 0.50
                    ).sum()
                )

                st.metric(
                    "High-Denial Agents",
                    high_denial,
                )

        st.subheader(
            "Behavioral Feature Matrix"
        )

        st.dataframe(
            behavior_df,
            width="stretch",
            hide_index=True,
        )

        try:

            available_features = [
                feature
                for feature
                in get_behavior_feature_names()
                if feature
                in behavior_df.columns
            ]

        except Exception:

            available_features = [
                column
                for column
                in behavior_df.columns
                if column
                != "agent_id"
            ]

        if available_features:

            selected_feature = (
                st.selectbox(
                    "Explore Feature",
                    available_features,
                    key="day21_feature_explorer",
                )
            )

            if "agent_id" in behavior_df.columns:

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
                    .sort_values(
                        by=selected_feature,
                        ascending=False,
                    )
                )

                st.bar_chart(
                    feature_chart,
                    width="stretch",
                )

    else:

        st.info(
            "No behavioral features are available."
        )


# ============================================================
# DAY 17 — SECURITY INVESTIGATION ENGINE
# ============================================================

if show_investigation:

    st.divider()

    st.header(
        "🔎 Security Investigation Engine"
    )

    st.caption(
        "Investigate individual events and retrieve "
        "supporting security evidence."
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

    run_col, clear_col = (
        st.columns(2)
    )

    with run_col:

        run_investigation = st.button(
            "🔍 Investigate Events",
            width="stretch",
            type="primary",
        )

    with clear_col:

        clear_investigation = st.button(
            "↺ Clear Results",
            width="stretch",
        )

    if clear_investigation:

        st.session_state.investigation_results = []

        st.session_state.investigation_executed = False

        st.rerun()

    if run_investigation:

        try:

            results = (
                get_investigation_events(
                    agent_id=(
                        None
                        if selected_agent == "ALL"
                        else selected_agent
                    ),
                    action=(
                        None
                        if selected_action == "ALL"
                        else selected_action
                    ),
                    decision=(
                        None
                        if selected_decision == "ALL"
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
                len(
                    results
                ),
            )

            st.dataframe(
                investigation_df,
                width="stretch",
                hide_index=True,
            )

            event_ids = [
                event.get(
                    "id"
                )
                for event
                in results
                if event.get(
                    "id"
                ) is not None
            ]

            if event_ids:

                st.subheader(
                    "Selected Event Evidence"
                )

                selected_event_id = st.selectbox(
                    "Event ID",
                    event_ids,
                    key="selected_investigation_event",
                )

                selected_event = None

                try:

                    selected_event = (
                        get_investigation_event(
                            int(
                                selected_event_id
                            )
                        )
                    )

                except Exception as error:

                    st.error(
                        "Unable to retrieve event: "
                        f"{error}"
                    )

                if selected_event:

                    evidence_rows = []

                    for field in [
                        "id",
                        "timestamp",
                        "agent_id",
                        "task_id",
                        "action",
                        "resource",
                        "decision",
                        "risk",
                        "reason",
                    ]:

                        evidence_rows.append(
                            {
                                "Evidence Field": field,
                                "Observed Value": str(
                                    selected_event.get(
                                        field,
                                        "",
                                    )
                                ),
                            }
                        )

                    evidence_df = pd.DataFrame(
                        evidence_rows
                    )

                    st.dataframe(
                        evidence_df,
                        width="stretch",
                        hide_index=True,
                    )

        else:

            st.info(
                "No events matched the investigation criteria."
            )


# ============================================================
# AGENT INTELLIGENCE
# ============================================================

if show_agents:

    st.divider()

    st.header(
        "👤 Agent Intelligence"
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

        if {
            "total_requests",
            "denied_requests",
        }.issubset(
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
                "Agent Request Activity"
            )

            st.bar_chart(
                activity_df,
                width="stretch",
            )

    else:

        st.info(
            "No agent activity is currently available."
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
# SECURITY ARCHITECTURE
# ============================================================

st.divider()

st.header(
    "🏗️ AegisGuard Security Research Architecture"
)

architecture1, architecture2 = (
    st.columns(2)
)

with architecture1:

    st.markdown(
        """
        ### Enforcement & Telemetry

        **Agent Request**

        ↓

        **Identity / Authorization**

        ↓

        **Policy Evaluation**

        ↓

        **Risk Assessment**

        ↓

        **ALLOW / DENY**

        ↓

        **Security Telemetry**
        """
    )

with architecture2:

    st.markdown(
        """
        ### Research Intelligence

        **Security Telemetry**

        ↓

        **Behavioral Features**

        ↓

        **Anomaly Detection**

        ↓

        **Integrated Intelligence**

        ↓

        **Controlled Scenarios**

        ↓

        **Experimental Evaluation**
        """
    )


# ============================================================
# DAY 21 RESEARCH MILESTONE
# ============================================================

st.divider()

st.header(
    "🔬 Day 21 Research Milestone"
)

st.markdown(
    """
    ### Controlled Security Scenario Framework

    Day 21 introduces a reproducible experimental layer
    to AegisGuard.

    The framework separates controlled behaviors into:

    **BENIGN**

    Expected and authorized agent behavior.

    **SUSPICIOUS**

    Behavior that deviates from expected access patterns.

    **MALICIOUS**

    Controlled unauthorized behavior designed to test
    security enforcement and detection.

    Each scenario contains a defined agent, task, action,
    resource and expected security decision.

    A deterministic random seed allows experiments to be
    reproduced using the same scenario selection.

    This framework establishes the experimental foundation
    for Days 22–30, where detection performance can be
    evaluated using measurable security metrics.
    """
)


# ============================================================
# RESEARCH METHODOLOGY
# ============================================================

st.subheader(
    "Experimental Research Pipeline"
)

st.markdown(
    """
    ```text
    Controlled Scenario
            ↓
    AegisGuard Security Engine
            ↓
    Authorization Decision
            ↓
    Risk Assessment
            ↓
    Security Telemetry
            ↓
    Behavioral Features
            ↓
    Anomaly Detection
            ↓
    Intelligence Prioritization
            ↓
    Investigation Evidence
            ↓
    Experimental Evaluation
    ```
    """
)


# ============================================================
# RESEARCH LIMITATION
# ============================================================

st.warning(
    "Research limitation: the Day 21 scenarios are "
    "controlled synthetic test cases. They should not be "
    "presented as evidence of real-world attack detection "
    "until they are evaluated against appropriately designed "
    "datasets and experiments."
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
    "Research Prototype • Day 21 • Controlled Security Scenarios"
)