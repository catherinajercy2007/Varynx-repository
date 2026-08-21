from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import streamlit as st


# ============================================================
# AEGISGUARD
# UNIFIED DAY 1–29 SECURITY + RESEARCH DASHBOARD
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
APP_DIR = PROJECT_ROOT / "app"
TESTS_DIR = PROJECT_ROOT / "tests"
EXPECTED_ENV = Path(r"D:\aegisguard-env").resolve()


st.set_page_config(
    page_title="AegisGuard Intelligence SOC",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SAFE HELPERS
# ============================================================

def safe_call(
    function: Callable | None,
    default: Any = None,
    *args: Any,
    **kwargs: Any,
) -> Any:
    if function is None:
        return default

    try:
        return function(*args, **kwargs)
    except Exception:
        return default


def as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)

    if hasattr(value, "model_dump"):
        try:
            return dict(value.model_dump())
        except Exception:
            pass

    if hasattr(value, "__dict__"):
        try:
            return dict(value.__dict__)
        except Exception:
            pass

    return {}


def dataframe_or_empty(rows: Any) -> pd.DataFrame:
    if rows is None:
        return pd.DataFrame()

    if isinstance(rows, pd.DataFrame):
        return rows.copy()

    try:
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


def safe_number(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def format_percent(value: Any) -> str:
    return f"{safe_number(value) * 100:.2f}%"


def download_dataframe(
    dataframe: pd.DataFrame,
    filename: str,
) -> None:

    if dataframe.empty:
        return

    csv_data = (
        dataframe
        .to_csv(index=False)
        .encode("utf-8")
    )

    st.download_button(
        label="⬇️ Download CSV",
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        key=f"download_{filename}",
    )


# ============================================================
# MODULE LOADER
# ============================================================

def load_modules() -> dict[str, Any]:

    modules: dict[str, Any] = {}

    # --------------------------------------------------------
    # Core analytics
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
            "get_total_events": get_total_events,
            "get_decision_counts": get_decision_counts,
            "get_risk_summary": get_risk_summary,
            "get_agent_activity": get_agent_activity,
            "get_high_risk_events": get_high_risk_events,
        }

    except Exception as exc:
        modules["analytics_error"] = str(exc)

    # --------------------------------------------------------
    # Behavior
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
    # Scenarios
    # --------------------------------------------------------

    try:
        from app.attack_scenarios import (
            get_attack_scenarios,
            get_attack_scenario_summary,
        )

        modules["scenarios"] = {
            "get_attack_scenarios":
                get_attack_scenarios,
            "get_attack_scenario_summary":
                get_attack_scenario_summary,
        }

    except Exception as exc:
        modules["scenarios_error"] = str(exc)

    # --------------------------------------------------------
    # Investigation
    # --------------------------------------------------------

    try:
        import app.investigation as investigation

        modules["investigation"] = investigation

    except Exception as exc:
        modules["investigation_error"] = str(exc)

    # --------------------------------------------------------
    # Experimental dataset
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
    # Detection evaluation
    # --------------------------------------------------------

    try:
        import app.evaluation as evaluation

        modules["evaluation"] = evaluation

    except Exception as exc:
        modules["evaluation_error"] = str(exc)

    # --------------------------------------------------------
    # Comparison
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
    # Repeated evaluation
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
    # Statistical evaluation — Day 28
    # --------------------------------------------------------

    try:
        import app.statistical_evaluation as statistical

        modules["statistical"] = statistical

    except Exception as exc:
        modules["statistical_error"] = str(exc)

    # --------------------------------------------------------
    # Multi-resolution behavior — Day 28
    # --------------------------------------------------------

    try:
        import app.multiresolution_behavior as multiresolution

        modules["multiresolution"] = multiresolution

    except Exception as exc:
        modules["multiresolution_error"] = str(exc)

    # --------------------------------------------------------
    # Cross-context correlation — Day 29
    # --------------------------------------------------------

    try:
        import app.cross_context_correlation as cross_context

        modules["cross_context"] = cross_context

    except Exception as exc:
        modules["cross_context_error"] = str(exc)

    return modules


MODULES = load_modules()


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "selected_agent": None,
    "selected_event": None,
    "experimental_dataset": None,
    "day26_results": None,
    "day26_dataset": None,
    "day27_results": None,
    "day27_config": None,
    "day28_profile": None,
    "day28_events": None,
    "day29_profile": None,
    "day29_summary": None,
    "day29_events": None,
    "test_result": None,
}


for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# UI
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 0.2rem;
    }

    .main-subtitle {
        font-size: 1rem;
        color: #667085;
        margin-bottom: 1.4rem;
    }

    .card {
        border: 1px solid rgba(128,128,128,0.22);
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 12px;
    }

    .footer {
        text-align: center;
        color: #667085;
        padding: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOAD CURRENT DATA
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
    analytics.get("get_total_events"),
    0,
)


decision_counts = safe_call(
    analytics.get("get_decision_counts"),
    {},
)


risk_summary = safe_call(
    analytics.get("get_risk_summary"),
    {},
)


agent_activity = safe_call(
    analytics.get("get_agent_activity"),
    [],
)


high_risk_events = safe_call(
    analytics.get("get_high_risk_events"),
    [],
)


suspicious_agents = safe_call(
    behavior.get("get_suspicious_agents"),
    [],
)


repeated_denials = safe_call(
    behavior.get("get_repeated_denials"),
    [],
)


