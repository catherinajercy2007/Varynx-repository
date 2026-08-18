import streamlit as st
import pandas as pd
import json
from datetime import datetime


# ============================================================
# AEGISGUARD
# BEHAVIOR-AWARE SECURITY INTELLIGENCE SOC
# ============================================================


st.set_page_config(
    page_title="AegisGuard Intelligence SOC",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# OPTIONAL APPLICATION IMPORTS
# ============================================================

def optional_imports():

    modules = {}

    # --------------------------------------------------------
    # ANALYTICS
    # --------------------------------------------------------

    try:

        from app.analytics import (
            get_total_events,
            get_decision_counts,
            get_risk_summary,
            get_agent_activity,
            get_high_risk_events,
        )

        modules["analytics"] = {
            "get_total_events":
                get_total_events,

            "get_decision_counts":
                get_decision_counts,

            "get_risk_summary":
                get_risk_summary,

            "get_agent_activity":
                get_agent_activity,

            "get_high_risk_events":
                get_high_risk_events,
        }

    except Exception as exc:

        modules["analytics_error"] = str(exc)

    # --------------------------------------------------------
    # BEHAVIOR
    # --------------------------------------------------------

    try:

        from app.behavior import (
            get_suspicious_agents,
            get_repeated_denials,
        )

        modules["behavior"] = {

            "get_suspicious_agents":
                get_suspicious_agents,

            "get_repeated_denials":
                get_repeated_denials,
        }

    except Exception as exc:

        modules["behavior_error"] = str(exc)

    # --------------------------------------------------------
    # CONTROLLED SCENARIOS
    # --------------------------------------------------------

    try:

        from app.attack_scenarios import (
            get_attack_scenarios,
        )

        modules["scenarios"] = {

            "get_attack_scenarios":
                get_attack_scenarios,
        }

    except Exception as exc:

        modules["scenarios_error"] = str(exc)

    # --------------------------------------------------------
    # REPEATED EVALUATION — DAY 27
    # --------------------------------------------------------

    try:

        from app.repeated_evaluation import (
            run_repeated_experiments,
            build_seed_summary,
            build_summary_table,
            calculate_consistency,
        )

        modules["repeated"] = {

            "run_repeated_experiments":
                run_repeated_experiments,

            "build_seed_summary":
                build_seed_summary,

            "build_summary_table":
                build_summary_table,

            "calculate_consistency":
                calculate_consistency,
        }

    except Exception as exc:

        modules["repeated_error"] = str(exc)

    # --------------------------------------------------------
    # COMPARISON — DAY 26
    # --------------------------------------------------------

    try:

        from app.comparison import (
            compare_detectors,
            build_comparison_table,
            build_event_comparison,
        )

        modules["comparison"] = {

            "compare_detectors":
                compare_detectors,

            "build_comparison_table":
                build_comparison_table,

            "build_event_comparison":
                build_event_comparison,
        }

    except Exception as exc:

        modules["comparison_error"] = str(exc)

    # --------------------------------------------------------
    # EXPERIMENTAL DATASET
    # --------------------------------------------------------

    try:

        from app.experimental_dataset import (
            generate_experimental_dataset,
        )

        modules["dataset"] = {

            "generate_experimental_dataset":
                generate_experimental_dataset,
        }

    except Exception as exc:

        modules["dataset_error"] = str(exc)

    # --------------------------------------------------------
    # EVALUATION MODULE
    #
    # IMPORTANT:
    # Do NOT use:
    #
    # from app.evaluation import *
    #
    # inside this function.
    #
    # --------------------------------------------------------

    try:

        import app.evaluation as evaluation

        modules["evaluation"] = evaluation

    except Exception as exc:

        modules["evaluation_error"] = str(exc)

    return modules


# ============================================================
# LOAD APPLICATION MODULES
# ============================================================

MODULES = optional_imports()


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {

    "selected_agent":
        None,

    "selected_event":
        None,

    "day26_results":
        None,

    "day26_dataset":
        None,

    "day27_results":
        None,

    "day27_config":
        None,

    "experimental_dataset":
        None,

    "experiment_history":
        [],
}


for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# CUSTOM UI
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 2.7rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 0.25rem;
    }

    .main-subtitle {
        font-size: 1.05rem;
        color: #667085;
        margin-bottom: 1.4rem;
    }

    .section-label {
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #667085;
    }

    .research-card {
        border: 1px solid rgba(128,128,128,0.22);
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 14px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SAFE HELPERS
# ============================================================

def safe_call(
    function,
    default=None,
    *args,
    **kwargs,
):

    if function is None:

        return default

    try:

        return function(
            *args,
            **kwargs,
        )

    except Exception:

        return default


def as_dict(value):

    if isinstance(
        value,
        dict,
    ):

        return value

    if hasattr(
        value,
        "model_dump",
    ):

        try:

            return value.model_dump()

        except Exception:

            pass

    if hasattr(
        value,
        "__dict__",
    ):

        try:

            return dict(
                value.__dict__
            )

        except Exception:

            pass

    return {}


def get_field(
    value,
    name,
    default="",
):

    if isinstance(
        value,
        dict,
    ):

        return value.get(
            name,
            default,
        )

    return getattr(
        value,
        name,
        default,
    )


def safe_number(
    value,
    default=0.0,
):

    try:

        return float(value)

    except (
        TypeError,
        ValueError,
    ):

        return default


def dataframe_or_empty(
    rows,
):

    if rows is None:

        return pd.DataFrame()

    if isinstance(
        rows,
        pd.DataFrame,
    ):

        return rows.copy()

    try:

        return pd.DataFrame(rows)

    except Exception:

        return pd.DataFrame()


def download_dataframe(
    dataframe,
    filename,
):

    if dataframe is None:

        return

    csv_data = (
        dataframe
        .to_csv(
            index=False
        )
        .encode("utf-8")
    )

    st.download_button(
        label="⬇️ Download CSV",
        data=csv_data,
        file_name=filename,
        mime="text/csv",
    )


# ============================================================
# LOAD DATA
# ============================================================

analytics = MODULES.get(
    "analytics",
    {},
)

behavior = MODULES.get(
    "behavior",
    {},
)

scenarios_module = MODULES.get(
    "scenarios",
    {},
)


total_events = safe_call(
    analytics.get(
        "get_total_events"
    ),
    0,
)


decision_counts = safe_call(
    analytics.get(
        "get_decision_counts"
    ),
    {},
)


risk_summary = safe_call(
    analytics.get(
        "get_risk_summary"
    ),
    {},
)


agent_activity = safe_call(
    analytics.get(
        "get_agent_activity"
    ),
    [],
)


high_risk_events = safe_call(
    analytics.get(
        "get_high_risk_events"
    ),
    [],
)


suspicious_agents = safe_call(
    behavior.get(
        "get_suspicious_agents"
    ),
    [],
)


repeated_denials = safe_call(
    behavior.get(
        "get_repeated_denials"
    ),
    [],
)


scenario_catalogue = safe_call(
    scenarios_module.get(
        "get_attack_scenarios"
    ),
    [],
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">'
    '🛡️ AegisGuard Intelligence SOC'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="main-subtitle">
    Behavior-aware security intelligence for autonomous AI agents —
    authorization, risk analysis, behavioral monitoring,
    anomaly detection, investigation and reproducible research evaluation.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "🛡️ AegisGuard"
)

st.sidebar.caption(
    "AI Agent Security Research Platform"
)

st.sidebar.divider()


dashboard_view = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Security Overview",
        "📈 Risk Intelligence",
        "🤖 Agent Intelligence",
        "🧠 Behavioral Analytics",
        "🚨 High-Risk Events",
        "🔎 Security Investigation",
        "🧪 Scenario Laboratory",
        "🧬 Experimental Dataset",
        "📊 Day 24 Evaluation",
        "⚖️ Day 26 Baseline Comparison",
        "🔬 Day 27 Repeated Evaluation",
        "📚 Research Interpretation",
        "⚙️ System Status",
    ],
)


