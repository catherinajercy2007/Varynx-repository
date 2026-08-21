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
# UNIFIED DAY 1–30 SECURITY + RESEARCH DASHBOARD
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
APP_DIR = PROJECT_ROOT / "app"
TESTS_DIR = PROJECT_ROOT / "tests"
EXPECTED_ENV = Path(r"D:\aegisguard-env").resolve()


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
# SAFE HELPERS
# ============================================================

def safe_call(
    function: Callable | None,
    default: Any = None,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Safely execute an optional project function."""
    if function is None:
        return default

    try:
        return function(*args, **kwargs)
    except Exception:
        return default


def as_dict(value: Any) -> dict[str, Any]:
    """Convert common project objects into dictionaries."""
    if isinstance(value, dict):
        return dict(value)

    if hasattr(value, "model_dump"):
        try:
            return dict(value.model_dump())
        except Exception:
            pass

    if hasattr(value, "dict"):
        try:
            return dict(value.dict())
        except Exception:
            pass

    if hasattr(value, "__dict__"):
        try:
            return dict(value.__dict__)
        except Exception:
            pass

    return {}


def dataframe_or_empty(value: Any) -> pd.DataFrame:
    """Safely convert arbitrary rows into a DataFrame."""
    if value is None:
        return pd.DataFrame()

    if isinstance(value, pd.DataFrame):
        return value.copy()

    try:
        return pd.DataFrame(value)
    except Exception:
        return pd.DataFrame()


def safe_number(
    value: Any,
    default: float = 0.0,
) -> float:
    """Safely convert a value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def format_percent(value: Any) -> str:
    """Format a 0–1 metric as a percentage."""
    return f"{safe_number(value) * 100:.2f}%"


def download_dataframe(
    dataframe: pd.DataFrame,
    filename: str,
    key: str | None = None,
) -> None:
    """Create a CSV download button when data exists."""
    if dataframe.empty:
        return

    csv_data = dataframe.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="⬇️ Download CSV",
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        key=key or f"download_{filename}",
    )


def extract_scalar_rows(
    data: Any,
) -> list[dict[str, Any]]:
    """Extract scalar dictionary values for dashboard tables."""
    if not isinstance(data, dict):
        return []

    rows = []

    for key, value in data.items():

        if isinstance(
            value,
            (str, int, float, bool),
        ):
            rows.append(
                {
                    "Metric": key,
                    "Value": value,
                }
            )

    return rows


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
    # Behavioral analytics
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
    # Attack scenarios
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
    # Evaluation
    # --------------------------------------------------------

    try:

        import app.evaluation as evaluation

        modules["evaluation"] = evaluation

    except Exception as exc:

        modules["evaluation_error"] = str(exc)

    # --------------------------------------------------------
    # Baseline comparison
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
    # Statistical evaluation
    # --------------------------------------------------------

    try:

        import app.statistical_evaluation as statistical

        modules["statistical"] = statistical

    except Exception as exc:

        modules["statistical_error"] = str(exc)

    # --------------------------------------------------------
    # Multi-resolution behavior
    # --------------------------------------------------------

    try:

        import app.multiresolution_behavior as multiresolution

        modules["multiresolution"] = multiresolution

    except Exception as exc:

        modules["multiresolution_error"] = str(exc)

    # --------------------------------------------------------
    # Cross-context correlation
    # --------------------------------------------------------

    try:

        import app.cross_context_correlation as cross_context

        modules["cross_context"] = cross_context

    except Exception as exc:

        modules["cross_context_error"] = str(exc)

    # --------------------------------------------------------
    # Day 30 — Adaptive Runtime Response
    # --------------------------------------------------------

    try:

        import app.adaptive_response as adaptive_response

        modules["adaptive_response"] = adaptive_response

    except Exception as exc:

        modules["adaptive_response_error"] = str(exc)

    return modules


MODULES = load_modules()


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "selected_agent":
        None,

    "selected_event":
        None,

    "experimental_dataset":
        None,

    "day26_results":
        None,

    "day26_dataset":
        None,

    "day27_results":
        None,

    "day27_config":
        None,

    "day28_profile":
        None,

    "day28_events":
        None,

    "day29_profile":
        None,

    "day29_summary":
        None,

    "day29_events":
        None,

    "day30_result":
        None,

    "day30_evidence":
        None,

    "test_result":
        None,
}


