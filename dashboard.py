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

from app.investigation import (
    get_investigation_events,
    get_investigation_event,
    get_investigation_filter_options,
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
# SESSION STATE
# ============================================================

if "investigation_results" not in st.session_state:
    st.session_state.investigation_results = []

if "investigation_executed" not in st.session_state:
    st.session_state.investigation_executed = False


# ============================================================
# HEADER
# ============================================================

st.title("🛡️ AegisGuard Security Operations Center")

st.caption(
    "Behavior-aware authorization, security analytics, "
    "agent monitoring and event investigation"
)

st.divider()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("SOC Controls")

    st.success("Security engine online")

    st.divider()

    st.subheader("Monitoring Modules")

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

    show_investigation = st.checkbox(
        "Investigation Engine",
        value=True,
    )

    st.divider()

    st.caption(
        "AegisGuard Research Prototype"
    )

    st.caption(
        "Day 17 • Security Investigation Engine"
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
        f"Unable to load AegisGuard security data: {error}"
    )

    st.stop()


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

authorization_col, risk_col = st.columns(2)


# ------------------------------------------------------------
# AUTHORIZATION DECISIONS
# ------------------------------------------------------------

with authorization_col:

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
# RISK SECURITY INDICATORS
# ------------------------------------------------------------

with risk_col:

    st.subheader("Risk Security Indicators")

    risk_data = pd.DataFrame(
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
        risk_data.set_index("Indicator"),
        width="stretch",
    )

    st.caption(
        "Indicators are derived from the current "
        "AegisGuard analytics layer."
    )


# ============================================================
# SECURITY INVESTIGATION ENGINE
# ============================================================

if show_investigation:

    st.divider()

    st.header("🔎 Security Investigation Engine")

    st.caption(
        "Investigate individual security events using "
        "structured filters and event-level evidence."
    )

    # --------------------------------------------------------
    # LOAD FILTER OPTIONS
    # --------------------------------------------------------

    try:

        filter_options = (
            get_investigation_filter_options()
        )

    except Exception as error:

        st.error(
            f"Unable to load investigation filters: {error}"
        )

        filter_options = {
            "agents": [],
            "tasks": [],
            "actions": [],
            "resources": [],
        }

    # --------------------------------------------------------
    # FILTER ROW 1
    # --------------------------------------------------------

    filter_col_1, filter_col_2, filter_col_3 = st.columns(3)

    with filter_col_1:

        selected_agent = st.selectbox(
            "Agent",
            ["ALL"] + filter_options.get(
                "agents",
                [],
            ),
            key="investigation_agent",
        )

    with filter_col_2:

        selected_task = st.selectbox(
            "Task",
            ["ALL"] + filter_options.get(
                "tasks",
                [],
            ),
            key="investigation_task",
        )

    with filter_col_3:

        selected_action = st.selectbox(
            "Action",
            ["ALL"] + filter_options.get(
                "actions",
                [],
            ),
            key="investigation_action",
        )

    # --------------------------------------------------------
    # FILTER ROW 2
    # --------------------------------------------------------

    filter_col_4, filter_col_5, filter_col_6 = st.columns(3)

    with filter_col_4:

        selected_resource = st.selectbox(
            "Resource",
            ["ALL"] + filter_options.get(
                "resources",
                [],
            ),
            key="investigation_resource",
        )

    with filter_col_5:

        selected_decision = st.selectbox(
            "Decision",
            [
                "ALL",
                "ALLOW",
                "DENY",
            ],
            key="investigation_decision",
        )

    with filter_col_6:

        selected_risk = st.selectbox(
            "Risk Level",
            [
                "ALL",
                "LOW",
                "MEDIUM",
                "HIGH",
                "CRITICAL",
            ],
            key="investigation_risk",
        )

    # --------------------------------------------------------
    # ADVANCED CONTROLS
    # --------------------------------------------------------

    with st.expander(
        "⚙️ Advanced Investigation Controls"
    ):

        advanced_col_1, advanced_col_2 = st.columns(2)

        with advanced_col_1:

            minimum_risk = st.number_input(
                "Minimum Risk",
                min_value=0,
                max_value=100,
                value=0,
                step=1,
                key="investigation_min_risk",
            )

        with advanced_col_2:

            maximum_risk = st.number_input(
                "Maximum Risk",
                min_value=0,
                max_value=100,
                value=100,
                step=1,
                key="investigation_max_risk",
            )

        investigation_limit = st.slider(
            "Maximum Events to Display",
            min_value=10,
            max_value=500,
            value=100,
            step=10,
            key="investigation_limit",
        )

    # --------------------------------------------------------
    # RISK RANGE VALIDATION
    # --------------------------------------------------------

    valid_risk_range = (
        minimum_risk <= maximum_risk
    )

    if not valid_risk_range:

        st.warning(
            "Minimum risk cannot be greater than "
            "maximum risk."
        )

    # --------------------------------------------------------
    # INVESTIGATION ACTIONS
    # --------------------------------------------------------

    action_col_1, action_col_2 = st.columns(2)

    with action_col_1:

        run_investigation = st.button(
            "🔍 Run Investigation",
            width="stretch",
            type="primary",
        )

    with action_col_2:

        reset_investigation = st.button(
            "↺ Reset Investigation",
            width="stretch",
        )

    # --------------------------------------------------------
    # RESET INVESTIGATION
    # --------------------------------------------------------

    if reset_investigation:

        st.session_state.investigation_results = []

        st.session_state.investigation_executed = False

        st.rerun()

    # --------------------------------------------------------
    # EXECUTE INVESTIGATION
    # --------------------------------------------------------

    if run_investigation and valid_risk_range:

        try:

            investigation_results = (
                get_investigation_events(

                    agent_id=(
                        None
                        if selected_agent == "ALL"
                        else selected_agent
                    ),

                    task_id=(
                        None
                        if selected_task == "ALL"
                        else selected_task
                    ),

                    action=(
                        None
                        if selected_action == "ALL"
                        else selected_action
                    ),

                    resource=(
                        None
                        if selected_resource == "ALL"
                        else selected_resource
                    ),

                    decision=(
                        None
                        if selected_decision == "ALL"
                        else selected_decision
                    ),

                    risk_level=(
                        None
                        if selected_risk == "ALL"
                        else selected_risk
                    ),

                    minimum_risk=(
                        None
                        if minimum_risk == 0
                        else minimum_risk
                    ),

                    maximum_risk=(
                        None
                        if maximum_risk == 100
                        else maximum_risk
                    ),

                    limit=investigation_limit,
                )
            )

            st.session_state.investigation_results = (
                investigation_results
            )

            st.session_state.investigation_executed = True

        except Exception as error:

            st.error(
                f"Investigation failed: {error}"
            )

            st.session_state.investigation_results = []

            st.session_state.investigation_executed = False

    # --------------------------------------------------------
    # INVESTIGATION RESULTS
    # --------------------------------------------------------

    if st.session_state.investigation_executed:

        investigation_results = (
            st.session_state.investigation_results
        )

        st.subheader(
            "Investigation Results"
        )

        result_col_1, result_col_2, result_col_3 = (
            st.columns(3)
        )

        # ----------------------------------------------------
        # MATCHING EVENTS
        # ----------------------------------------------------

        with result_col_1:

            st.metric(
                "Matching Events",
                len(investigation_results),
            )

        # ----------------------------------------------------
        # DENIED EVENTS
        # ----------------------------------------------------

        with result_col_2:

            denied_events = sum(
                1
                for event in investigation_results
                if str(
                    event.get("decision", "")
                ).upper()
                == "DENY"
            )

            st.metric(
                "Denied Events",
                denied_events,
            )

        # ----------------------------------------------------
        # CRITICAL EVENTS
        # ----------------------------------------------------

        with result_col_3:

            critical_events = sum(
                1
                for event in investigation_results
                if int(
                    event.get("risk", 0)
                ) >= 80
            )

            st.metric(
                "Critical Events",
                critical_events,
            )

        # ----------------------------------------------------
        # RESULTS TABLE
        # ----------------------------------------------------

        if investigation_results:

            investigation_df = pd.DataFrame(
                investigation_results
            )

            display_columns = [
                "id",
                "timestamp",
                "agent_id",
                "task_id",
                "action",
                "resource",
                "decision",
                "risk",
                "reason",
            ]

            display_columns = [
                column
                for column in display_columns
                if column in investigation_df.columns
            ]

            investigation_df = (
                investigation_df[
                    display_columns
                ].copy()
            )

            # Make displayed values predictable for
            # Streamlit/PyArrow serialization.
            if "risk" in investigation_df.columns:

                investigation_df["risk"] = pd.to_numeric(
                    investigation_df["risk"],
                    errors="coerce",
                ).fillna(0).astype(int)

            st.dataframe(
                investigation_df,
                width="stretch",
                hide_index=True,
            )

            # ------------------------------------------------
            # EVENT DETAIL
            # ------------------------------------------------

            st.subheader(
                "Event Investigation"
            )

            event_ids = [
                event["id"]
                for event in investigation_results
                if "id" in event
            ]

            if event_ids:

                selected_event_id = st.selectbox(
                    "Select Event ID",
                    event_ids,
                    key="selected_investigation_event",
                )

                try:

                    selected_event = (
                        get_investigation_event(
                            int(selected_event_id)
                        )
                    )

                except Exception as error:

                    selected_event = None

                    st.error(
                        f"Unable to load event details: {error}"
                    )

                if selected_event:

                    detail_col_1, detail_col_2 = (
                        st.columns(2)
                    )

                    # ----------------------------------------
                    # EVENT INFORMATION
                    # ----------------------------------------

                    with detail_col_1:

                        st.markdown(
                            f"""
                            **Event ID**

                            `{selected_event.get("id", "")}`

                            **Timestamp**

                            `{selected_event.get("timestamp", "")}`

                            **Agent**

                            `{selected_event.get("agent_id", "")}`

                            **Task**

                            `{selected_event.get("task_id", "")}`

                            **Decision**

                            `{selected_event.get("decision", "")}`
                            """
                        )

                    with detail_col_2:

                        st.markdown(
                            f"""
                            **Action**

                            `{selected_event.get("action", "")}`

                            **Resource**

                            `{selected_event.get("resource", "")}`

                            **Risk**

                            `{selected_event.get("risk", "")}`

                            **Reason**

                            `{selected_event.get("reason", "")}`
                            """
                        )

                    # ----------------------------------------
                    # INVESTIGATION EVIDENCE
                    # ----------------------------------------

                    st.subheader(
                        "Investigation Evidence"
                    )

                    # IMPORTANT:
                    # Convert every observed value to a string.
                    # This prevents mixed-type Arrow serialization
                    # errors when risk is an integer and the other
                    # fields are strings.

                    evidence_rows = [
                        {
                            "Evidence Field": "Agent",
                            "Observed Value": str(
                                selected_event.get(
                                    "agent_id",
                                    "",
                                )
                            ),
                        },
                        {
                            "Evidence Field": "Task",
                            "Observed Value": str(
                                selected_event.get(
                                    "task_id",
                                    "",
                                )
                            ),
                        },
                        {
                            "Evidence Field": "Action",
                            "Observed Value": str(
                                selected_event.get(
                                    "action",
                                    "",
                                )
                            ),
                        },
                        {
                            "Evidence Field": "Resource",
                            "Observed Value": str(
                                selected_event.get(
                                    "resource",
                                    "",
                                )
                            ),
                        },
                        {
                            "Evidence Field": "Decision",
                            "Observed Value": str(
                                selected_event.get(
                                    "decision",
                                    "",
                                )
                            ),
                        },
                        {
                            "Evidence Field": "Risk",
                            "Observed Value": str(
                                selected_event.get(
                                    "risk",
                                    "",
                                )
                            ),
                        },
                        {
                            "Evidence Field": "Reason",
                            "Observed Value": str(
                                selected_event.get(
                                    "reason",
                                    "",
                                )
                            ),
                        },
                    ]

                    evidence_df = pd.DataFrame(
                        evidence_rows,
                        columns=[
                            "Evidence Field",
                            "Observed Value",
                        ],
                    )

                    # Explicitly enforce string dtype.
                    evidence_df[
                        "Evidence Field"
                    ] = evidence_df[
                        "Evidence Field"
                    ].astype(str)

                    evidence_df[
                        "Observed Value"
                    ] = evidence_df[
                        "Observed Value"
                    ].astype(str)

                    st.dataframe(
                        evidence_df,
                        width="stretch",
                        hide_index=True,
                    )

            else:

                st.info(
                    "No event identifiers are available."
                )

        else:

            st.info(
                "No security events matched the "
                "selected investigation criteria."
            )


# ============================================================
# AGENT INTELLIGENCE
# ============================================================

if show_agent_activity:

    st.divider()

    st.subheader(
        "Agent Intelligence"
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

        # ----------------------------------------------------
        # AGENT RISK RANKING
        # ----------------------------------------------------

        if "maximum_risk" in agent_df.columns:

            st.subheader(
                "Agent Risk Ranking"
            )

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
                agent_df[
                    ranking_columns
                ]
                .sort_values(
                    by="maximum_risk",
                    ascending=False,
                )
            )

            if (
                not ranked_agents.empty
                and "agent_id" in ranked_agents.columns
            ):

                st.bar_chart(
                    ranked_agents.set_index(
                        "agent_id"
                    )["maximum_risk"],
                    width="stretch",
                )

        # ----------------------------------------------------
        # AGENT DENIAL RATE
        # ----------------------------------------------------

        if {
            "total_requests",
            "denied_requests",
        }.issubset(agent_df.columns):

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

            st.subheader(
                "Agent Denial Rate"
            )

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

            if not denial_rate_df.empty:

                st.bar_chart(
                    denial_rate_df.set_index(
                        "agent_id"
                    ),
                    width="stretch",
                )

            st.caption(
                "Denial rate represents the percentage "
                "of observed requests denied for each agent."
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

    st.subheader(
        "🚨 Suspicious Agents"
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

st.subheader(
    "Security Intelligence Summary"
)

summary_col_1, summary_col_2 = st.columns(2)


with summary_col_1:

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
        - Event-level investigation
        """
    )


with summary_col_2:

    st.markdown(
        """
        ### Research Evolution

        **Day 16**

        Advanced security operations

        **Day 17**

        Security investigation and evidence analysis

        **Day 18**

        Behavioral feature engineering

        **Day 19**

        Anomaly detection

        **Day 20**

        Integrated behavioral security intelligence
        """
    )


# ============================================================
# CURRENT SECURITY STATE
# ============================================================

st.divider()

st.subheader(
    "Current Security State"
)

total_denied = decisions.get(
    "DENY",
    0,
)

total_allowed = decisions.get(
    "ALLOW",
    0,
)

if total_events > 0:

    denial_percentage = (
        total_denied / total_events
    ) * 100

    allow_percentage = (
        total_allowed / total_events
    ) * 100

    state_col_1, state_col_2, state_col_3 = (
        st.columns(3)
    )

    with state_col_1:

        st.metric(
            "Authorization Denial Rate",
            f"{denial_percentage:.2f}%",
        )

    with state_col_2:

        st.metric(
            "Authorization Allow Rate",
            f"{allow_percentage:.2f}%",
        )

    with state_col_3:

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
    "Research Prototype • Day 17 • Security Investigation Engine"
)