st.sidebar.divider()

st.sidebar.markdown(
    "**Research Pipeline**"
)

st.sidebar.caption(
    "Authorization → Risk → Behavior → "
    "Anomaly → Intelligence → Experiments → Evaluation"
)

st.sidebar.divider()

st.sidebar.caption(
    "AegisGuard Research Prototype"
)


# ============================================================
# SECURITY OVERVIEW
# ============================================================

if dashboard_view == "🏠 Security Overview":

    st.header(
        "📊 Security Operations Overview"
    )

    st.caption(
        "Current authorization, risk and behavioral security posture."
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
            decision_counts.get(
                "ALLOW",
                0,
            ),
        )

    with c3:

        st.metric(
            "Denied",
            decision_counts.get(
                "DENY",
                0,
            ),
        )

    with c4:

        st.metric(
            "Average Risk",
            risk_summary.get(
                "average_risk",
                0,
            ),
        )

    with c5:

        st.metric(
            "Critical",
            risk_summary.get(
                "critical_events",
                0,
            ),
        )

    st.divider()

    st.subheader(
        "Authorization Decisions"
    )

    if decision_counts:

        decision_df = pd.DataFrame(
            {
                "Decision":
                    list(
                        decision_counts.keys()
                    ),

                "Events":
                    list(
                        decision_counts.values()
                    ),
            }
        )

        left, right = st.columns(
            [1, 2]
        )

        with left:

            st.dataframe(
                decision_df,
                width="stretch",
                hide_index=True,
            )

        with right:

            st.bar_chart(
                decision_df.set_index(
                    "Decision"
                ),
                width="stretch",
            )

    else:

        st.info(
            "No authorization decision data available."
        )


