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
# DATA LOADING
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


st.divider()


# ============================================================
# RISK OVERVIEW
# ============================================================

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
# DECISION + RISK DISTRIBUTION
# ============================================================

st.divider()

left_col, right_col = st.columns(2)


# ------------------------------------------------------------
# AUTHORIZATION DECISIONS
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# RISK DISTRIBUTION
# ------------------------------------------------------------

with right_col:

    st.subheader("Risk Distribution")

    risk_distribution = pd.DataFrame(
        {
            "Risk Level": [
                "Low",
                "Medium",
                "High",
                "Critical",
            ],
            "Events": [
                risk.get("low_risk_events", 0),
                risk.get("medium_risk_events", 0),
                risk.get("high_risk_events", 0),
                risk.get("critical_events", 0),
            ],
        }
    )

    risk_distribution = risk_distribution[
        risk_distribution["Events"] > 0
    ]

    if not risk_distribution.empty:

        st.bar_chart(
            risk_distribution.set_index(
                "Risk Level"
            ),
            width="stretch",
        )

    else:

        st.info(
            "No risk distribution data available."
        )


# ============================================================
# AGENT INTELLIGENCE
# ============================================================

if show_agent_activity:

    st.divider()

    st.subheader("Agent Intelligence")

    if agents:

        agent_df = pd.DataFrame(agents)

        st.dataframe(
            agent_df,
            width="stretch",
            hide_index=True,
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

    st.subheader("⚠️ Repeated Authorization Denials")

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

    st.subheader("🔥 High-Risk Security Events")

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
# SECURITY SUMMARY
# ============================================================

st.divider()

st.subheader("Security Summary")

summary_col1, summary_col2 = st.columns(2)


with summary_col1:

    st.markdown(
        """
        ### Current Protection Layers

        - Identity and authorization
        - Policy enforcement
        - Risk assessment
        - Security audit logging
        - Behavioral security analytics
        - Suspicious-agent detection
        - High-risk event monitoring
        """
    )


with summary_col2:

    st.markdown(
        """
        ### Research Direction

        **Current:** Deterministic security + behavioral analytics

        **Next:** Feature engineering + anomaly detection

        **Future:** Explainable ML-assisted security intelligence
        """
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