scenario_catalogue = safe_call(
    scenarios_module.get("get_attack_scenarios"),
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
    authorization, contextual risk, behavioral monitoring,
    controlled scenarios, reproducible evaluation,
    statistical analysis and cross-context intelligence.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🛡️ AegisGuard")

st.sidebar.caption(
    "AI Agent Security Research Platform"
)

st.sidebar.divider()


NAVIGATION = [
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
    "📐 Day 28 Statistical Evaluation",
    "🧬 Day 28 Multi-Resolution Behavior",
    "🔗 Day 29 Cross-Context Intelligence",
    "📚 Research Interpretation",
    "📅 Project Construction",
    "🚀 Deployment & Validation",
    "⚙️ System Status",
]


dashboard_view = st.sidebar.radio(
    "Navigation",
    NAVIGATION,
)


st.sidebar.divider()

st.sidebar.markdown(
    "**Research Pipeline**"
)

st.sidebar.caption(
    "Authorize → Observe → Understand → "
    "Detect → Evaluate → Correlate → Defend"
)

st.sidebar.divider()

st.sidebar.caption(
    "Current milestone: Day 29"
)


# ============================================================
# SECURITY OVERVIEW
# ============================================================

if dashboard_view == "🏠 Security Overview":

    st.header(
        "📊 Security Operations Overview"
    )

    c1, c2, c3, c4, c5 = st.columns(5)

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

    st.divider()

    st.subheader(
        "Current Research Stack"
    )

    stack = pd.DataFrame(
        [
            ["Authorization", "Policy enforcement", "Day 1–12"],
            ["Risk", "Contextual risk scoring", "Day 1–20"],
            ["Behavior", "Repeated behavioral evidence", "Day 13–20"],
            ["Scenarios", "Controlled ground-truth cases", "Day 21–22"],
            ["Dataset", "Reproducible experiments", "Day 23"],
            ["Evaluation", "Quantitative detection metrics", "Day 24–25"],
            ["Baseline", "Comparative evaluation", "Day 26"],
            ["Repeated", "Multi-seed robustness", "Day 27"],
            ["Statistics", "Statistical evaluation", "Day 28"],
            ["Multi-resolution", "Hierarchical behavior", "Day 28"],
            ["Cross-context", "Distributed behavior", "Day 29"],
        ],
        columns=[
            "Layer",
            "Function",
            "Milestone",
        ],
    )

    st.dataframe(
        stack,
        width="stretch",
        hide_index=True,
    )


# ============================================================
# RISK INTELLIGENCE
# ============================================================

elif dashboard_view == "📈 Risk Intelligence":

    st.header(
        "📈 Risk Intelligence"
    )

    r1, r2, r3, r4 = st.columns(4)

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

    high_df = dataframe_or_empty(
        high_risk_events
    )

    st.divider()

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
        "🧠 Behavioral Analytics"
    )

    suspicious_df = dataframe_or_empty(
        suspicious_agents
    )

    denial_df = dataframe_or_empty(
        repeated_denials
    )

    c1, c2 = st.columns(2)

    with c1:
        st.metric(
            "Suspicious Agents",
            len(suspicious_df),
        )

    with c2:
        st.metric(
            "Repeated Denial Patterns",
            len(denial_df),
        )

    st.divider()

    st.subheader(
        "Suspicious Agents"
    )

    if suspicious_df.empty:

        st.success(
            "No suspicious agents detected."
        )

    else:

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
        "Repeated Denials"
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
            range(len(high_df)),
            format_func=lambda i:
                f"Event {i + 1}",
            key="high_risk_event_select",
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

    agent_names: list[str] = []

    if (
        not agent_df.empty
        and "agent_id" in agent_df.columns
    ):

        agent_names.extend(
            agent_df[
                "agent_id"
            ]
            .dropna()
            .astype(str)
            .tolist()
        )

    if (
        not suspicious_df.empty
        and "agent_id" in suspicious_df.columns
    ):

        agent_names.extend(
            suspicious_df[
                "agent_id"
            ]
            .dropna()
            .astype(str)
            .tolist()
        )

    agent_names = sorted(
        set(agent_names)
    )

    if not agent_names:

        st.info(
            "No agents available for investigation."
        )

    else:

        selected_agent = st.selectbox(
            "Select Agent",
            agent_names,
            key="investigation_agent",
        )

        st.session_state[
            "selected_agent"
        ] = selected_agent

        if (
            not agent_df.empty
            and "agent_id" in agent_df.columns
        ):

            match_df = agent_df[
                agent_df[
                    "agent_id"
                ].astype(str)
                == str(selected_agent)
            ]

            if not match_df.empty:

                st.subheader(
                    "Agent Activity"
                )

                st.dataframe(
                    match_df,
                    width="stretch",
                    hide_index=True,
                )

        if (
            not suspicious_df.empty
            and "agent_id" in suspicious_df.columns
        ):

            behavior_match = suspicious_df[
                suspicious_df[
                    "agent_id"
                ].astype(str)
                == str(selected_agent)
            ]

            if not behavior_match.empty:

                st.subheader(
                    "Behavioral Evidence"
                )

                st.dataframe(
                    behavior_match,
                    width="stretch",
                    hide_index=True,
                )

        denial_rows = []

        for item in repeated_denials:

            item_dict = as_dict(item)

            if str(
                item_dict.get(
                    "agent_id",
                    "",
                )
            ) == str(selected_agent):

                denial_rows.append(
                    item_dict
                )

        denial_df = dataframe_or_empty(
            denial_rows
        )

        st.subheader(
            "Repeated Denial Evidence"
        )

        if denial_df.empty:

            st.info(
                "No repeated-denial evidence for this agent."
            )

        else:

            st.dataframe(
                denial_df,
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

    scenario_df = dataframe_or_empty(
        [
            as_dict(item)
            for item in scenario_catalogue
        ]
    )

    if scenario_df.empty:

        st.warning(
            "No controlled scenarios available."
        )

    else:

        st.metric(
            "Controlled Scenarios",
            len(scenario_df),
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

        summary_function = (
            scenarios_module.get(
                "get_attack_scenario_summary"
            )
        )

        summary = safe_call(
            summary_function,
            {},
        )

        if summary:

            st.subheader(
                "Scenario Summary"
            )

            summary_df = pd.DataFrame(
                [
                    {
                        "Metric": key,
                        "Value": value,
                    }
                    for key, value
                    in summary.items()
                    if not isinstance(
                        value,
                        (dict, list),
                    )
                ]
            )

            st.dataframe(
                summary_df,
                width="stretch",
                hide_index=True,
            )


# ============================================================
# EXPERIMENTAL DATASET
# ============================================================

elif dashboard_view == "🧬 Experimental Dataset":

    st.header(
        "🧬 Experimental Dataset Laboratory"
    )

    generate_dataset = (
        MODULES
        .get("dataset", {})
        .get("generate_experimental_dataset")
    )

    if generate_dataset is None:

        st.error(
            "Experimental dataset generator unavailable."
        )

    else:

        c1, c2 = st.columns(2)

        with c1:

            seed = st.number_input(
                "Dataset Seed",
                min_value=1,
                value=42,
                step=1,
                key="dataset_seed",
            )

        with c2:

            events_per_scenario = st.number_input(
                "Events per Scenario",
                min_value=1,
                max_value=100,
                value=5,
                step=1,
                key="dataset_events",
            )

        if st.button(
            "🧬 Generate Dataset",
            type="primary",
            key="generate_dataset",
        ):

            try:

                dataset = generate_dataset(
                    scenarios=list(
                        scenario_catalogue
                    ),
                    events_per_scenario=int(
                        events_per_scenario
                    ),
                    seed=int(seed),
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

                st.exception(exc)

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
# DAY 24 — QUANTITATIVE EVALUATION
# ============================================================

elif dashboard_view == "📊 Day 24 Evaluation":

    st.header(
        "📊 Day 24 — Quantitative Detection Evaluation"
    )

    st.markdown(
        """
        Evaluation dimensions:

        **Accuracy · Precision · Recall · F1 · Specificity ·
        False Positive Rate · False Negative Rate**
        """
    )

    dataset = st.session_state.get(
        "experimental_dataset"
    )

    evaluation_module = MODULES.get(
        "evaluation"
    )

    if not dataset:

        st.info(
            "Generate an experimental dataset first."
        )

    elif evaluation_module is None:

        st.error(
            "Evaluation module unavailable."
        )

    else:

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

        st.info(
            "Use the evaluation module's implemented metric functions "
            "for the authoritative quantitative results."
        )


# ============================================================
# DAY 26 — BASELINE COMPARISON
# ============================================================

elif dashboard_view == "⚖️ Day 26 Baseline Comparison":

    st.header(
        "⚖️ Day 26 — Baseline vs AegisGuard"
    )

    comparison = MODULES.get(
        "comparison",
        {},
    )

    compare_detectors = comparison.get(
        "compare_detectors"
    )

    generate_dataset = (
        MODULES
        .get("dataset", {})
        .get("generate_experimental_dataset")
    )

    if (
        compare_detectors is None
        or generate_dataset is None
    ):

        st.error(
            "Day 26 evaluation modules unavailable."
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
            key="run_day26",
        ):

            try:

                dataset = generate_dataset(
                    scenarios=list(
                        scenario_catalogue
                    ),
                    events_per_scenario=int(events),
                    seed=int(seed),
                )

                result = compare_detectors(
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
                ] = result

                st.success(
                    "Day 26 comparison completed."
                )

            except Exception as exc:

                st.error(
                    "Day 26 comparison failed."
                )

                st.exception(exc)

        result = st.session_state.get(
            "day26_results"
        )

        if result:

            baseline = result.get(
                "baseline",
                {},
            )

            aegisguard = result.get(
                "aegisguard",
                {},
            )

            rows = []

            metrics = [
                "accuracy",
                "precision",
                "recall",
                "f1_score",
                "specificity",
                "false_positive_rate",
                "false_negative_rate",
            ]

            for metric in metrics:

                baseline_value = safe_number(
                    baseline.get(
                        metric,
                        0,
                    )
                )

                aegisguard_value = safe_number(
                    aegisguard.get(
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

            if {
                "accuracy",
                "precision",
                "recall",
                "f1_score",
            }.intersection(
                comparison_df["Metric"]
            ):

                chart_df = (
                    comparison_df[
                        comparison_df[
                            "Metric"
                        ].isin(
                            [
                                "accuracy",
                                "precision",
                                "recall",
                                "f1_score",
                            ]
                        )
                    ]
                    .set_index(
                        "Metric"
                    )[
                        [
                            "Baseline",
                            "AegisGuard",
                        ]
                    ]
                )

                st.bar_chart(
                    chart_df,
                    width="stretch",
                )


# ============================================================
# DAY 27 — REPEATED EVALUATION
# ============================================================

elif dashboard_view == "🔬 Day 27 Repeated Evaluation":

    st.header(
        "🔬 Day 27 — Repeated Experimental Evaluation"
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

    if any(
        function is None
        for function in [
            run_experiments,
            build_seed_summary,
            build_summary_table,
            calculate_consistency,
        ]
    ):

        st.error(
            "Day 27 repeated evaluation module is unavailable."
        )

    else:

        c1, c2, c3 = st.columns(3)

        with c1:

            threshold = st.slider(
                "Detection Threshold",
                0,
                100,
                70,
                5,
                key="day27_threshold",
            )

        with c2:

            events = st.number_input(
                "Events per Scenario",
                1,
                50,
                5,
                key="day27_events",
            )

        with c3:

            experiment_count = st.number_input(
                "Experiments",
                2,
                20,
                5,
                key="day27_count",
            )

        seeds = [
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
        ][:int(experiment_count)]

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

            try:

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

                st.exception(exc)

        results = st.session_state.get(
            "day27_results"
        )

        if results:

            consistency = calculate_consistency(
                results,
                metric="f1_score",
            )

            c1, c2, c3, c4 = st.columns(4)

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
                    format_percent(
                        consistency.get(
                            "positive_rate",
                            0,
                        )
                    ),
                )

            with c4:
                st.metric(
                    "Mean F1 Difference",
                    f"{safe_number(consistency.get('mean_difference', 0)) * 100:+.2f}%",
                )

            seed_df = dataframe_or_empty(
                build_seed_summary(results)
            )

            if not seed_df.empty:

                display_df = seed_df.copy()

                for column in [
                    "baseline_accuracy",
                    "aegisguard_accuracy",
                    "baseline_f1",
                    "aegisguard_f1",
                    "baseline_recall",
                    "aegisguard_recall",
                    "f1_difference",
                ]:

                    if column in display_df.columns:

                        display_df[column] = (
                            pd.to_numeric(
                                display_df[column],
                                errors="coerce",
                            )
                            * 100
                        ).round(2)

                st.subheader(
                    "Seed-Level Results"
                )

                st.dataframe(
                    display_df,
                    width="stretch",
                    hide_index=True,
                )

                download_dataframe(
                    display_df,
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
                        .copy()
                        .set_index("seed")
                    )

                    chart_df.columns = [
                        "Baseline",
                        "AegisGuard",
                    ]

                    st.line_chart(
                        chart_df,
                        width="stretch",
                    )

            summary_df = dataframe_or_empty(
                build_summary_table(results)
            )

            if not summary_df.empty:

                st.subheader(
                    "Aggregate Statistics"
                )

                st.dataframe(
                    summary_df,
                    width="stretch",
                    hide_index=True,
                )

            st.warning(
                "Repeated evaluation supports robustness analysis, "
                "but does not by itself establish statistical significance."
            )

        else:

            st.info(
                "Run the Day 27 experiment to generate results."
            )


# ============================================================
# DAY 28 — STATISTICAL EVALUATION
# ============================================================

elif dashboard_view == "📐 Day 28 Statistical Evaluation":

    st.header(
        "📐 Day 28 — Statistical Evaluation"
    )

    statistical = MODULES.get(
        "statistical"
    )

    results = st.session_state.get(
        "day27_results"
    )

    if statistical is None:

        st.error(
            "app.statistical_evaluation could not be imported."
        )

        error = MODULES.get(
            "statistical_error"
        )

        if error:
            st.code(error)

    elif not results:

        st.info(
            "Run Day 27 repeated evaluation first."
        )

    else:

        st.success(
            "Repeated experimental results are available for statistical analysis."
        )

        result_df = dataframe_or_empty(
            results
        )

        if not result_df.empty:

            st.subheader(
                "Repeated Experiment Results"
            )

            st.dataframe(
                result_df,
                width="stretch",
                hide_index=True,
            )

        st.divider()

        st.subheader(
            "Available Statistical Functions"
        )

        functions = [
            name
            for name in dir(statistical)
            if not name.startswith("_")
            and callable(
                getattr(
                    statistical,
                    name,
                )
            )
        ]

        st.dataframe(
            pd.DataFrame(
                {
                    "Function":
                        functions
                }
            ),
            width="stretch",
            hide_index=True,
        )

        st.info(
            """
            The statistical module is treated as the authoritative
            implementation for statistical calculations. The dashboard
            deliberately does not invent p-values, confidence intervals,
            effect sizes or significance conclusions.
            """
        )

        paired_function = getattr(
            statistical,
            "calculate_paired_differences",
            None,
        )

        if paired_function is not None:

            try:

                differences = paired_function(
                    results
                )

                if differences:

                    st.subheader(
                        "Paired Differences"
                    )

                    difference_df = pd.DataFrame(
                        {
                            "Experiment":
                                range(
                                    1,
                                    len(differences) + 1,
                                ),

                            "Difference":
                                differences,
                        }
                    )

                    st.dataframe(
                        difference_df,
                        width="stretch",
                        hide_index=True,
                    )

            except Exception as exc:

                st.warning(
                    f"Paired-difference calculation unavailable for this result structure: {exc}"
                )


# ============================================================
# DAY 28 — MULTI-RESOLUTION
# ============================================================

elif dashboard_view == "🧬 Day 28 Multi-Resolution Behavior":

    st.header(
        "🧬 Day 28 — Multi-Resolution Behavioral Intelligence"
    )

    multiresolution = MODULES.get(
        "multiresolution"
    )

    if multiresolution is None:

        st.error(
            "Multi-resolution module unavailable."
        )

        error = MODULES.get(
            "multiresolution_error"
        )

        if error:
            st.code(error)

    else:

        events = (
            st.session_state.get(
                "day28_events"
            )
            or
            st.session_state.get(
                "experimental_dataset"
            )
            or []
        )

        events = [
            as_dict(event)
            for event in events
        ]

        st.metric(
            "Events Available",
            len(events),
        )

        st.markdown(
            """
            **Action → Capability → Resource → Context**

            Day 28 evaluates behavior at multiple resolutions instead
            of relying exclusively on isolated authorization decisions.
            """
        )

        if not events:

            st.info(
                "Generate an experimental dataset or provide events first."
            )

        else:

            if st.button(
                "Analyze Multi-Resolution Behavior",
                type="primary",
                key="day28_analyze",
            ):

                candidate_functions = [
                    "calculate_multi_resolution_profile",
                    "build_multi_resolution_profile",
                    "analyze_multi_resolution",
                    "calculate_behavioral_profile",
                ]

                profile = None

                for function_name in candidate_functions:

                    function = getattr(
                        multiresolution,
                        function_name,
                        None,
                    )

                    if callable(function):

                        try:

                            profile = function(
                                events
                            )

                            break

                        except Exception:

                            continue

                if profile is None:

                    st.error(
                        "No compatible multi-resolution analysis function was found."
                    )

                else:

                    st.session_state[
                        "day28_profile"
                    ] = profile

            profile = st.session_state.get(
                "day28_profile"
            )

            if profile:

                if isinstance(
                    profile,
                    dict,
                ):

                    scalar_rows = []

                    for key, value in profile.items():

                        if isinstance(
                            value,
                            (str, int, float, bool),
                        ):

                            scalar_rows.append(
                                {
                                    "Metric":
                                        key,

                                    "Value":
                                        value,
                                }
                            )

                    if scalar_rows:

                        st.subheader(
                            "Resolution Summary"
                        )

                        st.dataframe(
                            pd.DataFrame(
                                scalar_rows
                            ),
                            width="stretch",
                            hide_index=True,
                        )

                    with st.expander(
                        "View complete multi-resolution profile"
                    ):

                        st.json(profile)

                else:

                    st.write(profile)


# ============================================================
# DAY 29 — CROSS-CONTEXT INTELLIGENCE
# ============================================================

elif dashboard_view == "🔗 Day 29 Cross-Context Intelligence":

    st.header(
        "🔗 Day 29 — Cross-Context Behavioral Intelligence"
    )

    st.caption(
        "Identify distributed behavioral relationships across contexts, "
        "capabilities and resources."
    )

    cross_context = MODULES.get(
        "cross_context"
    )

    if cross_context is None:

        st.error(
            "Day 29 cross-context module unavailable."
        )

        error = MODULES.get(
            "cross_context_error"
        )

        if error:
            st.code(error)

    else:

        events = (
            st.session_state.get(
                "day29_events"
            )
            or
            st.session_state.get(
                "day28_events"
            )
            or
            st.session_state.get(
                "experimental_dataset"
            )
            or []
        )

        events = [
            as_dict(event)
            for event in events
        ]

        st.subheader(
            "Input Events"
        )

        input_mode = st.radio(
            "Source",
            [
                "Current Session Events",
                "Manual JSON",
            ],
            horizontal=True,
            key="day29_source",
        )

        if input_mode == "Manual JSON":

            default_json = json.dumps(
                [
                    {
                        "agent_id":
                            "agent-demo",

                        "action":
                            "document.read",

                        "capability":
                            "document.read",

                        "resource":
                            "document-A",

                        "context":
                            "context-A",
                    },

                    {
                        "agent_id":
                            "agent-demo",

                        "action":
                            "api.call",

                        "capability":
                            "api.call",

                        "resource":
                            "service-A",

                        "context":
                            "context-B",
                    },

                    {
                        "agent_id":
                            "agent-demo",

                        "action":
                            "api.call",

                        "capability":
                            "api.call",

                        "resource":
                            "service-B",

                        "context":
                            "context-C",
                    },
                ],
                indent=2,
            )

            raw_json = st.text_area(
                "Event JSON",
                value=default_json,
                height=260,
                key="day29_manual_json",
            )

            if st.button(
                "Load Manual Events",
                key="day29_load",
            ):

                try:

                    parsed = json.loads(
                        raw_json
                    )

                    if isinstance(
                        parsed,
                        dict,
                    ):

                        events = [
                            parsed
                        ]

                    elif isinstance(
                        parsed,
                        list,
                    ):

                        events = [
                            as_dict(item)
                            for item in parsed
                        ]

                    else:

                        raise ValueError(
                            "JSON must be an object or list."
                        )

                    st.session_state[
                        "day29_events"
                    ] = events

                    st.success(
                        f"Loaded {len(events)} events."
                    )

                except Exception as exc:

                    st.error(
                        f"Invalid event JSON: {exc}"
                    )

        st.metric(
            "Events",
            len(events),
        )

        if events:

            if st.button(
                "▶️ Run Cross-Context Analysis",
                type="primary",
                key="day29_analyze",
            ):

                try:

                    profile_function = getattr(
                        cross_context,
                        "build_cross_context_profile",
                        None,
                    )

                    summary_function = getattr(
                        cross_context,
                        "build_research_summary",
                        None,
                    )

                    if profile_function is None:

                        raise RuntimeError(
                            "build_cross_context_profile is missing."
                        )

                    profile = profile_function(
                        events
                    )

                    summary = (
                        summary_function(events)
                        if summary_function
                        else {}
                    )

                    st.session_state[
                        "day29_profile"
                    ] = profile

                    st.session_state[
                        "day29_summary"
                    ] = summary

                    st.session_state[
                        "day29_events"
                    ] = events

                    st.success(
                        "Day 29 analysis completed."
                    )

                except Exception as exc:

                    st.error(
                        "Day 29 analysis failed."
                    )

                    st.exception(exc)

            profile = st.session_state.get(
                "day29_profile"
            )

            summary = st.session_state.get(
                "day29_summary"
            )

            if profile:

                if not summary:

                    risk_function = getattr(
                        cross_context,
                        "calculate_cross_context_risk",
                        None,
                    )

                    correlations_function = getattr(
                        cross_context,
                        "calculate_context_correlations",
                        None,
                    )

                    score = safe_call(
                        risk_function,
                        0.0,
                        events,
                    )

                    correlations = safe_call(
                        correlations_function,
                        {},
                        events,
                    )

                    summary = {
                        "event_count":
                            len(events),

                        "context_count":
                            correlations.get(
                                "context_count",
                                0,
                            )
                            if isinstance(
                                correlations,
                                dict,
                            )
                            else 0,

                        "correlated_pairs":
                            correlations.get(
                                "correlated_pairs",
                                0,
                            )
                            if isinstance(
                                correlations,
                                dict,
                            )
                            else 0,

                        "cross_context_risk":
                            score,
                    }

                st.divider()

                c1, c2, c3, c4 = st.columns(4)

                with c1:

                    st.metric(
                        "Events",
                        summary.get(
                            "event_count",
                            len(events),
                        ),
                    )

                with c2:

                    st.metric(
                        "Contexts",
                        summary.get(
                            "context_count",
                            0,
                        ),
                    )

                with c3:

                    st.metric(
                        "Correlated Pairs",
                        summary.get(
                            "correlated_pairs",
                            0,
                        ),
                    )

                with c4:

                    st.metric(
                        "Cross-Context Risk",
                        f"{safe_number(summary.get('cross_context_risk', 0)):.2f}",
                    )

                st.divider()

                # ------------------------------------------------
                # Distributions
                # ------------------------------------------------

                distribution_functions = {
                    "Context":
                        "calculate_context_distribution",

                    "Capability":
                        "calculate_capability_distribution",

                    "Resource":
                        "calculate_resource_distribution",

                    "Action":
                        "calculate_action_distribution",
                }

                for label, function_name in (
                    distribution_functions.items()
                ):

                    function = getattr(
                        cross_context,
                        function_name,
                        None,
                    )

                    if not callable(function):
                        continue

                    distribution = safe_call(
                        function,
                        {},
                        events,
                    )

                    if distribution:

                        st.subheader(
                            f"{label} Distribution"
                        )

                        distribution_df = pd.DataFrame(
                            [
                                {
                                    label:
                                        key,

                                    "Count":
                                        value,
                                }
                                for key, value
                                in distribution.items()
                            ]
                        )

                        st.dataframe(
                            distribution_df,
                            width="stretch",
                            hide_index=True,
                        )

                # ------------------------------------------------
                # Diversity
                # ------------------------------------------------

                diversity_function = getattr(
                    cross_context,
                    "calculate_behavioral_diversity",
                    None,
                )

                diversity = safe_call(
                    diversity_function,
                    {},
                    events,
                )

                if diversity:

                    st.subheader(
                        "Behavioral Diversity"
                    )

                    diversity_df = pd.DataFrame(
                        [
                            {
                                "Dimension":
                                    key,

                                "Value":
                                    value,
                            }
                            for key, value
                            in diversity.items()
                        ]
                    )

                    st.dataframe(
                        diversity_df,
                        width="stretch",
                        hide_index=True,
                    )

                    st.bar_chart(
                        diversity_df.set_index(
                            "Dimension"
                        ),
                        width="stretch",
                    )

                # ------------------------------------------------
                # Entropy
                # ------------------------------------------------

                entropy_function = getattr(
                    cross_context,
                    "calculate_cross_context_entropy",
                    None,
                )

                entropy = safe_call(
                    entropy_function,
                    {},
                    events,
                )

                if entropy:

                    st.subheader(
                        "Cross-Context Entropy"
                    )

                    entropy_df = pd.DataFrame(
                        [
                            {
                                "Dimension":
                                    key,

                                "Entropy":
                                    value,
                            }
                            for key, value
                            in entropy.items()
                        ]
                    )

                    st.dataframe(
                        entropy_df,
                        width="stretch",
                        hide_index=True,
                    )

                # ------------------------------------------------
                # Correlations
                # ------------------------------------------------

                correlation_function = getattr(
                    cross_context,
                    "calculate_context_correlations",
                    None,
                )

                correlation_result = safe_call(
                    correlation_function,
                    {},
                    events,
                )

                if isinstance(
                    correlation_result,
                    dict,
                ):

                    relationships = (
                        correlation_result.get(
                            "relationships",
                            [],
                        )
                    )

                    correlation_df = (
                        dataframe_or_empty(
                            relationships
                        )
                    )

                    st.subheader(
                        "Context Correlations"
                    )

                    if correlation_df.empty:

                        st.info(
                            "No correlated context pairs detected."
                        )

                    else:

                        st.dataframe(
                            correlation_df,
                            width="stretch",
                            hide_index=True,
                        )

                        if (
                            "correlation_score"
                            in correlation_df.columns
                        ):

                            chart_df = (
                                correlation_df[
                                    [
                                        "context_a",
                                        "context_b",
                                        "correlation_score",
                                    ]
                                ]
                                .copy()
                            )

                            chart_df["pair"] = (
                                chart_df[
                                    "context_a"
                                ].astype(str)
                                + " ↔ "
                                + chart_df[
                                    "context_b"
                                ].astype(str)
                            )

                            st.bar_chart(
                                chart_df[
                                    [
                                        "pair",
                                        "correlation_score",
                                    ]
                                ].set_index(
                                    "pair"
                                ),
                                width="stretch",
                            )

                # ------------------------------------------------
                # Agent profiles
                # ------------------------------------------------

                agent_function = getattr(
                    cross_context,
                    "build_agent_profiles",
                    None,
                )

                agent_profiles = safe_call(
                    agent_function,
                    {},
                    events,
                )

                if agent_profiles:

                    st.subheader(
                        "Agent-Level Profiles"
                    )

                    rows = []

                    for agent_id, agent_profile in (
                        agent_profiles.items()
                    ):

                        agent_profile = (
                            agent_profile
                            if isinstance(
                                agent_profile,
                                dict,
                            )
                            else {}
                        )

                        correlations = (
                            agent_profile.get(
                                "correlations",
                                {},
                            )
                        )

                        rows.append(
                            {
                                "Agent":
                                    agent_id,

                                "Events":
                                    agent_profile.get(
                                        "event_count",
                                        0,
                                    ),

                                "Contexts":
                                    correlations.get(
                                        "context_count",
                                        0,
                                    ),

                                "Correlated Pairs":
                                    correlations.get(
                                        "correlated_pairs",
                                        0,
                                    ),

                                "Risk":
                                    agent_profile.get(
                                        "cross_context_risk",
                                        0,
                                    ),
                            }
                        )

                    if rows:

                        st.dataframe(
                            pd.DataFrame(rows),
                            width="stretch",
                            hide_index=True,
                        )

                st.divider()

                st.info(
                    """
                    Day 29 is a behavioral correlation signal.
                    Correlation does not prove malicious behavior.
                    A high score should support investigation or
                    reassessment rather than automatic attribution.
                    """
                )

                with st.expander(
                    "Complete Day 29 Profile"
                ):

                    st.json(profile)

            else:

                st.info(
                    "Run the Day 29 analysis to generate the profile."
                )

        else:

            st.info(
                "No behavioral events are available."
            )


# ============================================================
# RESEARCH INTERPRETATION
# ============================================================

elif dashboard_view == "📚 Research Interpretation":

    st.header(
        "📚 Research Interpretation"
    )

    st.subheader(
        "AegisGuard Research Question"
    )

    st.markdown(
        """
        **Can behavior-aware security intelligence provide measurable
        detection benefit beyond a simpler risk-only authorization
        baseline for autonomous AI agents?**
        """
    )

    st.divider()

    evidence_df = pd.DataFrame(
        [
            [
                "Authorization",
                "Allow / Deny decisions",
                "Security enforcement",
            ],
            [
                "Risk",
                "Contextual risk score",
                "Risk prioritization",
            ],
            [
                "Behavior",
                "Repeated behavior and denials",
                "Behavioral context",
            ],
            [
                "Controlled Scenarios",
                "Ground-truth attack/benign cases",
                "Reproducibility",
            ],
            [
                "Quantitative Evaluation",
                "Precision / Recall / F1",
                "Performance measurement",
            ],
            [
                "Baseline Comparison",
                "Baseline vs AegisGuard",
                "Comparative evidence",
            ],
            [
                "Repeated Evaluation",
                "Multiple random seeds",
                "Robustness",
            ],
            [
                "Statistical Evaluation",
                "Paired differences/statistics",
                "Research validation",
            ],
            [
                "Multi-Resolution",
                "Action/capability/resource/context",
                "Hierarchical behavior",
            ],
            [
                "Cross-Context",
                "Context relationships",
                "Distributed behavior",
            ],
        ],
        columns=[
            "Stage",
            "Evidence",
            "Purpose",
        ],
    )

    st.dataframe(
        evidence_df,
        width="stretch",
        hide_index=True,
    )

    st.divider()

    st.subheader(
        "Claims We Can Make Carefully"
    )

    for statement in [
        "The project contains controlled security scenarios.",
        "The experiments are designed to be reproducible.",
        "A baseline comparison framework exists.",
        "Repeated evaluation is implemented.",
        "Statistical evaluation is being added to the research workflow.",
        "Cross-context behavioral correlation is implemented as an experimental mechanism.",
    ]:

        st.markdown(
            f"✓ {statement}"
        )

    st.divider()

    st.subheader(
        "Claims We Should Not Make Without Evidence"
    )

    for statement in [
        "Universal superiority over existing systems.",
        "Complete protection against prompt injection.",
        "Zero false positives or false negatives.",
        "Production readiness based only on the dashboard.",
        "Patentability or guaranteed novelty.",
        "Real-world generalization from synthetic experiments alone.",
        "Statistical significance without running the statistical tests.",
    ]:

        st.markdown(
            f"⚠ {statement}"
        )


# ============================================================
# PROJECT CONSTRUCTION
# ============================================================

elif dashboard_view == "📅 Project Construction":

    st.header(
        "📅 AegisGuard Day 1–29 Construction"
    )

    milestones = [
        ("Days 1–12", "Security Foundation",
         "Identity, policy, authorization, risk, database and security controls."),
        ("Days 13–16", "Security Analytics",
         "Behavioral monitoring, security analytics and SOC dashboard."),
        ("Days 17–20", "Investigation + Intelligence",
         "Investigation, behavioral anomalies and integrated security intelligence."),
        ("Days 21–22", "Controlled Scenarios",
         "Controlled security scenarios and attack scenario framework."),
        ("Day 23", "Experimental Dataset",
         "Reproducible synthetic security dataset generation."),
        ("Days 24–25", "Detection Evaluation",
         "Quantitative detection and research evaluation."),
        ("Day 26", "Baseline Comparison",
         "AegisGuard compared against a simpler baseline."),
        ("Day 27", "Repeated Evaluation",
         "Multiple random seeds for robustness assessment."),
        ("Day 28", "Statistical Evaluation",
         "Statistical analysis of repeated experimental differences."),
        ("Day 28", "Multi-Resolution Behavior",
         "Behavior evaluated across multiple resolutions."),
        ("Day 29", "Cross-Context Correlation",
         "Relationships across execution contexts, capabilities and resources."),
    ]

    construction_df = pd.DataFrame(
        milestones,
        columns=[
            "Milestone",
            "Workstream",
            "Output",
        ],
    )

    st.dataframe(
        construction_df,
        width="stretch",
        hide_index=True,
    )

    st.divider()

    st.subheader(
        "Construction Discipline"
    )

    st.markdown(
        """
        Every milestone should follow:

        **Design → Implement → Test → Integrate → Experiment →
        Compare → Validate → Document**

        A feature is not considered research evidence merely because
        the Streamlit dashboard displays it.
        """
    )

    st.progress(
        29 / 70
    )

    st.caption(
        "Current roadmap position: Day 29 / 70"
    )


# ============================================================
# DEPLOYMENT & VALIDATION
# ============================================================

elif dashboard_view == "🚀 Deployment & Validation":

    st.header(
        "🚀 Deployment & Validation Center"
    )

    st.caption(
        "Verify the actual environment, modules, files and automated tests."
    )

    st.divider()

    # --------------------------------------------------------
    # Environment
    # --------------------------------------------------------

    st.subheader(
        "1. Python Environment"
    )

    executable = Path(
        sys.executable
    ).resolve()

    environment_ok = (
        EXPECTED_ENV in executable.parents
        or executable.parent.parent == EXPECTED_ENV
    )

    environment_df = pd.DataFrame(
        [
            {
                "Check":
                    "Python executable",

                "Value":
                    str(executable),

                "Status":
                    "READY"
                    if environment_ok
                    else "WARNING",
            },
            {
                "Check":
                    "Project directory",

                "Value":
                    str(PROJECT_ROOT),

                "Status":
                    "READY"
                    if PROJECT_ROOT.exists()
                    else "ERROR",
            },
            {
                "Check":
                    "App directory",

                "Value":
                    str(APP_DIR),

                "Status":
                    "READY"
                    if APP_DIR.exists()
                    else "ERROR",
            },
            {
                "Check":
                    "Tests directory",

                "Value":
                    str(TESTS_DIR),

                "Status":
                    "READY"
                    if TESTS_DIR.exists()
                    else "WARNING",
            },
        ]
    )

    st.dataframe(
        environment_df,
        width="stretch",
        hide_index=True,
    )

    if environment_ok:

        st.success(
            "D:\\aegisguard-env is active."
        )

    else:

        st.warning(
            "Dashboard is not running from D:\\aegisguard-env."
        )

    st.divider()

    # --------------------------------------------------------
    # Dependencies
    # --------------------------------------------------------

    st.subheader(
        "2. Dependency Health"
    )

    dependency_rows = []

    for package in [
        "streamlit",
        "pandas",
        "pytest",
        "scipy",
    ]:

        try:

            module = __import__(
                package
            )

            dependency_rows.append(
                {
                    "Package":
                        package,

                    "Version":
                        getattr(
                            module,
                            "__version__",
                            "installed",
                        ),

                    "Status":
                        "READY",
                }
            )

        except Exception as exc:

            dependency_rows.append(
                {
                    "Package":
                        package,

                    "Version":
                        str(exc),

                    "Status":
                        "ERROR",
                }
            )

    st.dataframe(
        pd.DataFrame(
            dependency_rows
        ),
        width="stretch",
        hide_index=True,
    )

    st.divider()

    # --------------------------------------------------------
    # Module health
    # --------------------------------------------------------

    st.subheader(
        "3. Application Module Health"
    )

    module_rows = []

    expected_modules = [
        "analytics",
        "behavior",
        "scenarios",
        "investigation",
        "dataset",
        "evaluation",
        "comparison",
        "repeated",
        "statistical",
        "multiresolution",
        "cross_context",
    ]

    for name in expected_modules:

        error = MODULES.get(
            f"{name}_error"
        )

        module_rows.append(
            {
                "Module":
                    name,

                "Status":
                    "READY"
                    if name in MODULES
                    else "UNAVAILABLE",

                "Details":
                    ""
                    if name in MODULES
                    else str(error or "Import failed"),
            }
        )

    st.dataframe(
        pd.DataFrame(module_rows),
        width="stretch",
        hide_index=True,
    )

    st.divider()

    # --------------------------------------------------------
    # Project files
    # --------------------------------------------------------

    st.subheader(
        "4. Required Project Files"
    )

    important_files = [
        "dashboard.py",
        "app/analytics.py",
        "app/behavior.py",
        "app/attack_scenarios.py",
        "app/experimental_dataset.py",
        "app/comparison.py",
        "app/repeated_evaluation.py",
        "app/statistical_evaluation.py",
        "app/multiresolution_behavior.py",
        "app/cross_context_correlation.py",
    ]

    file_rows = []

    for relative_path in important_files:

        path = PROJECT_ROOT / relative_path

        file_rows.append(
            {
                "File":
                    relative_path,

                "Exists":
                    path.exists(),

                "Size":
                    path.stat().st_size
                    if path.exists()
                    else 0,
            }
        )

    st.dataframe(
        pd.DataFrame(file_rows),
        width="stretch",
        hide_index=True,
    )

    st.divider()

    # --------------------------------------------------------
    # Full test suite
    # --------------------------------------------------------

    st.subheader(
        "5. Full Automated Test Suite"
    )

    if st.button(
        "▶️ Run Full pytest Suite",
        type="primary",
        key="deployment_tests",
    ):

        with st.spinner(
            "Running pytest..."
        ):

            try:

                completed = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pytest",
                        "-q",
                    ],
                    cwd=str(
                        PROJECT_ROOT
                    ),
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                output = (
                    completed.stdout
                    + "\n"
                    + completed.stderr
                )

                passed = (
                    completed.returncode == 0
                )

                st.session_state[
                    "test_result"
                ] = {
                    "passed":
                        passed,

                    "returncode":
                        completed.returncode,

                    "output":
                        output,

                    "timestamp":
                        datetime.now().isoformat(),
                }

            except Exception as exc:

                st.session_state[
                    "test_result"
                ] = {
                    "passed":
                        False,

                    "returncode":
                        -1,

                    "output":
                        str(exc),

                    "timestamp":
                        datetime.now().isoformat(),
                }

    test_result = st.session_state.get(
        "test_result"
    )

    if test_result:

        if test_result["passed"]:

            st.success(
                "FULL TEST SUITE PASSED"
            )

        else:

            st.error(
                "FULL TEST SUITE FAILED"
            )

        st.code(
            test_result["output"],
            language="text",
        )

    else:

        st.info(
            "Run the full test suite to verify the current project."
        )

    st.divider()

    # --------------------------------------------------------
    # Deployment verdict
    # --------------------------------------------------------

    tests_passed = bool(
        test_result
        and test_result.get(
            "passed",
            False,
        )
    )

    required_files_ready = all(
        (
            PROJECT_ROOT / path
        ).exists()
        for path in important_files
    )

    deployment_ready = (
        environment_ok
        and tests_passed
        and required_files_ready
    )

    if deployment_ready:

        st.success(
            "READY FOR TEST DEPLOYMENT"
        )

    else:

        st.warning(
            "Deployment readiness has not been established."
        )


# ============================================================
# SYSTEM STATUS
# ============================================================

elif dashboard_view == "⚙️ System Status":

    st.header(
        "⚙️ System Status"
    )

    status_rows = []

    for name in [
        "analytics",
        "behavior",
        "scenarios",
        "investigation",
        "dataset",
        "evaluation",
        "comparison",
        "repeated",
        "statistical",
        "multiresolution",
        "cross_context",
    ]:

        status_rows.append(
            {
                "Module":
                    name,

                "Status":
                    "READY"
                    if name in MODULES
                    else "UNAVAILABLE",

                "Error":
                    MODULES.get(
                        f"{name}_error",
                        "",
                    ),
            }
        )

    st.dataframe(
        pd.DataFrame(status_rows),
        width="stretch",
        hide_index=True,
    )

    st.divider()

    st.subheader(
        "Runtime"
    )

    runtime_df = pd.DataFrame(
        [
            {
                "Property":
                    "Python",

                "Value":
                    sys.version.split()[0],
            },
            {
                "Property":
                    "Executable",

                "Value":
                    sys.executable,
            },
            {
                "Property":
                    "Project",

                "Value":
                    str(PROJECT_ROOT),
            },
            {
                "Property":
                    "App",

                "Value":
                    str(APP_DIR),
            },
            {
                "Property":
                    "Tests",

                "Value":
                    str(TESTS_DIR),
            },
        ]
    )

    st.dataframe(
        runtime_df,
        width="stretch",
        hide_index=True,
    )

    st.divider()

    st.subheader(
        "Session State"
    )

    session_rows = []

    for key in DEFAULT_STATE:

        value = st.session_state.get(
            key
        )

        session_rows.append(
            {
                "State":
                    key,

                "Status":
                    "AVAILABLE"
                    if value
                    else "EMPTY",
            }
        )

    st.dataframe(
        pd.DataFrame(session_rows),
        width="stretch",
        hide_index=True,
    )

    st.divider()

    if st.button(
        "🧹 Clear Research Session",
        key="clear_session",
    ):

        for key in DEFAULT_STATE:

            if key in st.session_state:

                del st.session_state[key]

        st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div class="footer">
        🛡️ <strong>AegisGuard</strong>
        • Behavior-Aware Security for Autonomous AI Agents
        <br>
        Day 1–29 Unified Research Dashboard
        • Controlled Evaluation
        • Reproducible Experiments
        • Statistical Validation
        • Cross-Context Behavioral Intelligence
    </div>
    """,
    unsafe_allow_html=True,
)