# ============================================================
# RISK INTELLIGENCE
# ============================================================

elif dashboard_view == "📈 Risk Intelligence":

    st.header(
        "📈 Risk Intelligence"
    )

    r1, r2, r3, r4 = (
        st.columns(4)
    )

    with r1:

        st.metric(
            "Average Risk",
            risk_summary.get(
                "average_risk",
                0,
            ),
        )

    with r2:

        st.metric(
            "Maximum Risk",
            risk_summary.get(
                "maximum_risk",
                0,
            ),
        )

    with r3:

        st.metric(
            "High Risk",
            risk_summary.get(
                "high_risk_events",
                0,
            ),
        )

    with r4:

        st.metric(
            "Critical",
            risk_summary.get(
                "critical_events",
                0,
            ),
        )

    st.divider()

    high_df = dataframe_or_empty(
        high_risk_events
    )

    if high_df.empty:

        st.success(
            "No high-risk events detected."
        )

    else:

        st.dataframe(
            high_df,
            width="stretch",
            hide_index=True,
        )

        download_dataframe(
            high_df,
            "aegisguard_high_risk_events.csv",
        )


# ============================================================
# AGENT INTELLIGENCE
# ============================================================

elif dashboard_view == "🤖 Agent Intelligence":

    st.header(
        "🤖 Agent Intelligence"
    )

    agent_df = dataframe_or_empty(
        agent_activity
    )

    if agent_df.empty:

        st.info(
            "No agent activity available."
        )

    else:

        st.dataframe(
            agent_df,
            width="stretch",
            hide_index=True,
        )

        if {
            "agent_id",
            "total_requests",
        }.issubset(
            agent_df.columns
        ):

            chart_df = (
                agent_df[
                    [
                        "agent_id",
                        "total_requests",
                    ]
                ]
                .set_index(
                    "agent_id"
                )
            )

            st.bar_chart(
                chart_df,
                width="stretch",
            )

        download_dataframe(
            agent_df,
            "aegisguard_agent_activity.csv",
        )


# ============================================================
# BEHAVIORAL ANALYTICS
# ============================================================

elif dashboard_view == "🧠 Behavioral Analytics":

    st.header(
        "🧠 Behavioral Anomaly Detection"
    )

    suspicious_df = dataframe_or_empty(
        suspicious_agents
    )

    denial_df = dataframe_or_empty(
        repeated_denials
    )

    if suspicious_df.empty:

        st.success(
            "No suspicious agents detected."
        )

    else:

        st.metric(
            "Agents Analyzed",
            len(
                suspicious_df
            ),
        )

        st.dataframe(
            suspicious_df,
            width="stretch",
            hide_index=True,
        )

        download_dataframe(
            suspicious_df,
            "aegisguard_behavior_profiles.csv",
        )

    st.divider()

    st.subheader(
        "Repeated Denial Patterns"
    )

    if denial_df.empty:

        st.info(
            "No repeated denial patterns detected."
        )

    else:

        st.dataframe(
            denial_df,
            width="stretch",
            hide_index=True,
        )


