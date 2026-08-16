import streamlit as st
import pandas as pd

from app.analytics import (
    get_total_events,
    get_decision_counts,
    get_risk_summary,
    get_agent_activity,
    get_high_risk_events,
)

from app.behavior import (
    get_suspicious_agents,
    get_repeated_denials,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AegisGuard SOC",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# HEADER
# ============================================================

st.title("🛡️ AegisGuard Security Operations Center")

st.caption(
    "Behavior-aware authorization, risk monitoring, "
    "security analytics and agent activity intelligence"
)

st.divider()


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
        f"Unable to load AegisGuard security data: {error}"
    )

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("Security Controls")

    st.success("Security engine online")

    st.divider()

    st.subheader("Monitoring Scope")

    show_agent_activity = st.checkbox(
        "Agent Activity",
        value=True,
    )

    show_suspicious_agents = st.checkbox(
        "Suspicious Agents",
        value=True,
    )

    show_repeated_denials = st.checkbox(
        "Repeated Denials",
        value=True,
    )

    show_high_risk = st.checkbox(
        "High-Risk Events",
        value=True,
    )

    st.divider()

    st.caption(
        "AegisGuard Research Prototype"
    )

    st.caption(
        "Day 16 • Advanced Security Operations"
    )


# ============================================================
# SECURITY POSTURE
# ============================================================

st.subheader("Security Posture")

metric_1, metric_2, metric_3, metric_4, metric_5 = st.columns(5)


with metric_1:

    st.metric(
        "Total Events",
        total_events,
    )


with metric_2:

    st.metric(
        "Allowed",
        decisions.get("ALLOW", 0),
    )


with metric_3:

    st.metric(
        "Denied",
        decisions.get("DENY", 0),
    )


with metric_4:

    st.metric(
        "Average Risk",
        risk.get("average_risk", 0),
    )


with metric_5:

    st.metric(
        "Critical Events",
        risk.get("critical_events", 0),
    )


# ============================================================
# RISK OVERVIEW
# ============================================================

st.divider()

st.subheader("Risk Overview")

risk_1, risk_2, risk_3, risk_4 = st.columns(4)


with risk_1:

    st.metric(
        "Maximum Risk",
        risk.get("maximum_risk", 0),
    )


with risk_2:

    st.metric(
        "High-Risk Events",
        risk.get("high_risk_events", 0),
    )


with risk_3:

    st.metric(
        "Suspicious Agents",
        len(suspicious_agents),
    )


with risk_4:

    st.metric(
        "Repeated Denial Patterns",
        len(repeated_denials),
    )


# ============================================================
# AUTHORIZATION + RISK INDICATORS
# ============================================================

st.divider()

left_col, right_col = st.columns(2)


# ============================================================
# AUTHORIZATION DECISIONS
# ============================================================

with left_col:

    st.subheader("Authorization Decisions")

    decision_data = pd.DataFrame(
        {
            "Decision": list(decisions.keys()),
            "Count": list(decisions.values()),
        }
    )

    if not decision_data.empty:

        st.bar_chart(
            decision_data.set_index("Decision"),
            width="stretch",
        )

    else:

        st.info(
            "No authorization decisions available."
        )


# ============================================================
# RISK SECURITY INDICATORS
# ============================================================

with right_col:

    st.subheader("Risk Security Indicators")

    risk_indicator_data = pd.DataFrame(
        {
            "Indicator": [
                "Average Risk",
                "Maximum Risk",
                "High-Risk Events",
                "Critical Events",
            ],
            "Value": [
                risk.get("average_risk", 0),
                risk.get("maximum_risk", 0),
                risk.get("high_risk_events", 0),
                risk.get("critical_events", 0),
            ],
        }
    )

    st.bar_chart(
        risk_indicator_data.set_index("Indicator"),
        width="stretch",
    )

    st.caption(
        "Risk indicators are derived from the "
        "current AegisGuard analytics layer."
    )


# ============================================================
# AGENT INTELLIGENCE
# ============================================================

