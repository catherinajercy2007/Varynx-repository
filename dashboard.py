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
# INVESTIGATION ENGINE
# ============================================================

from app.investigation import (
    get_investigation_events,
    get_investigation_event,
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
}

for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:
        st.session_state[key] = value


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

    recommendations = {
        "CRITICAL":
            "Immediate investigation and containment review",

        "HIGH":
            "Prioritize analyst investigation",

        "MEDIUM":
            "Increase monitoring and review behavior",

        "LOW":
            "Continue normal monitoring",
    }

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
        "recommended_action":
            recommendations[priority],
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

    show_day21 = st.checkbox(
        "Day 21 Scenario Lab",
        value=True,
    )

    show_day22 = st.checkbox(
        "Day 22 Attack Research",
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
        Attack Scenario Research
        """
    )

    st.divider()

    st.caption(
        "AegisGuard Research Prototype"
    )

    st.caption(
        "Day 22 • Attack Scenario Framework"
    )


# ============================================================
# LOAD CORE DATA
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
# LOOKUPS
# ============================================================

anomaly_lookup = {
    str(
        item.get(
            "agent_id",
            "",
        )
    ): item

    for item
    in anomaly_results
}

suspicious_lookup = {
    str(
        item.get(
            "agent_id",
            "",
        )
    )

    for item
    in suspicious_agents
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
# DAY 16 — SECURITY OVERVIEW
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

    st.divider()

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

        priority_counts = (
            intelligence_df[
                "priority"
            ]
            .value_counts()
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
                "Avg Intelligence",
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

        intelligence_view = (
            intelligence_df
            .sort_values(
                "intelligence_score",
                ascending=False,
            )
        )

        st.dataframe(
            intelligence_view,
            width="stretch",
            hide_index=True,
        )

        st.subheader(
            "Agent Intelligence Scores"
        )

        st.bar_chart(
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
                "intelligence_score",
                ascending=False,
            ),
            width="stretch",
        )


# ============================================================
# DAY 21 — CONTROLLED SECURITY SCENARIOS
# ============================================================

if show_day21:

    st.divider()

    st.header(
        "🧪 Day 21 — Controlled Security Scenario Lab"
    )

    st.caption(
        "Reproducible benign, suspicious and malicious "
        "security scenarios."
    )

    try:

        scenario_summary = (
            get_scenario_summary()
        )

    except Exception as error:

        st.error(
            "Unable to load Day 21 scenarios: "
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

    scenario_filter = st.selectbox(
        "Scenario Class",
        [
            "ALL",
            BENIGN,
            SUSPICIOUS,
            MALICIOUS,
        ],
        key="day21_filter",
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

        columns = [
            "scenario_id",
            "scenario_type",
            "agent_id",
            "task_id",
            "action",
            "resource",
            "expected_behavior",
        ]

        st.dataframe(
            scenario_df[
                [
                    c
                    for c
                    in columns
                    if c
                    in scenario_df.columns
                ]
            ],
            width="stretch",
            hide_index=True,
        )

    if scenarios:

        selected_id = st.selectbox(
            "Inspect Scenario",
            [
                item[
                    "scenario_id"
                ]
                for item
                in scenarios
            ],
            key="day21_selected_id",
        )

        selected = next(
            (
                item
                for item
                in scenarios
                if item[
                    "scenario_id"
                ]
                == selected_id
            ),
            None,
        )

        if selected:

            left, right = (
                st.columns(2)
            )

            with left:

                st.markdown(
                    "### Definition"
                )

                st.write(
                    "**Agent:** "
                    f"`{selected['agent_id']}`"
                )

                st.write(
                    "**Task:** "
                    f"`{selected['task_id']}`"
                )

                st.write(
                    "**Class:** "
                    f"`{selected['scenario_type']}`"
                )

            with right:

                st.markdown(
                    "### Operation"
                )

                st.write(
                    "**Action:** "
                    f"`{selected['action']}`"
                )

                st.write(
                    "**Resource:** "
                    f"`{selected['resource']}`"
                )

                st.write(
                    "**Expected:** "
                    f"`{selected['expected_behavior']}`"
                )

            st.info(
                selected.get(
                    "description",
                    "",
                )
            )


# ============================================================
# DAY 22 — ATTACK SCENARIO RESEARCH LAB
# ============================================================

if show_day22:

    st.divider()

    st.header(
        "⚔️ Day 22 — Controlled Attack Scenario Research Lab"
    )

    st.caption(
        "Structured attack scenarios for reproducible "
        "security detection experiments."
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    try:

        attack_summary = (
            get_attack_scenario_summary()
        )

    except Exception as error:

        st.error(
            "Unable to load attack scenarios: "
            f"{error}"
        )

        attack_summary = {
            "total": 0,
            "malicious": 0,
            "benign": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }

    a1, a2, a3, a4, a5 = (
        st.columns(5)
    )

    with a1:

        st.metric(
            "Total Scenarios",
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

    st.divider()

    # --------------------------------------------------------
    # FILTERS
    # --------------------------------------------------------

    st.subheader(
        "Attack Scenario Catalog"
    )

    filter1, filter2 = (
        st.columns(2)
    )

    with filter1:

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

    with filter2:

        attack_severity = st.selectbox(
            "Severity",
            [
                "ALL",
                "CRITICAL",
                "HIGH",
                "MEDIUM",
                "LOW",
            ],
            key="day22_attack_severity",
        )

    if attack_type == "ALL":

        filtered_attacks = (
            get_attack_scenarios()
        )

    else:

        filtered_attacks = (
            get_attack_scenarios_by_type(
                attack_type
            )
        )

    if attack_severity != "ALL":

        filtered_attacks = [
            item
            for item
            in filtered_attacks
            if item[
                "severity"
            ]
            == attack_severity
        ]

    # --------------------------------------------------------
    # TABLE
    # --------------------------------------------------------

    if filtered_attacks:

        attack_df = pd.DataFrame(
            filtered_attacks
        )

        display_columns = [
            "scenario_id",
            "name",
            "scenario_type",
            "agent_id",
            "severity",
            "ground_truth",
            "expected_signal",
        ]

        display_columns = [
            column
            for column
            in display_columns
            if column
            in attack_df.columns
        ]

        st.dataframe(
            attack_df[
                display_columns
            ],
            width="stretch",
            hide_index=True,
        )

    else:

        st.info(
            "No attack scenarios match the selected filters."
        )

    # --------------------------------------------------------
    # INVESTIGATION
    # --------------------------------------------------------

    if filtered_attacks:

        st.subheader(
            "Attack Scenario Investigation"
        )

        selected_attack_id = st.selectbox(
            "Select Attack Scenario",
            [
                item[
                    "scenario_id"
                ]
                for item
                in filtered_attacks
            ],
            key="day22_selected_attack",
        )

        selected_attack = (
            get_attack_scenario(
                selected_attack_id
            )
        )

        if selected_attack:

            detail1, detail2 = (
                st.columns(2)
            )

            with detail1:

                st.markdown(
                    "### Scenario Definition"
                )

                st.write(
                    "**ID:** "
                    f"`{selected_attack['scenario_id']}`"
                )

                st.write(
                    "**Name:** "
                    f"{selected_attack['name']}"
                )

                st.write(
                    "**Category:** "
                    f"`{selected_attack['scenario_type']}`"
                )

                st.write(
                    "**Agent:** "
                    f"`{selected_attack['agent_id']}`"
                )

                st.write(
                    "**Task:** "
                    f"`{selected_attack['task_id']}`"
                )

                st.write(
                    "**Severity:** "
                    f"`{selected_attack['severity']}`"
                )

            with detail2:

                st.markdown(
                    "### Research Ground Truth"
                )

                st.write(
                    "**Ground Truth:** "
                    f"`{selected_attack['ground_truth']}`"
                )

                st.write(
                    "**Expected Signal:** "
                    f"`{selected_attack['expected_signal']}`"
                )

                st.markdown(
                    "**Actions**"
                )

                for action in selected_attack[
                    "actions"
                ]:

                    st.code(
                        action
                    )

                st.markdown(
                    "**Resources**"
                )

                for resource in selected_attack[
                    "resources"
                ]:

                    st.code(
                        resource
                    )

            st.info(
                selected_attack[
                    "description"
                ]
            )

            st.success(
                "Evaluation purpose: "
                + selected_attack[
                    "evaluation_purpose"
                ]
            )

    # --------------------------------------------------------
    # REPRODUCIBLE EXPERIMENT
    # --------------------------------------------------------

    st.subheader(
        "Reproducible Attack Experiment"
    )

    e1, e2 = (
        st.columns(2)
    )

    with e1:

        attack_count = st.number_input(
            "Scenario Count",
            min_value=1,
            max_value=8,
            value=8,
            step=1,
            key="day22_attack_count",
        )

    with e2:

        attack_seed = st.number_input(
            "Experiment Seed",
            min_value=0,
            max_value=999999,
            value=42,
            step=1,
            key="day22_attack_seed",
        )

    if st.button(
        "⚔️ Generate Attack Experiment",
        key="day22_generate_attack",
        type="primary",
    ):

        try:

            generated = (
                sample_attack_scenarios(
                    count=int(
                        attack_count
                    ),
                    seed=int(
                        attack_seed
                    ),
                )
            )

            st.session_state[
                "day22_attack_experiment"
            ] = pd.DataFrame(
                generated
            )

            st.success(
                "Reproducible attack experiment generated."
            )

        except Exception as error:

            st.error(
                "Attack experiment failed: "
                f"{error}"
            )

    # --------------------------------------------------------
    # EXPERIMENT OUTPUT
    # --------------------------------------------------------

    experiment_df = (
        st.session_state.get(
            "day22_attack_experiment"
        )
    )

    if experiment_df is not None:

        st.subheader(
            "Generated Experimental Dataset"
        )

        st.dataframe(
            experiment_df,
            width="stretch",
            hide_index=True,
        )

        attack_csv = (
            experiment_df
            .to_csv(
                index=False
            )
            .encode(
                "utf-8"
            )
        )

        st.download_button(
            "⬇️ Export Attack Experiment",
            data=attack_csv,
            file_name=(
                "aegisguard_day22_attack_scenarios.csv"
            ),
            mime="text/csv",
            key="day22_export",
        )

    # --------------------------------------------------------
    # SEVERITY DISTRIBUTION
    # --------------------------------------------------------

    st.subheader(
        "Attack Severity Distribution"
    )

    severity_df = pd.DataFrame(
        {
            "Severity": [
                "CRITICAL",
                "HIGH",
                "MEDIUM",
                "LOW",
            ],

            "Count": [
                attack_summary.get(
                    "critical",
                    0,
                ),

                attack_summary.get(
                    "high",
                    0,
                ),

                attack_summary.get(
                    "medium",
                    0,
                ),

                attack_summary.get(
                    "low",
                    0,
                ),
            ],
        }
    )

    st.bar_chart(
        severity_df.set_index(
            "Severity"
        ),
        width="stretch",
    )

    # --------------------------------------------------------
    # RESEARCH SIGNIFICANCE
    # --------------------------------------------------------

    st.subheader(
        "Day 22 Research Significance"
    )

    st.markdown(
        """
        Day 22 introduces a structured attack taxonomy
        for controlled security evaluation.

        Each scenario defines:

        **Attack Type → Agent → Task → Actions → Resources
        → Severity → Ground Truth → Expected Signal**

        The framework deliberately includes legitimate
        high-volume activity so that future experiments
        can measure false-positive behavior rather than
        evaluating only obvious malicious cases.

        These scenarios form the basis for the experimental
        dataset and evaluation pipeline planned for Days 23–30.
        """
    )


# ============================================================
# DAY 19 — ANOMALY DETECTION
# ============================================================

if show_anomalies:

    st.divider()

    st.header(
        "🚨 Behavioral Anomaly Detection"
    )

    an1, an2, an3, an4 = (
        st.columns(4)
    )

    with an1:

        st.metric(
            "Agents Analyzed",
            anomaly_summary.get(
                "agents_analyzed",
                0,
            ),
        )

    with an2:

        st.metric(
            "High Anomaly",
            anomaly_summary.get(
                "high_anomaly_agents",
                0,
            ),
        )

    with an3:

        st.metric(
            "Medium Anomaly",
            anomaly_summary.get(
                "medium_anomaly_agents",
                0,
            ),
        )

    with an4:

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

                    "Critical Requests":
                        safe_int(
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


# ============================================================
# DAY 18 — BEHAVIORAL FEATURES
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

            available_features = [
                feature
                for feature
                in feature_names
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
                    key="feature_explorer",
                )
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
# DAY 17 — INVESTIGATION
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

        investigation_agent = (
            st.selectbox(
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
        )

    with inv2:

        investigation_action = (
            st.selectbox(
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
        )

    with inv3:

        investigation_decision = (
            st.selectbox(
                "Decision",
                [
                    "ALL",
                    "ALLOW",
                    "DENY",
                ],
                key="investigation_decision",
            )
        )

    if st.button(
        "🔍 Investigate Events",
        type="primary",
        key="run_investigation",
    ):

        try:

            results = (
                get_investigation_events(
                    agent_id=(
                        None
                        if investigation_agent
                        == "ALL"
                        else investigation_agent
                    ),

                    action=(
                        None
                        if investigation_action
                        == "ALL"
                        else investigation_action
                    ),

                    decision=(
                        None
                        if investigation_decision
                        == "ALL"
                        else investigation_decision
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

    if (
        st.session_state[
            "investigation_executed"
        ]
    ):

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
                "No events matched the investigation criteria."
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

        required_agent_columns = {
            "total_requests",
            "denied_requests",
        }

        if required_agent_columns.issubset(
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

architecture_left, architecture_right = (
    st.columns(2)
)

with architecture_left:

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

with architecture_right:

    st.markdown(
        """
        ### Research Intelligence

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

        Attack Experiments

        ↓

        Quantitative Evaluation
        """
    )


# ============================================================
# DAY 22 RESEARCH MILESTONE
# ============================================================

st.divider()

st.header(
    "🔬 Day 22 Research Milestone"
)

st.markdown(
    """
    **Controlled Attack Scenario Framework**

    Day 22 extends the controlled scenario system into a
    structured attack taxonomy.

    The experimental framework now distinguishes:

    - Direct unauthorized access
    - Repeated authorization abuse
    - Privilege expansion
    - High-risk request bursts
    - Resource enumeration
    - Behavioral drift
    - Legitimate high-volume activity
    - Multi-stage attack sequences

    Every scenario has an explicit ground-truth label,
    severity classification and expected security signal.

    This makes the scenarios suitable for controlled
    experimental evaluation during the next phase of
    AegisGuard development.
    """
)


# ============================================================
# RESEARCH WARNING
# ============================================================

st.warning(
    "Research limitation: these are controlled synthetic "
    "scenarios. They must not be presented as evidence of "
    "real-world attack detection until validated through "
    "appropriate datasets, experiments and statistical analysis."
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
    "Research Prototype • Day 22 • Controlled Attack Scenarios"
)