# ============================================================
# HIGH-RISK EVENTS
# ============================================================

elif dashboard_view == "🚨 High-Risk Events":

    st.header(
        "🚨 High-Risk Event Monitor"
    )

    high_df = dataframe_or_empty(
        high_risk_events
    )

    if high_df.empty:

        st.success(
            "No high-risk events detected."
        )

    else:

        st.metric(
            "High-Risk Events",
            len(high_df),
        )

        st.dataframe(
            high_df,
            width="stretch",
            hide_index=True,
        )

        st.divider()

        event_index = st.selectbox(
            "Select event",
            range(
                len(high_df)
            ),
            format_func=lambda i:
                f"Event {i + 1}",
        )

        selected_event = (
            high_df.iloc[
                event_index
            ].to_dict()
        )

        st.session_state[
            "selected_event"
        ] = selected_event

        st.subheader(
            "Selected Event"
        )

        st.json(
            selected_event
        )


# ============================================================
# SECURITY INVESTIGATION
# ============================================================

elif dashboard_view == "🔎 Security Investigation":

    st.header(
        "🔎 Security Investigation"
    )

    agent_df = dataframe_or_empty(
        agent_activity
    )

    suspicious_df = dataframe_or_empty(
        suspicious_agents
    )

    agent_names = []

    if not agent_df.empty:

        if "agent_id" in agent_df.columns:

            agent_names.extend(
                agent_df[
                    "agent_id"
                ]
                .dropna()
                .astype(str)
                .tolist()
            )

    if not suspicious_df.empty:

        if "agent_id" in suspicious_df.columns:

            agent_names.extend(
                suspicious_df[
                    "agent_id"
                ]
                .dropna()
                .astype(str)
                .tolist()
            )

    agent_names = sorted(
        set(
            agent_names
        )
    )

    if not agent_names:

        st.info(
            "No agents available for investigation."
        )

    else:

        selected_agent = st.selectbox(
            "Select Agent",
            agent_names,
        )

        st.session_state[
            "selected_agent"
        ] = selected_agent

        st.subheader(
            "Agent Activity"
        )

        if (
            not agent_df.empty
            and "agent_id"
            in agent_df.columns
        ):

            match_df = agent_df[
                agent_df[
                    "agent_id"
                ].astype(str)
                == str(
                    selected_agent
                )
            ]

            if not match_df.empty:

                st.dataframe(
                    match_df,
                    width="stretch",
                    hide_index=True,
                )

        st.subheader(
            "Behavioral Evidence"
        )

        if (
            not suspicious_df.empty
            and "agent_id"
            in suspicious_df.columns
        ):

            behavior_match = suspicious_df[
                suspicious_df[
                    "agent_id"
                ].astype(str)
                == str(
                    selected_agent
                )
            ]

            if not behavior_match.empty:

                st.dataframe(
                    behavior_match,
                    width="stretch",
                    hide_index=True,
                )

        st.subheader(
            "Repeated Denial Evidence"
        )

        denial_matches = []

        for item in repeated_denials:

            if (
                str(
                    get_field(
                        item,
                        "agent_id",
                        "",
                    )
                )
                == str(
                    selected_agent
                )
            ):

                denial_matches.append(
                    as_dict(item)
                )

        denial_agent_df = (
            dataframe_or_empty(
                denial_matches
            )
        )

        if denial_agent_df.empty:

            st.info(
                "No repeated denial evidence for this agent."
            )

        else:

            st.dataframe(
                denial_agent_df,
                width="stretch",
                hide_index=True,
            )


# ============================================================
# SCENARIO LABORATORY
# ============================================================

