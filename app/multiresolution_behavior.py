from __future__ import annotations

from collections import Counter, defaultdict
from math import log2
from typing import Any, Dict, Iterable, List, Tuple


def _safe_string(value: Any) -> str:
    """Convert a value into a stable string representation."""
    if value is None:
        return "unknown"

    return str(value).strip() or "unknown"


def _event_agent_id(event: Dict[str, Any]) -> str:
    return _safe_string(
        event.get("agent_id")
    )


def _event_capability(event: Dict[str, Any]) -> str:
    """
    Extract the capability/action family.

    Priority:
    1. capability
    2. action
    3. operation
    """
    return _safe_string(
        event.get(
            "capability",
            event.get(
                "action",
                event.get(
                    "operation"
                ),
            ),
        )
    )


def _event_resource(event: Dict[str, Any]) -> str:
    return _safe_string(
        event.get(
            "resource",
            event.get(
                "resource_id",
                event.get(
                    "target"
                ),
            ),
        )
    )


def _event_context(event: Dict[str, Any]) -> str:
    """
    Extract the highest-confidence context available.

    This intentionally remains conservative rather than
    inventing context from unrelated fields.
    """
    return _safe_string(
        event.get(
            "context",
            event.get(
                "session_id",
                event.get(
                    "task_id",
                    "default"
                ),
            ),
        )
    )


def _event_risk(event: Dict[str, Any]) -> float:
    value = event.get(
        "risk_score",
        event.get(
            "risk",
            0.0
        ),
    )

    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return 0.0


