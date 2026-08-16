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
# AEGISGUARD — INVESTIGATION
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
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AegisGuard Intelligence SOC",
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


def clamp(value, minimum=0.0, maximum=100.0):
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
    Build a unified security-intelligence record.

    This is an integration layer, not a new ML model.
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
            /
            total_requests
        )

    else:

        denial_rate = 0.0


    # --------------------------------------------------------
    # ANOMALY SIGNAL
    # --------------------------------------------------------

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


    # Convert the statistical anomaly score
    # into a bounded intelligence signal.

    anomaly_signal = clamp(
        anomaly_score
        / 3.0
        * 100.0
    )


    # --------------------------------------------------------
    # DENIAL SIGNAL
    # --------------------------------------------------------

    denial_signal = clamp(
        denial_rate * 100.0
    )


    # --------------------------------------------------------
    # RISK SIGNAL
    # --------------------------------------------------------

    risk_signal = clamp(
        maximum_risk
    )


    # --------------------------------------------------------
    # SUSPICIOUS BEHAVIOR SIGNAL
    # --------------------------------------------------------

    suspicious_signal = 100.0 if (
        agent_id in suspicious_lookup
    ) else 0.0


    # --------------------------------------------------------
    # ANOMALY SEVERITY BONUS
    # --------------------------------------------------------

    severity_bonus = {

        "NORMAL": 0.0,

        "LOW": 5.0,

        "MEDIUM": 15.0,

        "HIGH": 25.0,

    }.get(
        anomaly_severity,
        0.0,
    )


    # --------------------------------------------------------
    # UNIFIED INTELLIGENCE SCORE
    # --------------------------------------------------------

    intelligence_score = (
        (risk_signal * 0.35)
        +
        (denial_signal * 0.25)
        +
        (anomaly_signal * 0.25)
        +
        (suspicious_signal * 0.15)
        +
        severity_bonus
    )


    intelligence_score = clamp(
        intelligence_score
    )


    # --------------------------------------------------------
    # PRIORITY
    # --------------------------------------------------------

    if intelligence_score >= 80:

        priority = "CRITICAL"

    elif intelligence_score >= 60:

        priority = "HIGH"

    elif intelligence_score >= 35:

        priority = "MEDIUM"

    else:

        priority = "LOW"


    # --------------------------------------------------------
    # RECOMMENDED ACTION
    # --------------------------------------------------------

    if priority == "CRITICAL":

        recommended_action = (
            "Immediate investigation and "
            "containment review"
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
    "Integrated behavior-aware security intelligence "
    "for autonomous AI agent authorization and monitoring"
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

    show_investigation = st.checkbox(
        "Investigation",
        value=True,
    )

    show_features = st.checkbox(
        "Behavioral Features",
        value=True,
    )

    show_anomalies = st.checkbox(
        "Anomaly Detection",
        value=True,
    )

    show_intelligence = st.checkbox(
        "Integrated Intelligence",
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
        **Day 16**
        Security Operations Center

        ↓

        **Day 17**
        Event Investigation

        ↓

        **Day 18**
        Behavioral Feature Engineering

        ↓

        **Day 19**
        Behavioral Anomaly Detection

        ↓

        **Day 20**
        Integrated Security Intelligence
        """
    )

    st.divider()

    st.caption(
        "AegisGuard Research Prototype"
    )

    st.caption(
        "Day 20 • Intelligence Integration"
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
        "Unable to load core AegisGuard security data: "
        f"{error}"
    )

    st.stop()


# ============================================================
# LOAD BEHAVIORAL DATA
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
# BUILD LOOKUP TABLES
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
# BUILD INTEGRATED AGENT INTELLIGENCE
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
# DAY 20 — SECURITY OVERVIEW
# ============================================================

if show_overview:

    st.header(
        "📊 Security Overview"
    )

    overview_1, overview_2, overview_3, overview_4, overview_5 = (
        st.columns(5)
    )


    with overview_1:

        st.metric(
            "Total Events",
            total_events,
        )


    with overview_2:

        st.metric(
            "Allowed",
            decisions.get(
                "ALLOW",
                0,
            ),
        )


    with overview_3:

        st.metric(
            "Denied",
            decisions.get(
                "DENY",
                0,
            ),
        )


    with overview_4:

        st.metric(
            "Average Risk",
            risk.get(
                "average_risk",
                0,
            ),
        )


    with overview_5:

        st.metric(
            "Critical Events",
            risk.get(
                "critical_events",
                0,
            ),
        )


    st.divider()

    risk_1, risk_2, risk_3, risk_4 = (
        st.columns(4)
    )


    with risk_1:

        st.metric(
            "Maximum Risk",
            risk.get(
                "maximum_risk",
                0,
            ),
        )


    with risk_2:

        st.metric(
            "High-Risk Events",
            risk.get(
                "high_risk_events",
                0,
            ),
        )


    with risk_3:

        st.metric(
            "Suspicious Agents",
            len(
                suspicious_agents
            ),
        )


    with risk_4:

        st.metric(
            "Repeated Denial Patterns",
            len(
                repeated_denials
            ),
        )


    chart_1, chart_2 = (
        st.columns(2)
    )


    with chart_1:

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


    with chart_2:

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
        "Unified prioritization of agent security behavior "
        "using authorization, risk, behavioral and anomaly signals."
    )


    if not intelligence_df.empty:

        # ----------------------------------------------------
        # INTELLIGENCE SUMMARY
        # ----------------------------------------------------

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


        intelligence_1, intelligence_2, intelligence_3, intelligence_4, intelligence_5 = (
            st.columns(5)
        )


        with intelligence_1:

            st.metric(
                "Avg Intelligence Score",
                avg_intelligence,
            )


        with intelligence_2:

            st.metric(
                "Critical",
                critical_count,
            )


        with intelligence_3:

            st.metric(
                "High",
                high_count,
            )


        with intelligence_4:

            st.metric(
                "Medium",
                medium_count,
            )


        with intelligence_5:

            st.metric(
                "Low",
                low_count,
            )


        # ----------------------------------------------------
        # PRIORITIZATION TABLE
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # INTELLIGENCE SCORE
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # SIGNAL CONTRIBUTION
        # ----------------------------------------------------

        st.subheader(
            "Security Signal Composition"
        )


        signal_df = intelligence_df[
            [
                "agent_id",
                "maximum_risk",
                "denial_rate",
                "anomaly_score",
            ]
        ].copy()


        signal_df = signal_df.rename(
            columns={
                "maximum_risk": "Risk Signal",
                "denial_rate": "Denial Signal",
                "anomaly_score": "Anomaly Signal",
            }
        )


        signal_df = (
            signal_df
            .set_index(
                "agent_id"
            )
        )


        st.dataframe(
            signal_df,
            width="stretch",
        )


        # ----------------------------------------------------
        # PRIORITY FILTER
        # ----------------------------------------------------

        st.subheader(
            "Priority Investigation Queue"
        )


        selected_priority = st.selectbox(
            "Select Priority",
            [
                "ALL",
                "CRITICAL",
                "HIGH",
                "MEDIUM",
                "LOW",
            ],
            key="selected_priority",
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
                "No agents currently match the selected priority."
            )


        # ----------------------------------------------------
        # SECURITY RECOMMENDATIONS
        # ----------------------------------------------------

        st.subheader(
            "Security Response Recommendations"
        )


        critical_agents = (
            intelligence_df[
                intelligence_df[
                    "priority"
                ]
                == "CRITICAL"
            ]
        )


        high_agents = (
            intelligence_df[
                intelligence_df[
                    "priority"
                ]
                == "HIGH"
            ]
        )


        if not critical_agents.empty:

            st.error(
                f"{len(critical_agents)} agent(s) require "
                "immediate investigation and containment review."
            )


        elif not high_agents.empty:

            st.warning(
                f"{len(high_agents)} agent(s) require "
                "prioritized analyst investigation."
            )


        else:

            st.success(
                "No critical or high-priority agent behavior "
                "is currently identified by the integrated baseline."
            )


    else:

        st.info(
            "Integrated intelligence requires agent activity data."
        )


# ============================================================
# DAY 19 — ANOMALY DETECTION
# ============================================================

if show_anomalies:

    st.divider()

    st.header(
        "🚨 Behavioral Anomaly Detection"
    )


    anomaly_1, anomaly_2, anomaly_3, anomaly_4 = (
        st.columns(4)
    )


    with anomaly_1:

        st.metric(
            "Agents Analyzed",
            anomaly_summary.get(
                "agents_analyzed",
                0,
            ),
        )


    with anomaly_2:

        st.metric(
            "High Anomaly",
            anomaly_summary.get(
                "high_anomaly_agents",
                0,
            ),
        )


    with anomaly_3:

        st.metric(
            "Medium Anomaly",
            anomaly_summary.get(
                "medium_anomaly_agents",
                0,
            ),
        )


    with anomaly_4:

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
                        )
                        * 100,
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
            ]
            .set_index(
                "Agent"
            ),
            width="stretch",
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


        feature_1, feature_2, feature_3 = (
            st.columns(3)
        )


        with feature_1:

            st.metric(
                "Agents Profiled",
                len(
                    behavior_df
                ),
            )


        with feature_2:

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


        with feature_3:

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


        available_features = [
            feature
            for feature
            in get_behavior_feature_names()
            if feature
            in behavior_df.columns
        ]


        if available_features:

            selected_feature = st.selectbox(
                "Explore Feature",
                available_features,
                key="day20_feature_explorer",
            )


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
# DAY 17 — INVESTIGATION ENGINE
# ============================================================

if show_investigation:

    st.divider()

    st.header(
        "🔎 Security Investigation Engine"
    )

    st.caption(
        "Use this layer to investigate events surfaced "
        "by the integrated intelligence pipeline."
    )


    try:

        filter_options = (
            get_investigation_filter_options()
        )

    except Exception:

        filter_options = {
            "agents": [],
            "tasks": [],
            "actions": [],
            "resources": [],
        }


    investigation_1, investigation_2, investigation_3 = (
        st.columns(3)
    )


    with investigation_1:

        selected_agent = st.selectbox(
            "Agent",
            [
                "ALL"
            ]
            + filter_options.get(
                "agents",
                [],
            ),
            key="day20_investigation_agent",
        )


    with investigation_2:

        selected_action = st.selectbox(
            "Action",
            [
                "ALL"
            ]
            + filter_options.get(
                "actions",
                [],
            ),
            key="day20_investigation_action",
        )


    with investigation_3:

        selected_decision = st.selectbox(
            "Decision",
            [
                "ALL",
                "ALLOW",
                "DENY",
            ],
            key="day20_investigation_decision",
        )


    investigation_button, reset_button = (
        st.columns(2)
    )


    with investigation_button:

        run_investigation = st.button(
            "🔍 Investigate Events",
            width="stretch",
            type="primary",
        )


    with reset_button:

        reset_investigation = st.button(
            "↺ Clear Results",
            width="stretch",
        )


    if reset_investigation:

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

        investigation_results = (
            st.session_state.investigation_results
        )


        if investigation_results:

            investigation_df = pd.DataFrame(
                investigation_results
            )


            st.metric(
                "Matching Events",
                len(
                    investigation_results
                ),
            )


            st.dataframe(
                investigation_df,
                width="stretch",
                hide_index=True,
            )


            event_ids = [
                event.get("id")
                for event
                in investigation_results
                if event.get("id")
                is not None
            ]


            if event_ids:

                st.subheader(
                    "Selected Event Evidence"
                )


                selected_event_id = st.selectbox(
                    "Event ID",
                    event_ids,
                    key="day20_selected_event",
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

            agent_chart_df = agent_df[
                [
                    "agent_id",
                    "total_requests",
                    "denied_requests",
                ]
            ].copy()


            agent_chart_df = (
                agent_chart_df
                .set_index(
                    "agent_id"
                )
            )


            st.subheader(
                "Request Activity"
            )


            st.bar_chart(
                agent_chart_df,
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
# SECURITY INTELLIGENCE ARCHITECTURE
# ============================================================

st.divider()

st.header(
    "🏗️ AegisGuard Intelligence Architecture"
)

architecture_col_1, architecture_col_2 = (
    st.columns(2)
)


with architecture_col_1:

    st.markdown(
        """
        ### Enforcement Layer

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

        **Audit Event**
        """
    )


with architecture_col_2:

    st.markdown(
        """
        ### Intelligence Layer

        **Audit Events**

        ↓

        **Behavioral Features**

        ↓

        **Anomaly Detection**

        ↓

        **Agent Intelligence Score**

        ↓

        **Priority Classification**

        ↓

        **Investigation Queue**
        """
    )


# ============================================================
# DAY 20 RESEARCH CONTRIBUTION
# ============================================================

st.divider()

st.header(
    "🔬 Day 20 Research Contribution"
)

st.markdown(
    """
    ### Integrated Security Intelligence

    AegisGuard now combines multiple security signals
    into an analyst-oriented intelligence layer.

    **1. Authorization Signal**

    Whether an agent's request was permitted or denied.

    **2. Risk Signal**

    The contextual risk associated with observed activity.

    **3. Behavioral Signal**

    Agent-level behavior represented through engineered
    statistical features.

    **4. Anomaly Signal**

    Deviation of observed behavior from the behavioral
    baseline.

    **5. Suspicion Signal**

    Existing behavioral security classifications.

    **6. Intelligence Score**

    A bounded prioritization score combining the above
    signals for analyst triage.

    **7. Investigation**

    High-priority agents can be traced back to individual
    security events and evidence.

    This creates a complete analytical path from:

    **Agent Request → Enforcement → Telemetry →
    Behavioral Analysis → Anomaly Detection →
    Intelligence → Investigation**
    """
)


# ============================================================
# RESEARCH LIMITATION
# ============================================================

st.warning(
    "Research limitation: the integrated intelligence score "
    "is a transparent prioritization baseline, not a validated "
    "production threat score. Its weights and thresholds must "
    "be experimentally evaluated against controlled datasets "
    "before making security-performance claims."
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
    "Research Prototype • Day 20 • Integrated Security Intelligence"
)