elif dashboard_view == "🧪 Scenario Laboratory":

    st.header(
        "🧪 Controlled Security Scenario Laboratory"
    )

    scenario_rows = [
        as_dict(
            scenario
        )
        for scenario in scenario_catalogue
    ]

    scenario_df = dataframe_or_empty(
        scenario_rows
    )

    if scenario_df.empty:

        st.warning(
            "No controlled scenarios available."
        )

    else:

        st.metric(
            "Controlled Scenarios",
            len(
                scenario_df
            ),
        )

        st.dataframe(
            scenario_df,
            width="stretch",
            hide_index=True,
        )

        download_dataframe(
            scenario_df,
            "aegisguard_controlled_scenarios.csv",
        )


# ============================================================
# EXPERIMENTAL DATASET
# ============================================================

elif dashboard_view == "🧬 Experimental Dataset":

    st.header(
        "🧬 Experimental Dataset Laboratory"
    )

    dataset_module = MODULES.get(
        "dataset",
        {},
    )

    generate_dataset = (
        dataset_module.get(
            "generate_experimental_dataset"
        )
    )

    if generate_dataset is None:

        st.error(
            "Experimental dataset generator unavailable."
        )

    else:

        seed = st.number_input(
            "Dataset Seed",
            min_value=1,
            value=42,
            step=1,
        )

        events_per_scenario = st.number_input(
            "Events per Scenario",
            min_value=1,
            max_value=100,
            value=5,
            step=1,
        )

        if st.button(
            "🧬 Generate Dataset",
            type="primary",
        ):

            try:

                dataset = generate_dataset(
                    scenarios=list(
                        scenario_catalogue
                    ),
                    events_per_scenario=int(
                        events_per_scenario
                    ),
                    seed=int(
                        seed
                    ),
                )

                st.session_state[
                    "experimental_dataset"
                ] = dataset

                st.success(
                    f"Generated {len(dataset)} events."
                )

            except Exception as exc:

                st.error(
                    "Dataset generation failed."
                )

                st.exception(
                    exc
                )

        dataset = st.session_state.get(
            "experimental_dataset"
        )

        if dataset:

            dataset_df = dataframe_or_empty(
                dataset
            )

            st.dataframe(
                dataset_df,
                width="stretch",
                hide_index=True,
            )

            download_dataframe(
                dataset_df,
                "aegisguard_experimental_dataset.csv",
            )

        else:

            st.info(
                "Generate a dataset to continue."
            )


# ============================================================
# DAY 24
# ============================================================

elif dashboard_view == "📊 Day 24 Evaluation":

    st.header(
        "📊 Day 24 — Quantitative Evaluation"
    )

    st.markdown(
        """
        ### Evaluation dimensions

        - Accuracy
        - Precision
        - Recall
        - F1 Score
        - Specificity
        - False Positive Rate
        - False Negative Rate
        - Confusion Matrix
        """
    )

    dataset = st.session_state.get(
        "experimental_dataset"
    )

    if dataset:

        dataset_df = dataframe_or_empty(
            dataset
        )

        st.metric(
            "Evaluation Events",
            len(dataset_df),
        )

        st.dataframe(
            dataset_df.head(100),
            width="stretch",
            hide_index=True,
        )

    else:

        st.info(
            "Generate an experimental dataset first."
        )


# ============================================================
# DAY 26
# ============================================================

