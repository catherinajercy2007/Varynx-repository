import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import streamlit as st


# ============================================================
# AEGISGUARD
# BEHAVIOR-AWARE SECURITY INTELLIGENCE SOC
#
# Dashboard responsibilities:
#   - Visualization
#   - Navigation
#   - Experiment orchestration
#   - Deployment validation
#   - Research progress tracking
#
# Security/research calculations remain in app/ modules.
# ============================================================


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
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
APP_DIR = PROJECT_ROOT / "app"
TESTS_DIR = PROJECT_ROOT / "tests"


# ============================================================
# CUSTOM STYLE
# ============================================================

st.markdown(
    """
    <style>

    /* --------------------------------------------------------
       Global
    -------------------------------------------------------- */

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    /* --------------------------------------------------------
       Header
    -------------------------------------------------------- */

    .ag-title {
        font-size: 2.55rem;
        font-weight: 800;
        letter-spacing: -0.035em;
        line-height: 1.05;
        margin-bottom: 0.25rem;
    }

    .ag-subtitle {
        color: #667085;
        font-size: 1rem;
        line-height: 1.5;
        margin-bottom: 1.5rem;
    }

    .ag-eyebrow {
        color: #667085;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }

    /* --------------------------------------------------------
       Cards
    -------------------------------------------------------- */

    .ag-card {
        border: 1px solid rgba(128, 128, 128, 0.20);
        border-radius: 16px;
        padding: 18px 20px;
        margin: 4px 0 14px 0;
        background: rgba(255, 255, 255, 0.025);
    }

    .ag-card-title {
        font-size: 1rem;
        font-weight: 750;
        margin-bottom: 0.35rem;
    }

    .ag-card-text {
        color: #667085;
        font-size: 0.88rem;
        line-height: 1.5;
    }

    /* --------------------------------------------------------
       Research milestone
    -------------------------------------------------------- */

    .ag-milestone {
        border-left: 4px solid #667085;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        background: rgba(128, 128, 128, 0.05);
    }

    .ag-milestone-day {
        font-size: 0.74rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #667085;
    }

    .ag-milestone-title {
        font-size: 1rem;
        font-weight: 750;
        margin-top: 2px;
    }

    /* --------------------------------------------------------
       Status
    -------------------------------------------------------- */

    .ag-status-ready {
        font-weight: 750;
    }

    .ag-status-warning {
        font-weight: 750;
    }

    /* --------------------------------------------------------
       Footer
    -------------------------------------------------------- */

    .ag-footer {
        color: #667085;
        font-size: 0.78rem;
        text-align: center;
        padding-top: 1rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# OPTIONAL APPLICATION IMPORTS
# ============================================================

def load_application_modules() -> Dict[str, Any]:
    """
    Import project modules individually.

    Every module is optional from the dashboard's perspective.
    A failed import is recorded instead of crashing the complete
    dashboard.
    """

    modules: Dict[str, Any] = {}

    # --------------------------------------------------------
    # Analytics
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
            "get_suspicious_agents": get_suspicious_agents,
            "get_repeated_denials": get_repeated_denials,
        }

    except Exception as exc:
        modules["behavior_error"] = str(exc)

    # --------------------------------------------------------
    # Controlled scenarios
    # --------------------------------------------------------

    try:
        from app.attack_scenarios import (
            get_attack_scenarios,
        )

        modules["scenarios"] = {
            "get_attack_scenarios": get_attack_scenarios,
        }

    except Exception as exc:
        modules["scenarios_error"] = str(exc)

    # --------------------------------------------------------
    # Repeated evaluation — Day 27
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
    # Comparison — Day 26
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
    # Statistical evaluation
    # --------------------------------------------------------

    try:
        import app.statistical_evaluation as statistical_evaluation

        modules["statistical"] = statistical_evaluation

    except Exception as exc:
        modules["statistical_error"] = str(exc)

    # --------------------------------------------------------
    # General evaluation
    # --------------------------------------------------------

    try:
        import app.evaluation as evaluation

        modules["evaluation"] = evaluation

    except Exception as exc:
        modules["evaluation_error"] = str(exc)

    # --------------------------------------------------------
    # Day 28 — Multi-resolution behavior
    # --------------------------------------------------------

    try:
        from app.multiresolution_behavior import (
            calculate_action_level_features,
            calculate_capability_features,
            calculate_resource_features,
            calculate_context_features,
            calculate_cross_context_features,
            calculate_multi_resolution_profile,
            calculate_behavioral_risk_index,
            build_agent_profiles,
        )

        modules["multiresolution"] = {
            "calculate_action_level_features":
                calculate_action_level_features,

            "calculate_capability_features":
                calculate_capability_features,

            "calculate_resource_features":
                calculate_resource_features,

            "calculate_context_features":
                calculate_context_features,

            "calculate_cross_context_features":
                calculate_cross_context_features,

            "calculate_multi_resolution_profile":
                calculate_multi_resolution_profile,

            "calculate_behavioral_risk_index":
                calculate_behavioral_risk_index,

            "build_agent_profiles":
                build_agent_profiles,
        }

    except Exception as exc:
        modules["multiresolution_error"] = str(exc)

    return modules


MODULES = load_application_modules()


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "selected_agent": None,
    "selected_event": None,

    "day26_results": None,
    "day26_dataset": None,

    "day27_results": None,
    "day27_config": None,

    "experimental_dataset": None,

    "day28_profile": None,
    "day28_events": None,

    "deployment_validation": None,

    "experiment_history": [],
}


for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# SAFE HELPERS
# ============================================================

def safe_call(
    function,
    default=None,
    *args,
    **kwargs,
):
    """
    Safely execute an optional application function.
    """

    if function is None:
        return default

    try:
        return function(
            *args,
            **kwargs,
        )

    except Exception:
        return default


def as_dict(value: Any) -> Dict[str, Any]:
    """
    Convert common model/object/dict structures into a dict.
    """

    if isinstance(value, dict):
        return value

    if hasattr(value, "model_dump"):

        try:
            return value.model_dump()

        except Exception:
            pass

    if hasattr(value, "__dict__"):

        try:
            return dict(value.__dict__)

        except Exception:
            pass

    return {}


def get_field(
    value: Any,
    name: str,
    default: Any = "",
) -> Any:

    if isinstance(value, dict):
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
    value: Any,
    default: float = 0.0,
) -> float:

    try:
        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return default


def dataframe_or_empty(
    rows: Any,
) -> pd.DataFrame:

    if rows is None:
        return pd.DataFrame()

    if isinstance(rows, pd.DataFrame):
        return rows.copy()

    try:
        return pd.DataFrame(rows)

    except Exception:
        return pd.DataFrame()


def download_dataframe(
    dataframe: pd.DataFrame,
    filename: str,
) -> None:

    if dataframe is None or dataframe.empty:
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
    )


def format_percentage(
    value: Any,
) -> str:

    number = safe_number(value)

    if abs(number) <= 1:
        number *= 100

    return f"{number:.2f}%"


def format_score(
    value: Any,
) -> str:

    return f"{safe_number(value):.2f}"


# ============================================================
# PROJECT CONSTRUCTION TIMELINE
# ============================================================

PROJECT_MILESTONES = [
    {
        "range": "Days 1–3",
        "title": "Foundation",
        "description":
            "Initial project structure, security model and core development foundation.",
        "validation":
            "Basic module execution and initial tests.",
    },
    {
        "range": "Days 4–5",
        "title": "Policy and Authorization",
        "description":
            "Agent identity, intent and authorization-oriented security controls.",
        "validation":
            "Authorization and policy tests.",
    },
    {
        "range": "Days 6–10",
        "title": "Security Engine",
        "description":
            "Risk assessment, security decisions and runtime enforcement.",
        "validation":
            "Security engine and decision tests.",
    },
    {
        "range": "Days 11–15",
        "title": "Security Analytics",
        "description":
            "Security monitoring, event analytics and agent activity analysis.",
        "validation":
            "Analytics and behavior tests.",
    },
    {
        "range": "Days 16–20",
        "title": "Security Intelligence",
        "description":
            "Security dashboard, investigation signals and integrated intelligence.",
        "validation":
            "Dashboard and security monitoring tests.",
    },
    {
        "range": "Day 21",
        "title": "Controlled Scenarios",
        "description":
            "Controlled security scenario framework for reproducible testing.",
        "validation":
            "Scenario-generation and scenario-behavior tests.",
    },
    {
        "range": "Days 22–25",
        "title": "Evaluation Framework",
        "description":
            "Experimental datasets and quantitative detector evaluation.",
        "validation":
            "Evaluation metrics and dataset tests.",
    },
    {
        "range": "Day 26",
        "title": "Baseline Comparison",
        "description":
            "Comparison of AegisGuard against a simpler baseline detector.",
        "validation":
            "Comparative performance metrics.",
    },
    {
        "range": "Day 27",
        "title": "Repeated Evaluation",
        "description":
            "Multi-seed repeated experiments for robustness assessment.",
        "validation":
            "Repeated evaluation and consistency tests.",
    },
    {
        "range": "Day 28",
        "title": "Multi-Resolution Behavioral Intelligence",
        "description":
            "Behavior is analyzed across action, capability, resource and context levels.",
        "validation":
            "Multi-resolution behavioral feature tests.",
    },
]


# ============================================================
# LOAD CORE DATA
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
    '<div class="ag-eyebrow">'
    'AUTONOMOUS AGENT SECURITY RESEARCH PLATFORM'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="ag-title">'
    '🛡️ AegisGuard Intelligence SOC'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="ag-subtitle">
    Behavior-aware continuous security intelligence for autonomous AI agents.
    Monitor authorization, risk, behavioral evidence, controlled experiments,
    reproducibility, research progress and deployment readiness from one interface.
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


dashboard_view = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Security Overview",

        "📈 Risk Intelligence",

        "🤖 Agent Intelligence",

        "🧠 Behavioral Analytics",

        "🧬 Day 28 Multi-Resolution",

        "🚨 High-Risk Events",

        "🔎 Security Investigation",

        "🧪 Scenario Laboratory",

        "🧬 Experimental Dataset",

        "📊 Day 24 Evaluation",

        "⚖️ Day 26 Baseline Comparison",

        "🔬 Day 27 Repeated Evaluation",

        "🧪 Statistical Evaluation",

        "📅 Project Construction",

        "🚀 Deployment & Validation",

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
    "Intelligence → Experiments → "
    "Statistical Validation → Research"
)

st.sidebar.divider()

st.sidebar.caption(
    f"Project root: {PROJECT_ROOT}"
)

st.sidebar.caption(
    f"Python: {sys.executable}"
)


# ============================================================
# SECURITY OVERVIEW
# ============================================================

if dashboard_view == "🏠 Security Overview":

    st.header(
        "Security Operations Overview"
    )

    st.caption(
        "Current authorization, risk and behavioral security posture."
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
            format_score(
                risk_summary.get(
                    "average_risk",
                    0,
                )
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

    left, right = st.columns(
        [1, 1]
    )

    with left:

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

            st.dataframe(
                decision_df,
                width="stretch",
                hide_index=True,
            )

        else:

            st.info(
                "No authorization decision data available."
            )

    with right:

        st.subheader(
            "Research Status"
        )

        st.markdown(
            """
            **Current research stage**

            Day 28 — Multi-Resolution Behavioral Intelligence

            **Core direction**

            Continuous authorization supported by
            behavioral evidence across multiple levels
            of context.

            **Validation principle**

            Every new mechanism must be tested against
            the existing baseline and evaluated for
            false-positive and false-negative effects.
            """
        )

    st.divider()

    st.subheader(
        "Current Security Pipeline"
    )

    pipeline = [
        "Identity",
        "Intent",
        "Authorization",
        "Risk",
        "Runtime Monitoring",
        "Behavior",
        "Multi-Resolution Analysis",
        "Continuous Reassessment",
        "Security Response",
        "Investigation",
    ]

    cols = st.columns(5)

    for index, stage in enumerate(pipeline):

        with cols[index % 5]:

            st.markdown(
                f"""
                <div class="ag-card">
                    <div class="ag-card-title">
                        {index + 1}. {stage}
                    </div>
                    <div class="ag-card-text">
                        Runtime security stage
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# RISK INTELLIGENCE
# ============================================================

elif dashboard_view == "📈 Risk Intelligence":

    st.header(
        "Risk Intelligence"
    )

    r1, r2, r3, r4 = st.columns(4)

    with r1:
        st.metric(
            "Average Risk",
            format_score(
                risk_summary.get(
                    "average_risk",
                    0,
                )
            ),
        )

    with r2:
        st.metric(
            "Maximum Risk",
            format_score(
                risk_summary.get(
                    "maximum_risk",
                    0,
                )
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
        "Agent Intelligence"
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
        "Behavioral Analytics"
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
            "Repeated-Denial Records",
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
# DAY 28 — MULTI-RESOLUTION BEHAVIOR
# ============================================================

elif dashboard_view == "🧬 Day 28 Multi-Resolution":

    st.header(
        "Day 28 — Multi-Resolution Behavioral Intelligence"
    )

    st.caption(
        "Experimental research mechanism: behavioral evidence "
        "is evaluated across multiple levels of context."
    )

    multiresolution = MODULES.get(
        "multiresolution",
        {},
    )

    if not multiresolution:

        st.error(
            "Day 28 multi-resolution module is unavailable."
        )

        error = MODULES.get(
            "multiresolution_error"
        )

        if error:
            st.code(
                error
            )

    else:

        st.markdown(
            """
            ### Behavioral hierarchy

            **Action → Capability → Resource → Context → Agent → Cross-Context**

            The purpose of this layer is to detect behavior that may
            appear harmless when evaluated in isolation but becomes
            suspicious when viewed across multiple contexts.

            This is an experimental research mechanism.
            Its weighting and thresholds require validation.
            """
        )

        st.divider()

        input_mode = st.radio(
            "Input source",
            [
                "Existing experimental dataset",
                "Existing high-risk events",
                "Manual event JSON",
            ],
            horizontal=True,
        )

        events_for_analysis: List[Dict[str, Any]] = []

        if input_mode == "Existing experimental dataset":

            dataset = st.session_state.get(
                "experimental_dataset"
            )

            if dataset:

                events_for_analysis = [
                    as_dict(item)
                    for item in dataset
                ]

                st.success(
                    f"Loaded {len(events_for_analysis)} events."
                )

            else:

                st.info(
                    "Generate an experimental dataset first."
                )

        elif input_mode == "Existing high-risk events":

            events_for_analysis = [
                as_dict(item)
                for item in high_risk_events
            ]

            st.info(
                f"Loaded {len(events_for_analysis)} high-risk events."
            )

        else:

            default_event = json.dumps(
                {
                    "agent_id": "agent-demo",
                    "action": "tool.call",
                    "resource": "example-resource",
                    "context": "example-context",
                    "risk_score": 65,
                },
                indent=2,
            )

            raw_json = st.text_area(
                "Paste event JSON",
                value=default_event,
                height=220,
            )

            if st.button(
                "Load JSON Event",
                key="day28_load_json",
            ):

                try:

                    parsed = json.loads(
                        raw_json
                    )

                    if isinstance(
                        parsed,
                        dict,
                    ):

                        events_for_analysis = [
                            parsed
                        ]

                        st.session_state[
                            "day28_events"
                        ] = events_for_analysis

                        st.success(
                            "Event loaded."
                        )

                    elif isinstance(
                        parsed,
                        list,
                    ):

                        events_for_analysis = [
                            as_dict(item)
                            for item in parsed
                        ]

                        st.session_state[
                            "day28_events"
                        ] = events_for_analysis

                        st.success(
                            f"Loaded {len(events_for_analysis)} events."
                        )

                    else:

                        st.error(
                            "JSON must be an object or list of objects."
                        )

                except json.JSONDecodeError as exc:

                    st.error(
                        f"Invalid JSON: {exc}"
                    )

            if not events_for_analysis:

                events_for_analysis = (
                    st.session_state.get(
                        "day28_events"
                    )
                    or []
                )

        if events_for_analysis:

            if st.button(
                "Analyze Multi-Resolution Behavior",
                type="primary",
                key="day28_analyze",
            ):

                try:

                    profile_function = (
                        multiresolution.get(
                            "calculate_multi_resolution_profile"
                        )
                    )

                    risk_function = (
                        multiresolution.get(
                            "calculate_behavioral_risk_index"
                        )
                    )

                    profile = safe_call(
                        profile_function,
                        {},
                        events_for_analysis,
                    )

                    if risk_function:

                        profile[
                            "behavioral_risk_index"
                        ] = safe_call(
                            risk_function,
                            0.0,
                            profile,
                        )

                    st.session_state[
                        "day28_profile"
                    ] = profile

                    st.session_state[
                        "day28_events"
                    ] = events_for_analysis

                    st.success(
                        "Multi-resolution analysis completed."
                    )

                except Exception as exc:

                    st.error(
                        "Day 28 analysis failed."
                    )

                    st.exception(
                        exc
                    )

            profile = st.session_state.get(
                "day28_profile"
            )

            if profile:

                st.divider()

                risk_index = safe_number(
                    profile.get(
                        "behavioral_risk_index",
                        0,
                    )
                )

                c1, c2, c3, c4 = st.columns(4)

                with c1:
                    st.metric(
                        "Events",
                        profile.get(
                            "event_count",
                            0,
                        ),
                    )

                with c2:
                    st.metric(
                        "Behavioral Risk Index",
                        f"{risk_index:.2f}",
                    )

                with c3:
                    st.metric(
                        "Capabilities",
                        profile.get(
                            "capability_level",
                            {},
                        ).get(
                            "capability_count",
                            0,
                        ),
                    )

                with c4:
                    st.metric(
                        "Contexts",
                        profile.get(
                            "context_level",
                            {},
                        ).get(
                            "context_count",
                            0,
                        ),
                    )

                st.divider()

                st.subheader(
                    "Resolution Summary"
                )

                resolution_rows = [
                    {
                        "Resolution":
                            "Action",

                        "Events":
                            profile.get(
                                "action_level",
                                {},
                            ).get(
                                "event_count",
                                0,
                            ),

                        "Signal":
                            "Individual event behavior",
                    },

                    {
                        "Resolution":
                            "Capability",

                        "Events":
                            profile.get(
                                "capability_level",
                                {},
                            ).get(
                                "capability_count",
                                0,
                            ),

                        "Signal":
                            "Capability diversity and risk",
                    },

                    {
                        "Resolution":
                            "Resource",

                        "Events":
                            profile.get(
                                "resource_level",
                                {},
                            ).get(
                                "resource_count",
                                0,
                            ),

                        "Signal":
                            "Resource diversity and risk",
                    },

                    {
                        "Resolution":
                            "Context",

                        "Events":
                            profile.get(
                                "context_level",
                                {},
                            ).get(
                                "context_count",
                                0,
                            ),

                        "Signal":
                            "Execution-context behavior",
                    },

                    {
                        "Resolution":
                            "Cross-Context",

                        "Events":
                            profile.get(
                                "cross_context",
                                {},
                            ).get(
                                "cross_context_activity",
                                0,
                            ),

                        "Signal":
                            "Distributed behavioral pattern",
                    },
                ]

                st.dataframe(
                    pd.DataFrame(
                        resolution_rows
                    ),
                    width="stretch",
                    hide_index=True,
                )

                st.divider()

                st.subheader(
                    "Cross-Context Signals"
                )

                cross_context = profile.get(
                    "cross_context",
                    {},
                )

                entropy_df = pd.DataFrame(
                    {
                        "Signal": [
                            "Context Entropy",
                            "Capability Entropy",
                            "Resource Entropy",
                        ],
                        "Value": [
                            cross_context.get(
                                "context_entropy",
                                0,
                            ),
                            cross_context.get(
                                "capability_entropy",
                                0,
                            ),
                            cross_context.get(
                                "resource_entropy",
                                0,
                            ),
                        ],
                    }
                )

                st.dataframe(
                    entropy_df,
                    width="stretch",
                    hide_index=True,
                )

                st.bar_chart(
                    entropy_df.set_index(
                        "Signal"
                    ),
                    width="stretch",
                )

                st.divider()

                st.subheader(
                    "Research Interpretation"
                )

                st.warning(
                    """
                    The Day 28 Behavioral Risk Index is an exploratory
                    research mechanism. Its current weighting is not
                    evidence of an optimal security model. Thresholds,
                    feature importance and generalization must be tested
                    using ablation studies and repeated experiments.
                    """
                )

                with st.expander(
                    "View complete behavioral profile"
                ):

                    st.json(
                        profile
                    )

        else:

            st.info(
                "Provide or generate events to perform Day 28 analysis."
            )


# ============================================================
# HIGH-RISK EVENTS
# ============================================================

elif dashboard_view == "🚨 High-Risk Events":

    st.header(
        "High-Risk Event Monitor"
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
        "Security Investigation"
    )

    agent_df = dataframe_or_empty(
        agent_activity
    )

    suspicious_df = dataframe_or_empty(
        suspicious_agents
    )

    agent_names: List[str] = []

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

        denial_agent_df = dataframe_or_empty(
            denial_matches
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
        "Controlled Security Scenario Laboratory"
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


# ============================================================
# EXPERIMENTAL DATASET
# ============================================================

elif dashboard_view == "🧬 Experimental Dataset":

    st.header(
        "Experimental Dataset Laboratory"
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
            "Generate Dataset",
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
# DAY 24 EVALUATION
# ============================================================

elif dashboard_view == "📊 Day 24 Evaluation":

    st.header(
        "Day 24 — Quantitative Evaluation"
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
# DAY 26 — BASELINE COMPARISON
# ============================================================

elif dashboard_view == "⚖️ Day 26 Baseline Comparison":

    st.header(
        "Day 26 — Baseline vs AegisGuard"
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
            "Run Day 26 Comparison",
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
# DAY 27 — REPEATED EVALUATION
# ============================================================

elif dashboard_view == "🔬 Day 27 Repeated Evaluation":

    st.header(
        "Day 27 — Repeated Experimental Evaluation"
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

        col1, col2, col3 = st.columns(3)

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
            "Run Day 27 Experiments",
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
                    format_percentage(
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
                Repeated experiments provide robustness evidence,
                but they do not by themselves prove statistical
                significance or real-world generalization.
                """
            )

        else:

            st.info(
                "Run the Day 27 experiment to generate results."
            )


# ============================================================
# STATISTICAL EVALUATION
# ============================================================

elif dashboard_view == "🧪 Statistical Evaluation":

    st.header(
        "Statistical Evaluation"
    )

    statistical = MODULES.get(
        "statistical",
        {},
    )

    if not statistical:

        st.error(
            "Statistical evaluation module is unavailable."
        )

        error = MODULES.get(
            "statistical_error"
        )

        if error:
            st.code(
                error
            )

    else:

        st.markdown(
            """
            Statistical analysis should be used to determine whether
            observed differences between AegisGuard and the baseline
            are consistent and practically meaningful.

            Statistical significance should not be confused with
            security superiority or real-world generalization.
            """
        )

        results = st.session_state.get(
            "day27_results"
        )

        if not results:

            st.info(
                "Run Day 27 repeated evaluation first."
            )

        else:

            st.subheader(
                "Repeated Evaluation Evidence"
            )

            try:

                results_df = dataframe_or_empty(
                    results
                )

                if not results_df.empty:

                    st.dataframe(
                        results_df,
                        width="stretch",
                        hide_index=True,
                    )

            except Exception:

                st.info(
                    "Results are available but could not be rendered as a table."
                )

            st.warning(
                """
                Use the statistical module and its tests as the
                authoritative source for significance, confidence
                intervals and effect sizes. The dashboard does not
                invent statistical conclusions.
                """
            )


# ============================================================
# PROJECT CONSTRUCTION
# ============================================================

elif dashboard_view == "📅 Project Construction":

    st.header(
        "Project Construction Timeline"
    )

    st.caption(
        "A day-by-day view of how AegisGuard evolved from its "
        "security foundation into a research and evaluation platform."
    )

    st.divider()

    for milestone in PROJECT_MILESTONES:

        st.markdown(
            f"""
            <div class="ag-milestone">

                <div class="ag-milestone-day">
                    {milestone["range"]}
                </div>

                <div class="ag-milestone-title">
                    {milestone["title"]}
                </div>

                <div class="ag-card-text">
                    {milestone["description"]}
                </div>

                <div class="ag-card-text">
                    <strong>Validation:</strong>
                    {milestone["validation"]}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    st.subheader(
        "Current Research Position"
    )

    current_day = 28

    progress = current_day / 35

    st.progress(
        min(
            progress,
            1.0,
        )
    )

    st.caption(
        f"Day {current_day} of the current research roadmap"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Completed Milestones",
            current_day,
        )

    with c2:

        st.metric(
            "Current Research Stage",
            "Day 28",
        )

    with c3:

        st.metric(
            "Primary Focus",
            "Behavioral Intelligence",
        )

    st.divider()

    st.subheader(
        "Construction Principle"
    )

    st.info(
        """
        Every new security mechanism should follow the same cycle:

        **Design → Implement → Unit Test → Integrate → Experiment →
        Compare → Repeat → Statistically Evaluate → Document**

        This prevents the project from becoming a collection of
        unvalidated features.
        """
    )


# ============================================================
# DEPLOYMENT & VALIDATION
# ============================================================

elif dashboard_view == "🚀 Deployment & Validation":

    st.header(
        "Deployment & Validation Center"
    )

    st.caption(
        "Runtime checks for the actual development environment, "
        "application modules, project structure and automated tests."
    )

    st.divider()

    # --------------------------------------------------------
    # Environment
    # --------------------------------------------------------

    st.subheader(
        "1. Python Environment"
    )

    python_executable = Path(
        sys.executable
    ).resolve()

    expected_environment = (
        Path("D:/aegisguard-env")
        .resolve()
    )

    environment_ok = (
        expected_environment
        in python_executable.parents
        or
        python_executable.parent.parent
        == expected_environment
    )

    environment_df = pd.DataFrame(
        [
            {
                "Check":
                    "Python executable",

                "Value":
                    str(
                        python_executable
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

    if not environment_ok:

        st.warning(
            """
            The dashboard is not running from D:\\aegisguard-env.

            Recommended environment:

            D:\\aegisguard-env\\Scripts\\Activate.ps1
            """
        )

    else:

        st.success(
            "The dashboard is running from the D: AegisGuard environment."
        )

    st.divider()

    # --------------------------------------------------------
    # Dependencies
    # --------------------------------------------------------

    st.subheader(
        "2. Dependency Health"
    )

    dependency_checks = []

    dependencies = [
        "streamlit",
        "pandas",
        "pytest",
        "scipy",
    ]

    for package_name in dependencies:

        try:

            module = __import__(
                package_name
            )

            version = getattr(
                module,
                "__version__",
                "installed",
            )

            dependency_checks.append(
                {
                    "Package":
                        package_name,

                    "Version":
                        version,

                    "Status":
                        "READY",
                }
            )

        except Exception as exc:

            dependency_checks.append(
                {
                    "Package":
                        package_name,

                    "Version":
                        str(exc),

                    "Status":
                        "ERROR",
                }
            )

    dependency_df = pd.DataFrame(
        dependency_checks
    )

    st.dataframe(
        dependency_df,
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

    module_names = [
        "analytics",
        "behavior",
        "scenarios",
        "comparison",
        "dataset",
        "repeated",
        "statistical",
        "evaluation",
        "multiresolution",
    ]

    module_rows = []

    for module_name in module_names:

        error_key = (
            f"{module_name}_error"
        )

        if module_name in MODULES:

            module_rows.append(
                {
                    "Module":
                        module_name,

                    "Status":
                        "READY",

                    "Details":
                        "Imported successfully",
                }
            )

        else:

            module_rows.append(
                {
                    "Module":
                        module_name,

                    "Status":
                        "ERROR",

                    "Details":
                        MODULES.get(
                            error_key,
                            "Module unavailable",
                        ),
                }
            )

    module_df = pd.DataFrame(
        module_rows
    )

    st.dataframe(
        module_df,
        width="stretch",
        hide_index=True,
    )

    st.divider()

    # --------------------------------------------------------
    # Required project files
    # --------------------------------------------------------

    st.subheader(
        "4. Project Structure"
    )

    required_files = [
        "dashboard.py",

        "app/analytics.py",
        "app/behavior.py",
        "app/attack_scenarios.py",
        "app/comparison.py",
        "app/experimental_dataset.py",
        "app/repeated_evaluation.py",
        "app/statistical_evaluation.py",
        "app/evaluation.py",
        "app/multiresolution_behavior.py",

        "tests/test_analytics.py",
        "tests/test_behavior.py",
        "tests/test_scenarios.py",
        "tests/test_repeated_evaluation.py",
        "tests/test_statistical_evaluation.py",
        "tests/test_multiresolution_behavior.py",
    ]

    file_rows = []

    for relative_path in required_files:

        path = PROJECT_ROOT / relative_path

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

    files_df = pd.DataFrame(
        file_rows
    )

    st.dataframe(
        files_df,
        width="stretch",
        hide_index=True,
    )

    st.divider()

    # --------------------------------------------------------
    # Test suite
    # --------------------------------------------------------

    st.subheader(
        "5. Automated Test Suite"
    )

    st.caption(
        "This executes pytest using the same Python interpreter "
        "that is running the dashboard."
    )

    if st.button(
        "Run Full Test Suite",
        type="primary",
        key="deployment_run_tests",
    ):

        with st.spinner(
            "Running full pytest suite..."
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

                test_output = (
                    completed.stdout
                    + "\n"
                    + completed.stderr
                )

                passed = (
                    completed.returncode == 0
                )

                st.session_state[
                    "deployment_validation"
                ] = {
                    "timestamp":
                        datetime.now().isoformat(),

                    "returncode":
                        completed.returncode,

                    "passed":
                        passed,

                    "output":
                        test_output,
                }

            except subprocess.TimeoutExpired:

                st.session_state[
                    "deployment_validation"
                ] = {
                    "timestamp":
                        datetime.now().isoformat(),

                    "returncode":
                        -1,

                    "passed":
                        False,

                    "output":
                        "Pytest timed out after 300 seconds.",
                }

            except Exception as exc:

                st.session_state[
                    "deployment_validation"
                ] = {
                    "timestamp":
                        datetime.now().isoformat(),

                    "returncode":
                        -1,

                    "passed":
                        False,

                    "output":
                        str(exc),
                }

    validation = st.session_state.get(
        "deployment_validation"
    )

    if validation:

        if validation["passed"]:

            st.success(
                "FULL TEST SUITE PASSED"
            )

        else:

            st.error(
                "FULL TEST SUITE FAILED"
            )

        st.caption(
            f"Validation time: {validation['timestamp']}"
        )

        st.code(
            validation["output"],
            language="text",
        )

    else:

        st.info(
            "Run the test suite to obtain actual validation status."
        )

    st.divider()

    # --------------------------------------------------------
    # Deployment readiness
    # --------------------------------------------------------

    st.subheader(
        "6. Deployment Readiness"

    )

    test_passed = bool(
        validation
        and validation.get(
            "passed",
            False,
        )
    )

    modules_ready = all(
        name in MODULES
        for name in module_names
    )

    required_files_ready = all(
        (
            PROJECT_ROOT / relative_path
        ).exists()
        for relative_path in required_files
    )

    deployment_ready = (
        environment_ok
        and modules_ready
        and required_files_ready
        and test_passed
    )

    readiness_rows = [
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
                if test_passed
                else "NOT VERIFIED",
        },
    ]

    readiness_df = pd.DataFrame(
        readiness_rows
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
            """
            Deployment readiness has NOT been established.

            AegisGuard should not claim deployment readiness until
            the environment, modules, required files and automated
            tests have all been verified.
            """
        )


# ============================================================
# RESEARCH INTERPRETATION
# ============================================================

elif dashboard_view == "📚 Research Interpretation":

    st.header(
        "Research Interpretation"
    )

    st.subheader(
        "Core Research Question"
    )

    st.markdown(
        """
        **Can continuous behavioral risk assessment improve
        security decisions for autonomous AI agents beyond
        simpler authorization or risk-only approaches?**
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
                    "Repeated behavior and denial patterns",

                "Purpose":
                    "Behavioral context",
            },

            {
                "Stage":
                    "Multi-Resolution",

                "Evidence":
                    "Action / capability / resource / context",

                "Purpose":
                    "Cross-resolution behavior",
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
                    "Baseline Comparison",

                "Evidence":
                    "Baseline vs AegisGuard",

                "Purpose":
                    "Comparative evaluation",
            },

            {
                "Stage":
                    "Repeated Evaluation",

                "Evidence":
                    "Multiple random seeds",

                "Purpose":
                    "Robustness assessment",
            },

            {
                "Stage":
                    "Statistical Evaluation",

                "Evidence":
                    "Statistical tests and effect sizes",

                "Purpose":
                    "Research validation",
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
        "Potential Research Contribution"
    )

    st.markdown(
        """
        The current research direction investigates a combination of:

        - continuous authorization
        - runtime behavioral monitoring
        - multi-resolution behavioral features
        - cross-context analysis
        - repeated experimental evaluation
        - baseline comparison
        - statistical validation
        - graduated security response

        These mechanisms should be treated as a research hypothesis
        until supported by controlled experiments and prior-art analysis.
        """
    )

    st.divider()

    st.subheader(
        "What the Project Should NOT Claim Yet"
    )

    limitations = [
        "Universal superiority over existing agent-security systems.",
        "Complete protection against prompt injection.",
        "Zero false positives or false negatives.",
        "Production readiness without deployment testing.",
        "Novelty merely because the implementation combines known mechanisms.",
        "Patentability without professional prior-art analysis.",
        "Real-world generalization from synthetic datasets alone.",
    ]

    for item in limitations:

        st.markdown(
            f"- {item}"
        )


# ============================================================
# SYSTEM STATUS
# ============================================================

elif dashboard_view == "⚙️ System Status":

    st.header(
        "System Status"
    )

    status_rows = []

    module_names = [
        "analytics",
        "behavior",
        "scenarios",
        "comparison",
        "dataset",
        "repeated",
        "statistical",
        "evaluation",
        "multiresolution",
    ]

    for module_name in module_names:

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
        "Environment"
    )

    environment_info = pd.DataFrame(
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
                    "Application",

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
        environment_info,
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
        "day28_profile",
        "deployment_validation",
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
        "Clear Research Session"
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
    <div class="ag-footer">
        🛡️ AegisGuard · Behavior-Aware Security for Autonomous AI Agents
        <br>
        Research Prototype · Controlled Evaluation · Reproducible Validation
    </div>
    """,
    unsafe_allow_html=True,
)