for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# VISUAL STYLE
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

    .research-card {
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
# CURRENT SECURITY DATA
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
    authorization, risk assessment, behavioral monitoring,
    multi-resolution analysis, cross-context intelligence,
    adaptive runtime response and reproducible research evaluation.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

st.sidebar.title(
    "🛡️ AegisGuard"
)

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

    "🛡️ Day 30 Adaptive Runtime Response",

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
    "Detect → Evaluate → Correlate → Adapt"
)

st.sidebar.divider()

st.sidebar.caption(
    "Current milestone: Day 30"
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
        "AegisGuard Research Stack"
    )

    stack = pd.DataFrame(
        [
            [
                "Authorization",
                "Policy enforcement",
                "Days 1–12",
            ],
            [
                "Risk",
                "Contextual risk scoring",
                "Days 1–20",
            ],
            [
                "Behavior",
                "Repeated behavioral evidence",
                "Days 13–20",
            ],
            [
                "Scenarios",
                "Controlled ground-truth cases",
                "Days 21–22",
            ],
            [
                "Dataset",
                "Reproducible experiments",
                "Day 23",
            ],
            [
                "Evaluation",
                "Quantitative detection metrics",
                "Days 24–25",
            ],
            [
                "Baseline",
                "Comparative evaluation",
                "Day 26",
            ],
            [
                "Repeated",
                "Multi-seed robustness",
                "Day 27",
            ],
            [
                "Statistics",
                "Statistical evaluation",
                "Day 28",
            ],
            [
                "Multi-resolution",
                "Hierarchical behavior",
                "Day 28",
            ],
            [
                "Cross-context",
                "Distributed behavior",
                "Day 29",
            ],
            [
                "Adaptive Response",
                "Graduated runtime response",
                "Day 30",
            ],
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
            "download_high_risk",
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
            "download_agent_activity",
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
            "download_behavior_profiles",
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
            range(
                len(high_df)
            ),
            format_func=lambda index:
                f"Event {index + 1}",
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
        and "agent_id"
        in agent_df.columns
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
        and "agent_id"
        in suspicious_df.columns
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
            ) == str(
                selected_agent
            ):

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
            "download_scenarios",
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
                        "Metric":
                            key,

                        "Value":
                            value,
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
        .get(
            "generate_experimental_dataset"
        )
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
                "download_dataset",
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
            "for authoritative quantitative results."
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
        .get(
            "generate_experimental_dataset"
        )
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
                    events_per_scenario=int(
                        events
                    ),
                    seed=int(
                        seed
                    ),
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

                st.exception(
                    exc
                )

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

            if not chart_df.empty:

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

                st.exception(
                    exc
                )

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
                build_seed_summary(
                    results
                )
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
                    "download_day27",
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
                        .set_index(
                            "seed"
                        )
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
                build_summary_table(
                    results
                )
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
            "Repeated experimental results are available."
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
            for name in dir(
                statistical
            )
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

        paired_function = getattr(
            statistical,
            "calculate_paired_differences",
            None,
        )

        if paired_function is not None:

            try:

                differences = (
                    paired_function(
                        results
                    )
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
                                    len(
                                        differences
                                    ) + 1,
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
                    "Paired-difference calculation "
                    f"unavailable: {exc}"
                )

        st.info(
            """
            Statistical outputs should be interpreted using the
            implemented statistical evaluation functions. The dashboard
            does not manufacture significance claims.
            """
        )


# ============================================================
# DAY 28 — MULTI-RESOLUTION BEHAVIOR
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

            Day 28 evaluates behavior at multiple resolutions rather
            than relying exclusively on isolated authorization decisions.
            """
        )

        if not events:

            st.info(
                "Generate an experimental dataset first."
            )

        else:

            if st.button(
                "▶️ Analyze Multi-Resolution Behavior",
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
                        "No compatible multi-resolution "
                        "analysis function was found."
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

                    scalar_rows = (
                        extract_scalar_rows(
                            profile
                        )
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
                        "Complete Multi-Resolution Profile"
                    ):

                        st.json(
                            profile
                        )


# ============================================================
# DAY 29 — CROSS-CONTEXT INTELLIGENCE
# ============================================================

elif dashboard_view == "🔗 Day 29 Cross-Context Intelligence":

    st.header(
        "🔗 Day 29 — Cross-Context Behavioral Intelligence"
    )

    st.caption(
        "Identify distributed behavioral relationships across "
        "contexts, capabilities and resources."
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

        input_mode = st.radio(
            "Input Source",
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

                    if profile_function is None:

                        raise RuntimeError(
                            "build_cross_context_profile is missing."
                        )

                    profile = (
                        profile_function(
                            events
                        )
                    )

                    summary_function = getattr(
                        cross_context,
                        "build_research_summary",
                        None,
                    )

                    summary = (
                        summary_function(
                            events
                        )
                        if callable(
                            summary_function
                        )
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

                    st.exception(
                        exc
                    )

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

                    score = safe_call(
                        risk_function,
                        0.0,
                        events,
                    )

                    summary = {
                        "event_count":
                            len(events),

                        "cross_context_risk":
                            score,
                    }

                c1, c2, c3 = st.columns(3)

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
                        "Cross-Context Risk",
                        f"{safe_number(summary.get('cross_context_risk', 0)):.2f}",
                    )

                with c3:

                    st.metric(
                        "Contexts",
                        len(
                            {
                                str(
                                    event.get(
                                        "context",
                                        "",
                                    )
                                )
                                for event in events
                                if event.get(
                                    "context"
                                )
                            }
                        ),
                    )

                st.divider()

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

                with st.expander(
                    "Complete Day 29 Profile"
                ):

                    st.json(
                        profile

                    )


# ============================================================
# DAY 30 — ADAPTIVE RUNTIME RESPONSE
# ============================================================

elif dashboard_view == "🛡️ Day 30 Adaptive Runtime Response":

    st.header(
        "🛡️ Day 30 — Adaptive Runtime Response"
    )

    st.caption(
        "Convert accumulated security evidence into a graduated "
        "runtime response instead of relying exclusively on binary "
        "allow/deny enforcement."
    )

    adaptive = MODULES.get(
        "adaptive_response"
    )

    if adaptive is None:

        st.error(
            "Day 30 adaptive response module is unavailable."
        )

        error = MODULES.get(
            "adaptive_response_error"
        )

        if error:
            st.code(
                error
            )

        st.markdown(
            """
            Expected module:

            ```text
            app/adaptive_response.py
            ```
            """

        )

    else:

        st.markdown(
            """
            ### Adaptive security model

            Day 30 introduces a graduated response layer:

            **ALLOW → ALLOW WITH MONITORING → STEP-UP VERIFICATION
            → REDUCE SCOPE → DENY / ESCALATE**

            The purpose is to avoid treating every suspicious signal
            as an immediate binary denial.

            The response should depend on accumulated evidence such as:

            - risk score
            - behavioral anomaly score
            - repeated denials
            - cross-context evidence
            - contextual security signals

            This is an experimental runtime-response mechanism and
            requires controlled evaluation before production use.
            """
        )

        st.divider()

        st.subheader(
            "Security Evidence"
        )

        evidence_source = st.radio(
            "Evidence Source",
            [
                "Manual Evidence",
                "Selected High-Risk Event",
                "Current Risk Summary",
                "Day 29 Cross-Context Result",
            ],
            horizontal=True,
            key="day30_evidence_source",
        )

        evidence: dict[str, Any] = {}

        if evidence_source == "Manual Evidence":

            c1, c2, c3 = st.columns(3)

            with c1:

                risk_score = st.slider(
                    "Risk Score",
                    min_value=0,
                    max_value=100,
                    value=45,
                    step=1,
                    key="day30_risk_score",
                )

            with c2:

                anomaly_score = st.slider(
                    "Anomaly Score",
                    min_value=0,
                    max_value=100,
                    value=20,
                    step=1,
                    key="day30_anomaly_score",
                )

            with c3:

                denial_count = st.number_input(
                    "Repeated Denials",
                    min_value=0,
                    max_value=1000,
                    value=0,
                    step=1,
                    key="day30_denial_count",
                )

            evidence = {
                "risk_score":
                    risk_score,

                "anomaly_score":
                    anomaly_score,

                "repeated_denials":
                    denial_count,
            }

        elif evidence_source == "Selected High-Risk Event":

            selected_event = st.session_state.get(
                "selected_event"
            )

            if not selected_event:

                high_df = dataframe_or_empty(
                    high_risk_events
                )

                if high_df.empty:

                    st.info(
                        "No high-risk event is available."
                    )

                else:

                    event_index = st.selectbox(
                        "Select High-Risk Event",
                        range(
                            len(high_df)
                        ),
                        format_func=lambda index:
                            f"Event {index + 1}",
                        key="day30_high_risk_event",
                    )

                    selected_event = (
                        high_df.iloc[
                            event_index
                        ].to_dict()
                    )

            if selected_event:

                evidence = as_dict(
                    selected_event
                )

                st.json(
                    evidence
                )

        elif evidence_source == "Current Risk Summary":

            evidence = {
                "risk_score":
                    risk_summary.get(
                        "average_risk",
                        0,
                    ),

                "anomaly_score":
                    0,

                "repeated_denials":
                    len(
                        repeated_denials
                    ),

                "high_risk_events":
                    risk_summary.get(
                        "high_risk_events",
                        0,
                    ),

                "critical_events":
                    risk_summary.get(
                        "critical_events",
                        0,
                    ),
            }

            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Evidence":
                                key,

                            "Value":
                                value,
                        }

                        for key, value
                        in evidence.items()
                    ]
                ),
                width="stretch",
                hide_index=True,
            )

        else:

            day29_summary = (
                st.session_state.get(
                    "day29_summary"
                )
                or {}
            )

            day29_profile = (
                st.session_state.get(
                    "day29_profile"
                )
                or {}
            )

            cross_context_risk = safe_number(
                day29_summary.get(
                    "cross_context_risk",
                    day29_profile.get(
                        "cross_context_risk",
                        0,
                    )
                    if isinstance(
                        day29_profile,
                        dict,
                    )
                    else 0,
                )
            )

            evidence = {
                "risk_score":
                    risk_summary.get(
                        "average_risk",
                        0,
                    ),

                "anomaly_score":
                    cross_context_risk,

                "repeated_denials":
                    len(
                        repeated_denials
                    ),

                "cross_context_risk":
                    cross_context_risk,
            }

            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Evidence":
                                key,

                            "Value":
                                value,
                        }

                        for key, value
                        in evidence.items()
                    ]
                ),
                width="stretch",
                hide_index=True,
            )

        st.divider()

        if evidence:

            st.session_state[
                "day30_evidence"
            ] = evidence

            st.subheader(
                "Adaptive Response Engine"
            )

            response_function = getattr(
                adaptive,
                "calculate_adaptive_response",
                None,
            )

            if not callable(
                response_function
            ):

                st.error(
                    "calculate_adaptive_response() "
                    "was not found in app.adaptive_response."
                )

                available_functions = [
                    name
                    for name in dir(
                        adaptive
                    )
                    if not name.startswith("_")
                    and callable(
                        getattr(
                            adaptive,
                            name,
                        )
                    )
                ]

                if available_functions:

                    st.subheader(
                        "Available Functions"
                    )

                    st.dataframe(
                        pd.DataFrame(
                            {
                                "Function":
                                    available_functions
                            }
                        ),
                        width="stretch",
                        hide_index=True,
                    )

            else:

                if st.button(
                    "▶️ Calculate Adaptive Response",
                    type="primary",
                    key="day30_calculate",
                ):

                    try:

                        result = (
                            response_function(
                                evidence
                            )
                        )

                        if not isinstance(
                            result,
                            dict,
                        ):

                            result = {
                                "action":
                                    str(
                                        result
                                    )
                            }

                        st.session_state[
                            "day30_result"
                        ] = result

                        st.success(
                            "Adaptive response calculated."
                        )

                    except Exception as exc:

                        st.session_state[
                            "day30_result"
                        ] = None

                        st.error(
                            "Adaptive response calculation failed."
                        )

                        st.exception(
                            exc
                        )

                result = st.session_state.get(
                    "day30_result"
                )

                if result:

                    st.divider()

                    action = str(
                        result.get(
                            "action",
                            "UNKNOWN",
                        )
                    )

                    reason = result.get(
                        "reason",
                        result.get(
                            "rationale",
                            "",
                        ),
                    )

                    response_score = result.get(
                        "score",
                        result.get(
                            "risk_score",
                            result.get(
                                "adaptive_score",
                                None,
                            ),
                        ),
                    )

                    st.subheader(
                        "Runtime Decision"
                    )

                    c1, c2, c3 = st.columns(3)

                    with c1:

                        st.metric(
                            "Response",
                            action,
                        )

                    with c2:

                        if response_score is None:

                            st.metric(
                                "Adaptive Score",
                                "N/A",
                            )

                        else:

                            st.metric(
                                "Adaptive Score",
                                f"{safe_number(response_score):.2f}",
                            )

                    with c3:

                        st.metric(
                            "Evidence Fields",
                            len(
                                evidence
                            ),
                        )

                    if action in {
                        "ALLOW",
                        "ALLOW_WITH_MONITORING",
                    }:

                        st.success(
                            f"Recommended response: {action}"
                        )

                    elif action in {
                        "STEP_UP_VERIFICATION",
                        "REDUCE_SCOPE",
                    }:

                        st.warning(
                            f"Recommended response: {action}"
                        )

                    elif action in {
                        "DENY",
                        "ESCALATE",
                    }:

                        st.error(
                            f"Recommended response: {action}"
                        )

                    else:

                        st.info(
                            f"Response: {action}"
                        )

                    if reason:

                        st.subheader(
                            "Decision Rationale"
                        )

                        st.write(
                            reason
                        )

                    st.divider()

                    st.subheader(
                        "Evidence Used"
                    )

                    evidence_df = pd.DataFrame(
                        [
                            {
                                "Evidence":
                                    key,

                                "Value":
                                    value,
                            }

                            for key, value
                            in evidence.items()
                        ]
                    )

                    st.dataframe(
                        evidence_df,
                        width="stretch",
                        hide_index=True,
                    )

                    st.divider()

                    st.subheader(
                        "Adaptive Response Lifecycle"
                    )

                    lifecycle_df = pd.DataFrame(
                        [
                            {
                                "Stage":
                                    1,

                                "Security Evidence":
                                    "Risk + behavior + context",

                                "Purpose":
                                    "Collect runtime evidence",
                            },
                            {
                                "Stage":
                                    2,

                                "Security Evidence":
                                    "Evidence aggregation",

                                "Purpose":
                                    "Assess current behavioral state",
                            },
                            {
                                "Stage":
                                    3,

                                "Security Evidence":
                                    "Adaptive response",

                                "Purpose":
                                    "Select graduated response",
                            },
                            {
                                "Stage":
                                    4,

                                "Security Evidence":
                                    "Runtime enforcement",

                                "Purpose":
                                    "Apply the selected action",
                            },
                            {
                                "Stage":
                                    5,

                                "Security Evidence":
                                    "Reassessment",

                                "Purpose":
                                    "Continue monitoring after intervention",
                            },
                        ]
                    )

                    st.dataframe(
                        lifecycle_df,
                        width="stretch",
                        hide_index=True,
                    )

                    with st.expander(
                        "Complete Adaptive Response Object"
                    ):

                        st.json(
                            result
                        )

                    st.warning(
                        """
                        Day 30 is intentionally designed as an adaptive
                        decision layer, not as proof that any particular
                        response threshold is optimal. Thresholds and
                        response policies must be validated through
                        controlled experiments, false-positive analysis,
                        false-negative analysis and deployment testing.
                        """
                    )

        else:

            st.info(
                "Provide security evidence to calculate a runtime response."
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
        detection and response benefits beyond a simpler risk-only
        authorization baseline for autonomous AI agents?**
        """
    )

    st.divider()

    evidence_df = pd.DataFrame(
        [
            [
                "Authorization",
                "Allow / Deny",
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
                "Ground-truth cases",
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
                "Multiple seeds",
                "Robustness",
            ],
            [
                "Statistical Evaluation",
                "Paired differences",
                "Research validation",
            ],
            [
                "Multi-Resolution",
                "Action / capability / resource / context",
                "Hierarchical behavior",
            ],
            [
                "Cross-Context",
                "Context relationships",
                "Distributed behavior",
            ],
            [
                "Adaptive Response",
                "Graduated runtime action",
                "Runtime mitigation",
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

    claims = [
        "Controlled security scenarios exist.",
        "The experiments are designed to be reproducible.",
        "A baseline comparison framework exists.",
        "Repeated evaluation is implemented.",
        "Statistical evaluation is implemented.",
        "Multi-resolution behavioral analysis is implemented.",
        "Cross-context behavioral correlation is implemented.",
        "An adaptive runtime response layer is implemented.",
    ]

    for claim in claims:

        st.markdown(
            f"✓ {claim}"
        )

    st.divider()

    st.subheader(
        "Claims Requiring Further Evidence"
    )

    limitations = [
        "Universal superiority over existing agent-security systems.",
        "Complete protection against prompt injection.",
        "Zero false positives or false negatives.",
        "Optimal adaptive-response thresholds.",
        "Production readiness.",
        "Patentability or guaranteed novelty.",
        "Real-world generalization from synthetic experiments alone.",
        "Statistical significance without executing the statistical tests.",
    ]

    for limitation in limitations:

        st.markdown(
            f"⚠ {limitation}"
        )


# ============================================================
# PROJECT CONSTRUCTION
# ============================================================

elif dashboard_view == "📅 Project Construction":

    st.header(
        "📅 AegisGuard Day 1–30 Construction"
    )

    milestones = [
        (
            "Days 1–12",
            "Security Foundation",
            "Identity, policy, authorization, risk and core security controls.",
        ),
        (
            "Days 13–16",
            "Security Analytics",
            "Behavioral monitoring, security analytics and SOC dashboard.",
        ),
        (
            "Days 17–20",
            "Investigation + Intelligence",
            "Investigation, anomaly monitoring and integrated intelligence.",
        ),
        (
            "Days 21–22",
            "Controlled Scenarios",
            "Controlled attack and benign security scenarios.",
        ),
        (
            "Day 23",
            "Experimental Dataset",
            "Reproducible experimental dataset generation.",
        ),
        (
            "Days 24–25",
            "Detection Evaluation",
            "Quantitative detection and research evaluation.",
        ),
        (
            "Day 26",
            "Baseline Comparison",
            "AegisGuard compared with a simpler baseline.",
        ),
        (
            "Day 27",
            "Repeated Evaluation",
            "Multi-seed robustness evaluation.",
        ),
        (
            "Day 28",
            "Statistical Evaluation",
            "Statistical analysis of repeated experimental differences.",
        ),
        (
            "Day 28",
            "Multi-Resolution Behavior",
            "Hierarchical behavioral analysis.",
        ),
        (
            "Day 29",
            "Cross-Context Correlation",
            "Distributed behavioral relationship analysis.",
        ),
        (
            "Day 30",
            "Adaptive Runtime Response",
            "Graduated runtime response based on accumulated evidence.",
        ),
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
        Every milestone follows:

        **Design → Implement → Unit Test → Integrate →
        Experiment → Compare → Validate → Document**

        A dashboard feature is not research evidence merely because
        it is displayed successfully.
        """
    )

    st.progress(
        30 / 70
    )

    st.caption(
        "Current roadmap position: Day 30 / 70"
    )


# ============================================================
# DEPLOYMENT & VALIDATION
# ============================================================

elif dashboard_view == "🚀 Deployment & Validation":

    st.header(
        "🚀 Deployment & Validation Center"
    )

    st.caption(
        "Verify environment, dependencies, modules, required files "
        "and the complete automated test suite."
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
        or executable.parent.parent
        == EXPECTED_ENV
    )

    environment_df = pd.DataFrame(
        [
            {
                "Check":
                    "Python executable",

                "Value":
                    str(
                        executable
                    ),

                "Status":
                    "READY"
                    if environment_ok
                    else "WARNING",
            },
            {
                "Check":
                    "Project directory",

                "Value":
                    str(
                        PROJECT_ROOT
                    ),

                "Status":
                    "READY"
                    if PROJECT_ROOT.exists()
                    else "ERROR",
            },
            {
                "Check":
                    "App directory",

                "Value":
                    str(
                        APP_DIR
                    ),

                "Status":
                    "READY"
                    if APP_DIR.exists()
                    else "ERROR",
            },
            {
                "Check":
                    "Tests directory",

                "Value":
                    str(
                        TESTS_DIR
                    ),

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
        "adaptive_response",
    ]

    module_rows = []

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
                    else str(
                        error
                        or "Import failed"
                    ),
            }
        )

    st.dataframe(
        pd.DataFrame(
            module_rows
        ),
        width="stretch",
        hide_index=True,
    )

    st.divider()

    # --------------------------------------------------------
    # Required project files
    # --------------------------------------------------------

    st.subheader(
        "4. Required Project Files"
    )

    important_files = [
        "dashboard.py",

        "app/analytics.py",
        "app/behavior.py",
        "app/attack_scenarios.py",
        "app/investigation.py",
        "app/experimental_dataset.py",
        "app/evaluation.py",
        "app/comparison.py",
        "app/repeated_evaluation.py",
        "app/statistical_evaluation.py",
        "app/multiresolution_behavior.py",
        "app/cross_context_correlation.py",
        "app/adaptive_response.py",
    ]

    file_rows = []

    for relative_path in important_files:

        path = (
            PROJECT_ROOT
            / relative_path
        )

        file_rows.append(
            {
                "File":
                    relative_path,

                "Exists":
                    path.exists(),

                "Size":
                    (
                        path.stat().st_size
                        if path.exists()
                        else 0
                    ),
            }
        )

    st.dataframe(
        pd.DataFrame(
            file_rows
        ),
        width="stretch",
        hide_index=True,
    )

    st.divider()

    # --------------------------------------------------------
    # Full pytest suite
    # --------------------------------------------------------

    st.subheader(
        "5. Full Automated Test Suite"
    )

    st.caption(
        "pytest is executed with the same Python interpreter "
        "running the dashboard."
    )

    if st.button(
        "▶️ Run Full pytest Suite",
        type="primary",
        key="deployment_tests",
    ):

        with st.spinner(
            "Running complete pytest suite..."
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

                st.session_state[
                    "test_result"
                ] = {
                    "passed":
                        completed.returncode == 0,

                    "returncode":
                        completed.returncode,

                    "output":
                        output,

                    "timestamp":
                        datetime.now().isoformat(),
                }

            except subprocess.TimeoutExpired:

                st.session_state[
                    "test_result"
                ] = {
                    "passed":
                        False,

                    "returncode":
                        -1,

                    "output":
                        "pytest timed out after 300 seconds.",

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

        if test_result.get(
            "passed",
            False,
        ):

            st.success(
                "FULL TEST SUITE PASSED"
            )

        else:

            st.error(
                "FULL TEST SUITE FAILED"
            )

        st.caption(
            "Validation time: "
            + str(
                test_result.get(
                    "timestamp",
                    "",
                )
            )
        )

        st.code(
            test_result.get(
                "output",
                "",
            ),
            language="text",
        )

    else:

        st.info(
            "Run the full test suite to obtain actual validation status."
        )

    st.divider()

    # --------------------------------------------------------
    # Deployment verdict
    # --------------------------------------------------------

    st.subheader(
        "6. Deployment Readiness"
    )

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

    modules_ready = all(
        name in MODULES
        for name in expected_modules
    )

    deployment_ready = (
        environment_ok
        and tests_passed
        and required_files_ready
        and modules_ready
    )

    readiness_df = pd.DataFrame(
        [
            {
                "Requirement":
                    "D: Python environment",

                "Status":
                    "READY"
                    if environment_ok
                    else "NOT READY",
            },
            {
                "Requirement":
                    "Application modules",

                "Status":
                    "READY"
                    if modules_ready
                    else "NOT READY",
            },
            {
                "Requirement":
                    "Required files",

                "Status":
                    "READY"
                    if required_files_ready
                    else "NOT READY",
            },
            {
                "Requirement":
                    "Automated tests",

                "Status":
                    "PASSED"
                    if tests_passed
                    else "NOT VERIFIED",
            },
        ]
    )

    st.dataframe(
        readiness_df,
        width="stretch",
        hide_index=True,
    )

    if deployment_ready:

        st.success(
            "READY FOR TEST DEPLOYMENT"
        )

    else:

        st.warning(
            "Deployment readiness has NOT been established."
        )


# ============================================================
# SYSTEM STATUS
# ============================================================

elif dashboard_view == "⚙️ System Status":

    st.header(
        "⚙️ System Status"
    )

    status_rows = []

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
        "adaptive_response",
    ]

    for name in expected_modules:

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
        pd.DataFrame(
            status_rows
        ),
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
                    str(
                        PROJECT_ROOT
                    ),
            },
            {
                "Property":
                    "App",

                "Value":
                    str(
                        APP_DIR
                    ),
            },
            {
                "Property":
                    "Tests",

                "Value":
                    str(
                        TESTS_DIR
                    ),
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
        pd.DataFrame(
            session_rows
        ),
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

                del st.session_state[
                    key
                ]

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
        Day 1–30 Unified Research Dashboard
        • Controlled Evaluation
        • Reproducible Experiments
        • Statistical Validation
        • Cross-Context Intelligence
        • Adaptive Runtime Response
    </div>
    """,
    unsafe_allow_html=True,
)