elif dashboard_view == "⚖️ Day 26 Baseline Comparison":

    st.header(
        "⚖️ Day 26 — Baseline vs AegisGuard"
    )

    comparison_module = MODULES.get(
        "comparison",
        {},
    )

    compare_detectors = (
        comparison_module.get(
            "compare_detectors"
        )
    )

    dataset_module = MODULES.get(
        "dataset",
        {},
    )

    generate_dataset = (
        dataset_module.get(
            "generate_experimental_dataset"
        )
    )

    if (
        compare_detectors is None
        or generate_dataset is None
    ):

        st.error(
            "Day 26 evaluation modules are unavailable."
        )

    else:

        threshold = st.slider(
            "Detection Threshold",
            0,
            100,
            70,
            5,
            key="day26_threshold",
        )

        events = st.number_input(
            "Events per Scenario",
            1,
            100,
            5,
            key="day26_events",
        )

        seed = st.number_input(
            "Experiment Seed",
            1,
            100000,
            42,
            key="day26_seed",
        )

        if st.button(
            "▶️ Run Day 26 Comparison",
            type="primary",
        ):

            try:

                dataset = generate_dataset(
                    scenarios=list(
                        scenario_catalogue
                    ),
                    events_per_scenario=int(
                        events
                    ),
                    seed=int(
                        seed
                    ),
                )

                comparison = compare_detectors(
                    dataset,
                    threshold=float(
                        threshold
                    ),
                )

                st.session_state[
                    "day26_dataset"
                ] = dataset

                st.session_state[
                    "day26_results"
                ] = comparison

                st.success(
                    "Day 26 comparison completed."
                )

            except Exception as exc:

                st.error(
                    "Day 26 comparison failed."
                )

                st.exception(
                    exc
                )

        comparison = st.session_state.get(
            "day26_results"
        )

        if comparison:

            baseline = comparison.get(
                "baseline",
                {},
            )

            aegisguard_result = comparison.get(
                "aegisguard",
                {},
            )

            rows = []

            for metric in [
                "accuracy",
                "precision",
                "recall",
                "f1_score",
                "specificity",
                "false_positive_rate",
                "false_negative_rate",
            ]:

                baseline_value = safe_number(
                    baseline.get(
                        metric,
                        0,
                    )
                )

                aegisguard_value = safe_number(
                    aegisguard_result.get(
                        metric,
                        0,
                    )
                )

                rows.append(
                    {
                        "Metric":
                            metric,

                        "Baseline":
                            round(
                                baseline_value * 100,
                                2,
                            ),

                        "AegisGuard":
                            round(
                                aegisguard_value * 100,
                                2,
                            ),

                        "Difference":
                            round(
                                (
                                    aegisguard_value
                                    - baseline_value
                                )
                                * 100,
                                2,
                            ),
                    }
                )

            comparison_df = pd.DataFrame(
                rows
            )

            st.dataframe(
                comparison_df,
                width="stretch",
                hide_index=True,
            )

            st.subheader(
                "F1 Comparison"
            )

            f1_df = pd.DataFrame(
                {
                    "F1 Score": {
                        "Baseline":
                            baseline.get(
                                "f1_score",
                                0,
                            ),

                        "AegisGuard":
                            aegisguard_result.get(
                                "f1_score",
                                0,
                            ),
                    }
                }
            )

            st.bar_chart(
                f1_df,
                width="stretch",
            )


# ============================================================
# DAY 27
# ============================================================

