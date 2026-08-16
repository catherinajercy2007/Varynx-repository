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
    page_title="AegisGuard Security Dashboard",
    page_icon="🛡️",
    layout="wide",
)


# ============================================================
# HEADER
# ============================================================

st.title("🛡️ AegisGuard Security Dashboard")
st.caption(
    "Authorization, risk and behavioral security monitoring"
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
    st.error(f"Unable to load security data: {error}")
    st.stop()


# ============================================================
# TOP SECURITY METRICS
# ============================================================

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Total Events",
        total_events,
    )

with col2:
    st.metric(
        "Allowed",
        decisions.get("ALLOW", 0),
    )

with col3:
    st.metric(
        "Denied",
        decisions.get("DENY", 0),
    )

with col4:
    st.metric(
        "Average Risk",
        risk.get("average_risk", 0),
    )

with col5:
    st.metric(
        "Critical Events",
        risk.get("critical_events", 0),
    )


st.divider()


# ============================================================
# RISK SUMMARY
# ============================================================

st.subheader("Risk Summary")

risk_col1, risk_col2, risk_col3 = st.columns(3)

with risk_col1:
    st.metric(
        "Maximum Risk",
        risk.get("maximum_risk", 0),
    )

with risk_col2:
    st.metric(
        "High-Risk Events",
        risk.get("high_risk_events", 0),
    )

with risk_col3:
    st.metric(
        "Suspicious Agents",
        len(suspicious_agents),
    )


st.divider()


# ============================================================
# AUTHORIZATION DECISIONS
# ============================================================

st.subheader("Authorization Decisions")

decision_data = pd.DataFrame(
    {
        "Decision": list(decisions.keys()),
        "Count": list(decisions.values()),
    }
)

if not decision_data.empty:
    st.bar_chart(
        decision_data.set_index("Decision")
    )
else:
    st.info("No authorization events available.")


st.divider()


# ============================================================
# AGENT ACTIVITY
# ============================================================

st.subheader("Agent Activity")

if agents:
    agent_df = pd.DataFrame(agents)

    st.dataframe(
        agent_df,
        width="stretch",
        hide_index=True,
    )
else:
    st.info("No agent activity available.")


# ============================================================
# SUSPICIOUS AGENTS
# ============================================================

st.subheader("Suspicious Agents")

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

st.subheader("Repeated Denials")

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

st.subheader("High-Risk Events")

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
# FOOTER
# ============================================================

st.divider()

st.caption(
    "AegisGuard — Security Analytics and Risk Monitoring"
)