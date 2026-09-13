from typing import Any

from app.features import (
    get_behavioral_features,
)


# ============================================================
# ANOMALY CONFIGURATION
# ============================================================

ANOMALY_FEATURES = [
    "denial_rate",
    "average_risk",
    "maximum_risk",
    "high_risk_requests",
    "critical_requests",
    "action_diversity",
    "resource_diversity",
    "task_diversity",
]


# ============================================================
# THRESHOLDS
# ============================================================

LOW_THRESHOLD = 0.75
MEDIUM_THRESHOLD = 1.50
HIGH_THRESHOLD = 2.50


# ============================================================
# SAFE STATISTICAL HELPERS
# ============================================================

def _mean(values: list[float]) -> float:

    if not values:
        return 0.0

    return sum(values) / len(values)


def _standard_deviation(
    values: list[float],
    mean: float,
) -> float:

    if len(values) < 2:
        return 0.0

    variance = sum(
        (value - mean) ** 2
        for value in values
    ) / len(values)

    return variance ** 0.5


def _z_score(
    value: float,
    mean: float,
    standard_deviation: float,
) -> float:

    if standard_deviation == 0:
        return 0.0

    return (
        value - mean
    ) / standard_deviation


# ============================================================
# ANOMALY SEVERITY
# ============================================================

def _severity_from_score(
    score: float,
) -> str:

    if score >= HIGH_THRESHOLD:
        return "HIGH"

    if score >= MEDIUM_THRESHOLD:
        return "MEDIUM"

    if score >= LOW_THRESHOLD:
        return "LOW"

    return "NORMAL"


# ============================================================
# FEATURE BASELINE
# ============================================================

def get_behavioral_baseline() -> dict[str, dict[str, float]]:

    features = get_behavioral_features()

    baseline = {}

    for feature_name in ANOMALY_FEATURES:

        values = [
            float(
                row.get(
                    feature_name,
                    0,
                )
                or 0
            )
            for row in features
        ]

        mean = _mean(values)

        standard_deviation = (
            _standard_deviation(
                values,
                mean,
            )
        )

        baseline[feature_name] = {
            "mean": round(
                mean,
                6,
            ),
            "standard_deviation": round(
                standard_deviation,
                6,
            ),
        }

    return baseline


# ============================================================
# AGENT ANOMALY ANALYSIS
# ============================================================

def get_behavioral_anomalies() -> list[dict[str, Any]]:

    features = get_behavioral_features()

    if not features:
        return []

    baseline = get_behavioral_baseline()

    results = []

    for agent in features:

        feature_scores = {}

        for feature_name in ANOMALY_FEATURES:

            value = float(
                agent.get(
                    feature_name,
                    0,
                )
                or 0
            )

            feature_baseline = baseline[
                feature_name
            ]

            z_score = abs(
                _z_score(
                    value,
                    feature_baseline["mean"],
                    feature_baseline[
                        "standard_deviation"
                    ],
                )
            )

            feature_scores[
                feature_name
            ] = round(
                z_score,
                4,
            )

        if feature_scores:

            anomaly_score = (
                sum(
                    feature_scores.values()
                )
                /
                len(feature_scores)
            )

        else:

            anomaly_score = 0.0

        severity = (
            _severity_from_score(
                anomaly_score
            )
        )

        anomalous_features = [
            feature_name
            for feature_name, score
            in feature_scores.items()
            if score >= LOW_THRESHOLD
        ]

        results.append(
            {
                "agent_id": agent[
                    "agent_id"
                ],
                "anomaly_score": round(
                    anomaly_score,
                    4,
                ),
                "anomaly_severity": severity,
                "anomalous_features": (
                    anomalous_features
                ),
                "feature_scores": (
                    feature_scores
                ),
                "denial_rate": agent.get(
                    "denial_rate",
                    0,
                ),
                "average_risk": agent.get(
                    "average_risk",
                    0,
                ),
                "maximum_risk": agent.get(
                    "maximum_risk",
                    0,
                ),
                "critical_requests": agent.get(
                    "critical_requests",
                    0,
                ),
                "total_requests": agent.get(
                    "total_requests",
                    0,
                ),
            }
        )

    results.sort(
        key=lambda item: item[
            "anomaly_score"
        ],
        reverse=True,
    )

    return results


# ============================================================
# SINGLE AGENT ANALYSIS
# ============================================================

def get_agent_anomaly(
    agent_id: str,
) -> dict[str, Any] | None:

    if not agent_id:

        raise ValueError(
            "agent_id cannot be empty"
        )

    anomalies = (
        get_behavioral_anomalies()
    )

    for anomaly in anomalies:

        if anomaly[
            "agent_id"
        ] == agent_id:

            return anomaly

    return None


# ============================================================
# ANOMALY SUMMARY
# ============================================================

def get_anomaly_summary() -> dict[str, int]:

    anomalies = (
        get_behavioral_anomalies()
    )

    return {
        "agents_analyzed": len(
            anomalies
        ),
        "high_anomaly_agents": sum(
            1
            for item in anomalies
            if item[
                "anomaly_severity"
            ]
            == "HIGH"
        ),
        "medium_anomaly_agents": sum(
            1
            for item in anomalies
            if item[
                "anomaly_severity"
            ]
            == "MEDIUM"
        ),
        "low_anomaly_agents": sum(
            1
            for item in anomalies
            if item[
                "anomaly_severity"
            ]
            == "LOW"
        ),
        "normal_agents": sum(
            1
            for item in anomalies
            if item[
                "anomaly_severity"
            ]
            == "NORMAL"
        ),
    }