elif dashboard_view == "🔬 Day 27 Repeated Evaluation":

    st.header(
        "🔬 Day 27 — Repeated Experimental Evaluation"
    )

    st.caption(
        "Reproducible multi-seed comparison of AegisGuard against the baseline."
    )

    repeated = MODULES.get(
        "repeated",
        {},
    )

    run_experiments = repeated.get(
        "run_repeated_experiments"
    )

    build_seed_summary = repeated.get(
        "build_seed_summary"
    )

    build_summary_table = repeated.get(
        "build_summary_table"
    )

    calculate_consistency = repeated.get(
        "calculate_consistency"
    )

    if (
        run_experiments is None
        or build_seed_summary is None
        or build_summary_table is None
        or calculate_consistency is None
    ):

        st.error(
            "Day 27 repeated evaluation module is unavailable."
        )

    else:

        col1, col2, col3 = (
            st.columns(3)
        )

        with col1:

            threshold = st.slider(
                "Detection Threshold",
                0,
                100,
                70,
                5,
                key="day27_threshold",
            )

        with col2:

            events = st.number_input(
                "Events per Scenario",
                1,
                50,
                5,
                key="day27_events",
            )

        with col3:

            experiment_count = st.number_input(
                "Experiments",
                2,
                20,
                5,
                key="day27_count",
            )

        seed_pool = [
            42,
            101,
            202,
            303,
            404,
            505,
            606,
            707,
            808,
            909,
            1001,
            1102,
            1203,
            1304,
            1405,
            1506,
            1607,
            1708,
            1809,
            2001,
        ]

        seeds = seed_pool[
            :int(
                experiment_count
            )
        ]

        st.info(
            "Seeds: "
            + ", ".join(
                str(seed)
                for seed in seeds
            )
        )

        if st.button(
            "▶️ Run Day 27 Experiments",
            type="primary",
            key="run_day27",
        ):

            if not scenario_catalogue:

                st.error(
                    "No controlled scenarios are available."
                )

            else:

                try:

                    with st.spinner(
                        "Running repeated experiments..."
                    ):

                        results = run_experiments(
                            scenarios=list(
                                scenario_catalogue
                            ),
                            seeds=seeds,
                            events_per_scenario=int(
                                events
                            ),
                            threshold=float(
                                threshold
                            ),
                        )

                    st.session_state[
                        "day27_results"
                    ] = results

                    st.session_state[
                        "day27_config"
                    ] = {
                        "threshold":
                            threshold,

                        "events_per_scenario":
                            events,

                        "seeds":
                            seeds,
                    }

                    st.success(
                        f"Completed {len(results)} experiments."
                    )

                except Exception as exc:

                    st.error(
                        "Day 27 experiment failed."
                    )

                    st.exception(
                        exc
                    )

        results = st.session_state.get(
            "day27_results"
        )

        if results:

            consistency = (
                calculate_consistency(
                    results,
                    metric="f1_score",
                )
            )

            st.divider()

            c1, c2, c3, c4 = (
                st.columns(4)
            )

            with c1:

                st.metric(
                    "Experiments",
                    consistency.get(
                        "experiments",
                        0,
                    ),
                )

            with c2:

                st.metric(
                    "AegisGuard Wins",
                    consistency.get(
                        "positive_runs",
                        0,
                    ),
                )

            with c3:

                st.metric(
                    "Win Rate",
                    f"{safe_number(consistency.get('positive_rate', 0)) * 100:.2f}%",
                )

            with c4:

                st.metric(
                    "Mean F1 Difference",
                    f"{safe_number(consistency.get('mean_difference', 0)) * 100:+.2f}%",
                )

            st.divider()

            st.subheader(
                "Seed-Level Results"
            )

            seed_df = build_seed_summary(
                results
            )

            if not seed_df.empty:

                seed_display = seed_df.copy()

                for column in [
                    "baseline_accuracy",
                    "aegisguard_accuracy",
                    "baseline_f1",
                    "aegisguard_f1",
                    "baseline_recall",
                    "aegisguard_recall",
                    "f1_difference",
                ]:

                    if column in seed_display.columns:

                        seed_display[
                            column
                        ] = (
                            seed_display[
                                column
                            ]
                            * 100
                        ).round(2)

                st.dataframe(
                    seed_display,
                    width="stretch",
                    hide_index=True,
                )

                download_dataframe(
                    seed_display,
                    "aegisguard_day27_results.csv",
                )

                if {
                    "seed",
                    "baseline_f1",
                    "aegisguard_f1",
                }.issubset(
                    seed_df.columns
                ):

                    chart_df = (
                        seed_df[
                            [
                                "seed",
                                "baseline_f1",
                                "aegisguard_f1",
                            ]
                        ]
                        .set_index(
                            "seed"
                        )
                    )

                    chart_df.columns = [
                        "Baseline",
                        "AegisGuard",
                    ]

                    st.subheader(
                        "F1 Score Across Seeds"
                    )

                    st.line_chart(
                        chart_df,
                        width="stretch",
                    )

            st.divider()

            st.subheader(
                "Aggregate Statistics"
            )

            summary_df = build_summary_table(
                results
            )

            if not summary_df.empty:

                summary_display = (
                    summary_df.copy()
                )

                for column in [
                    "baseline_mean",
                    "baseline_std",
                    "baseline_min",
                    "baseline_max",
                    "aegisguard_mean",
                    "aegisguard_std",
                    "aegisguard_min",
                    "aegisguard_max",
                    "mean_difference",
                    "difference_std",
                ]:

                    if column in summary_display.columns:

                        summary_display[
                            column
                        ] = (
                            summary_display[
                                column
                            ]
                            * 100
                        ).round(2)

                st.dataframe(
                    summary_display,
                    width="stretch",
                    hide_index=True,
                )

            st.warning(
                """
                Research caution: repeated experiments provide
                robustness evidence, but do not by themselves prove
                statistical significance or real-world generalization.
                """
            )

        else:

            st.info(
                "Run the Day 27 experiment to generate results."
            )


