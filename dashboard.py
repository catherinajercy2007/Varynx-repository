import streamlit as st
import pandas as pd


# ============================================================
# AEGISGUARD ANALYTICS
# ============================================================

from app.analytics import (
    get_total_events,
    get_decision_counts,
    get_risk_summary,
    get_agent_activity,
    get_high_risk_events,
)


# ============================================================
# AEGISGUARD BEHAVIOR ANALYTICS
# ============================================================

from app.behavior import (
    get_suspicious_agents,
    get_repeated_denials,
)


# ============================================================
# AEGISGUARD INVESTIGATION
# ============================================================

from app.investigation import (
    get_investigation_events,
    get_investigation_event,
    get_investigation_filter_options,
)


# ============================================================
# AEGISGUARD BEHAVIORAL FEATURES
# ============================================================

from app.features import (
    get_behavioral_features,
    get_behavior_feature_names,
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

st.title(
    "🛡️ AegisGuard Security Operations Center"
)

st.caption(
    "Behavior-aware authorization, security analytics, "
    "agent monitoring, investigation and behavioral "
    "feature intelligence"
)

st.divider()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("SOC Controls")

    st.success(
        "Security engine online"
    )

    st.divider()

    st.subheader(
        "Monitoring Modules"
    )

    show_agent_activity = st.checkbox(
        "Agent Activity",
        value=True,
    )

    show_investigation = st.checkbox(
        "Investigation Engine",
        value=True,
    )

    show_behavioral_features = st.checkbox(
        "Behavioral Features",
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

    st.subheader(
        "Research Pipeline"
    )

    st.markdown(
        """
        **Day 16**

        Security Operations

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
        """
    )

    st.divider()

    st.caption(
        "AegisGuard Research Prototype"
    )

    st.caption(
        "Day 18 • Behavioral Feature Engineering"
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
        f"Unable to load AegisGuard security data: {error}"
    )

    st.stop()


# ============================================================
# SECURITY POSTURE
# ============================================================

st.subheader(
    "Security Posture"
)

metric_1, metric_2, metric_3, metric_4, metric_5 = (
    st.columns(5)
)


with metric_1:

    st.metric(
        "Total Events",
        total_events,
    )


with metric_2:

    st.metric(
        "Allowed",
        decisions.get(
            "ALLOW",
            0,
        ),
    )


with metric_3:

    st.metric(
        "Denied",
        decisions.get(
            "DENY",
            0,
        ),
    )


with metric_4:

    st.metric(
        "Average Risk",
        risk.get(
            "average_risk",
            0,
        ),
    )


with metric_5:

    st.metric(
        "Critical Events",
        risk.get(
            "critical_events",
            0,
        ),
    )


# ============================================================
# RISK OVERVIEW
# ============================================================

st.divider()

st.subheader(
    "Risk Overview"
)

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


# ============================================================
# AUTHORIZATION + RISK ANALYTICS
# ============================================================

st.divider()

authorization_col, risk_col = (
    st.columns(2)
)


# ============================================================
# AUTHORIZATION DECISIONS
# ============================================================

with authorization_col:

    st.subheader(
        "Authorization Decisions"
    )

    decision_data = pd.DataFrame(
        {
            "Decision": list(
                decisions.keys()
            ),
            "Count": list(
                decisions.values()
            ),
        }
    )

    if not decision_data.empty:

        st.bar_chart(
            decision_data.set_index(
                "Decision"
            ),
            width="stretch",
        )

    else:

        st.info(
            "No authorization decisions available."
        )


# ============================================================
# RISK INDICATORS
# ============================================================

with risk_col:

    st.subheader(
        "Risk Security Indicators"
    )

    risk_data = pd.DataFrame(
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
        risk_data.set_index(
            "Indicator"
        ),
        width="stretch",
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
        "Investigate individual security events using "
        "structured event-level filters and evidence."
    )


    # --------------------------------------------------------
    # LOAD INVESTIGATION FILTER OPTIONS
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

    filter_1, filter_2, filter_3 = (
        st.columns(3)
    )


    with filter_1:

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


    with filter_2:

        selected_task = st.selectbox(
            "Task",
            [
                "ALL"
            ]
            + filter_options.get(
                "tasks",
                [],
            ),
            key="investigation_task",
        )


    with filter_3:

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


    # --------------------------------------------------------
    # FILTER ROW 2
    # --------------------------------------------------------

    filter_4, filter_5, filter_6 = (
        st.columns(3)
    )


    with filter_4:

        selected_resource = st.selectbox(
            "Resource",
            [
                "ALL"
            ]
            + filter_options.get(
                "resources",
                [],
            ),
            key="investigation_resource",
        )


    with filter_5:

        selected_decision = st.selectbox(
            "Decision",
            [
                "ALL",
                "ALLOW",
                "DENY",
            ],
            key="investigation_decision",
        )


    with filter_6:

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
    # ADVANCED INVESTIGATION CONTROLS
    # --------------------------------------------------------

    with st.expander(
        "⚙️ Advanced Investigation Controls"
    ):

        advanced_1, advanced_2 = (
            st.columns(2)
        )


        with advanced_1:

            minimum_risk = st.number_input(
                "Minimum Risk",
                min_value=0,
                max_value=100,
                value=0,
                step=1,
                key="investigation_min_risk",
            )


        with advanced_2:

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


    valid_risk_range = (
        minimum_risk <= maximum_risk
    )


    if not valid_risk_range:

        st.warning(
            "Minimum risk cannot be greater than "
            "maximum risk."
        )


    # --------------------------------------------------------
    # INVESTIGATION BUTTONS
    # --------------------------------------------------------

    action_1, action_2 = (
        st.columns(2)
    )


    with action_1:

        run_investigation = st.button(
            "🔍 Run Investigation",
            width="stretch",
            type="primary",
        )


    with action_2:

        reset_investigation = st.button(
            "↺ Reset Investigation",
            width="stretch",
        )


    # --------------------------------------------------------
    # RESET
    # --------------------------------------------------------

    if reset_investigation:

        st.session_state.investigation_results = []

        st.session_state.investigation_executed = False

        st.rerun()


    # --------------------------------------------------------
    # RUN INVESTIGATION
    # --------------------------------------------------------

    if (
        run_investigation
        and valid_risk_range
    ):

        try:

            results = (
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
                results
            )

            st.session_state.investigation_executed = (
                True
            )


        except Exception as error:

            st.error(
                f"Investigation failed: {error}"
            )

            st.session_state.investigation_results = []

            st.session_state.investigation_executed = (
                False
            )


    # --------------------------------------------------------
    # INVESTIGATION RESULTS
    # --------------------------------------------------------

    if st.session_state.investigation_executed:

        investigation_results = (
            st.session_state.investigation_results
        )


        result_1, result_2, result_3 = (
            st.columns(3)
        )


        with result_1:

            st.metric(
                "Matching Events",
                len(
                    investigation_results
                ),
            )


        with result_2:

            denied_events = sum(
                1
                for event
                in investigation_results
                if str(
                    event.get(
                        "decision",
                        "",
                    )
                ).upper()
                == "DENY"
            )

            st.metric(
                "Denied Events",
                denied_events,
            )


        with result_3:

            critical_events = sum(
                1
                for event
                in investigation_results
                if int(
                    event.get(
                        "risk",
                        0,
                    )
                )
                >= 80
            )

            st.metric(
                "Critical Events",
                critical_events,
            )


        # ----------------------------------------------------
        # RESULTS
        # ----------------------------------------------------

        if investigation_results:

            st.subheader(
                "Investigation Results"
            )


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
                for column
                in display_columns
                if column
                in investigation_df.columns
            ]


            investigation_df = (
                investigation_df[
                    display_columns
                ].copy()
            )


            if "risk" in investigation_df.columns:

                investigation_df[
                    "risk"
                ] = pd.to_numeric(
                    investigation_df[
                        "risk"
                    ],
                    errors="coerce",
                ).fillna(0).astype(int)


            st.dataframe(
                investigation_df,
                width="stretch",
                hide_index=True,
            )


            # ------------------------------------------------
            # EVENT INVESTIGATION
            # ------------------------------------------------

            st.subheader(
                "Event Investigation"
            )


            event_ids = [
                event.get("id")
                for event
                in investigation_results
                if event.get("id")
                is not None
            ]


            if event_ids:

                selected_event_id = (
                    st.selectbox(
                        "Select Event ID",
                        event_ids,
                        key=(
                            "selected_investigation_event"
                        ),
                    )
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
                        "Unable to load event details: "
                        f"{error}"
                    )


                if selected_event is None:

                    st.warning(
                        "The selected security event "
                        "could not be found."
                    )


                else:

                    # ----------------------------------------
                    # EVENT CONTEXT
                    # ----------------------------------------

                    detail_1, detail_2 = (
                        st.columns(2)
                    )


                    with detail_1:

                        st.markdown(
                            "### Event Context"
                        )

                        st.write(
                            "**Event ID:** "
                            f"`{selected_event.get('id', '')}`"
                        )

                        st.write(
                            "**Timestamp:** "
                            f"`{selected_event.get('timestamp', '')}`"
                        )

                        st.write(
                            "**Agent:** "
                            f"`{selected_event.get('agent_id', '')}`"
                        )

                        st.write(
                            "**Task:** "
                            f"`{selected_event.get('task_id', '')}`"
                        )


                    with detail_2:

                        st.markdown(
                            "### Security Decision"
                        )

                        st.write(
                            "**Action:** "
                            f"`{selected_event.get('action', '')}`"
                        )

                        st.write(
                            "**Resource:** "
                            f"`{selected_event.get('resource', '')}`"
                        )

                        st.write(
                            "**Decision:** "
                            f"`{selected_event.get('decision', '')}`"
                        )

                        st.write(
                            "**Risk:** "
                            f"`{selected_event.get('risk', '')}`"
                        )


                    # ----------------------------------------
                    # DECISION REASON
                    # ----------------------------------------

                    st.markdown(
                        "### Decision Reason"
                    )

                    st.info(
                        str(
                            selected_event.get(
                                "reason",
                                "No decision reason recorded.",
                            )
                        )
                    )


                    # ----------------------------------------
                    # INVESTIGATION EVIDENCE
                    # ----------------------------------------

                    st.markdown(
                        "### Investigation Evidence"
                    )


                    evidence_rows = [

                        {
                            "Evidence Field": "Event ID",
                            "Observed Value": str(
                                selected_event.get(
                                    "id",
                                    "",
                                )
                            ),
                        },

                        {
                            "Evidence Field": "Timestamp",
                            "Observed Value": str(
                                selected_event.get(
                                    "timestamp",
                                    "",
                                )
                            ),
                        },

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


                    evidence_df = (
                        evidence_df.astype(str)
                    )


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
# DAY 18 — BEHAVIORAL FEATURE ANALYTICS
# ============================================================

if show_behavioral_features:

    st.divider()

    st.header(
        "🧠 Behavioral Feature Analytics"
    )

    st.caption(
        "Deterministic behavioral features derived "
        "from historical AegisGuard security telemetry."
    )


    # --------------------------------------------------------
    # LOAD BEHAVIORAL FEATURES
    # --------------------------------------------------------

    try:

        behavioral_features = (
            get_behavioral_features()
        )

    except Exception as error:

        st.error(
            "Unable to calculate behavioral features: "
            f"{error}"
        )

        behavioral_features = []


    if behavioral_features:

        behavior_df = pd.DataFrame(
            behavioral_features
        )


        # ----------------------------------------------------
        # BEHAVIORAL POSTURE
        # ----------------------------------------------------

        st.subheader(
            "Behavioral Security Posture"
        )


        behavior_metric_1, behavior_metric_2, behavior_metric_3, behavior_metric_4 = (
            st.columns(4)
        )


        with behavior_metric_1:

            st.metric(
                "Agents Profiled",
                len(
                    behavior_df
                ),
            )


        with behavior_metric_2:

            mean_agent_risk = round(
                float(
                    behavior_df[
                        "average_risk"
                    ].mean()
                ),
                2,
            )

            st.metric(
                "Mean Agent Risk",
                mean_agent_risk,
            )


        with behavior_metric_3:

            high_denial_agents = int(
                (
                    behavior_df[
                        "denial_rate"
                    ]
                    >= 0.50
                ).sum()
            )

            st.metric(
                "High-Denial Agents",
                high_denial_agents,
            )


        with behavior_metric_4:

            critical_behavior_agents = int(
                (
                    behavior_df[
                        "critical_requests"
                    ]
                    > 0
                ).sum()
            )

            st.metric(
                "Agents With Critical Requests",
                critical_behavior_agents,
            )


        # ----------------------------------------------------
        # FEATURE MATRIX
        # ----------------------------------------------------

        st.subheader(
            "Behavioral Feature Matrix"
        )

        st.caption(
            "Each row represents the measured behavioral "
            "profile of one observed agent."
        )


        st.dataframe(
            behavior_df,
            width="stretch",
            hide_index=True,
        )


        # ----------------------------------------------------
        # FEATURE SELECTOR
        # ----------------------------------------------------

        st.subheader(
            "Behavioral Feature Explorer"
        )


        available_feature_names = [
            feature
            for feature
            in get_behavior_feature_names()
            if feature
            in behavior_df.columns
        ]


        if available_feature_names:

            selected_feature = st.selectbox(
                "Select Behavioral Feature",
                available_feature_names,
                key="selected_behavior_feature",
            )


            feature_chart_df = (
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
                feature_chart_df,
                width="stretch",
            )


        # ----------------------------------------------------
        # DENIAL RATE
        # ----------------------------------------------------

        if {
            "agent_id",
            "denial_rate",
        }.issubset(
            behavior_df.columns
        ):

            st.subheader(
                "Agent Denial Rate"
            )


            denial_rate_df = (
                behavior_df[
                    [
                        "agent_id",
                        "denial_rate",
                    ]
                ]
                .set_index(
                    "agent_id"
                )
                .sort_values(
                    by="denial_rate",
                    ascending=False,
                )
            )


            st.bar_chart(
                denial_rate_df,
                width="stretch",
            )


        # ----------------------------------------------------
        # AVERAGE RISK
        # ----------------------------------------------------

        if {
            "agent_id",
            "average_risk",
        }.issubset(
            behavior_df.columns
        ):

            st.subheader(
                "Agent Average Risk"
            )


            average_risk_df = (
                behavior_df[
                    [
                        "agent_id",
                        "average_risk",
                    ]
                ]
                .set_index(
                    "agent_id"
                )
                .sort_values(
                    by="average_risk",
                    ascending=False,
                )
            )


            st.bar_chart(
                average_risk_df,
                width="stretch",
            )


        # ----------------------------------------------------
        # BEHAVIORAL DIVERSITY
        # ----------------------------------------------------

        diversity_columns = [
            "agent_id",
            "action_diversity",
            "resource_diversity",
            "task_diversity",
        ]


        if all(
            column
            in behavior_df.columns
            for column
            in diversity_columns
        ):

            st.subheader(
                "Behavioral Diversity"
            )


            diversity_df = (
                behavior_df[
                    diversity_columns
                ]
                .set_index(
                    "agent_id"
                )
            )


            st.bar_chart(
                diversity_df,
                width="stretch",
            )


        # ----------------------------------------------------
        # HIGH-RISK BEHAVIOR
        # ----------------------------------------------------

        high_risk_feature_columns = [
            "agent_id",
            "high_risk_requests",
            "critical_requests",
        ]


        if all(
            column
            in behavior_df.columns
            for column
            in high_risk_feature_columns
        ):

            st.subheader(
                "High-Risk Behavioral Activity"
            )


            high_risk_behavior_df = (
                behavior_df[
                    high_risk_feature_columns
                ]
                .set_index(
                    "agent_id"
                )
            )


            st.bar_chart(
                high_risk_behavior_df,
                width="stretch",
            )


        # ----------------------------------------------------
        # BEHAVIORAL RESEARCH INTERPRETATION
        # ----------------------------------------------------

        st.subheader(
            "Behavioral Feature Interpretation"
        )


        st.markdown(
            """
            **Denial Rate**

            Measures the proportion of requests rejected
            by the authorization layer.

            **Average Risk**

            Represents the mean risk score associated with
            an agent's observed requests.

            **Critical Requests**

            Counts requests reaching the critical-risk
            threshold.

            **Action Diversity**

            Measures how many distinct actions an agent
            performs relative to its request volume.

            **Resource Diversity**

            Measures the breadth of resources accessed
            by an agent relative to its request volume.

            **Task Diversity**

            Measures the number of distinct tasks observed
            for an agent relative to total requests.
            """
        )


    else:

        st.info(
            "No behavioral feature data is currently available."
        )


# ============================================================
# DAY 16 — AGENT INTELLIGENCE
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

        if (
            "maximum_risk"
            in agent_df.columns
        ):

            ranking_columns = [
                column
                for column
                in [
                    "agent_id",
                    "total_requests",
                    "denied_requests",
                    "maximum_risk",
                ]
                if column
                in agent_df.columns
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


            if not ranked_agents.empty:

                st.subheader(
                    "Agent Risk Ranking"
                )


                st.bar_chart(
                    ranked_agents.set_index(
                        "agent_id"
                    )[
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
        }.issubset(
            agent_df.columns
        ):

            agent_df[
                "denial_rate"
            ] = 0.0


            valid_requests = (
                agent_df[
                    "total_requests"
                ]
                > 0
            )


            agent_df.loc[
                valid_requests,
                "denial_rate",
            ] = (
                agent_df.loc[
                    valid_requests,
                    "denied_requests",
                ]
                /
                agent_df.loc[
                    valid_requests,
                    "total_requests",
                ]
            )


            agent_df[
                "denial_rate"
            ] = (
                agent_df[
                    "denial_rate"
                ]
                * 100
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


summary_col_1, summary_col_2 = (
    st.columns(2)
)


with summary_col_1:

    st.markdown(
        """
        ### Current Security Layers

        - Identity and authorization
        - Policy enforcement
        - Contextual risk assessment
        - Security audit logging
        - Security analytics
        - Behavioral analytics
        - Event-level investigation
        - Behavioral feature engineering
        - Suspicious-agent detection
        - Repeated-denial detection
        - High-risk event monitoring
        """
    )


with summary_col_2:

    st.markdown(
        """
        ### Research Pipeline

        **Raw Telemetry**

        Security authorization events

        ↓

        **Investigation**

        Event-level evidence analysis

        ↓

        **Feature Engineering**

        Agent behavioral representation

        ↓

        **Anomaly Detection**

        Statistical / ML-based detection

        ↓

        **Security Intelligence**

        Behavior-aware decision support
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
        total_denied
        /
        total_events
    ) * 100


    allow_percentage = (
        total_allowed
        /
        total_events
    ) * 100


    state_1, state_2, state_3 = (
        st.columns(3)
    )


    with state_1:

        st.metric(
            "Authorization Denial Rate",
            f"{denial_percentage:.2f}%",
        )


    with state_2:

        st.metric(
            "Authorization Allow Rate",
            f"{allow_percentage:.2f}%",
        )


    with state_3:

        st.metric(
            "Agents Observed",
            len(
                agents
            ),
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
    "Research note: Behavioral features in this phase "
    "are deterministic statistical representations derived "
    "from security telemetry. They are not machine-learning "
    "predictions. These features will form the input layer "
    "for controlled anomaly-detection experiments."
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
    "Research Prototype • Day 18 • Behavioral Feature Engineering"
)