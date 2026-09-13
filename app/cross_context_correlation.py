"""
AegisGuard Day 29
Cross-Context Behavioral Correlation

Purpose
-------
Detect behavioral relationships that may not be visible when
individual actions, capabilities, resources, or contexts are
evaluated independently.

This module is intentionally deterministic and dependency-light
so it can be tested independently and integrated with the
multi-resolution behavioral layer later.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple


# ============================================================
# BASIC HELPERS
# ============================================================


def _as_dict(event: Any) -> Dict[str, Any]:
    """Convert a supported event object into a dictionary."""

    if isinstance(event, Mapping):
        return dict(event)

    if hasattr(event, "model_dump"):
        try:
            return dict(event.model_dump())
        except Exception:
            pass

    if hasattr(event, "__dict__"):
        try:
            return dict(event.__dict__)
        except Exception:
            pass

    return {}


def _value(
    event: Mapping[str, Any],
    *names: str,
    default: str = "UNKNOWN",
) -> str:
    """Return the first usable value for a field."""

    for name in names:
        value = event.get(name)

        if value is not None and str(value).strip():
            return str(value)

    return default


def _normalise_events(
    events: Iterable[Any],
) -> List[Dict[str, Any]]:
    """Convert input events into normalized dictionaries."""

    if events is None:
        return []

    normalized: List[Dict[str, Any]] = []

    for event in events:

        item = _as_dict(event)

        if item:
            normalized.append(item)

    return normalized


# ============================================================
# DISTRIBUTION FUNCTIONS
# ============================================================


def _distribution(
    events: Iterable[Any],
    field_names: Sequence[str],
) -> Dict[str, int]:
    """Build a frequency distribution for an event field."""

    normalized = _normalise_events(events)

    counter: Counter[str] = Counter()

    for event in normalized:

        value = _value(
            event,
            *field_names,
        )

        counter[value] += 1

    return dict(counter)


def calculate_context_distribution(
    events: Iterable[Any],
) -> Dict[str, int]:
    """
    Calculate event distribution across execution contexts.
    """

    return _distribution(
        events,
        (
            "context",
            "context_id",
            "execution_context",
            "session_context",
        ),
    )


def calculate_capability_distribution(
    events: Iterable[Any],
) -> Dict[str, int]:
    """
    Calculate event distribution across capabilities.
    """

    return _distribution(
        events,
        (
            "capability",
            "capability_id",
            "tool",
            "tool_name",
        ),
    )


def calculate_resource_distribution(
    events: Iterable[Any],
) -> Dict[str, int]:
    """
    Calculate event distribution across resources.
    """

    return _distribution(
        events,
        (
            "resource",
            "resource_id",
            "target",
            "target_resource",
        ),
    )


def calculate_action_distribution(
    events: Iterable[Any],
) -> Dict[str, int]:
    """
    Calculate event distribution across actions.
    """

    return _distribution(
        events,
        (
            "action",
            "action_type",
            "operation",
            "event_type",
        ),
    )


# ============================================================
# ENTROPY
# ============================================================


def calculate_entropy(
    distribution: Mapping[str, int],
) -> float:
    """
    Calculate Shannon entropy using log2.

    Empty or invalid distributions return 0.0.
    """

    if not distribution:
        return 0.0

    total = sum(
        max(
            int(count),
            0,
        )
        for count in distribution.values()
    )

    if total <= 0:
        return 0.0

    entropy = 0.0

    for count in distribution.values():

        count = max(
            int(count),
            0,
        )

        if count == 0:
            continue

        probability = (
            count / total
        )

        entropy -= (
            probability
            * math.log2(
                probability
            )
        )

    return entropy


def calculate_cross_context_entropy(
    events: Iterable[Any],
) -> Dict[str, float]:
    """
    Calculate entropy for contexts, capabilities and resources.

    Returns a dictionary rather than a single number so that the
    dashboard can inspect each behavioral resolution separately.
    """

    context_distribution = (
        calculate_context_distribution(
            events
        )
    )

    capability_distribution = (
        calculate_capability_distribution(
            events
        )
    )

    resource_distribution = (
        calculate_resource_distribution(
            events
        )
    )

    return {
        "context_entropy":
            calculate_entropy(
                context_distribution
            ),

        "capability_entropy":
            calculate_entropy(
                capability_distribution
            ),

        "resource_entropy":
            calculate_entropy(
                resource_distribution
            ),
    }


# ============================================================
# NORMALIZED ENTROPY
# ============================================================


def _normalized_entropy(
    distribution: Mapping[str, int],
) -> float:
    """
    Normalize entropy to approximately [0, 1].

    A single category produces 0.
    A uniform distribution produces approximately 1.
    """

    if not distribution:
        return 0.0

    active_categories = sum(
        1
        for value in distribution.values()
        if int(value) > 0
    )

    if active_categories <= 1:
        return 0.0

    entropy = calculate_entropy(
        distribution
    )

    maximum_entropy = math.log2(
        active_categories
    )

    if maximum_entropy <= 0:
        return 0.0

    return min(
        entropy / maximum_entropy,
        1.0,
    )


# ============================================================
# CONTEXT-CAPABILITY RELATIONSHIPS
# ============================================================


def calculate_context_capability_matrix(
    events: Iterable[Any],
) -> Dict[str, Dict[str, int]]:
    """
    Build a context -> capability frequency matrix.

    Example:

        {
            "context-a": {
                "read": 3,
                "search": 2
            },
            "context-b": {
                "api_call": 4
            }
        }
    """

    normalized = _normalise_events(
        events
    )

    matrix: Dict[
        str,
        Dict[str, int]
    ] = defaultdict(
        lambda: defaultdict(int)
    )

    for event in normalized:

        context = _value(
            event,
            "context",
            "context_id",
            "execution_context",
            "session_context",
        )

        capability = _value(
            event,
            "capability",
            "capability_id",
            "tool",
            "tool_name",
        )

        matrix[
            context
        ][
            capability
        ] += 1

    return {
        context: dict(
            capabilities
        )
        for context, capabilities
        in matrix.items()
    }


# ============================================================
# CONTEXT-RESOURCE RELATIONSHIPS
# ============================================================


def calculate_context_resource_matrix(
    events: Iterable[Any],
) -> Dict[str, Dict[str, int]]:
    """
    Build a context -> resource frequency matrix.
    """

    normalized = _normalise_events(
        events
    )

    matrix: Dict[
        str,
        Dict[str, int]
    ] = defaultdict(
        lambda: defaultdict(int)
    )

    for event in normalized:

        context = _value(
            event,
            "context",
            "context_id",
            "execution_context",
            "session_context",
        )

        resource = _value(
            event,
            "resource",
            "resource_id",
            "target",
            "target_resource",
        )

        matrix[
            context
        ][
            resource
        ] += 1

    return {
        context: dict(
            resources
        )
        for context, resources
        in matrix.items()
    }


# ============================================================
# CROSS-CONTEXT CORRELATION
# ============================================================


def _pair_key(
    first: str,
    second: str,
) -> Tuple[str, str]:

    if first <= second:
        return first, second

    return second, first


def calculate_context_correlations(
    events: Iterable[Any],
) -> Dict[str, Any]:
    """
    Calculate relationships between contexts.

    A relationship exists when two contexts are associated with
    the same capability or resource.

    This is not causal inference. It is behavioral co-occurrence.
    """

    normalized = _normalise_events(
        events
    )

    context_capabilities: Dict[
        str,
        set
    ] = defaultdict(set)

    context_resources: Dict[
        str,
        set
    ] = defaultdict(set)

    for event in normalized:

        context = _value(
            event,
            "context",
            "context_id",
            "execution_context",
            "session_context",
        )

        capability = _value(
            event,
            "capability",
            "capability_id",
            "tool",
            "tool_name",
        )

        resource = _value(
            event,
            "resource",
            "resource_id",
            "target",
            "target_resource",
        )

        context_capabilities[
            context
        ].add(
            capability
        )

        context_resources[
            context
        ].add(
            resource
        )

    contexts = sorted(
        set(
            context_capabilities.keys()
        )
        |
        set(
            context_resources.keys()
        )
    )

    correlations: List[Dict[str, Any]] = []

    for index, first_context in enumerate(
        contexts
    ):

        for second_context in contexts[
            index + 1:
        ]:

            shared_capabilities = (
                context_capabilities[
                    first_context
                ]
                &
                context_capabilities[
                    second_context
                ]
            )

            shared_resources = (
                context_resources[
                    first_context
                ]
                &
                context_resources[
                    second_context
                ]
            )

            capability_union = (
                context_capabilities[
                    first_context
                ]
                |
                context_capabilities[
                    second_context
                ]
            )

            resource_union = (
                context_resources[
                    first_context
                ]
                |
                context_resources[
                    second_context
                ]
            )

            capability_similarity = (
                len(
                    shared_capabilities
                )
                /
                len(
                    capability_union
                )
                if capability_union
                else 0.0
            )

            resource_similarity = (
                len(
                    shared_resources
                )
                /
                len(
                    resource_union
                )
                if resource_union
                else 0.0
            )

            correlation_score = (
                capability_similarity
                + resource_similarity
            ) / 2.0

            if correlation_score > 0:

                correlations.append(
                    {
                        "context_a":
                            first_context,

                        "context_b":
                            second_context,

                        "shared_capabilities":
                            sorted(
                                shared_capabilities
                            ),

                        "shared_resources":
                            sorted(
                                shared_resources
                            ),

                        "capability_similarity":
                            capability_similarity,

                        "resource_similarity":
                            resource_similarity,

                        "correlation_score":
                            correlation_score,
                    }
                )

    correlations.sort(
        key=lambda item:
            item[
                "correlation_score"
            ],
        reverse=True,
    )

    return {
        "context_count":
            len(contexts),

        "correlated_pairs":
            len(correlations),

        "relationships":
            correlations,
    }


# ============================================================
# DIVERSITY SIGNAL
# ============================================================


def calculate_behavioral_diversity(
    events: Iterable[Any],
) -> Dict[str, float]:
    """
    Calculate normalized behavioral diversity.

    Higher values indicate broader distribution across contexts,
    capabilities and resources.
    """

    context_distribution = (
        calculate_context_distribution(
            events
        )
    )

    capability_distribution = (
        calculate_capability_distribution(
            events
        )
    )

    resource_distribution = (
        calculate_resource_distribution(
            events
        )
    )

    return {
        "context_diversity":
            _normalized_entropy(
                context_distribution
            ),

        "capability_diversity":
            _normalized_entropy(
                capability_distribution
            ),

        "resource_diversity":
            _normalized_entropy(
                resource_distribution
            ),
    }


# ============================================================
# CROSS-CONTEXT RISK
# ============================================================


def calculate_cross_context_risk(
    events: Iterable[Any],
) -> float:
    """
    Calculate an experimental cross-context risk score.

    Score range:
        0–100

    Components:
        - context diversity
        - capability diversity
        - resource diversity
        - context correlation

    This is a research score, not a production security verdict.
    """

    normalized = _normalise_events(
        events
    )

    if not normalized:
        return 0.0

    diversity = (
        calculate_behavioral_diversity(
            normalized
        )
    )

    correlations = (
        calculate_context_correlations(
            normalized
        )
    )

    relationship_scores = [
        safe_score(
            item.get(
                "correlation_score",
                0.0,
            )
        )
        for item in correlations[
            "relationships"
        ]
    ]

    if relationship_scores:

        correlation_signal = (
            sum(
                relationship_scores
            )
            /
            len(
                relationship_scores
            )
        )

    else:

        correlation_signal = 0.0

    diversity_signal = (
        0.4
        * diversity[
            "context_diversity"
        ]
        +
        0.3
        * diversity[
            "capability_diversity"
        ]
        +
        0.3
        * diversity[
            "resource_diversity"
        ]
    )

    combined_signal = (
        0.65
        * diversity_signal
        +
        0.35
        * correlation_signal
    )

    return round(
        min(
            max(
                combined_signal
                * 100.0,
                0.0,
            ),
            100.0,
        ),
        6,
    )


def safe_score(
    value: Any,
) -> float:

    try:

        return min(
            max(
                float(value),
                0.0,
            ),
            1.0,
        )

    except (
        TypeError,
        ValueError,
    ):

        return 0.0


# ============================================================
# COMPLETE PROFILE
# ============================================================


def build_cross_context_profile(
    events: Iterable[Any],
) -> Dict[str, Any]:
    """
    Build the complete Day 29 cross-context behavioral profile.
    """

    normalized = _normalise_events(
        events
    )

    entropy = (
        calculate_cross_context_entropy(
            normalized
        )
    )

    diversity = (
        calculate_behavioral_diversity(
            normalized
        )
    )

    correlations = (
        calculate_context_correlations(
            normalized
        )
    )

    context_capability_matrix = (
        calculate_context_capability_matrix(
            normalized
        )
    )

    context_resource_matrix = (
        calculate_context_resource_matrix(
            normalized
        )
    )

    risk = (
        calculate_cross_context_risk(
            normalized
        )
    )

    return {
        "event_count":
            len(normalized),

        "context_distribution":
            calculate_context_distribution(
                normalized
            ),

        "capability_distribution":
            calculate_capability_distribution(
                normalized
            ),

        "resource_distribution":
            calculate_resource_distribution(
                normalized
            ),

        "action_distribution":
            calculate_action_distribution(
                normalized
            ),

        "entropy":
            entropy,

        "diversity":
            diversity,

        "correlations":
            correlations,

        "context_capability_matrix":
            context_capability_matrix,

        "context_resource_matrix":
            context_resource_matrix,

        "cross_context_risk":
            risk,
    }


# ============================================================
# AGENT-LEVEL PROFILES
# ============================================================


def build_agent_profiles(
    events: Iterable[Any],
) -> Dict[str, Dict[str, Any]]:
    """
    Build one cross-context profile per agent.

    Events without an agent identifier are grouped under
    'UNKNOWN_AGENT'.
    """

    normalized = _normalise_events(
        events
    )

    grouped: Dict[
        str,
        List[Dict[str, Any]]
    ] = defaultdict(list)

    for event in normalized:

        agent_id = _value(
            event,
            "agent_id",
            "agent",
            "agent_identifier",
        )

        grouped[
            agent_id
        ].append(
            event
        )

    return {
        agent_id:
            build_cross_context_profile(
                agent_events
            )
        for agent_id, agent_events
        in grouped.items()
    }


# ============================================================
# CLASSIFICATION
# ============================================================


def classify_cross_context_risk(
    score: float,
    low_threshold: float = 30.0,
    high_threshold: float = 70.0,
) -> str:
    """
    Convert the experimental score into a descriptive category.

    LOW       < low_threshold
    ELEVATED  < high_threshold
    HIGH      >= high_threshold
    """

    score = float(score)

    if score < low_threshold:
        return "LOW"

    if score < high_threshold:
        return "ELEVATED"

    return "HIGH"


# ============================================================
# RESEARCH SUMMARY
# ============================================================


def build_research_summary(
    events: Iterable[Any],
) -> Dict[str, Any]:
    """
    Produce a compact summary suitable for dashboard display.
    """

    profile = build_cross_context_profile(
        events
    )

    score = profile[
        "cross_context_risk"
    ]

    classification = (
        classify_cross_context_risk(
            score
        )
    )

    correlations = profile[
        "correlations"
    ]

    return {
        "event_count":
            profile[
                "event_count"
            ],

        "context_count":
            correlations[
                "context_count"
            ],

        "correlated_pairs":
            correlations[
                "correlated_pairs"
            ],

        "cross_context_risk":
            score,

        "risk_class":
            classification,

        "context_entropy":
            profile[
                "entropy"
            ][
                "context_entropy"
            ],

        "capability_entropy":
            profile[
                "entropy"
            ][
                "capability_entropy"
            ],

        "resource_entropy":
            profile[
                "entropy"
            ][
                "resource_entropy"
            ],

        "context_diversity":
            profile[
                "diversity"
            ][
                "context_diversity"
            ],

        "capability_diversity":
            profile[
                "diversity"
            ][
                "capability_diversity"
            ],

        "resource_diversity":
            profile[
                "diversity"
            ][
                "resource_diversity"
            ],
    }


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "calculate_context_distribution",
    "calculate_capability_distribution",
    "calculate_resource_distribution",
    "calculate_action_distribution",
    "calculate_entropy",
    "calculate_cross_context_entropy",
    "calculate_context_capability_matrix",
    "calculate_context_resource_matrix",
    "calculate_context_correlations",
    "calculate_behavioral_diversity",
    "calculate_cross_context_risk",
    "build_cross_context_profile",
    "build_agent_profiles",
    "classify_cross_context_risk",
    "build_research_summary",
]