# ============================================================
# RESEARCH INTERPRETATION
# ============================================================

elif dashboard_view == "📚 Research Interpretation":

    st.header(
        "📚 Research Interpretation"
    )

    st.subheader(
        "Core Research Question"
    )

    st.markdown(
        """
        **Does behavior-aware security intelligence provide
        measurable detection benefit beyond a simpler
        risk-only authorization baseline?**
        """
    )

    st.divider()

    evidence_df = pd.DataFrame(
        [
            {
                "Stage":
                    "Authorization",

                "Evidence":
                    "Allow / Deny decisions",

                "Purpose":
                    "Security enforcement",
            },

            {
                "Stage":
                    "Risk",

                "Evidence":
                    "Risk score",

                "Purpose":
                    "Risk prioritization",
            },

            {
                "Stage":
                    "Behavior",

                "Evidence":
                    "Repeated behavior / denial patterns",

                "Purpose":
                    "Behavioral context",
            },

            {
                "Stage":
                    "Controlled Experiments",

                "Evidence":
                    "Ground-truth scenarios",

                "Purpose":
                    "Reproducible evaluation",
            },

            {
                "Stage":
                    "Quantitative Evaluation",

                "Evidence":
                    "Precision / Recall / F1",

                "Purpose":
                    "Performance measurement",
            },

            {
                "Stage":
                    "Repeated Evaluation",

                "Evidence":
                    "Multiple random seeds",

                "Purpose":
                    "Robustness assessment",
            },
        ]
    )

    st.dataframe(
        evidence_df,
        width="stretch",
        hide_index=True,
    )

    st.divider()

    st.subheader(
        "Current Research Discipline"
    )

    st.markdown(
        """
        ### We can reasonably report

        - Controlled security scenarios.
        - Reproducible experimental execution.
        - Baseline comparison.
        - Behavior-aware detection signals.
        - Quantitative performance metrics.
        - Multi-seed repeated evaluation.

        ### We should NOT claim yet

        - Universal superiority.
        - Production readiness.
        - Real-world generalization.
        - Statistical significance without statistical testing.
        - Novelty merely because the implementation is different.
        """
    )


# ============================================================
# SYSTEM STATUS
# ============================================================

elif dashboard_view == "⚙️ System Status":

    st.header(
        "⚙️ System Status"
    )

    status_rows = []

    for module_name in [
        "analytics",
        "behavior",
        "scenarios",
        "comparison",
        "dataset",
        "repeated",
        "evaluation",
    ]:

        status_rows.append(
            {
                "Module":
                    module_name,

                "Status":
                    (
                        "READY"
                        if module_name in MODULES
                        else "UNAVAILABLE"
                    ),
            }
        )

    status_df = pd.DataFrame(
        status_rows
    )

    st.dataframe(
        status_df,
        width="stretch",
        hide_index=True,
    )

    st.divider()

    st.subheader(
        "Session State"
    )

    session_rows = []

    for key in [
        "selected_agent",
        "selected_event",
        "day26_results",
        "day27_results",
        "experimental_dataset",
    ]:

        value = st.session_state.get(
            key
        )

        session_rows.append(
            {
                "State":
                    key,

                "Status":
                    (
                        "AVAILABLE"
                        if value
                        else "EMPTY"
                    ),
            }
        )

    st.dataframe(
        pd.DataFrame(
            session_rows
        ),
        width="stretch",
        hide_index=True,
    )

    st.divider()

    if st.button(
        "🧹 Clear Research Session"
    ):

        for key in DEFAULT_STATE:

            if key in st.session_state:

                del st.session_state[
                    key
                ]

        st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🛡️ AegisGuard • Behavior-Aware Security for Autonomous AI Agents"
)

st.caption(
    "Research Prototype • Controlled Evaluation • Reproducible Experiments"
)