def group_events_by_agent(
    events: Iterable[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Group runtime events by agent identity."""

    grouped = defaultdict(list)

    for event in events:
        grouped[
            _event_agent_id(event)
        ].append(event)

    return dict(grouped)


def group_events_by_capability(
    events: Iterable[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Group events by capability/action family."""

    grouped = defaultdict(list)

    for event in events:
        grouped[
            _event_capability(event)
        ].append(event)

    return dict(grouped)


def group_events_by_resource(
    events: Iterable[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Group events by resource."""

    grouped = defaultdict(list)

    for event in events:
        grouped[
            _event_resource(event)
        ].append(event)

    return dict(grouped)


def group_events_by_context(
    events: Iterable[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Group events by execution context."""

    grouped = defaultdict(list)

    for event in events:
        grouped[
            _event_context(event)
        ].append(event)

    return dict(grouped)


def calculate_action_level_features(
    events: Iterable[Dict[str, Any]],
) -> Dict[str, float]:
    """
    Calculate behavior at the individual-action level.
    """

    events = list(events)

    if not events:
        return {
            "event_count": 0,
            "average_risk": 0.0,
            "maximum_risk": 0.0,
            "high_risk_ratio": 0.0,
        }

    risks = [
        _event_risk(event)
        for event in events
    ]

    high_risk = [
        risk
        for risk in risks
        if risk >= 70
    ]

    return {
        "event_count": len(events),
        "average_risk": (
            sum(risks) / len(risks)
        ),
        "maximum_risk": max(risks),
        "high_risk_ratio": (
            len(high_risk)
            / len(events)
        ),
    }


def calculate_capability_features(
    events: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calculate behavioral features at the capability level.
    """

    events = list(events)

    counts = Counter(
        _event_capability(event)
        for event in events
    )

    capability_risks = defaultdict(list)

    for event in events:
        capability_risks[
            _event_capability(event)
        ].append(
            _event_risk(event)
        )

    average_risk = {
        capability: (
            sum(risks) / len(risks)
        )
        for capability, risks
        in capability_risks.items()
        if risks
    }

    return {
        "capability_count":
            len(counts),

        "capability_request_counts":
            dict(counts),

        "capability_average_risk":
            average_risk,

        "dominant_capability":
            (
                counts.most_common(1)[0][0]
                if counts
                else "unknown"
            ),
    }


def calculate_resource_features(
    events: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calculate behavioral features at resource level.
    """

    events = list(events)

    counts = Counter(
        _event_resource(event)
        for event in events
    )

    resource_risks = defaultdict(list)

    for event in events:
        resource_risks[
            _event_resource(event)
        ].append(
            _event_risk(event)
        )

    average_risk = {
        resource: (
            sum(risks) / len(risks)
        )
        for resource, risks
        in resource_risks.items()
        if risks
    }

    return {
        "resource_count":
            len(counts),

        "resource_request_counts":
            dict(counts),

        "resource_average_risk":
            average_risk,
    }


def calculate_context_features(
    events: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calculate behavior at execution-context level.
    """

    events = list(events)

    context_counts = Counter(
        _event_context(event)
        for event in events
    )

    context_risks = defaultdict(list)

    for event in events:
        context_risks[
            _event_context(event)
        ].append(
            _event_risk(event)
        )

    context_average_risk = {
        context: (
            sum(risks) / len(risks)
        )
        for context, risks
        in context_risks.items()
        if risks
    }

    return {
        "context_count":
            len(context_counts),

        "context_request_counts":
            dict(context_counts),

        "context_average_risk":
            context_average_risk,
    }


def calculate_entropy(
    values: Iterable[Any],
) -> float:
    """
    Shannon entropy of a categorical distribution.

    Higher entropy means activity is distributed across
    more categories rather than concentrated in one.
    """

    values = list(values)

    if not values:
        return 0.0

    counts = Counter(values)

    total = len(values)

    entropy = 0.0

    for count in counts.values():

        probability = (
            count / total
        )

        entropy -= (
            probability
            * log2(probability)
        )

    return entropy


def calculate_cross_context_features(
    events: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calculate features describing behavior distributed
    across contexts.

    This is intentionally descriptive at Day 28.
    It does not yet make an attack decision.
    """

    events = list(events)

    if not events:
        return {
            "context_entropy": 0.0,
            "capability_entropy": 0.0,
            "resource_entropy": 0.0,
            "cross_context_activity": 0,
        }

    contexts = [
        _event_context(event)
        for event in events
    ]

    capabilities = [
        _event_capability(event)
        for event in events
    ]

    resources = [
        _event_resource(event)
        for event in events
    ]

    return {
        "context_entropy":
            calculate_entropy(contexts),

        "capability_entropy":
            calculate_entropy(
                capabilities
            ),

        "resource_entropy":
            calculate_entropy(
                resources
            ),

        "cross_context_activity":
            len(set(contexts)),
    }


def calculate_multi_resolution_profile(
    events: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build a complete multi-resolution behavioral profile.

    This combines descriptive features from:

    - action
    - capability
    - resource
    - context
    - cross-context behavior
    """

    events = list(events)

    agents = group_events_by_agent(
        events
    )

    agent_id = (
        next(iter(agents))
        if len(agents) == 1
        else "multiple"
    )

    return {
        "agent_id": agent_id,

        "event_count":
            len(events),

        "action_level":
            calculate_action_level_features(
                events
            ),

        "capability_level":
            calculate_capability_features(
                events
            ),

        "resource_level":
            calculate_resource_features(
                events
            ),

        "context_level":
            calculate_context_features(
                events
            ),

        "cross_context":
            calculate_cross_context_features(
                events
            ),
    }


def calculate_behavioral_risk_index(
    profile: Dict[str, Any],
) -> float:
    """
    Produce a descriptive multi-resolution behavioral
    index between 0 and 100.

    IMPORTANT:
    This is an experimental research feature, not a
    validated security score.

    The weighting is intentionally simple for Day 28.
    Later experiments should evaluate and validate the
    weighting through ablation studies.
    """

    action = profile.get(
        "action_level",
        {}
    )

    cross_context = profile.get(
        "cross_context",
        {}
    )

    average_risk = float(
        action.get(
            "average_risk",
            0.0
        )
    )

    high_risk_ratio = float(
        action.get(
            "high_risk_ratio",
            0.0
        )
    )

    context_entropy = float(
        cross_context.get(
            "context_entropy",
            0.0
        )
    )

    capability_entropy = float(
        cross_context.get(
            "capability_entropy",
            0.0
        )
    )

    # Conservative normalization for exploratory analysis.
    entropy_signal = min(
        100.0,
        (
            context_entropy
            + capability_entropy
        )
        * 20.0,
    )

    score = (
        average_risk * 0.60
        + high_risk_ratio * 100.0 * 0.25
        + entropy_signal * 0.15
    )

    return round(
        max(
            0.0,
            min(
                100.0,
                score,
            ),
        ),
        4,
    )


def build_agent_profiles(
    events: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Generate one multi-resolution profile per agent.
    """

    grouped = group_events_by_agent(
        events
    )

    profiles = []

    for agent_id, agent_events in grouped.items():

        profile = (
            calculate_multi_resolution_profile(
                agent_events
            )
        )

        profile["agent_id"] = agent_id

        profile[
            "behavioral_risk_index"
        ] = calculate_behavioral_risk_index(
            profile
        )

        profiles.append(profile)

    return profiles