if show_agent_activity:

    st.divider()

    st.subheader("Agent Intelligence")

    if agents:

        # ----------------------------------------------------
        # CREATE AGENT DATAFRAME
        # ----------------------------------------------------

        agent_df = pd.DataFrame(agents)

        # ----------------------------------------------------
        # AGENT ACTIVITY TABLE
        # ----------------------------------------------------

        st.dataframe(
            agent_df,
            width="stretch",
            hide_index=True,
        )

        # ----------------------------------------------------
        # AGENT RISK RANKING
        # ----------------------------------------------------

        if "maximum_risk" in agent_df.columns:

            st.subheader("Agent Risk Ranking")

            ranking_columns = [
                column
                for column in [
                    "agent_id",
                    "total_requests",
                    "denied_requests",
                    "maximum_risk",
                ]
                if column in agent_df.columns
            ]

            ranked_agents = (
                agent_df[ranking_columns]
                .sort_values(
                    by="maximum_risk",
                    ascending=False,
                )
            )

            st.bar_chart(
                ranked_agents.set_index("agent_id")[
                    "maximum_risk"
                ],
                width="stretch",
            )

        # ----------------------------------------------------
        # AGENT DENIAL RATE
        # ----------------------------------------------------

        if {
            "total_requests",
            "denied_requests",
        }.issubset(agent_df.columns):

            # Avoid division by zero
            agent_df["denial_rate"] = 0.0

            valid_requests = (
                agent_df["total_requests"] > 0
            )

            agent_df.loc[
                valid_requests,
                "denial_rate",
            ] = (
                agent_df.loc[
                    valid_requests,
                    "denied_requests",
                ]
                / agent_df.loc[
                    valid_requests,
                    "total_requests",
                ]
            )

            agent_df["denial_rate"] = (
                agent_df["denial_rate"] * 100
            ).round(2)

            st.subheader("Agent Denial Rate")

            denial_rate_df = (
                agent_df[
                    [
                        "agent_id",
                        "denial_rate",
                    ]
                ]
                .sort_values(
                    by="denial_rate",
                    ascending=False,
                )
            )

            st.bar_chart(
                denial_rate_df.set_index(
                    "agent_id"
                ),
                width="stretch",
            )

            st.caption(
                "Denial rate represents the percentage of "
                "observed requests denied for each agent."
            )

    else:

        st.info(
            "No agent activity available."
        )


# ============================================================
# SUSPICIOUS AGENTS
# ============================================================

if show_suspicious_agents:

    st.divider()

    st.subheader("🚨 Suspicious Agents")

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
# REPEATED DENIAL PATTERNS
# ============================================================

if show_repeated_denials:

    st.divider()

    st.subheader(
        "⚠️ Repeated Authorization Denials"
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

        st.success(
            "No repeated denial patterns detected."
        )


# ============================================================
# HIGH-RISK EVENTS
# ============================================================

if show_high_risk:

    st.divider()

    st.subheader(
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
# SECURITY INTELLIGENCE SUMMARY
# ============================================================

st.divider()

st.subheader("Security Intelligence Summary")

summary_col1, summary_col2 = st.columns(2)


# ------------------------------------------------------------
# CURRENT PROTECTION
# ------------------------------------------------------------

with summary_col1:

    st.markdown(
        """
        ### Current Protection Layers

        - Identity and authorization
        - Policy enforcement
        - Contextual risk assessment
        - Security audit logging
        - Security analytics
        - Behavioral security analytics
        - Suspicious-agent detection
        - Repeated-denial detection
        - High-risk event monitoring
        """
    )


# ------------------------------------------------------------
# RESEARCH ROADMAP
# ------------------------------------------------------------

with summary_col2:

    st.markdown(
        """
        ### Research Evolution

        **Current — Day 16**

        Deterministic security + behavioral monitoring

        **Next — Days 17–18**

        Security investigation + behavioral feature engineering

        **Next — Day 19**

        Anomaly detection research

        **Next — Day 20**

        Integrated behavioral + anomaly intelligence
        """
    )


# ============================================================
# CURRENT SECURITY STATE
# ============================================================

st.divider()

st.subheader("Current Security State")

total_denied = decisions.get("DENY", 0)
total_allowed = decisions.get("ALLOW", 0)

if total_events > 0:

    denial_percentage = (
        total_denied / total_events
    ) * 100

    allow_percentage = (
        total_allowed / total_events
    ) * 100

    state_col1, state_col2, state_col3 = st.columns(3)

    with state_col1:

        st.metric(
            "Authorization Denial Rate",
            f"{denial_percentage:.2f}%",
        )

    with state_col2:

        st.metric(
            "Authorization Allow Rate",
            f"{allow_percentage:.2f}%",
        )

    with state_col3:

        st.metric(
            "Agents Observed",
            len(agents),
        )

else:

    st.info(
        "No security events are currently available."
    )


# ============================================================
# RESEARCH NOTE
# ============================================================

st.divider()

st.info(
    "Research note: Current dashboard metrics represent "
    "development and security-test telemetry. Controlled "
    "datasets with ground-truth labels will be introduced "
    "during the experimental research phases."
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
    "Research Prototype • Day 16 • Advanced Security Operations"
)